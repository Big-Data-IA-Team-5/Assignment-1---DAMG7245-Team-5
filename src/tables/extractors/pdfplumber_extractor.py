"""
PDFPlumber-based table extraction functionality.

This module provides functions for extracting tables from PDFs using
the pdfplumber library, which is good for borderless tables.
"""

import pandas as pd
import pdfplumber
from pathlib import Path
from typing import List, Dict, Any


def extract_tables_pdfplumber(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extract tables using pdfplumber - all pages.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of extracted table dictionaries with metadata
    """
    print("\n=== PDFPLUMBER TABLE DETECTION ===")

    results = []

    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        print(f"Processing all {total_pages} pages...")

        for page_num, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()

            if page_tables:
                print(f"Page {page_num + 1}: Found {len(page_tables)} tables")

                for i, table_data in enumerate(page_tables):
                    if table_data and len(table_data) > 1:
                        df = pd.DataFrame(table_data[1:], columns=table_data[0])
                        df = df.dropna(how="all").dropna(axis=1, how="all")

                        if not df.empty:
                            print(f"  Table {i+1}: {df.shape[0]} rows x {df.shape[1]} cols")

                            results.append({
                                "page": page_num + 1,
                                "table_num": i + 1,
                                "method": "pdfplumber",
                                "shape": df.shape,
                                "dataframe": df,
                            })
            else:
                # Only print for first few and last few pages to avoid spam
                if page_num < 3 or page_num >= total_pages - 3:
                    print(f"Page {page_num + 1}: No tables detected")
                elif page_num == 3:
                    print("  ... (skipping no-table page messages) ...")

    return results