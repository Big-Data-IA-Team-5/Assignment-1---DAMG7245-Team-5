
---

# 📄 Project LANTERN – Smart PDF & XBRL Processing Pipeline

**Team 5 – DAMG7245, Fall 2025**

[![Status](https://img.shields.io/badge/Status-Complete-green.svg)](https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![XBRL](https://img.shields.io/badge/XBRL-Supported-orange.svg)](https://www.xbrl.org)

---

## 🧭 Table of Contents

* [Overview](#overview)
* [System Requirements](#system-requirements)
* [Setup & Quick Start](#setup--quick-start)
* [Pipeline Labs](#pipeline-labs)
* [DVC Pipeline](#dvc-pipeline)
* [Pipeline Diagram](#pipeline-diagram)
* [Lab 11: XBRL Cross-Verification](#lab-11-xbrl-cross-verification)
* [Optional Google Document AI](#optional-google-document-ai)
* [Output Structure](#output-structure)
* [Troubleshooting](#troubleshooting)
* [Performance](#performance)
* [Team](#team)
* [License](#license)

---

## Overview

Project LANTERN is a **production-ready pipeline** for extracting and validating structured data from PDF filings and XBRL files.

**Features:**

* PDF text, tables, layout, metadata extraction
* AI-enhanced processing via Docling
* Optional Google Document AI integration
* XBRL cross-verification of financial data
* DVC-powered reproducibility, caching, and versioning

---

## System Requirements

* **Python:** 3.7+ (3.10–3.12 recommended)
* **RAM:** 4 GB minimum (8 GB+ for large PDFs)
* **Disk Space:** 2 GB free
* **OS:** Windows / macOS / Linux
* **Optional:** Tesseract OCR, Java, Google AI credentials

**System Packages:**

* macOS: `brew install tesseract && xcode-select --install`
* Ubuntu/Debian: `sudo apt-get install -y tesseract-ocr libtesseract-dev build-essential`
* Windows: Install Tesseract OCR (UB Mannheim) and add to `PATH`

---

## Setup & Quick Start

**Smart Setup (Recommended)**

```bash
git clone https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5.git
cd Assignment-1---DAMG7245-Team-5

# Smart cross-platform setup
python3 setup/smart_setup.py

# Activate environment
source activate.sh       # Windows: activate.bat

# Run the DVC pipeline
dvc repro
```

**Traditional Setup**

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r setup/requirements.txt
```

**Verify Setup**

```bash
python3 setup/verify_setup.py
```

---

## Pipeline Labs

| Lab    | Purpose                                 | Outputs                  | Status     |
| ------ | --------------------------------------- | ------------------------ | ---------- |
| Lab 1  | Text extraction (OCR fallback)          | `.txt`, per-page         | ✅ Working  |
| Lab 2  | Table extraction (Camelot + PDFPlumber) | `.csv`, index + analysis | ✅ Working  |
| Lab 3  | Layout analysis                         | `layout_*.json`          | ✅ Working  |
| Lab 4  | Docling AI processing                   | `.json`, `.md`           | ✅ Working  |
| Lab 5  | Metadata & provenance                   | `.jsonl`, summaries      | ✅ Working  |
| Lab 6  | Multi-format export                     | Markdown / JSON / TXT    | ✅ Working  |
| Lab 7  | Google Document AI (optional)           | AI extracts + comparison | ✅ Optional |
| Lab 11 | XBRL Verification                       | CSV / summary            | ✅ Working  |

**Manual Execution (Alternative to DVC)**

```bash
python3 run_complete_pipeline.py --out data/parsed --hybrid-tables --verbose

# Individual labs
python3 src/text/extract_text.py      --in data/raw/your.pdf --out data/parsed/
python3 src/tables/extract_tables.py  --in data/raw/your.pdf --out data/parsed/ --hybrid
python3 src/layout/extract_layout.py  --in data/raw/your.pdf --out data/parsed/
python3 src/docling/extract_docling.py --in data/raw/your.pdf --out data/parsed/
python3 src/metadata/extract_metadata.py --in data/raw/your.pdf --out data/parsed/
python3 src/formats/convert_formats.py --in data/parsed/<doc>/metadata/<doc>.jsonl --out data/parsed/<doc>/
```

---

## DVC Pipeline

**Sequential stages:** Text → Tables → Layout → Docling → Export
**Caching & reproducibility:** Only changed stages rerun
**Versioning:** Track pipeline state via `dvc.lock`

```bash
dvc status
dvc dag
dvc repro                # Run full pipeline
dvc repro parse          # Run only text extraction
dvc repro tables
dvc repro layout
dvc repro docling
dvc repro export
dvc pipeline show
dvc metrics show
dvc plots show
dvc push                 # Upload to remote
dvc pull                 # Download from remote
dvc checkout             # Restore workspace
```

---

## Pipeline Diagram

```mermaid
graph TD
    A[data/raw/*.pdf] --> B[Lab 1: Text Extraction]
    A --> C[Lab 2: Table Extraction]
    B --> C
    A --> D[Lab 3: Layout Analysis]
    B --> D
    C --> D
    A --> E[Lab 4: Docling AI Analysis]
    B --> E
    C --> E
    D --> E
    A --> F[Lab 5-6: Metadata & Format Export]
    B --> F
    C --> F
    D --> F
    E --> F
    F --> G[data/intermediate/formats/]
    B --> H[Lab 7: Google Document AI]
    C --> H
    D --> H
    H --> F
    F --> I[Lab 11: XBRL Cross-Verification]
    F --> J[Databases / Storage]
    I --> J

---

## Lab 11: XBRL Cross-Verification

* Parse XBRL using Simple XML parser or Arelle
* Extract Revenue, Net Income, Total Assets
* Map PDF tables to XBRL taxonomy using mapping dictionary
* Validate numerical values and report discrepancies

**Run XBRL verification**

```bash
python3 src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl
```

---

## Optional Google Document AI

```bash
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12
```

---

## Output Structure

**Main pipeline**

```
data/parsed/
└─ <document>_<timestamp>/
   ├─ text/
   ├─ tables/
   ├─ layout/
   ├─ docling/
   ├─ metadata/
   └─ formats/
LANTERN_Pipeline_Report_<timestamp>.md
pipeline_summary_<timestamp>.json
```

**Lab 7 (Google AI)**

```
reports/google_ai/lab7_session_<timestamp>/
├─ temp_pdfs/
├─ raw_google_ai_results/
├─ parsed_results/
├─ parsed_data_comparison/
└─ final_reports/
```

---

## Troubleshooting

* Activate virtual environment
* Install missing dependencies: `pip install -r setup/requirements.txt`
* Ensure PDFs are in `data/raw/`
* Tesseract OCR must be on `PATH`
* Check DVC status and repair cache if needed

---

## Performance

* 100-page PDF: ~4–6 minutes, ~4 GB RAM
* Lab 7 (2 pages): ~3–5 seconds, ~2 GB RAM
* Timestamped outputs for traceability
* Cache efficiency: 80–85% stage skip on reruns

---

## Team

**Team 5 – DAMG7245 (Fall 2025)**
Big Data Analytics Project – SEC Filing Processing Pipeline

---

## License

MIT License – see project files for details

---

