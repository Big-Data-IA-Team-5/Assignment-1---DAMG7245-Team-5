"""
Page Extraction Utility for Google Document AI
Team 5 - DAMG7245 Fall 2025

This module provides functionality to extract specific pages from a PDF
and create temporary PDFs for Google Document AI processing.
"""

try:
    import PyPDF2
except ImportError:
    print("PyPDF2 is required. Install it with: pip install PyPDF2")
    raise

import logging
import random
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class PDFPageExtractor:
    """
    A utility class for extracting specific pages from PDF files.
    """

    def __init__(self, pdf_path):
        """
        Initialize the PDF page extractor.

        Args:
            pdf_path (str): Path to the original PDF file
        """
        self.pdf_path = Path(pdf_path)
        self.reader = None
        self.pdf_file_handle = None
        self.total_pages = 0

        if not self.pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        self._load_pdf()

    def __del__(self):
        """Close the PDF file handle when the object is destroyed."""
        if hasattr(self, "pdf_file_handle") and self.pdf_file_handle:
            self.pdf_file_handle.close()

    def close(self):
        """Explicitly close the PDF file handle."""
        if self.pdf_file_handle:
            self.pdf_file_handle.close()
            self.pdf_file_handle = None

    def _load_pdf(self):
        """Load the PDF file and initialize the reader."""
        try:
            self.pdf_file_handle = open(self.pdf_path, "rb")
            self.reader = PyPDF2.PdfReader(self.pdf_file_handle)
            self.total_pages = len(self.reader.pages)
            logger.info(
                f"Loaded PDF: {self.pdf_path.name} with {self.total_pages} pages"
            )
        except Exception as e:
            logger.error(f"Failed to load PDF: {e}")
            raise

    def get_page_info(self):
        """
        Get information about the PDF file.

        Returns:
            dict: Information about the PDF including total pages, file size, etc.
        """
        try:
            metadata = self.reader.metadata if self.reader else None
        except:
            metadata = None  # Handle cases where metadata access fails

        return {
            "file_name": self.pdf_path.name,
            "file_path": str(self.pdf_path),
            "total_pages": self.total_pages,
            "file_size_mb": self.pdf_path.stat().st_size / (1024 * 1024),
            "metadata": metadata,
        }

    def extract_pages(self, page_numbers, output_path=None):
        """
        Extract specific pages from the PDF and create a new temporary PDF.

        Args:
            page_numbers: List of page numbers to extract (0-indexed)
            output_path: Path for the output PDF. If None, auto-generate.

        Returns:
            Path to the created temporary PDF
        """
        # Validate page numbers
        invalid_pages = [p for p in page_numbers if p < 0 or p >= self.total_pages]
        if invalid_pages:
            raise ValueError(
                f"Invalid page numbers: {invalid_pages}. PDF has {self.total_pages} pages (0-{self.total_pages-1})"
            )

        # Generate output path if not provided
        if output_path is None:
            pages_str = "_".join(
                map(str, [p + 1 for p in page_numbers])
            )  # Convert to 1-indexed for filename
            output_path = (
                self.pdf_path.parent
                / "temp_pdfs"
                / f"{self.pdf_path.stem}_pages_{pages_str}.pdf"
            )

        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Create new PDF with selected pages
        try:
            with open(self.pdf_path, "rb") as input_file:
                reader = PyPDF2.PdfReader(input_file)
                writer = PyPDF2.PdfWriter()

                # Add selected pages to writer
                for page_num in page_numbers:
                    writer.add_page(reader.pages[page_num])

                # Write to temporary file
                with open(output_path, "wb") as output_file:
                    writer.write(output_file)

            logger.info(
                f"Created temporary PDF with {len(page_numbers)} pages: {output_path}"
            )
            return str(output_path)

        except Exception as e:
            logger.error(f"Failed to extract pages: {e}")
            raise

    def extract_random_pages(self, num_pages=2, seed=None):
        """
        Extract random pages from the PDF.

        Args:
            num_pages: Number of random pages to extract
            seed: Random seed for reproducible results

        Returns:
            (temp_pdf_path, selected_page_numbers)
        """
        if seed is not None:
            random.seed(seed)

        if num_pages > self.total_pages:
            raise ValueError(
                f"Cannot extract {num_pages} pages from a {self.total_pages}-page PDF"
            )

        # Select random pages (0-indexed)
        selected_pages = sorted(random.sample(range(self.total_pages), num_pages))

        logger.info(
            f"Randomly selected pages: {[p+1 for p in selected_pages]} (1-indexed)"
        )

        temp_pdf_path = self.extract_pages(selected_pages)

        return temp_pdf_path, selected_pages

    def extract_specific_pages(self, page_numbers):
        """
        Extract specific pages (1-indexed for user convenience).

        Args:
            page_numbers: List of page numbers to extract (1-indexed)

        Returns:
            Path to the created temporary PDF
        """
        # Convert to 0-indexed
        zero_indexed_pages = [p - 1 for p in page_numbers]

        logger.info(f"Extracting pages: {page_numbers} (1-indexed)")

        return self.extract_pages(zero_indexed_pages)


def extract_pages_for_google_ai(pdf_path, page_numbers, output_dir=None):
    """
    Convenience function to extract pages for Google Document AI processing.

    Args:
        pdf_path: Path to the original PDF
        page_numbers: Page numbers to extract (1-indexed)
        output_dir: Directory for temporary files

    Returns:
        Information about the extraction including temp PDF path
    """
    extractor = PDFPageExtractor(pdf_path)

    if output_dir:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        pages_str = "_".join(map(str, page_numbers))
        output_path = output_dir / f"{Path(pdf_path).stem}_pages_{pages_str}.pdf"
    else:
        output_path = None

    temp_pdf_path = extractor.extract_specific_pages(page_numbers)

    return {
        "original_pdf": pdf_path,
        "temp_pdf": temp_pdf_path,
        "extracted_pages": page_numbers,
        "total_pages_in_original": extractor.total_pages,
        "pdf_info": extractor.get_page_info(),
        "temp_file_size_mb": Path(temp_pdf_path).stat().st_size / (1024 * 1024),
    }


# Example usage and testing
if __name__ == "__main__":
    # Example: Extract pages 5 and 12 from Tesla PDF
    pdf_file = "data/raw/tesla.pdf"

    try:
        # Method 1: Extract specific pages
        extractor = PDFPageExtractor(pdf_file)
        print(f"PDF Info: {extractor.get_page_info()}")

        # Extract pages 5 and 12 (1-indexed)
        temp_pdf = extractor.extract_specific_pages([5, 12])
        print(f"Temporary PDF created: {temp_pdf}")

        # Method 2: Extract random pages
        temp_pdf_random, selected_pages = extractor.extract_random_pages(
            num_pages=2, seed=42
        )
        print(
            f"Random pages {[p+1 for p in selected_pages]} extracted to: {temp_pdf_random}"
        )

        # Method 3: Using convenience function
        result = extract_pages_for_google_ai(pdf_file, [1, 10], "data/temp")
        print(f"Extraction result: {result}")

    except Exception as e:
        print(f"Error: {e}")
