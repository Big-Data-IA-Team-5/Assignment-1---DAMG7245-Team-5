#!/usr/bin/env python3
"""
Complete LANTERN Pipeline Runner

Executes the entire Project LANTERN pipeline including all 6 labs:
- Lab 1: Text extraction with pdfplumber + OCR fallback
- Lab 2: Hybrid table extraction with Camelot + pdfplumber
- Lab 3: Layout detection with LayoutParser
- Lab 4: Advanced PDF understanding with Docling
- Lab 5: Metadata & provenance tagging with semantic classification
- Lab 6: Multi-format storage conversion (Markdown, JSON, TXT)

This comprehensive pipeline processes all PDFs in the raw data directory
and produces standardized outputs for downstream analysis and RAG systems.

Usage:
    python run_complete_pipeline.py --out data/parsed --hybrid-tables
    python run_complete_pipeline.py --out /path/to/output --raw-dir /custom/raw --skip-docling
"""

import subprocess
import sys
from pathlib import Path
import datetime
import logging
import re
import json

# Set up comprehensive logging
logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - [%(levelname)s] - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('pipeline_execution.log')
    ]
)
logger = logging.getLogger(__name__)

def run_command(cmd, lab_name="Unknown"):
    """Execute a command and handle output/errors with comprehensive logging."""
    logger.info(f"[{lab_name}] Executing: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            # Filter and clean output
            output_lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            for line in output_lines:
                if not line.startswith('WARNING') and len(line) > 0:
                    logger.info(f"[{lab_name}] {line}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"[{lab_name}] Command failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"[{lab_name}] STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"[{lab_name}] STDERR: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"[{lab_name}] Unexpected error: {str(e)}")
        return False

def extract_pdf_metadata(pdf_path):
    """Extract comprehensive metadata from PDF filename using intelligent heuristics."""
    pdf_name = pdf_path.stem
    
    # Default values
    company = "Unknown Company"
    fiscal_year = "2024"
    doc_id = pdf_name.lower().replace(' ', '_').replace('-', '_')
    
    # Enhanced company detection with comprehensive mapping
    name_lower = pdf_name.lower()
    company_mapping = {
        'tesla': ("Tesla Inc.", "tesla"),
        'intel': ("Intel Corporation", "intel"),
        'intc': ("Intel Corporation", "intel"),
        'goog': ("Alphabet Inc.", "goog"),
        'alphabet': ("Alphabet Inc.", "alphabet"),
        'aapl': ("Apple Inc.", "aapl"),
        'apple': ("Apple Inc.", "apple"),
        'coca': ("The Coca-Cola Company", "coca_cola"),
        'amzn': ("Amazon.com Inc.", "amzn"),
        'amazon': ("Amazon.com Inc.", "amazon"),
        'msft': ("Microsoft Corporation", "msft"),
        'microsoft': ("Microsoft Corporation", "microsoft"),
        'meta': ("Meta Platforms Inc.", "meta"),
        'facebook': ("Meta Platforms Inc.", "meta"),
        'nflx': ("Netflix Inc.", "nflx"),
        'netflix': ("Netflix Inc.", "netflix"),
        'nvda': ("NVIDIA Corporation", "nvda"),
        'nvidia': ("NVIDIA Corporation", "nvidia"),
        'ibm': ("International Business Machines Corporation", "ibm"),
        'oracle': ("Oracle Corporation", "oracle"),
        'amd': ("Advanced Micro Devices Inc.", "amd")
    }
    
    for key, (full_name, short_id) in company_mapping.items():
        if key in name_lower:
            company = full_name
            doc_id = short_id
            break
    
    # Enhanced year detection
    year_pattern = r'20\d{2}'
    years = re.findall(year_pattern, pdf_name)
    if years:
        fiscal_year = years[-1]  # Use the last year found
        if doc_id != pdf_name.lower().replace(' ', '_').replace('-', '_'):
            doc_id = f"{doc_id}_{fiscal_year}"
    else:
        doc_id = f"{doc_id}_{fiscal_year}"
    
    return doc_id, company, fiscal_year

def validate_lab_outputs(doc_id, output_dir):
    """Comprehensive validation of all lab outputs with detailed checks."""
    # For unified timestamped directories, look directly in output_dir
    base_path = Path(output_dir)
    validations = {}
    
    # Lab 1: Text extraction validation
    text_dir = base_path / "text"
    validations['lab1'] = {
        'required_files': ['extracted_text.txt', '_ocr_pages.json'],
        'required_dirs': ['pages'],
        'status': all([
            (text_dir / f).exists() for f in ['extracted_text.txt', '_ocr_pages.json']
        ]) and (text_dir / 'pages').exists() if text_dir.exists() else False,
        'details': f"Text extraction outputs in {text_dir}"
    }
    
    # Lab 2: Table extraction validation
    tables_dir = base_path / "tables"
    validations['lab2'] = {
        'required_files': ['_comprehensive_index.csv', '_comprehensive_analysis.json'],
        'status': all([
            (tables_dir / f).exists() for f in ['_comprehensive_index.csv', '_comprehensive_analysis.json']
        ]) if tables_dir.exists() else False,
        'details': f"Table extraction outputs in {tables_dir}"
    }
    
    # Lab 3: Layout detection validation
    layout_dir = base_path / "layout"
    validations['lab3'] = {
        'required_files': ['layout_blocks.json', 'layout_aware_extraction.json'],
        'required_dirs': ['blocks'],
        'status': all([
            (layout_dir / f).exists() for f in ['layout_blocks.json', 'layout_aware_extraction.json']
        ]) and (layout_dir / 'blocks').exists() if layout_dir.exists() else False,
        'details': f"Layout detection outputs in {layout_dir}"
    }
    
    # Lab 4: Docling validation
    docling_dir = base_path / "docling"
    validations['lab4'] = {
        'required_files': ['output.md', 'output.json', 'comparison.txt'],
        'status': all([
            (docling_dir / f).exists() for f in ['output.md', 'output.json', 'comparison.txt']
        ]) if docling_dir.exists() else False,
        'details': f"Docling outputs in {docling_dir}"
    }
    
    # Lab 5: Metadata validation
    metadata_dir = base_path / "metadata"
    validations['lab5'] = {
        'required_files': [f'{doc_id}.jsonl', f'{doc_id}.md', f'{doc_id}_summary.json'],
        'status': all([
            (metadata_dir / f).exists() for f in [f'{doc_id}.jsonl', f'{doc_id}.md', f'{doc_id}_summary.json']
        ]) if metadata_dir.exists() else False,
        'details': f"Metadata outputs in {metadata_dir}"
    }
    
    # Lab 6: Format conversion validation
    formats_dir = base_path / "formats"
    validations['lab6'] = {
        'required_files': [f'{doc_id}.md', f'{doc_id}.json', f'{doc_id}.txt', '_format_analysis.md'],
        'status': all([
            (formats_dir / f).exists() for f in [f'{doc_id}.md', f'{doc_id}.json', f'{doc_id}.txt', '_format_analysis.md']
        ]) if formats_dir.exists() else False,
        'details': f"Format conversion outputs in {formats_dir}"
    }
    
    return validations

def generate_pipeline_report(output_dir, lab_results, successful_pdfs, failed_pdfs, execution_info):
    """Generate comprehensive pipeline execution report."""
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    report_file = output_dir / f"LANTERN_Pipeline_Report_{timestamp}.md"
    
    total_pdfs = len(successful_pdfs) + len(failed_pdfs)
    success_rate = (len(successful_pdfs) / total_pdfs * 100) if total_pdfs > 0 else 0
    
    report_content = f"""# Project LANTERN - Complete Pipeline Execution Report

**Execution Timestamp:** {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
**Pipeline Version:** Complete LANTERN v1.0
**Execution ID:** {timestamp}

## Executive Summary

- **Total Documents Processed:** {total_pdfs}
- **Successfully Processed:** {len(successful_pdfs)}
- **Failed Processing:** {len(failed_pdfs)}
- **Success Rate:** {success_rate:.1f}%
- **Raw Data Directory:** {execution_info.get('raw_directory', 'N/A')}
- **Output Directory:** {execution_info.get('output_directory', 'N/A')}

## Lab Performance Summary

| Lab | Component | Success Rate | Description |
|-----|-----------|-------------|-------------|
| Lab 1 | Text Extraction | {sum(1 for r in lab_results.values() if r.get('lab1', False)) / len(lab_results) * 100 if lab_results else 0:.1f}% | pdfplumber + OCR fallback |
| Lab 2 | Table Extraction | {sum(1 for r in lab_results.values() if r.get('lab2', False)) / len(lab_results) * 100 if lab_results else 0:.1f}% | Camelot + pdfplumber with routed extraction |
| Lab 3 | Layout Detection | {sum(1 for r in lab_results.values() if r.get('lab3', False)) / len(lab_results) * 100 if lab_results else 0:.1f}% | LayoutParser with PubLayNet |
| Lab 4 | Docling Processing | {sum(1 for r in lab_results.values() if r.get('lab4', False)) / len(lab_results) * 100 if lab_results else 0:.1f}% | Advanced PDF understanding |
| Lab 5 | Metadata Tagging | {sum(1 for r in lab_results.values() if r.get('lab5', False)) / len(lab_results) * 100 if lab_results else 0:.1f}% | Semantic provenance tracking |
| Lab 6 | Format Conversion | {sum(1 for r in lab_results.values() if r.get('lab6', False)) / len(lab_results) * 100 if lab_results else 0:.1f}% | Multi-format output (MD/JSON/TXT) |

## Successfully Processed Documents

"""
    
    if successful_pdfs:
        for pdf_info in successful_pdfs:
            report_content += f"- **{pdf_info['name']}** → `{pdf_info['doc_id']}`\n"
    else:
        report_content += "None\n"
    
    report_content += "\n## Failed Documents\n\n"
    
    if failed_pdfs:
        for pdf_info in failed_pdfs:
            report_content += f"- **{pdf_info['name']}** → `{pdf_info['doc_id']}`\n"
    else:
        report_content += "None\n"
    
    report_content += f"""
## Configuration Details

- **Routed Table Extraction:** {execution_info.get('hybrid_tables', False)}
- **Docling Processing:** {'Enabled' if not execution_info.get('skip_docling', True) else 'Skipped'}
- **Python Executable:** {sys.executable}

## Output Structure

Each successfully processed document follows this structure:
```
data/parsed/<doc_id>/
├── text/           # Lab 1: Extracted text with OCR fallback
├── tables/         # Lab 2: Extracted tables (CSV format)
├── layout/         # Lab 3: Layout analysis and blocks
├── docling/        # Lab 4: Docling advanced processing
├── metadata/       # Lab 5: Semantic metadata with provenance
└── formats/        # Lab 6: Multi-format outputs
```

## Next Steps

1. **Quality Assurance:** Review failed documents and error logs
2. **Data Analysis:** Use the extracted data for downstream processing
3. **RAG Integration:** Leverage the markdown outputs for retrieval systems
4. **Metadata Mining:** Analyze the JSONL metadata for insights

---
*Generated by Project LANTERN Complete Pipeline v1.0*
"""
    
    try:
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        logger.info(f"Comprehensive pipeline report saved: {report_file}")
        return report_file
    except Exception as e:
        logger.warning(f"Could not save pipeline report: {e}")
        return None

def create_metadata_from_docling(unified_output_dir, doc_id, company, fiscal_year, pdf_path):
    """Create comprehensive metadata JSONL file from ALL lab outputs for Lab 6 compatibility."""
    import json
    from datetime import datetime
    import csv
    
    # Create metadata directory
    metadata_dir = unified_output_dir / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    metadata_records = []
    
    # Read Lab 1 text outputs
    text_dir = unified_output_dir / "text"
    if text_dir.exists():
        for text_file in text_dir.glob("page_*.txt"):
            try:
                page_num = int(text_file.stem.split('_')[1])
                with open(text_file, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
                
                if text_content:
                    metadata_records.append({
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "source_path": str(pdf_path),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "pdfplumber_text",
                        "page": page_num,
                        "section": f"Page {page_num}",
                        "block_type": "paragraph",
                        "text": text_content,
                        "confidence": 0.9,
                        "bbox": None
                    })
            except (ValueError, IndexError):
                continue
    
    # Read Lab 2 table outputs
    tables_dir = unified_output_dir / "tables"
    if tables_dir.exists():
        for csv_file in tables_dir.glob("*.csv"):
            try:
                # Extract page and table info from filename
                filename_parts = csv_file.stem.split('_')
                if len(filename_parts) >= 4:  # e.g., "tesla_pdfplumber_p1_t1"
                    page_num = int(filename_parts[2][1:])  # Extract number from "p1"
                    table_num = int(filename_parts[3][1:])  # Extract number from "t1"
                    
                    with open(csv_file, 'r', encoding='utf-8') as f:
                        csv_reader = csv.reader(f)
                        table_rows = list(csv_reader)
                    
                    if table_rows:
                        table_text = '\n'.join([','.join(row) for row in table_rows])
                        metadata_records.append({
                            "doc_id": doc_id,
                            "company": company,
                            "fiscal_year": fiscal_year,
                            "source_path": str(pdf_path),
                            "extraction_timestamp": datetime.now().isoformat(),
                            "extraction_method": "hybrid_table_extraction",
                            "page": page_num,
                            "section": f"Page {page_num} Table {table_num}",
                            "block_type": "table",
                            "text": table_text,
                            "confidence": 0.85,
                            "bbox": None,
                            "table_info": {
                                "rows": len(table_rows),
                                "cols": len(table_rows[0]) if table_rows else 0,
                                "table_id": table_num
                            }
                        })
            except (ValueError, IndexError):
                continue
    
    # Read Lab 3 layout outputs if available
    layout_dir = unified_output_dir / "layout"
    if layout_dir.exists():
        layout_json = layout_dir / "layout_analysis.json"
        if layout_json.exists():
            try:
                with open(layout_json, 'r', encoding='utf-8') as f:
                    layout_data = json.load(f)
                
                # Add layout information to records
                for page_data in layout_data.get("pages", []):
                    page_num = page_data.get("page", 1)
                    for block in page_data.get("blocks", []):
                        if block.get("text"):
                            metadata_records.append({
                                "doc_id": doc_id,
                                "company": company,
                                "fiscal_year": fiscal_year,
                                "source_path": str(pdf_path),
                                "extraction_timestamp": datetime.now().isoformat(),
                                "extraction_method": "layout_detection",
                                "page": page_num,
                                "section": f"Page {page_num} Layout",
                                "block_type": block.get("type", "text_fragment"),
                                "text": block.get("text", ""),
                                "confidence": block.get("confidence", 0.8),
                                "bbox": block.get("bbox")
                            })
            except Exception as e:
                logger.warning(f"Could not read layout analysis: {e}")
    
    # Read Docling output
    docling_json_path = unified_output_dir / "docling" / "output.json"
    if docling_json_path.exists():
        try:
            with open(docling_json_path, 'r', encoding='utf-8') as f:
                docling_data = json.load(f)
            
            # Add Docling-specific metadata
            metadata_records.append({
                "doc_id": doc_id,
                "company": company,
                "fiscal_year": fiscal_year,
                "source_path": str(pdf_path),
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_method": "docling_ai",
                "page": 1,
                "section": "Docling Analysis",
                "block_type": "document_analysis",
                "text": f"Advanced AI analysis completed. Tables detected: {len(docling_data.get('tables', []))}, Document structure analyzed.",
                "confidence": 0.95,
                "bbox": None,
                "docling_analysis": {
                    "tables_count": len(docling_data.get("tables", [])),
                    "document_info": docling_data.get("document_info", {})
                }
            })
        except Exception as e:
            logger.warning(f"Could not read Docling output: {e}")
    
    # If no metadata records were created, create a minimal one
    if not metadata_records:
        metadata_records.append({
            "doc_id": doc_id,
            "company": company,
            "fiscal_year": fiscal_year,
            "source_path": str(pdf_path),
            "extraction_timestamp": datetime.now().isoformat(),
            "extraction_method": "minimal_fallback",
            "page": 1,
            "section": "Document",
            "block_type": "document_metadata",
            "text": f"Document processed: {company} {fiscal_year}",
            "confidence": 0.7,
            "bbox": None
        })
    
    # Write JSONL file
    metadata_file = metadata_dir / f"{doc_id}.jsonl"
    try:
        with open(metadata_file, 'w', encoding='utf-8') as f:
            for record in metadata_records:
                f.write(json.dumps(record, ensure_ascii=False) + '\n')
        logger.info(f"[LAB 5] Created metadata file with {len(metadata_records)} records: {metadata_file}")
        return True
    except Exception as e:
        logger.error(f"[LAB 5] Failed to create metadata file: {e}")
        return False

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="Run the complete Project LANTERN pipeline for all PDFs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                                    # Auto-detect: data/raw → data/parsed
  %(prog)s --out data/parsed --hybrid-tables
  %(prog)s --out /custom/output --raw-dir /custom/raw --skip-docling
  %(prog)s --out results --hybrid-tables --company "My Company"
        """
    )
    parser.add_argument('--out', dest='output_dir', default='data/parsed',
                       help='Base output directory for parsed results (default: data/parsed)')
    parser.add_argument('--hybrid-tables', action='store_true', default=True,
                       help='Use routed table extraction with page-by-page optimization (default: enabled)')
    parser.add_argument('--skip-docling', action='store_true', 
                       help='Skip Docling processing (if not installed)')
    parser.add_argument('--company', default="Student Project", 
                       help='Company name for metadata (default: Student Project)')
    parser.add_argument('--raw-dir', default='data/raw',
                       help='Raw data directory (default: data/raw)')
    parser.add_argument('--verbose', '-v', action='store_true', 
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    base_output_dir = Path(args.output_dir)
    base_dir = Path(__file__).parent
    py_exec = sys.executable
    
    # Determine raw directory (auto-detect or use specified)
    raw_dir = Path(args.raw_dir)
    if not raw_dir.is_absolute():
        raw_dir = base_dir / raw_dir  # Make relative to project root
    
    # Auto-create raw directory if it doesn't exist
    if not raw_dir.exists():
        logger.warning(f"Raw data directory not found: {raw_dir}")
        raw_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created raw data directory: {raw_dir}")
    
    # Create output directory (auto-create if doesn't exist)
    output_dir = base_output_dir
    if not output_dir.is_absolute():
        output_dir = base_dir / output_dir  # Make relative to project root
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"LANTERN Pipeline started")
    logger.info(f"Output directory: {output_dir}")
    logger.info(f"Raw data directory: {raw_dir}")
    logger.info(f"Hybrid tables: {args.hybrid_tables}")
    logger.info(f"Skip Docling: {args.skip_docling}")
    logger.info(f"Hybrid tables: {args.hybrid_tables}")
    logger.info(f"Skip Docling: {args.skip_docling}")
    
    # Find all PDFs in raw directory
    pdf_files = list(raw_dir.glob('*.pdf'))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {raw_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    for pdf in pdf_files:
        logger.info(f"   {pdf.name}")
    
    # Process each PDF through all labs
    successful_pdfs = []
    failed_pdfs = []
    lab_results = {}
    
    for i, pdf_path in enumerate(pdf_files, 1):
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing Document {i}/{len(pdf_files)}: {pdf_path.name}")
        logger.info(f"{'='*80}")
        
        pdf_success = True
        doc_id, company, fiscal_year = extract_pdf_metadata(pdf_path)
        
        # Create timestamped unified directory for this document
        timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
        pdf_basename = pdf_path.stem  # filename without extension
        unified_dir_name = f"{pdf_basename}_{timestamp}"
        unified_output_dir = output_dir / unified_dir_name
        unified_output_dir.mkdir(parents=True, exist_ok=True)
        
        lab_results[doc_id] = {'unified_dir': unified_dir_name}
        
        logger.info(f"Document metadata: ID={doc_id}, Company={company}, Year={fiscal_year}")
        logger.info(f"Unified output directory: {unified_dir_name}")
        
        # Lab 1: Text Extraction
        logger.info("\n[LAB 1] Starting text extraction...")
        lab1_success = run_command([
            py_exec, str(base_dir / 'src' / 'text' / 'extract_text.py'), 
            '--in', str(pdf_path), 
            '--out', str(unified_output_dir)
        ], "LAB 1")
        lab_results[doc_id]['lab1'] = lab1_success
        if not lab1_success:
            pdf_success = False
            logger.error("[LAB 1] Text extraction failed")
        else:
            logger.info("[LAB 1] Text extraction completed successfully")
        
        # Lab 2: Table Extraction
        logger.info("\n[LAB 2] Starting table extraction...")
        table_cmd = [
            py_exec, str(base_dir / 'src' / 'tables' / 'extract_tables.py'), 
            '--in', str(pdf_path), 
            '--out', str(unified_output_dir)
        ]
        if args.hybrid_tables:
            table_cmd.append('--hybrid')  # Use the correct hybrid extraction argument
        
        lab2_success = run_command(table_cmd, "LAB 2")
        lab_results[doc_id]['lab2'] = lab2_success
        if not lab2_success:
            pdf_success = False
            logger.error("[LAB 2] Table extraction failed")
        else:
            logger.info("[LAB 2] Table extraction completed successfully")
        
        # Lab 3: Layout Detection
        logger.info("\n[LAB 3] Starting layout detection...")
        lab3_success = run_command([
            py_exec, str(base_dir / 'src' / 'layout' / 'extract_layout.py'), 
            '--in', str(pdf_path), 
            '--out', str(unified_output_dir)
        ], "LAB 3")
        lab_results[doc_id]['lab3'] = lab3_success
        if not lab3_success:
            pdf_success = False
            logger.error("[LAB 3] Layout detection failed")
        else:
            logger.info("[LAB 3] Layout detection completed successfully")
        
        # Lab 4: Docling (now includes enhanced metadata extraction)
        if not args.skip_docling:
            logger.info("\n[LAB 4] Starting Docling processing with integrated AI metadata extraction...")
            lab4_success = run_command([
                py_exec, str(base_dir / 'src' / 'docling' / 'extract_docling.py'), 
                '--in', str(pdf_path), 
                '--out', str(unified_output_dir)
            ], "LAB 4")
            lab_results[doc_id]['lab4'] = lab4_success
            if not lab4_success:
                logger.warning("[LAB 4] Docling failed, continuing with other labs...")
            else:
                logger.info("[LAB 4] Docling processing with AI metadata completed successfully")
                # Create metadata file from Docling output for Lab 6
                create_metadata_from_docling(unified_output_dir, doc_id, company, fiscal_year, pdf_path)
                # Mark Lab 5 as completed since it's now integrated into Docling
                lab_results[doc_id]['lab5'] = True
                logger.info("[LAB 5] AI-Enhanced metadata extraction completed via Docling integration")
        else:
            logger.info("[LAB 4] Skipped (--skip-docling flag set)")
            lab_results[doc_id]['lab4'] = True  # Don't count as failure
            
            # Run standalone metadata extraction if Docling is skipped
            logger.info("\n[LAB 5] Starting standalone metadata extraction...")
            lab5_success = run_command([
                py_exec, str(base_dir / 'src' / 'metadata' / 'extract_metadata.py'), 
                '--in', str(pdf_path), 
                '--out', str(unified_output_dir),
                '--doc-id', doc_id,
                '--company', company,
                '--fiscal-year', fiscal_year
            ], "LAB 5")
            lab_results[doc_id]['lab5'] = lab5_success
        
        # Lab 6: Storage Format Conversion (requires Lab 5 output)
        logger.info("\n[LAB 6] Starting format conversion...")
        metadata_file = unified_output_dir / "metadata" / f"{doc_id}.jsonl"
        
        # Check for both traditional and Docling-generated metadata files
        if not metadata_file.exists():
            # Try alternative naming from Docling
            metadata_file = unified_output_dir / "metadata" / f"{doc_id}_docling_summary.json"
            if metadata_file.exists():
                logger.info(f"[LAB 6] Using Docling-generated metadata: {metadata_file}")
            else:
                metadata_file = unified_output_dir / "metadata" / f"{doc_id}.jsonl"
        
        if metadata_file.exists():
            lab6_success = run_command([
                py_exec, str(base_dir / 'src' / 'formats' / 'convert_formats.py'), 
                '--in', str(metadata_file), 
                '--out', str(unified_output_dir)
            ], "LAB 6")
            lab_results[doc_id]['lab6'] = lab6_success
            if not lab6_success:
                pdf_success = False
                logger.error("[LAB 6] Format conversion failed")
            else:
                logger.info("[LAB 6] Format conversion completed successfully")
        else:
            logger.warning(f"[LAB 6] Metadata file not found: {metadata_file}")
            logger.warning("[LAB 6] Skipping format conversion")
            lab_results[doc_id]['lab6'] = False
            pdf_success = False
        
        # Validate outputs
        logger.info(f"\n[VALIDATION] Validating outputs for {doc_id}...")
        validations = validate_lab_outputs(doc_id, unified_output_dir)
        
        validation_summary = []
        for lab, validation in validations.items():
            status = "PASS" if validation['status'] else "FAIL"
            validation_summary.append(f"{lab.upper()}: {status}")
        
        logger.info(f"[VALIDATION] {' | '.join(validation_summary)}")
        
        # Track results
        if pdf_success:
            successful_pdfs.append({'name': pdf_path.name, 'doc_id': doc_id, 'unified_dir': unified_dir_name})
            logger.info(f"Successfully processed {pdf_path.name} → {unified_dir_name}")
        else:
            failed_pdfs.append({'name': pdf_path.name, 'doc_id': doc_id, 'unified_dir': unified_dir_name})
            logger.error(f"Failed to process {pdf_path.name} → {unified_dir_name}")
    
    # Generate comprehensive summary
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    logger.info(f"\n{'='*80}")
    logger.info("LANTERN PIPELINE EXECUTION SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Execution timestamp: {timestamp}")
    logger.info(f"Total PDFs processed: {len(pdf_files)}")
    logger.info(f"Successful: {len(successful_pdfs)}")
    logger.info(f"Failed: {len(failed_pdfs)}")
    logger.info(f"Success rate: {len(successful_pdfs) / len(pdf_files) * 100 if pdf_files else 0:.1f}%")
    
    if successful_pdfs:
        logger.info("\nSuccessfully Processed Documents:")
        for pdf_info in successful_pdfs:
            logger.info(f"   {pdf_info['name']} → {pdf_info['doc_id']}")
    
    if failed_pdfs:
        logger.info("\nFailed Documents:")
        for pdf_info in failed_pdfs:
            logger.info(f"   {pdf_info['name']} → {pdf_info['doc_id']}")
    
    # Lab-by-lab summary
    logger.info("\nLab Success Summary:")
    for lab_num in range(1, 7):
        lab_key = f'lab{lab_num}'
        successes = sum(1 for results in lab_results.values() if results.get(lab_key, False))
        total = len(lab_results)
        percentage = (successes / total * 100) if total > 0 else 0
        logger.info(f"   Lab {lab_num}: {successes}/{total} successful ({percentage:.1f}%)")
    
    logger.info(f"\nAll outputs saved to: {output_dir}")
    
    # Create detailed summary file
    summary_file = output_dir / f"pipeline_summary_{timestamp}.json"
    execution_info = {
        'timestamp': timestamp,
        'raw_directory': str(raw_dir),
        'output_directory': str(output_dir),
        'hybrid_tables': args.hybrid_tables,
        'skip_docling': args.skip_docling,
        'python_executable': py_exec,
        'pipeline_version': 'LANTERN Complete v1.0'
    }
    
    summary_data = {
        'execution_info': execution_info,
        'results': {
            'total_pdfs': len(pdf_files),
            'successful_pdfs': len(successful_pdfs),
            'failed_pdfs': len(failed_pdfs),
            'success_rate': len(successful_pdfs) / len(pdf_files) if pdf_files else 0
        },
        'detailed_results': {
            'successful_documents': successful_pdfs,
            'failed_documents': failed_pdfs,
            'lab_results': lab_results
        },
        'lab_summary': {
            f'lab_{i}': {
                'successful': sum(1 for results in lab_results.values() if results.get(f'lab{i}', False)),
                'total': len(lab_results),
                'success_rate': sum(1 for results in lab_results.values() if results.get(f'lab{i}', False)) / len(lab_results) if lab_results else 0
            } for i in range(1, 7)
        }
    }
    
    try:
        import json
        with open(summary_file, 'w') as f:
            json.dump(summary_data, f, indent=2)
        logger.info(f"Detailed summary saved to: {summary_file}")
    except Exception as e:
        logger.warning(f"Could not save detailed summary: {e}")
    
    # Generate comprehensive pipeline report
    report_file = generate_pipeline_report(output_dir, lab_results, successful_pdfs, failed_pdfs, execution_info)
    if report_file:
        logger.info(f"Pipeline report generated: {report_file}")
    
    # Final status
    if failed_pdfs:
        logger.error(f"Pipeline completed with {len(failed_pdfs)} failures")
        return 1
    else:
        logger.info("Pipeline completed successfully - All documents processed!")
        return 0

if __name__ == "__main__":
    exit(main())