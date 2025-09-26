"""
Table processing and quality enhancement functionality.

This module provides functions for cleaning, processing, and enhancing
extracted tables to improve their quality and usability.
"""

import re
import pandas as pd
from typing import List, Dict, Any, Optional


def clean_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    """
    Clean a dataframe by removing empty rows/columns and whitespace.
    
    Args:
        df: Input dataframe
        
    Returns:
        Cleaned dataframe
    """
    if df.empty:
        return df
        
    # Remove empty rows and columns
    df = df.dropna(how="all").dropna(axis=1, how="all")
    
    # Clean string values
    for col in df.columns:
        if df[col].dtype == "object":
            df[col] = df[col].astype(str).str.strip()
            df[col] = df[col].replace(["nan", "None", ""], pd.NA)
    
    return df


def check_financial_content(df: pd.DataFrame) -> bool:
    """
    Check if a dataframe contains financial content.
    
    Args:
        df: Input dataframe
        
    Returns:
        True if financial content is detected
    """
    financial_keywords = [
        "revenue", "income", "expense", "profit", "cash", "balance",
        "assets", "liability", "dividend", "earnings", "$", "million",
        "billion", "fiscal", "quarter", "year ended", "december"
    ]
    
    text_content = df.to_string().lower()
    return any(keyword in text_content for keyword in financial_keywords)


def assess_table_content_quality(df: pd.DataFrame) -> float:
    """
    Assess the quality of table content to filter out noise.
    
    Args:
        df: Input dataframe
        
    Returns:
        Quality score between 0.0 and 1.0
    """
    if df.empty:
        return 0.0

    total_cells = df.size
    meaningful_cells = 0

    for col in df.columns:
        for cell in df[col]:
            if pd.notna(cell):
                cell_str = str(cell).strip()
                if cell_str and cell_str not in ["", "nan", "None"]:
                    # Check for meaningful content
                    if len(cell_str) >= 2 and (
                        re.search(r"[a-zA-Z]", cell_str) or  # Contains letters
                        re.search(r"\\d", cell_str)           # Contains numbers
                    ):
                        meaningful_cells += 1

    return meaningful_cells / total_cells if total_cells > 0 else 0.0


def enhance_table_quality(df: pd.DataFrame, table_id: str) -> Optional[pd.DataFrame]:
    """
    Enhance table quality with comprehensive cleaning.
    
    Args:
        df: Input dataframe
        table_id: Identifier for the table
        
    Returns:
        Enhanced dataframe or None if table is too poor quality
    """
    if df is None or df.empty:
        return None

    # Make a copy to avoid modifying original
    df_clean = df.copy()

    # Step 1: Clean up NA values and empty cells
    df_clean = clean_dataframe(df_clean)

    # Step 2: Check if we still have meaningful content
    if df_clean.empty or df_clean.shape[0] < 2 or df_clean.shape[1] < 2:
        return None

    # Step 3: Assess content quality
    quality_score = assess_table_content_quality(df_clean)
    
    # Only keep tables with reasonable quality
    if quality_score < 0.3:
        return None

    return df_clean


def consolidate_results(
    lattice_results: List[Dict[str, Any]], 
    stream_results: List[Dict[str, Any]], 
    pdfplumber_results: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Consolidate results from different extraction methods.
    
    Args:
        lattice_results: Results from Camelot lattice mode
        stream_results: Results from Camelot stream mode  
        pdfplumber_results: Results from pdfplumber
        
    Returns:
        Dictionary with consolidated results and analysis
    """
    all_results = {
        "lattice": lattice_results,
        "stream": stream_results, 
        "pdfplumber": pdfplumber_results
    }
    
    total_tables = len(lattice_results) + len(stream_results) + len(pdfplumber_results)
    
    # Count tables with financial content
    financial_count = 0
    for results in all_results.values():
        for table in results:
            if "dataframe" in table and check_financial_content(table["dataframe"]):
                financial_count += 1
    
    analysis = {
        "total_tables": total_tables,
        "financial_tables": financial_count,
        "methods_used": len([r for r in all_results.values() if r]),
        "by_method": {method: len(results) for method, results in all_results.items()},
        "results": all_results
    }
    
    return analysis