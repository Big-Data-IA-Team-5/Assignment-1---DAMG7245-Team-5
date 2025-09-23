"""
Phase One Pipeline Runner - Fixed Version

Runs all Phase 1 labs in sequence for all PDFs in data/raw/:
- Lab 1: Text extraction with pdfplumber + OCR fallback
- Lab 2: Table extraction with hybrid Camelot + pdfplumber
- Lab 3: Layout detection with LayoutParser
- Lab 4: Advanced PDF understanding with Docling
- Lab 5: Metadata & provenance tagging
- Lab 6: Storage format conversion (Markdown, JSON, TXT)

All labs now properly handle raw data input and follow standardized output structure.
"""

import subprocess
import sys
from pathlib import Path
import datetime
import logging
import re

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def run_command(cmd, lab_name="Unknown"):
    """Execute a command and handle output/errors with better logging."""
    logger.info(f"[{lab_name}] Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        if result.stdout:
            # Filter and clean output
            output_lines = [line.strip() for line in result.stdout.split('\n') if line.strip()]
            for line in output_lines:
                logger.info(f"[{lab_name}] {line}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"[{lab_name}] Command failed with exit code {e.returncode}")
        if e.stdout:
            logger.error(f"[{lab_name}] STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"[{lab_name}] STDERR: {e.stderr}")
        return False

def extract_pdf_metadata(pdf_path):
    """Extract metadata from PDF filename with improved heuristics."""
    pdf_name = pdf_path.stem
    
    # Default values
    company = "Unknown Company"
    fiscal_year = "2024"
    doc_id = pdf_name
    
    # Enhanced company detection
    name_lower = pdf_name.lower()
    if 'tesla' in name_lower:
        company = "Tesla Inc."
        doc_id = "tesla_2024"
    elif 'goog' in name_lower or 'alphabet' in name_lower:
        company = "Alphabet Inc."
        doc_id = "goog_2024"
    elif 'aapl' in name_lower or 'apple' in name_lower:
        company = "Apple Inc."
        doc_id = "aapl_2024"
    elif 'coca' in name_lower and 'cola' in name_lower:
        company = "The Coca-Cola Company"
        doc_id = "coca_cola_2024"
    elif 'amzn' in name_lower or 'amazon' in name_lower:
        company = "Amazon.com Inc."
        doc_id = "amzn_2024"
    elif 'msft' in name_lower or 'microsoft' in name_lower:
        company = "Microsoft Corporation"
        doc_id = "msft_2024"
    
    # Enhanced year detection
    year_pattern = r'20\d{2}'
    years = re.findall(year_pattern, pdf_name)
    if years:
        fiscal_year = years[0]
        doc_id = doc_id.replace("2024", fiscal_year)
    
    return doc_id, company, fiscal_year

def validate_lab_outputs(doc_id, output_dir):
    """Validate that each lab produced expected outputs."""
    base_path = Path(output_dir) / doc_id
    validations = {}
    
    # Lab 1: Text extraction
    text_dir = base_path / "text"
    validations['lab1'] = {
        'required_files': ['combined.txt', '_ocr_pages.json'],
        'required_dirs': ['pages'],
        'status': all([
            (text_dir / f).exists() for f in ['combined.txt', '_ocr_pages.json']
        ]) and (text_dir / 'pages').exists()
    }
    
    # Lab 2: Table extraction
    tables_dir = base_path / "tables"
    validations['lab2'] = {
        'required_files': ['_index.csv', '_summary.json'],
        'status': all([
            (tables_dir / f).exists() for f in ['_index.csv', '_summary.json']
        ]) if tables_dir.exists() else False
    }
    
    # Lab 3: Layout detection
    layout_dir = base_path / "layout"
    validations['lab3'] = {
        'required_files': ['layout_blocks.json', 'layout_aware_extraction.json'],
        'required_dirs': ['blocks'],
        'status': all([
            (layout_dir / f).exists() for f in ['layout_blocks.json', 'layout_aware_extraction.json']
        ]) and (layout_dir / 'blocks').exists() if layout_dir.exists() else False
    }
    
    # Lab 4: Docling
    docling_dir = base_path / "docling"
    validations['lab4'] = {
        'required_files': ['comparison.txt'],
        'status': (docling_dir / 'comparison.txt').exists() if docling_dir.exists() else False
    }
    
    # Lab 5: Metadata
    metadata_dir = base_path / "metadata"
    validations['lab5'] = {
        'required_files': [f'{doc_id}.jsonl', f'{doc_id}.md', f'{doc_id}_summary.json'],
        'status': all([
            (metadata_dir / f).exists() for f in [f'{doc_id}.jsonl', f'{doc_id}.md', f'{doc_id}_summary.json']
        ]) if metadata_dir.exists() else False
    }
    
    # Lab 6: Format conversion
    formats_dir = base_path / "formats"
    validations['lab6'] = {
        'required_files': [f'{doc_id}.md', f'{doc_id}.json', f'{doc_id}.txt', '_format_analysis.md'],
        'status': all([
            (formats_dir / f).exists() for f in [f'{doc_id}.md', f'{doc_id}.json', f'{doc_id}.txt', '_format_analysis.md']
        ]) if formats_dir.exists() else False
    }
    
    return validations

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run all Phase 1 labs in sequence for all PDFs in data/raw.")
    parser.add_argument('--out', dest='output_dir', required=True, help='Base output directory for parsed results')
    parser.add_argument('--hybrid-tables', action='store_true', help='Use hybrid table extraction (recommended)')
    parser.add_argument('--skip-docling', action='store_true', help='Skip Docling processing (if not installed)')
    parser.add_argument('--company', default="Student Project", help='Company name for metadata (default: Student Project)')
    parser.add_argument('--raw-dir', help='Raw data directory (default: data/raw)')
    
    args = parser.parse_args()
    
    base_output_dir = Path(args.output_dir)
    base_dir = Path(__file__).parent
    py_exec = sys.executable
    
    # Determine raw directory
    if args.raw_dir:
        raw_dir = Path(args.raw_dir)
    else:
        raw_dir = base_dir / 'data' / 'raw'
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir = base_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Pipeline started - Output directory: {output_dir}")
    logger.info(f"Raw data directory: {raw_dir}")
    
    # Find all PDFs in raw directory
    pdf_files = list(raw_dir.glob('*.pdf'))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {raw_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF through all labs
    successful_pdfs = []
    failed_pdfs = []
    lab_results = {}
    
    for pdf_path in pdf_files:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {pdf_path.name}")
        logger.info(f"{'='*80}")
        
        pdf_success = True
        doc_id, company, fiscal_year = extract_pdf_metadata(pdf_path)
        lab_results[doc_id] = {}
        
        logger.info(f"Document metadata: ID={doc_id}, Company={company}, Year={fiscal_year}")
        
        # Lab 1: Text Extraction
        logger.info("\n[LAB 1] Starting text extraction...")
        lab1_success = run_command([
            py_exec, str(base_dir / 'src' / 'text' / 'extract_text.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir)
        ], "LAB 1")
        lab_results[doc_id]['lab1'] = lab1_success
        if not lab1_success:
            pdf_success = False
        
        # Lab 2: Table Extraction
        logger.info("\n[LAB 2] Starting table extraction...")
        table_cmd = [
            py_exec, str(base_dir / 'src' / 'tables' / 'extract_tables.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir)
        ]
        if args.hybrid_tables:
            table_cmd.append('--hybrid')
        
        lab2_success = run_command(table_cmd, "LAB 2")
        lab_results[doc_id]['lab2'] = lab2_success
        if not lab2_success:
            pdf_success = False
        
        # Lab 3: Layout Detection
        logger.info("\n[LAB 3] Starting layout detection...")
        lab3_success = run_command([
            py_exec, str(base_dir / 'src' / 'layout' / 'extract_layout.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir)
        ], "LAB 3")
        lab_results[doc_id]['lab3'] = lab3_success
        if not lab3_success:
            pdf_success = False
        
        # Lab 4: Docling (optional)
        if not args.skip_docling:
            logger.info("\n[LAB 4] Starting Docling processing...")
            lab4_success = run_command([
                py_exec, str(base_dir / 'src' / 'docling' / 'extract_docling.py'), 
                '--in', str(pdf_path), 
                '--out', str(output_dir)
            ], "LAB 4")
            lab_results[doc_id]['lab4'] = lab4_success
            if not lab4_success:
                logger.warning("[LAB 4] Docling failed, continuing with other labs...")
        else:
            logger.info("[LAB 4] Skipped (--skip-docling flag set)")
            lab_results[doc_id]['lab4'] = True  # Don't count as failure
        
        # Lab 5: Metadata & Provenance Tagging
        logger.info("\n[LAB 5] Starting metadata extraction...")
        lab5_success = run_command([
            py_exec, str(base_dir / 'src' / 'metadata' / 'extract_metadata.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir),
            '--doc-id', doc_id,
            '--company', company,
            '--fiscal-year', fiscal_year
        ], "LAB 5")
        lab_results[doc_id]['lab5'] = lab5_success
        if not lab5_success:
            pdf_success = False
        
        # Lab 6: Storage Format Conversion (requires Lab 5 output)
        logger.info("\n[LAB 6] Starting format conversion...")
        metadata_file = output_dir / doc_id / "metadata" / f"{doc_id}.jsonl"
        
        if metadata_file.exists():
            lab6_success = run_command([
                py_exec, str(base_dir / 'src' / 'formats' / 'convert_formats.py'), 
                '--in', str(metadata_file), 
                '--out', str(output_dir)
            ], "LAB 6")
            lab_results[doc_id]['lab6'] = lab6_success
            if not lab6_success:
                pdf_success = False
        else:
            logger.warning(f"[LAB 6] Metadata file not found: {metadata_file}")
            logger.warning("[LAB 6] Skipping format conversion")
            lab_results[doc_id]['lab6'] = False
            pdf_success = False
        
        # Validate outputs
        logger.info(f"\n[VALIDATION] Validating outputs for {doc_id}...")
        validations = validate_lab_outputs(doc_id, output_dir)
        
        validation_summary = []
        for lab, validation in validations.items():
            status = "✅" if validation['status'] else "❌"
            validation_summary.append(f"{lab.upper()}: {status}")
        
        logger.info(f"[VALIDATION] {' | '.join(validation_summary)}")
        
        # Track results
        if pdf_success:
            successful_pdfs.append({'name': pdf_path.name, 'doc_id': doc_id})
            logger.info(f"✅ Successfully processed {pdf_path.name} -> {doc_id}")
        else:
            failed_pdfs.append({'name': pdf_path.name, 'doc_id': doc_id})
            logger.error(f"❌ Failed to process {pdf_path.name} -> {doc_id}")
    
    # Generate comprehensive summary
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    logger.info(f"\n{'='*80}")
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Execution timestamp: {timestamp}")
    logger.info(f"Total PDFs processed: {len(pdf_files)}")
    logger.info(f"Successful: {len(successful_pdfs)}")
    logger.info(f"Failed: {len(failed_pdfs)}")
    
    if successful_pdfs:
        logger.info("\nSuccessful Documents:")
        for pdf_info in successful_pdfs:
            logger.info(f"  ✅ {pdf_info['name']} → {pdf_info['doc_id']}")
    
    if failed_pdfs:
        logger.info("\nFailed Documents:")
        for pdf_info in failed_pdfs:
            logger.info(f"  ❌ {pdf_info['name']} → {pdf_info['doc_id']}")
    
    # Lab-by-lab summary
    logger.info("\nLab Success Summary:")
    for lab_num in range(1, 7):
        lab_key = f'lab{lab_num}'
        successes = sum(1 for results in lab_results.values() if results.get(lab_key, False))
        total = len(lab_results)
        logger.info(f"  Lab {lab_num}: {successes}/{total} successful")
    
    logger.info(f"\nAll outputs saved to: {output_dir}")
    
    # Create detailed summary file
    summary_file = output_dir / f"pipeline_summary_{timestamp}.json"
    summary_data = {
        'execution_info': {
            'timestamp': timestamp,
            'raw_directory': str(raw_dir),
            'output_directory': str(output_dir),
            'hybrid_tables': args.hybrid_tables,
            'skip_docling': args.skip_docling
        },
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
                'total': len(lab_results)
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
    
    # Exit with appropriate code
    return 0 if not failed_pdfs else 1

if __name__ == "__main__":
    exit(main())

def main():
    import argparse
    parser = argparse.ArgumentParser(description="Run all Phase 1 labs in sequence for all PDFs in data/raw.")
    parser.add_argument('--out', dest='output_dir', required=True, help='Base output directory for parsed results')
    parser.add_argument('--hybrid-tables', action='store_true', help='Use hybrid table extraction (recommended)')
    parser.add_argument('--skip-docling', action='store_true', help='Skip Docling processing (if not installed)')
    parser.add_argument('--company', default="Student Project", help='Company name for metadata (default: Student Project)')
    parser.add_argument('--raw-dir', help='Raw data directory (default: data/raw)')
    
    args = parser.parse_args()
    
    base_output_dir = Path(args.output_dir)
    base_dir = Path(__file__).parent
    py_exec = sys.executable
    
    # Determine raw directory
    if args.raw_dir:
        raw_dir = Path(args.raw_dir)
    else:
        raw_dir = base_dir / 'data' / 'raw'
    
    if not raw_dir.exists():
        logger.error(f"Raw data directory not found: {raw_dir}")
        sys.exit(1)
    
    # Create output directory
    output_dir = base_output_dir
    output_dir.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Pipeline started - Output directory: {output_dir}")
    logger.info(f"Raw data directory: {raw_dir}")
    
    # Find all PDFs in raw directory
    pdf_files = list(raw_dir.glob('*.pdf'))
    
    if not pdf_files:
        logger.error(f"No PDF files found in {raw_dir}")
        sys.exit(1)
    
    logger.info(f"Found {len(pdf_files)} PDF files to process")
    
    # Process each PDF through all labs
    successful_pdfs = []
    failed_pdfs = []
    lab_results = {}
    
    for pdf_path in pdf_files:
        logger.info(f"\n{'='*80}")
        logger.info(f"Processing: {pdf_path.name}")
        logger.info(f"{'='*80}")
        
        pdf_success = True
        doc_id, company, fiscal_year = extract_pdf_metadata(pdf_path)
        lab_results[doc_id] = {}
        
        logger.info(f"Document metadata: ID={doc_id}, Company={company}, Year={fiscal_year}")
        
        # Lab 1: Text Extraction
        logger.info("\n[LAB 1] Starting text extraction...")
        lab1_success = run_command([
            py_exec, str(base_dir / 'src' / 'text' / 'extract_text.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir)
        ], "LAB 1")
        lab_results[doc_id]['lab1'] = lab1_success
        if not lab1_success:
            pdf_success = False
        
        # Lab 2: Table Extraction
        logger.info("\n[LAB 2] Starting table extraction...")
        table_cmd = [
            py_exec, str(base_dir / 'src' / 'tables' / 'extract_tables.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir)
        ]
        if args.hybrid_tables:
            table_cmd.append('--hybrid')
        
        lab2_success = run_command(table_cmd, "LAB 2")
        lab_results[doc_id]['lab2'] = lab2_success
        if not lab2_success:
            pdf_success = False
        
        # Lab 3: Layout Detection
        logger.info("\n[LAB 3] Starting layout detection...")
        lab3_success = run_command([
            py_exec, str(base_dir / 'src' / 'layout' / 'extract_layout.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir)
        ], "LAB 3")
        lab_results[doc_id]['lab3'] = lab3_success
        if not lab3_success:
            pdf_success = False
        
        # Lab 4: Docling (optional)
        if not args.skip_docling:
            logger.info("\n[LAB 4] Starting Docling processing...")
            lab4_success = run_command([
                py_exec, str(base_dir / 'src' / 'docling' / 'extract_docling.py'), 
                '--in', str(pdf_path), 
                '--out', str(output_dir)
            ], "LAB 4")
            lab_results[doc_id]['lab4'] = lab4_success
            if not lab4_success:
                logger.warning("[LAB 4] Docling failed, continuing with other labs...")
        else:
            logger.info("[LAB 4] Skipped (--skip-docling flag set)")
            lab_results[doc_id]['lab4'] = True  # Don't count as failure
        
        # Lab 5: Metadata & Provenance Tagging
        logger.info("\n[LAB 5] Starting metadata extraction...")
        lab5_success = run_command([
            py_exec, str(base_dir / 'src' / 'metadata' / 'extract_metadata.py'), 
            '--in', str(pdf_path), 
            '--out', str(output_dir),
            '--doc-id', doc_id,
            '--company', company,
            '--fiscal-year', fiscal_year
        ], "LAB 5")
        lab_results[doc_id]['lab5'] = lab5_success
        if not lab5_success:
            pdf_success = False
        
        # Lab 6: Storage Format Conversion (requires Lab 5 output)
        logger.info("\n[LAB 6] Starting format conversion...")
        metadata_file = output_dir / doc_id / "metadata" / f"{doc_id}.jsonl"
        
        if metadata_file.exists():
            lab6_success = run_command([
                py_exec, str(base_dir / 'src' / 'formats' / 'convert_formats.py'), 
                '--in', str(metadata_file), 
                '--out', str(output_dir)
            ], "LAB 6")
            lab_results[doc_id]['lab6'] = lab6_success
            if not lab6_success:
                pdf_success = False
        else:
            logger.warning(f"[LAB 6] Metadata file not found: {metadata_file}")
            logger.warning("[LAB 6] Skipping format conversion")
            lab_results[doc_id]['lab6'] = False
            pdf_success = False
        
        # Validate outputs
        logger.info(f"\n[VALIDATION] Validating outputs for {doc_id}...")
        validations = validate_lab_outputs(doc_id, output_dir)
        
        validation_summary = []
        for lab, validation in validations.items():
            status = "✅" if validation['status'] else "❌"
            validation_summary.append(f"{lab.upper()}: {status}")
        
        logger.info(f"[VALIDATION] {' | '.join(validation_summary)}")
        
        # Track results
        if pdf_success:
            successful_pdfs.append({'name': pdf_path.name, 'doc_id': doc_id})
            logger.info(f"✅ Successfully processed {pdf_path.name} -> {doc_id}")
        else:
            failed_pdfs.append({'name': pdf_path.name, 'doc_id': doc_id})
            logger.error(f"❌ Failed to process {pdf_path.name} -> {doc_id}")
    
    # Generate comprehensive summary
    timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
    logger.info(f"\n{'='*80}")
    logger.info("PIPELINE EXECUTION SUMMARY")
    logger.info(f"{'='*80}")
    logger.info(f"Execution timestamp: {timestamp}")
    logger.info(f"Total PDFs processed: {len(pdf_files)}")
    logger.info(f"Successful: {len(successful_pdfs)}")
    logger.info(f"Failed: {len(failed_pdfs)}")
    
    if successful_pdfs:
        logger.info("\nSuccessful Documents:")
        for pdf_info in successful_pdfs:
            logger.info(f"  ✅ {pdf_info['name']} → {pdf_info['doc_id']}")
    
    if failed_pdfs:
        logger.info("\nFailed Documents:")
        for pdf_info in failed_pdfs:
            logger.info(f"  ❌ {pdf_info['name']} → {pdf_info['doc_id']}")
    
    # Lab-by-lab summary
    logger.info("\nLab Success Summary:")
    for lab_num in range(1, 7):
        lab_key = f'lab{lab_num}'
        successes = sum(1 for results in lab_results.values() if results.get(lab_key, False))
        total = len(lab_results)
        logger.info(f"  Lab {lab_num}: {successes}/{total} successful")
    
    logger.info(f"\nAll outputs saved to: {output_dir}")
    
    # Create detailed summary file
    summary_file = output_dir / f"pipeline_summary_{timestamp}.json"
    summary_data = {
        'execution_info': {
            'timestamp': timestamp,
            'raw_directory': str(raw_dir),
            'output_directory': str(output_dir),
            'hybrid_tables': args.hybrid_tables,
            'skip_docling': args.skip_docling
        },
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
                'total': len(lab_results)
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
    
    # Exit with appropriate code
    return 0 if not failed_pdfs else 1

if __name__ == "__main__":
    exit(main())
