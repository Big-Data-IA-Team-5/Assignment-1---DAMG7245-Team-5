"""
Camelot-based table extraction functionality.

This module provides functions for extracting tables from PDFs using
the Camelot library with both lattice and stream modes.
"""

import camelot
from pathlib import Path
from typing import List, Dict, Any


def extract_tables_camelot_lattice(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extract tables using Camelot lattice mode.
    
    Lattice mode relies on ruling lines to detect table boundaries.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of extracted table dictionaries with metadata
    """
    print("=== CAMELOT LATTICE MODE ===")

    try:
        tables = camelot.read_pdf(str(pdf_path), flavor="lattice", pages="all")
        print(f"Found {len(tables)} tables using lattice mode")

        results = []
        for i, table in enumerate(tables):
            print(
                f"  Table {i+1}: {table.shape[0]} rows x {table.shape[1]} cols, "
                f"accuracy: {table.accuracy:.2f}"
            )

            results.append({
                "table_num": i + 1,
                "method": "camelot_lattice",
                "shape": table.shape,
                "accuracy": table.accuracy,
                "dataframe": table.df,
                "page": table.page,
            })

        return results

    except Exception as e:
        print(f"Lattice mode error: {e}")
        return []


def extract_tables_camelot_stream(pdf_path: Path) -> List[Dict[str, Any]]:
    """
    Extract tables using Camelot stream mode.
    
    Stream mode infers columns by grouping text spans.
    
    Args:
        pdf_path: Path to the PDF file
        
    Returns:
        List of extracted table dictionaries with metadata
    """
    print("\n=== CAMELOT STREAM MODE ===")

    try:
        tables = camelot.read_pdf(str(pdf_path), flavor="stream", pages="all")
        print(f"Found {len(tables)} tables using stream mode")

        results = []
        for i, table in enumerate(tables):
            print(
                f"  Table {i+1}: {table.shape[0]} rows x {table.shape[1]} cols, "
                f"accuracy: {table.accuracy:.2f}, page: {table.page}"
            )

            results.append({
                "table_num": i + 1,
                "method": "camelot_stream",
                "shape": table.shape,
                "accuracy": table.accuracy,
                "dataframe": table.df,
                "page": table.page,
            })

        return results

    except Exception as e:
        print(f"Stream mode error: {e}")
        return []