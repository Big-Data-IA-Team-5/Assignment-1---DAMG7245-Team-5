#!/usr/bin/env python3
"""
Lab 2: Hybrid Table Extraction (Camelot + pdfplumber)

- Camelot lattice: best for ruled/bordered tables
- Camelot stream: best for borderless/financial
- pdfplumber: general-purpose fallback

Outputs (under <OUT>/tables):
  - <basename>_<method>_p<page>_t<table>.csv
  - _comprehensive_index.csv
  - _comprehensive_analysis.json
"""

from __future__ import annotations

import argparse
import json
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Optional deps guarded (so script can run even if one engine is missing)
try:
    import camelot  # type: ignore
except Exception:  # pragma: no cover
    camelot = None

try:
    import pdfplumber  # type: ignore
except Exception:  # pragma: no cover
    pdfplumber = None


# ---------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------
LOG = logging.getLogger("lab2.tables")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - [%(levelname)s] - %(message)s",
    )


# ---------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------
@dataclass
class TableResult:
    page: int
    table_num: int
    method: str  # 'camelot_lattice' | 'camelot_stream' | 'pdfplumber'
    df: pd.DataFrame
    shape: Tuple[int, int]
    accuracy: Optional[float] = None  # camelot only
    content_quality: Optional[float] = None
    financial_score: Optional[int] = None


# ---------------------------------------------------------------------
# Utilities (cleaning/heuristics)
# ---------------------------------------------------------------------
_MISSING = {"<NA>", "nan", "NaN", "None", "", " ", "—", "-", "null", "NULL"}


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """Basic cleanup: normalize empties and drop all-empty rows/cols."""
    if df is None or df.empty:
        return df
    out = df.copy()
    out = out.applymap(lambda x: "" if (isinstance(x, str) and x.strip() in _MISSING) else x)
    out.replace(list(_MISSING), "", inplace=True)
    out.dropna(how="all", inplace=True)
    out.dropna(axis=1, how="all", inplace=True)
    return out


_FINANCIAL_KEYWORDS_HIGH = {
    "revenue", "income", "assets", "liabilities", "equity", "earnings", "profit", "loss", "cash flow"
}
_FINANCIAL_KEYWORDS_MED = {
    "total", "million", "billion", "thousand", "cost", "expense", "operating", "net", "cash", "sales"
}


def financial_score(df: pd.DataFrame) -> int:
    """Weighted keyword/pattern score for financial-ish tables."""
    if df is None or df.empty:
        return 0
    text = df.to_string().lower()
    score = sum(3 for k in _FINANCIAL_KEYWORDS_HIGH if k in text)
    score += sum(2 for k in _FINANCIAL_KEYWORDS_MED if k in text)
    score += text.count("$") + text.count("%")
    # numeric patterns
    for pat in (r"\$\s*[\d,]+", r"\(\s*[\d,]+\s*\)", r"[\d,]+\s*%", r"[\d,]+\.\d+"):
        if re.search(pat, text):
            score += 1
    # structural hints (years in headers, currency col)
    if any(re.search(r"20\d{2}", str(c)) for c in df.columns):
        score += 2
    for col in df.columns:
        sample = " ".join(map(str, df[col].dropna().head(5)))
        if "$" in sample or "%" in sample:
            score += 1
    return score


def content_quality(df: pd.DataFrame) -> float:
    """Simple content density/structure score in [0,1]."""
    if df is None or df.empty or df.size == 0:
        return 0.0
    total = int(df.size)
    meaningful = 0
    structured = 0
    for _, col in df.items():
        for cell in col:
            s = str(cell).strip()
            if s and s.lower() not in {"nan", "none"}:
                meaningful += 1
                if re.search(r"\d", s):
                    structured += 1
    base = meaningful / total
    bonus = min(structured / total, 0.25)
    return min(base + bonus, 1.0)


def safe_headers_and_frame(table_data: List[List[str]]) -> Optional[pd.DataFrame]:
    """Create a DataFrame from list-of-lists with header detection."""
    if not table_data:
        return None
    first_row = table_data[0] or []
    def _is_header_cell(x: str) -> bool:
        x = str(x or "").strip()
        return bool(x and not re.match(r"^[\d,.\$\(\)\-\s%]+$", x))
    header_ratio = sum(_is_header_cell(c) for c in first_row) / max(1, len(first_row))
    if header_ratio >= 0.5 and len(table_data) > 1:
        headers = [str(c).strip() if c else f"Column_{i+1}" for i, c in enumerate(first_row)]
        rows = table_data[1:]
    else:
        max_cols = max(len(r) for r in table_data if r)
        headers = [f"Column_{i+1}" for i in range(max_cols)]
        rows = [list(r) + [""] * (max_cols - len(r)) for r in table_data]
    if not rows:
        rows = [first_row]
    try:
        df = pd.DataFrame(rows, columns=headers)
        return clean_dataframe(df)
    except Exception:
        return None


# ---------------------------------------------------------------------
# Extractors
# ---------------------------------------------------------------------
def camelot_lattice(pdf_path: Path) -> List[TableResult]:
    results: List[TableResult] = []
    if camelot is None:
        LOG.warning("Camelot unavailable; skipping lattice.")
        return results
    try:
        LOG.info("Camelot (lattice): scanning all pages…")
        tables = camelot.read_pdf(str(pdf_path), flavor="lattice", pages="all")
        LOG.info("Camelot (lattice): %d tables", len(tables))
        for i, t in enumerate(tables, start=1):
            df = clean_dataframe(t.df)
            if df is None or df.empty:
                continue
            res = TableResult(
                page=int(t.page),
                table_num=i,
                method="camelot_lattice",
                df=df,
                shape=df.shape,
                accuracy=float(getattr(t, "accuracy", 0.0)),
                content_quality=content_quality(df),
                financial_score=financial_score(df),
            )
            results.append(res)
    except Exception as e:
        LOG.warning("Camelot lattice error: %s", e)
    return results


def camelot_stream(pdf_path: Path) -> List[TableResult]:
    results: List[TableResult] = []
    if camelot is None:
        LOG.warning("Camelot unavailable; skipping stream.")
        return results
    try:
        LOG.info("Camelot (stream): scanning all pages…")
        tables = camelot.read_pdf(
            str(pdf_path),
            flavor="stream",
            pages="all",
            edge_tol=50,
            row_tol=2,
            column_tol=0,
            split_text=True,
            flag_size=True,
        )
        LOG.info("Camelot (stream): %d tables", len(tables))
        for i, t in enumerate(tables, start=1):
            df = clean_dataframe(t.df)
            if df is None or df.empty:
                continue
            res = TableResult(
                page=int(t.page),
                table_num=i,
                method="camelot_stream",
                df=df,
                shape=df.shape,
                accuracy=float(getattr(t, "accuracy", 0.0)),
                content_quality=content_quality(df),
                financial_score=financial_score(df),
            )
            results.append(res)
    except Exception as e:
        LOG.warning("Camelot stream error: %s", e)
    return results


def plumber_all_pages(pdf_path: Path) -> List[TableResult]:
    results: List[TableResult] = []
    if pdfplumber is None:
        LOG.warning("pdfplumber unavailable; skipping pdfplumber.")
        return results
    try:
        with pdfplumber.open(pdf_path) as pdf:
            LOG.info("pdfplumber: processing %d pages…", len(pdf.pages))
            kept_on_page = 0
            for p_idx, page in enumerate(pdf.pages, start=1):
                try:
                    raw_tables = page.extract_tables() or []
                except Exception as e:
                    LOG.debug("pdfplumber page %d extract_tables error: %s", p_idx, e)
                    raw_tables = []
                page_kept = 0
                for i, table_data in enumerate(raw_tables, start=1):
                    if not table_data or len(table_data) == 0:
                        continue
                    df = safe_headers_and_frame(table_data)
                    if df is None or df.empty:
                        continue
                    q = content_quality(df)
                    # modest threshold; early pages in financial docs can be header-dense
                    min_q = 0.2 if p_idx <= 20 else 0.35
                    if q < min_q:
                        continue
                    result = TableResult(
                        page=p_idx,
                        table_num=page_kept + 1,
                        method="pdfplumber",
                        df=df,
                        shape=df.shape,
                        content_quality=q,
                        financial_score=financial_score(df),
                    )
                    results.append(result)
                    page_kept += 1
                kept_on_page += page_kept
            LOG.info("pdfplumber: kept %d tables", kept_on_page)
    except Exception as e:
        LOG.warning("pdfplumber error: %s", e)
    return results


# ---------------------------------------------------------------------
# Merge & ranking
# ---------------------------------------------------------------------
def _content_sig(df: pd.DataFrame, max_chars: int = 400) -> str:
    """Short text signature to compare similarity."""
    return df.to_string()[:max_chars].lower().strip()


def dedupe_tables(tables: List[TableResult]) -> List[TableResult]:
    """Deduplicate by (page, shape, content signature) with tolerance."""
    unique: List[TableResult] = []
    seen: Dict[Tuple[int, Tuple[int, int], str], TableResult] = {}
    for t in tables:
        sig = (t.page, t.shape, _content_sig(t.df))
        # If exact seen, keep the higher-quality variant
        if sig in seen:
            prev = seen[sig]
            prev_score = (prev.content_quality or 0) + (prev.accuracy or 0) / 100.0
            curr_score = (t.content_quality or 0) + (t.accuracy or 0) / 100.0
            if curr_score > prev_score:
                seen[sig] = t
        else:
            seen[sig] = t
    unique.extend(seen.values())
    # Stable sort by page then by a composite score
    def score(x: TableResult) -> float:
        return (x.content_quality or 0) + (x.accuracy or 0) / 100.0 + min((x.shape[0] * x.shape[1]) / 150.0, 0.25)
    unique.sort(key=lambda x: (x.page, -score(x)))
    return unique


def choose_preferred_method(
    lattice: List[TableResult], stream: List[TableResult], plumber: List[TableResult]
) -> Dict[str, str]:
    # Simple scoring: count + avg accuracy + avg quality
    def agg(lst: List[TableResult]) -> Tuple[int, float, float]:
        if not lst:
            return (0, 0.0, 0.0)
        acc = float(np.mean([t.accuracy for t in lst if t.accuracy is not None])) if any(
            t.accuracy is not None for t in lst
        ) else 0.0
        qual = float(np.mean([t.content_quality or 0 for t in lst]))
        return (len(lst), acc, qual)

    l_cnt, l_acc, l_q = agg(lattice)
    s_cnt, s_acc, s_q = agg(stream)
    p_cnt, _, p_q = agg(plumber)

    scores = {
        "camelot_lattice": l_cnt + l_acc + l_q,
        "camelot_stream": s_cnt + s_acc + s_q + 0.2,  # slight bonus for borderless handling
        "pdfplumber": p_cnt + p_q * 1.2,  # slight quality weight
    }
    method = max(scores.items(), key=lambda kv: kv[1])[0]
    reasons = {
        "camelot_lattice": "Higher accuracy on bordered/ruling-line tables.",
        "camelot_stream": "Better performance on borderless/financial layouts.",
        "pdfplumber": "Most consistent general-purpose extraction across pages.",
    }
    return {"method": method, "reason": reasons[method]}


# ---------------------------------------------------------------------
# Save outputs
# ---------------------------------------------------------------------
def save_results(
    tables_dir: Path,
    base_name: str,
    lattice: List[TableResult],
    stream: List[TableResult],
    plumber: List[TableResult],
    merged_unique: List[TableResult],
) -> Tuple[int, Path, Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    saved = 0
    index_rows = []

    def _save_group(group: List[TableResult]):
        nonlocal saved
        for t in group:
            fname = f"{base_name}_{t.method}_p{t.page}_t{t.table_num}.csv"
            path = tables_dir / fname
            try:
                t.df.to_csv(path, index=False, encoding="utf-8")
                saved += 1
                index_rows.append(
                    {
                        "filename": fname,
                        "method": t.method,
                        "page": t.page,
                        "rows": t.shape[0],
                        "cols": t.shape[1],
                        "accuracy": round(t.accuracy or 0.0, 2) if t.accuracy is not None else "",
                        "content_quality": round(t.content_quality or 0.0, 3),
                        "financial_score": t.financial_score or 0,
                    }
                )
            except Exception as e:
                LOG.warning("Failed to save %s: %s", path, e)

    # Save the merged unique set (final curated outputs)
    _save_group(merged_unique)

    # Write index
    index_path = tables_dir / "_comprehensive_index.csv"
    pd.DataFrame(index_rows).sort_values(["page", "method", "filename"]).to_csv(index_path, index=False)

    # Analysis
    analysis = {
        "summary": {
            "total_tables_saved": saved,
            "pages_with_tables": sorted({t.page for t in merged_unique}),
            "methods_used": sorted({t.method for t in merged_unique}),
        },
        "methods_comparison": {
            "camelot_lattice": {
                "tables_found": len(lattice),
                "avg_accuracy": round(float(np.mean([t.accuracy for t in lattice if t.accuracy is not None])) if lattice else 0.0, 2),
                "avg_quality": round(float(np.mean([t.content_quality or 0 for t in lattice])) if lattice else 0.0, 3),
                "pages": sorted({t.page for t in lattice}),
            },
            "camelot_stream": {
                "tables_found": len(stream),
                "avg_accuracy": round(float(np.mean([t.accuracy for t in stream if t.accuracy is not None])) if stream else 0.0, 2),
                "avg_quality": round(float(np.mean([t.content_quality or 0 for t in stream])) if stream else 0.0, 3),
                "pages": sorted({t.page for t in stream}),
            },
            "pdfplumber": {
                "tables_found": len(plumber),
                "avg_quality": round(float(np.mean([t.content_quality or 0 for t in plumber])) if plumber else 0.0, 3),
                "pages": sorted({t.page for t in plumber}),
            },
        },
        "preferred_method": choose_preferred_method(lattice, stream, plumber),
    }
    analysis_path = tables_dir / "_comprehensive_analysis.json"
    analysis_path.write_text(json.dumps(analysis, indent=2), encoding="utf-8")

    LOG.info("Saved %d CSVs", saved)
    LOG.info("Index: %s", index_path)
    LOG.info("Analysis: %s", analysis_path)

    return saved, index_path, analysis_path


# ---------------------------------------------------------------------
# Main orchestration
# ---------------------------------------------------------------------
def extract_tables_assignment_hybrid(pdf_path: Path, output_dir: Path, use_hybrid: bool) -> Dict:
    base_name = pdf_path.stem
    tables_dir = output_dir / "tables"
    LOG.info("Processing: %s", pdf_path.name)
    LOG.info("Output dir: %s", tables_dir)

    # Run extractors
    lattice = camelot_lattice(pdf_path)
    stream = camelot_stream(pdf_path)
    plumber = plumber_all_pages(pdf_path)

    # Merge & dedupe
    merged_unique = dedupe_tables(lattice + stream + plumber)

    # If --hybrid flag set, we already used multiple methods; nothing else needed.
    saved, index_path, analysis_path = save_results(
        tables_dir, base_name, lattice, stream, plumber, merged_unique
    )

    return {
        "total_tables": len(merged_unique),
        "files_saved": saved,
        "index": str(index_path),
        "analysis": str(analysis_path),
    }


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Lab 2: Table Extraction with Camelot + pdfplumber")
    p.add_argument("--in", dest="input_pdf", required=True, help="Input PDF file path")
    p.add_argument("--out", dest="output_dir", required=True, help="Output directory")
    p.add_argument("--hybrid", action="store_true", help="Use hybrid extraction (default behavior)")
    p.add_argument("--verbose", "-v", action="store_true", help="Verbose logging")
    return p.parse_args()


def main() -> int:
    args = parse_args()
    setup_logging(args.verbose)

    pdf_path = Path(args.input_pdf)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if not pdf_path.exists():
        LOG.error("PDF not found: %s", pdf_path)
        return 1

    try:
        result = extract_tables_assignment_hybrid(pdf_path, output_dir, use_hybrid=args.hybrid)
        LOG.info("Table extraction completed.")
        LOG.info("Result: %s", json.dumps(result, indent=2))
        return 0
    except Exception as e:
        LOG.exception("Table extraction failed: %s", e)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
