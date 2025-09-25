"""
XBRL Cross-Verification Module for Project LANTERN

This module provides functionality to parse XBRL filings, map PDF table data
to XBRL concepts, and perform cross-verification to identify discrepancies.

Modules:
    - parse_xbrl: XBRL parsing and DataFrame extraction
    - map_pdf_to_xbrl: Mapping PDF table labels to XBRL concepts
    - validate_xbrl: Cross-verification and discrepancy reporting
"""

__version__ = "1.0.0"
__author__ = "DAMG7245 Team 5"

from .parse_xbrl import XBRLParser
from .map_pdf_to_xbrl import PDFXBRLMapper
from .validate_xbrl import XBRLValidator

__all__ = ["XBRLParser", "PDFXBRLMapper", "XBRLValidator"]