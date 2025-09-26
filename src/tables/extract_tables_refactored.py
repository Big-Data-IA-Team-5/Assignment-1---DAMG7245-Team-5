"""
Main table extraction interface using modular components.

This module provides a clean, production-ready interface for table extraction
using the refactored modular components.
"""

import json
from pathlib import Path
from typing import Dict, Any, List, Optional

from .extractors.camelot_extractor import (
    extract_tables_camelot_lattice,
    extract_tables_camelot_stream,
)
from .extractors.pdfplumber_extractor import extract_tables_pdfplumber
from .processors.table_processor import (
    consolidate_results,
    enhance_table_quality,
    check_financial_content,
)


class TableExtractor:
    """Production-ready table extraction class."""
    
    def __init__(self, output_dir: Optional[Path] = None):
        """
        Initialize the table extractor.
        
        Args:
            output_dir: Directory to save extracted tables
        """
        self.output_dir = output_dir or Path("data/parsed/tables")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def extract_all_methods(self, pdf_path: Path) -> Dict[str, Any]:
        """
        Extract tables using all available methods.
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dictionary containing results from all extraction methods
        """
        print(f"\\n{'=' * 60}")
        print(f"EXTRACTING TABLES FROM: {pdf_path.name}")
        print(f"{'=' * 60}")
        
        # Extract using all methods
        lattice_results = extract_tables_camelot_lattice(pdf_path)
        stream_results = extract_tables_camelot_stream(pdf_path)
        pdfplumber_results = extract_tables_pdfplumber(pdf_path)
        
        # Consolidate and analyze results
        analysis = consolidate_results(lattice_results, stream_results, pdfplumber_results)
        
        # Enhance table quality
        enhanced_results = self._enhance_all_tables(analysis["results"])
        analysis["enhanced_results"] = enhanced_results
        
        return analysis
    
    def _enhance_all_tables(self, results: Dict[str, List]) -> Dict[str, List]:
        """Enhance table quality for all extraction methods."""
        enhanced = {}
        
        for method, tables in results.items():
            enhanced_tables = []
            for table in tables:
                if "dataframe" in table:
                    enhanced_df = enhance_table_quality(
                        table["dataframe"], 
                        f"{method}_{table.get('table_num', 0)}"
                    )
                    if enhanced_df is not None:
                        table["dataframe"] = enhanced_df
                        table["enhanced"] = True
                        enhanced_tables.append(table)
                    else:
                        table["enhanced"] = False
                        # Keep original for analysis but mark as poor quality
                        enhanced_tables.append(table)
            
            enhanced[method] = enhanced_tables
        
        return enhanced
    
    def save_results(self, analysis: Dict[str, Any], pdf_name: str) -> Dict[str, Any]:
        """
        Save extraction results to files.
        
        Args:
            analysis: Analysis results from extract_all_methods
            pdf_name: Name of the source PDF (without extension)
            
        Returns:
            Dictionary with save statistics
        """
        saved_tables = 0
        financial_tables = []
        
        # Create method-specific directories
        for method in ["lattice", "stream", "pdfplumber"]:
            method_dir = self.output_dir / method
            method_dir.mkdir(exist_ok=True)
        
        # Save enhanced results
        enhanced_results = analysis.get("enhanced_results", {})
        
        for method, tables in enhanced_results.items():
            for table in tables:
                if table.get("enhanced", False) and "dataframe" in table:
                    df = table["dataframe"]
                    
                    # Generate filename
                    page = table.get("page", "unknown")
                    table_num = table.get("table_num", 0)
                    filename = f"{pdf_name}_{method}_p{page}_t{table_num}.csv"
                    filepath = self.output_dir / method / filename
                    
                    # Save to CSV
                    df.to_csv(filepath, index=False)
                    saved_tables += 1
                    
                    # Check for financial content
                    if check_financial_content(df):
                        financial_tables.append(str(filepath))
        
        # Save analysis summary
        summary = {
            "pdf_name": pdf_name,
            "total_extracted": analysis["total_tables"],
            "saved_tables": saved_tables,
            "financial_tables_count": len(financial_tables),
            "financial_tables": financial_tables,
            "methods_summary": analysis["by_method"],
        }
        
        summary_file = self.output_dir / f"{pdf_name}_extraction_summary.json"
        with open(summary_file, "w") as f:
            json.dump(summary, f, indent=2)
        
        return summary


def main():
    """Main function with command line interface."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Production Table Extraction with Modular Architecture"
    )
    parser.add_argument("--input", "-i", required=True, help="Input PDF file path")
    parser.add_argument("--output", "-o", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    # Validate input
    pdf_path = Path(args.input)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    # Initialize extractor
    extractor = TableExtractor(output_dir=Path(args.output))
    
    try:
        # Extract tables
        analysis = extractor.extract_all_methods(pdf_path)
        
        # Save results
        summary = extractor.save_results(analysis, pdf_path.stem)
        
        # Print summary
        print(f"\\n{'=' * 60}")
        print("EXTRACTION COMPLETE")
        print(f"{'=' * 60}")
        print(f"Total tables found: {summary['total_extracted']}")
        print(f"Tables saved: {summary['saved_tables']}")
        print(f"Financial tables: {summary['financial_tables_count']}")
        print(f"Results saved to: {extractor.output_dir}")
        
        return 0
        
    except Exception as e:
        print(f"Extraction failed: {e}")
        return 1


if __name__ == "__main__":
    exit(main())