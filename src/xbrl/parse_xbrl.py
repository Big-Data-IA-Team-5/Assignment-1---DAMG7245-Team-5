"""
XBRL Parser Module for Project LANTERN

This module handles parsing XBRL files and extracting financial data
into structured DataFrames for cross-verification with PDF table data.

Dependencies:
    - arelle: XBRL processing library
    - pandas: Data manipulation
    - lxml: XML processing
"""

import os
import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Any
from pathlib import Path
import json
from datetime import datetime
import warnings

# Suppress arelle warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)

try:
    # Fix Python 3.11 compatibility issues with collections
    import collections
    import collections.abc
    
    # Map deprecated collections attributes to collections.abc
    for attr_name in ['MutableSet', 'MutableMapping', 'MutableSequence', 'Mapping', 'Sequence', 'Set']:
        if not hasattr(collections, attr_name):
            setattr(collections, attr_name, getattr(collections.abc, attr_name))
    
    from arelle import Cntlr
    from arelle.ModelInstanceObject import ModelFact
    ARELLE_AVAILABLE = True
    # Import ModelXbrl as Any to avoid type issues when arelle is not available
    try:
        from arelle import ModelXbrl
    except ImportError:
        ModelXbrl = Any
except ImportError as e:
    ARELLE_AVAILABLE = False
    ModelXbrl = Any
    ModelFact = Any
    Cntlr = Any
    print(f"Warning: arelle library not available. Error: {e}")
    print("This may be due to Python version compatibility issues.")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class XBRLParser:
    """
    XBRL Parser for extracting financial data from XBRL filings.
    
    This class provides methods to parse XBRL files, extract key financial
    concepts, and convert them to pandas DataFrames for analysis.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize XBRL Parser.
        
        Args:
            config: Optional configuration dictionary with parsing parameters
        """
        if not ARELLE_AVAILABLE:
            raise ImportError("arelle library is required. Install with: pip install arelle")
        
        self.config = config or {}
        self.controller = None
        
        # Key financial concepts to extract
        self.key_concepts = self.config.get('key_concepts', [
            # Revenue and Income
            "Revenues", "Revenue", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet", "OperatingRevenues", "TotalRevenues",
            
            # Net Income
            "NetIncomeLoss", "NetIncomeAttributableToCommonShareholders",
            "NetIncomeAvailableToCommonStockholdersBasic", "ProfitLoss",
            
            # Assets
            "Assets", "AssetsCurrent", "AssetsNoncurrent", "TotalAssets",
            
            # Liabilities
            "Liabilities", "LiabilitiesCurrent", "LiabilitiesNoncurrent", 
            "TotalLiabilities", "LiabilitiesAndStockholdersEquity",
            
            # Equity
            "StockholdersEquity", "TotalStockholdersEquity", "ShareholdersEquity",
            
            # Cash Flow
            "CashAndCashEquivalentsAtCarryingValue", "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInInvestingActivities", "NetCashProvidedByUsedInFinancingActivities",
            
            # Additional key items
            "CostOfGoodsAndServicesSold", "CostOfRevenue", "OperatingIncomeLoss",
            "GrossProfit", "ResearchAndDevelopmentExpense", "SellingGeneralAndAdministrativeExpense"
        ])
        
        # Context filters for relevant periods
        self.context_filters = self.config.get('context_filters', {
            'period_type': ['instant', 'duration'],
            'exclude_segments': True  # Exclude segment-specific data
        })
    
    def initialize_controller(self):
        """Initialize the Arelle controller."""
        if self.controller is None:
            # Create controller with minimal configuration to avoid directory issues
            self.controller = Cntlr.Cntlr(logFileName=None, hasGui=False)
            logger.info("Arelle controller initialized")
    
    def parse_xbrl_file(self, xbrl_path: str) -> pd.DataFrame:
        """
        Parse a single XBRL file and extract financial data.
        
        Args:
            xbrl_path: Path to the XBRL file
            
        Returns:
            DataFrame with extracted XBRL facts
        """
        self.initialize_controller()
        
        if not os.path.exists(xbrl_path):
            raise FileNotFoundError(f"XBRL file not found: {xbrl_path}")
        
        logger.info(f"Parsing XBRL file: {xbrl_path}")
        
        try:
            # Load the XBRL model
            model_xbrl = self.controller.modelManager.load(xbrl_path)
            
            if model_xbrl is None:
                raise ValueError(f"Failed to load XBRL model from {xbrl_path}")
            
            # Extract facts
            facts_data = self._extract_facts(model_xbrl)
            
            # Convert to DataFrame
            df_xbrl = pd.DataFrame(facts_data)
            
            if df_xbrl.empty:
                logger.warning(f"No relevant facts found in {xbrl_path}")
                return pd.DataFrame()
            
            # Clean and process the data
            df_xbrl = self._clean_xbrl_data(df_xbrl)
            
            logger.info(f"Extracted {len(df_xbrl)} facts from XBRL file")
            return df_xbrl
            
        except Exception as e:
            logger.error(f"Error parsing XBRL file {xbrl_path}: {str(e)}")
            raise
        
        finally:
            # Clean up model to free memory
            if 'model_xbrl' in locals() and model_xbrl:
                model_xbrl.close()
    
    def _extract_facts(self, model_xbrl: ModelXbrl) -> List[Dict[str, Any]]:
        """
        Extract relevant facts from XBRL model.
        
        Args:
            model_xbrl: Loaded XBRL model
            
        Returns:
            List of fact dictionaries
        """
        facts_data = []
        
        for fact in model_xbrl.facts:
            try:
                concept_name = fact.concept.localName if fact.concept else None
                
                # Filter by key concepts
                if concept_name and self._is_relevant_concept(concept_name):
                    fact_data = self._extract_fact_data(fact)
                    if fact_data:
                        facts_data.append(fact_data)
                        
            except Exception as e:
                logger.warning(f"Error processing fact: {str(e)}")
                continue
        
        return facts_data
    
    def _is_relevant_concept(self, concept_name: str) -> bool:
        """
        Check if a concept is in our list of key financial concepts.
        
        Args:
            concept_name: Name of the XBRL concept
            
        Returns:
            True if concept is relevant
        """
        return concept_name in self.key_concepts
    
    def _extract_fact_data(self, fact: ModelFact) -> Optional[Dict[str, Any]]:
        """
        Extract data from a single XBRL fact.
        
        Args:
            fact: XBRL fact object
            
        Returns:
            Dictionary with fact data or None if invalid
        """
        try:
            # Get basic fact information
            concept_name = fact.concept.localName
            value = fact.value
            context_id = fact.contextID
            
            # Get context information
            context = fact.context if fact.context else None
            period_info = self._extract_period_info(context) if context else {}
            
            # Get unit information
            unit_info = self._extract_unit_info(fact)
            
            # Skip if value is None or empty
            if value is None or value == "":
                return None
            
            # Convert numeric values
            numeric_value = self._convert_to_numeric(value)
            
            fact_data = {
                'concept': concept_name,
                'value': value,
                'numeric_value': numeric_value,
                'context_id': context_id,
                'unit': unit_info.get('unit'),
                'currency': unit_info.get('currency'),
                'period_type': period_info.get('period_type'),
                'start_date': period_info.get('start_date'),
                'end_date': period_info.get('end_date'),
                'instant_date': period_info.get('instant_date'),
                'segment': period_info.get('segment'),
                'entity': period_info.get('entity')
            }
            
            return fact_data
            
        except Exception as e:
            logger.warning(f"Error extracting fact data: {str(e)}")
            return None
    
    def _extract_period_info(self, context) -> Dict[str, Any]:
        """
        Extract period information from context.
        
        Args:
            context: XBRL context object
            
        Returns:
            Dictionary with period information
        """
        period_info = {}
        
        try:
            if hasattr(context, 'period'):
                period = context.period
                
                if hasattr(period, 'isInstantPeriod') and period.isInstantPeriod:
                    period_info['period_type'] = 'instant'
                    if hasattr(period, 'instant'):
                        period_info['instant_date'] = str(period.instant)
                elif hasattr(period, 'isStartEndPeriod') and period.isStartEndPeriod:
                    period_info['period_type'] = 'duration'
                    if hasattr(period, 'startDate'):
                        period_info['start_date'] = str(period.startDate)
                    if hasattr(period, 'endDate'):
                        period_info['end_date'] = str(period.endDate)
            
            # Extract entity information
            if hasattr(context, 'entity'):
                entity = context.entity
                if hasattr(entity, 'identifier'):
                    period_info['entity'] = str(entity.identifier)
            
            # Extract segment information (for dimensional data)
            if hasattr(context, 'segDimValues') and context.segDimValues:
                period_info['segment'] = str(context.segDimValues)
            
        except Exception as e:
            logger.warning(f"Error extracting period info: {str(e)}")
        
        return period_info
    
    def _extract_unit_info(self, fact) -> Dict[str, Optional[str]]:
        """
        Extract unit and currency information from fact.
        
        Args:
            fact: XBRL fact object
            
        Returns:
            Dictionary with unit information
        """
        unit_info = {'unit': None, 'currency': None}
        
        try:
            if hasattr(fact, 'unit') and fact.unit:
                unit = fact.unit
                if hasattr(unit, 'measures'):
                    measures = unit.measures
                    if measures and len(measures) > 0:
                        if len(measures[0]) > 0:
                            measure = measures[0][0]
                            unit_info['unit'] = measure.localName
                            
                            # Check if it's a currency
                            if measure.namespaceURI and 'iso4217' in measure.namespaceURI.lower():
                                unit_info['currency'] = measure.localName
                            
        except Exception as e:
            logger.warning(f"Error extracting unit info: {str(e)}")
        
        return unit_info
    
    def _convert_to_numeric(self, value: str) -> Optional[float]:
        """
        Convert string value to numeric.
        
        Args:
            value: String value from XBRL
            
        Returns:
            Numeric value or None if conversion fails
        """
        try:
            # Remove common formatting
            cleaned_value = str(value).replace(',', '').replace('$', '').strip()
            return float(cleaned_value)
        except (ValueError, TypeError):
            return None
    
    def _clean_xbrl_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Clean and process the extracted XBRL data.
        
        Args:
            df: Raw XBRL DataFrame
            
        Returns:
            Cleaned DataFrame
        """
        # Remove duplicates based on concept, context, and value
        df = df.drop_duplicates(subset=['concept', 'context_id', 'numeric_value'])
        
        # Filter out segment-specific data if configured
        if self.context_filters.get('exclude_segments', True):
            df = df[df['segment'].isna()]
        
        # Sort by concept and period
        df = df.sort_values(['concept', 'end_date', 'instant_date'], na_position='last')
        
        return df
    
    def parse_multiple_xbrl_files(self, xbrl_directory: str, 
                                file_pattern: str = "*.xml") -> Dict[str, pd.DataFrame]:
        """
        Parse multiple XBRL files in a directory.
        
        Args:
            xbrl_directory: Directory containing XBRL files
            file_pattern: File pattern to match (default: *.xml)
            
        Returns:
            Dictionary mapping file names to DataFrames
        """
        xbrl_path = Path(xbrl_directory)
        if not xbrl_path.exists():
            raise FileNotFoundError(f"Directory not found: {xbrl_directory}")
        
        xbrl_files = list(xbrl_path.glob(file_pattern))
        if not xbrl_files:
            logger.warning(f"No XBRL files found in {xbrl_directory} with pattern {file_pattern}")
            return {}
        
        results = {}
        for xbrl_file in xbrl_files:
            try:
                df = self.parse_xbrl_file(str(xbrl_file))
                if not df.empty:
                    results[xbrl_file.name] = df
                    logger.info(f"Successfully parsed {xbrl_file.name}")
                else:
                    logger.warning(f"No data extracted from {xbrl_file.name}")
            except Exception as e:
                logger.error(f"Failed to parse {xbrl_file.name}: {str(e)}")
        
        return results
    
    def save_parsed_data(self, df: pd.DataFrame, output_path: str, 
                        format: str = 'csv') -> None:
        """
        Save parsed XBRL data to file.
        
        Args:
            df: DataFrame to save
            output_path: Output file path
            format: Output format ('csv', 'json', 'xlsx')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'csv':
            df.to_csv(output_path, index=False)
        elif format.lower() == 'json':
            df.to_json(output_path, orient='records', indent=2)
        elif format.lower() == 'xlsx':
            df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved XBRL data to {output_path}")
    
    def get_concept_summary(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Get summary of concepts found in XBRL data.
        
        Args:
            df: XBRL DataFrame
            
        Returns:
            Summary DataFrame with concept statistics
        """
        if df.empty:
            return pd.DataFrame()
        
        summary = df.groupby('concept').agg({
            'numeric_value': ['count', 'sum', 'mean', 'min', 'max'],
            'currency': lambda x: x.mode()[0] if not x.mode().empty else None,
            'period_type': lambda x: x.mode()[0] if not x.mode().empty else None
        }).round(2)
        
        # Flatten column names
        summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
        summary = summary.reset_index()
        
        return summary


def main():
    """
    Example usage of XBRLParser.
    """
    parser = XBRLParser()
    
    # Example: Parse a single XBRL file
    # xbrl_file = "data/raw/xbrl/TSLA_2023.xml"
    # df = parser.parse_xbrl_file(xbrl_file)
    # print(f"Extracted {len(df)} facts")
    
    # Example: Parse multiple files
    # results = parser.parse_multiple_xbrl_files("data/raw/xbrl/")
    # for filename, df in results.items():
    #     print(f"{filename}: {len(df)} facts")
    
    print("XBRL Parser module loaded successfully")


if __name__ == "__main__":
    main()