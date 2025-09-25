import argparse
import json
import logging
import os
from datetime import datetime
from pathlib import Path

import pdfplumber
import pytesseract


def extract_text_with_pdfplumber(pdf_path):
    """
    Lab 1: Text Extraction with OCR Fallback

    Goal: Extract per-page text while preserving reading order and handle scanned pages
    with OCR. Detects pages where no text is extracted and applies Tesseract OCR.

    Core tasks:
    - Use pdfplumber to iterate through pages with layout parameters
    - Call Page.extract_text() with x_density and y_density for better layout
    - Detect pages needing OCR and apply Tesseract via pytesseract
    - Save per-page text files and log which pages required OCR
    - Persist word bounding boxes using page.extract_words()
    """
    extracted_pages = []
    ocr_pages = []

    # Setup logging for OCR tracking
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    with pdfplumber.open(pdf_path) as pdf:
        logger.info(f"Processing {len(pdf.pages)} pages from {pdf_path}")

        for page_num, page in enumerate(pdf.pages):
            # Extract text with experimental layout parameters for better reading order
            text = page.extract_text(
                x_density=7.25,  # Experimental layout parameter for character spacing
                y_density=13,  # Experimental layout parameter for line spacing
            )

            # Extract words with bounding boxes for chunking and layout analysis
            words_with_bbox = page.extract_words()

            # Check if meaningful text was extracted (threshold: 50 characters)
            if text and len(text.strip()) > 50:
                # Successful text extraction with pdfplumber
                page_data = {
                    "page_num": page_num + 1,
                    "text": text,
                    "word_count": len(words_with_bbox),
                    "char_count": len(text),
                    "extraction_method": "pdfplumber",
                    "words_with_bbox": words_with_bbox,
                    "needs_ocr": False,
                    "layout_params": {"x_density": 7.25, "y_density": 13},
                }
                logger.info(
                    f"Page {page_num + 1}: Extracted {len(text)} characters with pdfplumber"
                )
            else:
                # No text found - likely a scanned page, apply OCR fallback
                logger.warning(
                    f"Page {page_num + 1}: No text extracted, applying OCR fallback"
                )
                try:
                    # Convert page to image for OCR processing
                    page_image = page.to_image(
                        resolution=300
                    )  # Higher resolution for better OCR

                    # Apply Tesseract OCR
                    ocr_text = pytesseract.image_to_string(
                        page_image.original,
                        config="--oem 3 --psm 6",  # OCR Engine Mode 3, Page Segmentation Mode 6
                    )

                    if ocr_text and len(ocr_text.strip()) > 10:
                        # Successful OCR extraction
                        ocr_pages.append(page_num + 1)
                        page_data = {
                            "page_num": page_num + 1,
                            "text": ocr_text,
                            "word_count": len(ocr_text.split()),
                            "char_count": len(ocr_text),
                            "extraction_method": "tesseract_ocr",
                            "words_with_bbox": [],  # OCR doesn't provide bbox info
                            "needs_ocr": True,
                            "ocr_config": "--oem 3 --psm 6",
                        }
                        logger.info(
                            f"Page {page_num + 1}: OCR extracted {len(ocr_text)} characters"
                        )
                    else:
                        # OCR failed or produced minimal text
                        page_data = {
                            "page_num": page_num + 1,
                            "text": "",
                            "word_count": 0,
                            "char_count": 0,
                            "extraction_method": "failed",
                            "words_with_bbox": [],
                            "needs_ocr": True,
                            "error": "OCR produced insufficient text",
                        }
                        logger.error(
                            f"Page {page_num + 1}: OCR failed to extract meaningful text"
                        )

                except Exception as e:
                    # OCR processing failed
                    page_data = {
                        "page_num": page_num + 1,
                        "text": "",
                        "word_count": 0,
                        "char_count": 0,
                        "extraction_method": "failed",
                        "words_with_bbox": [],
                        "needs_ocr": True,
                        "error": str(e),
                    }
                    logger.error(f"Page {page_num + 1}: OCR processing failed: {e}")

            extracted_pages.append(page_data)

    # Log summary
    logger.info(
        f"Extraction complete: {len(extracted_pages)} pages processed, {len(ocr_pages)} pages required OCR"
    )
    return extracted_pages, ocr_pages


def save_extracted_data(pages_data, ocr_pages, pdf_name, out_dir):
    """
    Save extracted text data with checkpoint requirements:
    - Per-page .txt files for each PDF
    - A log recording pages that needed OCR
    - Persist word bounding boxes for chunking and layout analysis
    """
    # Output directly to the unified directory structure: <unified_output_dir>/text/
    text_root = Path(out_dir) / "text"
    pages_dir = text_root / "pages"
    pages_dir.mkdir(parents=True, exist_ok=True)

    combined_text = ""
    ocr_log_entries = []

    # Process each page
    for page in pages_data:
        page_num = page["page_num"]

        # Checkpoint 1: Per-page .txt files exist for each PDF
        page_txt = pages_dir / f"page_{page_num:03d}.txt"
        with open(page_txt, "w", encoding="utf-8") as f:
            f.write(page["text"])

        # Add to combined text
        combined_text += f"--- PAGE {page_num} ---\n"
        combined_text += page["text"] + "\n\n"

        # Track OCR usage for logging
        if page["needs_ocr"]:
            ocr_log_entries.append(
                {
                    "page_num": page_num,
                    "extraction_method": page["extraction_method"],
                    "char_count": page["char_count"],
                    "timestamp": datetime.now().isoformat(),
                    "success": page["extraction_method"] != "failed",
                }
            )

        # Checkpoint 3: Persist word bounding boxes using page.extract_words()
        words_file = pages_dir / f"page_{page_num:03d}_words.json"
        with open(words_file, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "page_num": page_num,
                    "words_with_bbox": page["words_with_bbox"],
                    "extraction_method": page["extraction_method"],
                    "word_count": (
                        len(page["words_with_bbox"]) if page["words_with_bbox"] else 0
                    ),
                    "note": "Bounding boxes help with chunking and layout analysis",
                },
                f,
                indent=2,
            )

    # Save combined text file
    combined_file = text_root / "extracted_text.txt"
    with open(combined_file, "w", encoding="utf-8") as f:
        f.write(combined_text)

    # Checkpoint 2: A log records pages that needed OCR
    ocr_log = {
        "pdf_name": pdf_name,
        "total_pages": len(pages_data),
        "pages_requiring_ocr": len(ocr_pages),
        "ocr_pages_list": ocr_pages,
        "processing_timestamp": datetime.now().isoformat(),
        "detailed_log": ocr_log_entries,
        "summary": {
            "successful_pdfplumber": len(
                [p for p in pages_data if p["extraction_method"] == "pdfplumber"]
            ),
            "successful_ocr": len(
                [p for p in pages_data if p["extraction_method"] == "tesseract_ocr"]
            ),
            "failed_extraction": len(
                [p for p in pages_data if p["extraction_method"] == "failed"]
            ),
        },
    }

    ocr_log_file = text_root / "_ocr_pages.json"
    with open(ocr_log_file, "w", encoding="utf-8") as f:
        json.dump(ocr_log, f, indent=2)

    # Create extraction summary report
    summary_report = text_root / "_extraction_summary.md"
    with open(summary_report, "w", encoding="utf-8") as f:
        f.write(f"# Text Extraction Summary - {pdf_name}\n\n")
        f.write(
            f"**Processing Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        )
        f.write(f"## Overview\n")
        f.write(f"- **Total Pages:** {len(pages_data)}\n")
        f.write(
            f"- **Successfully Extracted (pdfplumber):** {ocr_log['summary']['successful_pdfplumber']}\n"
        )
        f.write(f"- **Required OCR:** {ocr_log['summary']['successful_ocr']}\n")
        f.write(
            f"- **Failed Extraction:** {ocr_log['summary']['failed_extraction']}\n\n"
        )

        if ocr_pages:
            f.write(f"## Pages Requiring OCR\n")
            f.write(
                f"The following pages were scanned/image-based and required OCR fallback:\n"
            )
            for page_num in ocr_pages:
                f.write(f"- Page {page_num}\n")
            f.write(f"\n")

        f.write(f"## File Outputs\n")
        f.write(f"- **Per-page text files:** `pages/page_XXX.txt`\n")
        f.write(f"- **Word bounding boxes:** `pages/page_XXX_words.json`\n")
        f.write(f"- **Combined text:** `extracted_text.txt`\n")
        f.write(f"- **OCR log:** `_ocr_pages.json`\n")
        f.write(f"\n## Technical Details\n")
        f.write(f"- **pdfplumber layout parameters:** x_density=7.25, y_density=13\n")
        f.write(f"- **OCR engine:** Tesseract with config '--oem 3 --psm 6'\n")
        f.write(f"- **OCR resolution:** 300 DPI for optimal accuracy\n")

    print(f"Lab 1 Text Extraction Complete:")
    print(f"   Per-page .txt files: {len(pages_data)} files created")
    print(f"   OCR log: {len(ocr_pages)} pages required OCR")
    print(f"   Word bounding boxes: Saved for layout analysis")
    print(f"   Output location: {text_root}")


def main():
    parser = argparse.ArgumentParser(
        description="Lab 1: Text Extraction with pdfplumber + OCR fallback"
    )
    parser.add_argument(
        "--in", dest="input_path", required=True, help="Input PDF file or directory"
    )
    parser.add_argument(
        "--out",
        dest="output_dir",
        required=True,
        help="Output directory for parsed results",
    )
    args = parser.parse_args()

    input_path = Path(args.input_path)
    out_dir = Path(args.output_dir)

    if input_path.is_dir():
        pdf_files = list(input_path.glob("*.pdf"))
    else:
        pdf_files = [input_path]

    for pdf_path in pdf_files:
        print(f"\nProcessing: {pdf_path.name}")
        pages_data, ocr_pages = extract_text_with_pdfplumber(pdf_path)
        save_extracted_data(pages_data, ocr_pages, pdf_path.name, out_dir)


if __name__ == "__main__":
    main()
