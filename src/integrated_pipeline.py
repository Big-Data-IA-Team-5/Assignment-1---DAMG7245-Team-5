import argparse
import json
from datetime import datetime
from pathlib import Path

# Import functions from individual labs
from lab1_text_extraction import extract_text_with_pdfplumber, save_extracted_data
from lab3_layout_detection_simple import (
    manual_layout_detection,
    route_blocks_to_extractors,
    save_layout_detection_results,
)
from lab4_docling_advanced import (
    analyze_docling_structure,
    export_docling_formats,
    load_pdf_with_docling,
)

from src.tables.extract_tables import (
    extract_tables_assignment_hybrid,
    extract_tables_camelot_lattice,
    extract_tables_camelot_stream,
    extract_tables_pdfplumber,
)


def run_pipeline(pdf_path, output_dir):
    """Run the integrated pipeline for text, table, layout, and Docling extraction."""
    timestamp = datetime.now().strftime("run_%Y%m%d_%H%M%S")
    output_root = Path(output_dir) / timestamp / pdf_path.stem
    output_root.mkdir(parents=True, exist_ok=True)

    # Lab 1: Text Extraction
    print("\n=== Lab 1: Text Extraction ===")
    pages_data, ocr_pages = extract_text_with_pdfplumber(pdf_path)
    save_extracted_data(pages_data, ocr_pages, pdf_path.name)

    # Lab 2: Table Extraction
    print("\n=== Lab 2: Table Extraction ===")
    table_analysis = extract_tables_assignment_hybrid(pdf_path, output_root)

    # Lab 3: Layout Detection
    print("\n=== Lab 3: Layout Detection ===")
    layout_data = manual_layout_detection(pdf_path)
    routing_results = route_blocks_to_extractors(layout_data, pdf_path)
    save_layout_detection_results(layout_data, routing_results, [], pdf_path.name)

    # Lab 4: Docling Integration
    print("\n=== Lab 4: Docling Integration ===")
    doc, _ = load_pdf_with_docling(pdf_path)
    if doc:
        analyze_docling_structure(doc)
        export_docling_formats(doc, pdf_path.name)

    print("\nPipeline completed successfully.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Run the integrated pipeline for PDF processing."
    )
    parser.add_argument(
        "--in", dest="input_pdf", required=True, help="Path to the input PDF file."
    )
    parser.add_argument(
        "--out", dest="output_dir", required=True, help="Directory to save the outputs."
    )
    args = parser.parse_args()

    pdf_path = Path(args.input_pdf)
    output_dir = Path(args.output_dir)

    if not pdf_path.exists():
        print(f"Error: Input PDF file '{pdf_path}' does not exist.")
    else:
        run_pipeline(pdf_path, output_dir)
