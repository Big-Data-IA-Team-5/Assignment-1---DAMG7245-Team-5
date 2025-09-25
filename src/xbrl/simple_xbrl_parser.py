"""
Simple XBRL Parser Module for Project LANTERN

This module provides a fallback XBRL parser using basic XML parsing
when the arelle library has compatibility issues.

Dependencies:
    - lxml: XML processing
    - pandas: Data manipulation
"""

import os
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from datetime import datetime
import warnings
from lxml import etree
import xml.etree.ElementTree as ET

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SimpleXBRLParser:
    """
    Simple XBRL Parser for extracting financial data from XBRL filings.
    
    This class provides basic XBRL parsing using XML parsing when
    the arelle library is not available or has compatibility issues.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize Simple XBRL Parser.
        
        Args:
            config: Optional configuration dictionary with parsing parameters
        """
        self.config = config or {}
        
        # Common XBRL namespaces
        self.namespaces = {
            'xbrli': 'http://www.xbrl.org/2003/instance',
            'link': 'http://www.xbrl.org/2003/linkbase',
            'xlink': 'http://www.w3.org/1999/xlink',
            'us-gaap': 'http://fasb.org/us-gaap/2023',
            'dei': 'http://xbrl.sec.gov/dei/2023',
            'tsla': 'http://www.tesla.com/20240630',
        }
        
        # Key financial concepts to look for
        self.key_concepts = [
            'Revenues', 'Revenue', 'SalesRevenueNet',
            'NetIncomeLoss', 'NetIncome', 'ProfitLoss',
            'Assets', 'TotalAssets', 'AssetsCurrent',
            'Liabilities', 'LiabilitiesAndStockholdersEquity',
            'StockholdersEquity', 'ShareholdersEquity',
            'CashAndCashEquivalentsAtCarryingValue',
            'OperatingIncomeLoss', 'GrossProfit',
            'CostOfRevenue', 'CostOfGoodsAndServicesSold',
            'ResearchAndDevelopmentExpense',
            'SellingGeneralAndAdministrativeExpenses',
            'PropertyPlantAndEquipmentNet',
            'Goodwill', 'IntangibleAssetsNetExcludingGoodwill'
        ]
    
    def parse_xbrl_file(self, xbrl_path: str) -> pd.DataFrame:
        """
        Parse XBRL file and extract financial facts.
        
        Args:
            xbrl_path: Path to the XBRL file
            
        Returns:
            DataFrame containing extracted financial facts
        """
        logger.info(f"Parsing XBRL file: {xbrl_path}")
        
        if not os.path.exists(xbrl_path):
            raise FileNotFoundError(f"XBRL file not found: {xbrl_path}")
        
        try:
            # Parse XML
            tree = etree.parse(xbrl_path)
            root = tree.getroot()
            
            # Update namespaces from the document
            self._update_namespaces(root)
            
            # Extract facts
            facts = self._extract_facts_from_xml(root)
            
            # Convert to DataFrame
            if facts:
                df = pd.DataFrame(facts)
                df = self._clean_and_process_data(df)
                logger.info(f"Successfully extracted {len(df)} facts from XBRL file")
                return df
            else:
                logger.warning("No facts found in XBRL file")
                return pd.DataFrame()
                
        except Exception as e:
            logger.error(f"Error parsing XBRL file: {e}")
            raise
    
    def _update_namespaces(self, root):
        """Update namespaces from the XML document."""
        # Extract namespaces from the root element
        for prefix, uri in root.nsmap.items():
            if prefix:  # Skip default namespace (None)
                self.namespaces[prefix] = uri
    
    def _extract_facts_from_xml(self, root) -> List[Dict[str, Any]]:
        """
        Extract financial facts from XML root element.
        
        Args:
            root: XML root element
            
        Returns:
            List of fact dictionaries
        """
        facts = []
        
        # Find all elements that look like financial facts
        for elem in root.iter():
            # Skip if element has no text content
            if elem.text is None or elem.text.strip() == '':
                continue
            
            # Get the local name (concept name)
            local_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
            
            # Check if this looks like a financial concept
            if self._is_relevant_concept(local_name):
                fact = self._extract_fact_data(elem, local_name)
                if fact:
                    facts.append(fact)
        
        return facts
    
    def _is_relevant_concept(self, concept_name: str) -> bool:
        """
        Check if a concept is relevant for financial analysis.
        
        Args:
            concept_name: Name of the concept
            
        Returns:
            True if concept is relevant
        """
        if not concept_name:
            return False
        
        # Check against key concepts list
        for key_concept in self.key_concepts:
            if key_concept.lower() in concept_name.lower():
                return True
        
        # Check for common financial patterns
        financial_patterns = [
            'revenue', 'income', 'profit', 'loss', 'asset', 'liability',
            'equity', 'cash', 'expense', 'cost', 'sales', 'earnings',
            'balance', 'debt', 'capital', 'investment', 'dividend'
        ]
        
        concept_lower = concept_name.lower()
        return any(pattern in concept_lower for pattern in financial_patterns)
    
    def _extract_fact_data(self, elem, concept_name: str) -> Optional[Dict[str, Any]]:
        """
        Extract data from a fact element.
        
        Args:
            elem: XML element
            concept_name: Name of the concept
            
        Returns:
            Dictionary with fact data or None
        """
        try:
            # Get the value
            value_text = elem.text.strip() if elem.text else ''
            if not value_text:
                return None
            
            # Try to parse as numeric
            numeric_value = self._parse_numeric_value(value_text)
            
            # Extract attributes
            context_ref = elem.get('contextRef', '')
            unit_ref = elem.get('unitRef', '')
            decimals = elem.get('decimals', '')
            precision = elem.get('precision', '')
            
            # Get period information from context
            period_info = self._extract_period_info(elem, context_ref)
            
            fact_data = {
                'concept': concept_name,
                'value': numeric_value if numeric_value is not None else value_text,
                'value_text': value_text,
                'context_ref': context_ref,
                'unit_ref': unit_ref,
                'decimals': decimals,
                'precision': precision,
                'namespace': elem.tag.split('}')[0].strip('{}') if '}' in elem.tag else '',
                **period_info
            }
            
            return fact_data
            
        except Exception as e:
            logger.debug(f"Error extracting fact data for {concept_name}: {e}")
            return None
    
    def _parse_numeric_value(self, value_text: str) -> Optional[float]:
        """Parse numeric value from text."""
        try:
            # Remove common formatting
            clean_value = value_text.replace(',', '').replace('$', '').replace('(', '-').replace(')', '')
            return float(clean_value)
        except (ValueError, TypeError):
            return None
    
    def _extract_period_info(self, elem, context_ref: str) -> Dict[str, str]:
        """
        Extract period information for a fact.
        
        Args:
            elem: XML element
            context_ref: Context reference
            
        Returns:
            Dictionary with period information
        """
        period_info = {
            'period_start': '',
            'period_end': '',
            'period_type': '',
            'segment': ''
        }
        
        try:
            # Find the context element
            root = elem.getroottree().getroot()
            
            # Look for context with matching id
            for context in root.iter():
                if context.get('id') == context_ref:
                    # Extract period information
                    for period in context.iter():
                        tag_name = period.tag.split('}')[-1] if '}' in period.tag else period.tag
                        
                        if tag_name == 'startDate' and period.text:
                            period_info['period_start'] = period.text.strip()
                        elif tag_name == 'endDate' and period.text:
                            period_info['period_end'] = period.text.strip()
                        elif tag_name == 'instant' and period.text:
                            period_info['period_end'] = period.text.strip()
                            period_info['period_type'] = 'instant'
                        elif period_info['period_start'] and period_info['period_end']:
                            period_info['period_type'] = 'duration'
                    break
        except Exception as e:
            logger.debug(f"Error extracting period info: {e}")
        
        return period_info
    
    def _clean_and_process_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process the extracted DataFrame.
        
        Args:
            df: Raw DataFrame
            
        Returns:
            Processed DataFrame
        """
        if df.empty:
            return df
        
        # Sort by concept name
        df = df.sort_values('concept')
        
        # Add metadata
        df['extraction_timestamp'] = datetime.now().isoformat()
        df['parser_type'] = 'simple_xml'
        
        # Filter out empty values
        df = df[df['value_text'].str.strip() != '']
        
        return df.reset_index(drop=True)
    
    def parse_multiple_xbrl_files(self, directory: str, file_pattern: str = "*.xml") -> Dict[str, pd.DataFrame]:
        """
        Parse multiple XBRL files from a directory.
        
        Args:
            directory: Directory containing XBRL files
            file_pattern: File pattern to match (simplified to just *.xml)
            
        Returns:
            Dictionary mapping file names to DataFrames
        """
        import glob
        
        xbrl_data = {}
        
        # Handle the pattern - just use *.xml for simplicity
        pattern = os.path.join(directory, "*.xml")
        xbrl_files = glob.glob(pattern)
        
        # Also try other common XBRL extensions
        for ext in ['*.xbrl', '*.htm']:
            pattern = os.path.join(directory, ext)
            xbrl_files.extend(glob.glob(pattern))
        
        logger.info(f"Found {len(xbrl_files)} XBRL files in {directory}")
        
        for file_path in xbrl_files:
            try:
                filename = os.path.basename(file_path)
                logger.info(f"Parsing XBRL file: {filename}")
                
                df = self.parse_xbrl_file(file_path)
                xbrl_data[filename] = df
                
                logger.info(f"Successfully parsed {filename} - {len(df)} facts extracted")
                
            except Exception as e:
                logger.error(f"Error parsing {file_path}: {str(e)}")
                continue
        
        if not xbrl_data:
            logger.warning(f"No XBRL files successfully parsed from {directory}")
        
        return xbrl_data