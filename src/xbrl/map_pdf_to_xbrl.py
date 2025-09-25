"""
PDF-to-XBRL Mapping Module for Project LANTERN

This module provides functionality to map PDF table labels to XBRL concepts
using fuzzy matching and predefined mapping rules.

Dependencies:
    - fuzzywuzzy: Fuzzy string matching
    - pandas: Data manipulation
    - python-Levenshtein: Fast string matching (optional but recommended)
"""

import pandas as pd
import logging
from typing import Dict, List, Optional, Tuple, Set
import json
import re
from pathlib import Path

try:
    from fuzzywuzzy import fuzz, process
    FUZZYWUZZY_AVAILABLE = True
except ImportError:
    FUZZYWUZZY_AVAILABLE = False
    print("Warning: fuzzywuzzy not available. Please install with: pip install fuzzywuzzy python-Levenshtein")

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class PDFXBRLMapper:
    """
    PDF-to-XBRL Mapper for mapping PDF table labels to XBRL concepts.
    
    This class provides methods to automatically map extracted PDF table headers
    and labels to standardized XBRL concepts using fuzzy matching and predefined
    mapping rules.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize PDF-to-XBRL Mapper.
        
        Args:
            config: Optional configuration dictionary with mapping parameters
        """
        if not FUZZYWUZZY_AVAILABLE:
            logger.warning("fuzzywuzzy library not available. Some features may not work.")
        
        self.config = config or {}
        
        # Fuzzy matching parameters
        self.fuzzy_threshold = self.config.get('fuzzy_threshold', 80)
        self.fuzzy_scorer = self.config.get('fuzzy_scorer', fuzz.token_sort_ratio)
        
        # Initialize predefined mappings
        self.concept_mappings = self._load_concept_mappings()
        self.synonym_mappings = self._load_synonym_mappings()
        self.xbrl_concepts = self._load_xbrl_concepts()
        
        # Preprocessing patterns
        self.preprocessing_patterns = self._load_preprocessing_patterns()
    
    def _load_concept_mappings(self) -> Dict[str, str]:
        """
        Load predefined concept mappings from PDF labels to XBRL concepts.
        
        Returns:
            Dictionary mapping PDF labels to XBRL concepts
        """
        # Predefined mappings for common financial statement items
        mappings = {
            # Revenue mappings
            "revenue": "Revenues",
            "revenues": "Revenues",
            "total revenue": "Revenues",
            "total revenues": "Revenues",
            "net revenue": "Revenues",
            "net revenues": "Revenues",
            "sales": "Revenues",
            "net sales": "Revenues",
            "total sales": "Revenues",
            "revenue from operations": "Revenues",
            "operating revenue": "OperatingRevenues",
            "operating revenues": "OperatingRevenues",
            
            # Cost mappings
            "cost of revenue": "CostOfRevenue",
            "cost of revenues": "CostOfRevenue",
            "cost of sales": "CostOfGoodsAndServicesSold",
            "cost of goods sold": "CostOfGoodsAndServicesSold",
            "cogs": "CostOfGoodsAndServicesSold",
            
            # Profit/Income mappings
            "net income": "NetIncomeLoss",
            "net income (loss)": "NetIncomeLoss",
            "net loss": "NetIncomeLoss",
            "profit": "NetIncomeLoss",
            "profit (loss)": "NetIncomeLoss",
            "net profit": "NetIncomeLoss",
            "net profit (loss)": "NetIncomeLoss",
            "income from operations": "OperatingIncomeLoss",
            "operating income": "OperatingIncomeLoss",
            "operating income (loss)": "OperatingIncomeLoss",
            "gross profit": "GrossProfit",
            "gross margin": "GrossProfit",
            
            # Asset mappings
            "total assets": "Assets",
            "assets": "Assets",
            "current assets": "AssetsCurrent",
            "non-current assets": "AssetsNoncurrent",
            "noncurrent assets": "AssetsNoncurrent",
            "cash": "CashAndCashEquivalentsAtCarryingValue",
            "cash and cash equivalents": "CashAndCashEquivalentsAtCarryingValue",
            "cash and equivalents": "CashAndCashEquivalentsAtCarryingValue",
            
            # Liability mappings
            "total liabilities": "Liabilities",
            "liabilities": "Liabilities",
            "current liabilities": "LiabilitiesCurrent",
            "non-current liabilities": "LiabilitiesNoncurrent",
            "noncurrent liabilities": "LiabilitiesNoncurrent",
            
            # Equity mappings
            "stockholders' equity": "StockholdersEquity",
            "shareholders' equity": "StockholdersEquity",
            "stockholders equity": "StockholdersEquity",
            "shareholders equity": "StockholdersEquity",
            "total equity": "StockholdersEquity",
            "total stockholders' equity": "StockholdersEquity",
            "total shareholders' equity": "StockholdersEquity",
            
            # Expense mappings
            "research and development": "ResearchAndDevelopmentExpense",
            "r&d": "ResearchAndDevelopmentExpense",
            "rd": "ResearchAndDevelopmentExpense",
            "selling, general and administrative": "SellingGeneralAndAdministrativeExpense",
            "sg&a": "SellingGeneralAndAdministrativeExpense",
            "sga": "SellingGeneralAndAdministrativeExpense",
            "selling general and administrative": "SellingGeneralAndAdministrativeExpense",
            
            # Cash flow mappings
            "operating cash flow": "NetCashProvidedByUsedInOperatingActivities",
            "cash from operations": "NetCashProvidedByUsedInOperatingActivities",
            "cash flow from operations": "NetCashProvidedByUsedInOperatingActivities",
            "investing cash flow": "NetCashProvidedByUsedInInvestingActivities",
            "cash from investing": "NetCashProvidedByUsedInInvestingActivities",
            "cash flow from investing": "NetCashProvidedByUsedInInvestingActivities",
            "financing cash flow": "NetCashProvidedByUsedInFinancingActivities",
            "cash from financing": "NetCashProvidedByUsedInFinancingActivities",
            "cash flow from financing": "NetCashProvidedByUsedInFinancingActivities",
        }
        
        # Load custom mappings from config if available
        custom_mappings = self.config.get('custom_mappings', {})
        mappings.update(custom_mappings)
        
        return mappings
    
    def _load_synonym_mappings(self) -> Dict[str, List[str]]:
        """
        Load synonym mappings for XBRL concepts.
        
        Returns:
            Dictionary mapping XBRL concepts to lists of synonyms
        """
        synonyms = {
            "Revenues": [
                "revenue", "revenues", "sales", "net sales", "total revenue",
                "net revenue", "total revenues", "net revenues"
            ],
            "NetIncomeLoss": [
                "net income", "net loss", "profit", "net profit", "earnings",
                "net earnings", "income", "profit loss", "net income loss"
            ],
            "Assets": [
                "total assets", "assets"
            ],
            "StockholdersEquity": [
                "stockholders equity", "shareholders equity", "total equity",
                "stockholders' equity", "shareholders' equity"
            ],
            "CostOfRevenue": [
                "cost of revenue", "cost of sales", "cost of goods sold", "cogs"
            ],
            "GrossProfit": [
                "gross profit", "gross margin", "gross income"
            ],
            "OperatingIncomeLoss": [
                "operating income", "income from operations", "operating profit",
                "operating income loss"
            ]
        }
        
        return synonyms
    
    def _load_xbrl_concepts(self) -> List[str]:
        """
        Load list of standard XBRL concepts.
        
        Returns:
            List of XBRL concept names
        """
        concepts = [
            # Revenue concepts
            "Revenues", "Revenue", "RevenueFromContractWithCustomerExcludingAssessedTax",
            "SalesRevenueNet", "OperatingRevenues", "TotalRevenues",
            
            # Income concepts
            "NetIncomeLoss", "NetIncomeAttributableToCommonShareholders",
            "NetIncomeAvailableToCommonStockholdersBasic", "ProfitLoss",
            "OperatingIncomeLoss", "GrossProfit",
            
            # Asset concepts
            "Assets", "AssetsCurrent", "AssetsNoncurrent", "TotalAssets",
            "CashAndCashEquivalentsAtCarryingValue",
            
            # Liability concepts
            "Liabilities", "LiabilitiesCurrent", "LiabilitiesNoncurrent", 
            "TotalLiabilities", "LiabilitiesAndStockholdersEquity",
            
            # Equity concepts
            "StockholdersEquity", "TotalStockholdersEquity", "ShareholdersEquity",
            
            # Cost/Expense concepts
            "CostOfGoodsAndServicesSold", "CostOfRevenue",
            "ResearchAndDevelopmentExpense", "SellingGeneralAndAdministrativeExpense",
            
            # Cash Flow concepts
            "NetCashProvidedByUsedInOperatingActivities",
            "NetCashProvidedByUsedInInvestingActivities",
            "NetCashProvidedByUsedInFinancingActivities"
        ]
        
        return concepts
    
    def _load_preprocessing_patterns(self) -> List[Tuple[str, str]]:
        """
        Load preprocessing patterns for cleaning PDF labels.
        
        Returns:
            List of (pattern, replacement) tuples
        """
        patterns = [
            # Remove common prefixes/suffixes
            (r'\(in \$.*?\)', ''),  # Remove "(in $millions)" etc.
            (r'\(in thousands.*?\)', ''),  # Remove "(in thousands)" etc.
            (r'\$', ''),  # Remove dollar signs
            (r'\(.*?000.*?\)', ''),  # Remove amount indicators
            
            # Clean punctuation and spacing
            (r'[^\w\s&]', ' '),  # Replace non-alphanumeric (except &) with space
            (r'\s+', ' '),  # Multiple spaces to single space
            (r'^\s+|\s+$', ''),  # Trim whitespace
            
            # Standardize common terms
            (r'\b(and|&)\b', 'and'),  # Standardize "and"
            (r'\brd\b', 'research and development'),  # Expand R&D
            (r'\br&d\b', 'research and development'),
            (r'\bsga\b', 'selling general and administrative'),
            (r'\bsg&a\b', 'selling general and administrative'),
            (r'\bcogs\b', 'cost of goods sold'),
        ]
        
        return patterns
    
    def preprocess_label(self, label: str) -> str:
        """
        Preprocess a PDF label for better matching.
        
        Args:
            label: Raw PDF table label
            
        Returns:
            Cleaned label
        """
        if not label or not isinstance(label, str):
            return ""
        
        cleaned = label.lower().strip()
        
        # Apply preprocessing patterns
        for pattern, replacement in self.preprocessing_patterns:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)
        
        return cleaned.strip()
    
    def map_label_to_concept_exact(self, label: str) -> Optional[str]:
        """
        Try to map a label to XBRL concept using exact matching.
        
        Args:
            label: PDF table label
            
        Returns:
            Matching XBRL concept or None
        """
        cleaned_label = self.preprocess_label(label)
        
        # Check direct mapping
        if cleaned_label in self.concept_mappings:
            return self.concept_mappings[cleaned_label]
        
        return None
    
    def map_label_to_concept_fuzzy(self, label: str, 
                                 concepts: Optional[List[str]] = None) -> Optional[Tuple[str, int]]:
        """
        Try to map a label to XBRL concept using fuzzy matching.
        
        Args:
            label: PDF table label
            concepts: List of concepts to match against (default: self.xbrl_concepts)
            
        Returns:
            Tuple of (matching_concept, confidence_score) or None
        """
        if not FUZZYWUZZY_AVAILABLE:
            return None
        
        cleaned_label = self.preprocess_label(label)
        if not cleaned_label:
            return None
        
        # Use provided concepts or default list
        search_concepts = concepts or self.xbrl_concepts
        
        # Create search list including synonyms
        search_terms = []
        for concept in search_concepts:
            search_terms.append(concept)
            # Add synonyms if available
            if concept in self.synonym_mappings:
                search_terms.extend(self.synonym_mappings[concept])
        
        # Remove duplicates and convert to lowercase
        search_terms = list(set(term.lower() for term in search_terms))
        
        # Find best match
        try:
            match_result = process.extractOne(
                cleaned_label, 
                search_terms,
                scorer=self.fuzzy_scorer
            )
            
            if match_result and match_result[1] >= self.fuzzy_threshold:
                matched_term, score = match_result
                
                # Map back to original concept
                original_concept = self._map_term_to_concept(matched_term, search_concepts)
                if original_concept:
                    return original_concept, score
                    
        except Exception as e:
            logger.warning(f"Error in fuzzy matching for '{label}': {str(e)}")
        
        return None
    
    def _map_term_to_concept(self, matched_term: str, concepts: List[str]) -> Optional[str]:
        """
        Map a matched term back to its original XBRL concept.
        
        Args:
            matched_term: The matched term from fuzzy search
            concepts: List of original concepts
            
        Returns:
            Original XBRL concept or None
        """
        # Check if it's a direct concept match
        for concept in concepts:
            if concept.lower() == matched_term:
                return concept
        
        # Check if it's a synonym
        for concept, synonyms in self.synonym_mappings.items():
            if matched_term in [s.lower() for s in synonyms]:
                return concept
        
        return None
    
    def map_pdf_labels_to_xbrl(self, pdf_labels: List[str], 
                              xbrl_concepts: Optional[List[str]] = None,
                              include_confidence: bool = False) -> Dict[str, any]:
        """
        Map a list of PDF table labels to XBRL concepts.
        
        Args:
            pdf_labels: List of labels from PDF tables
            xbrl_concepts: Optional list of available XBRL concepts
            include_confidence: Whether to include confidence scores
            
        Returns:
            Dictionary mapping PDF labels to XBRL concepts
        """
        mapping = {}
        available_concepts = xbrl_concepts or self.xbrl_concepts
        
        for label in pdf_labels:
            if not label or not isinstance(label, str):
                continue
            
            # Try exact match first
            exact_match = self.map_label_to_concept_exact(label)
            if exact_match:
                if include_confidence:
                    mapping[label] = {"concept": exact_match, "confidence": 100, "method": "exact"}
                else:
                    mapping[label] = exact_match
                continue
            
            # Try fuzzy match
            fuzzy_result = self.map_label_to_concept_fuzzy(label, available_concepts)
            if fuzzy_result:
                concept, confidence = fuzzy_result
                if include_confidence:
                    mapping[label] = {"concept": concept, "confidence": confidence, "method": "fuzzy"}
                else:
                    mapping[label] = concept
            else:
                # No match found
                if include_confidence:
                    mapping[label] = {"concept": None, "confidence": 0, "method": "none"}
                else:
                    mapping[label] = None
        
        return mapping
    
    def create_mapping_dataframe(self, pdf_labels: List[str], 
                               xbrl_concepts: Optional[List[str]] = None) -> pd.DataFrame:
        """
        Create a DataFrame with mapping results.
        
        Args:
            pdf_labels: List of labels from PDF tables
            xbrl_concepts: Optional list of available XBRL concepts
            
        Returns:
            DataFrame with mapping results
        """
        mapping_results = self.map_pdf_labels_to_xbrl(
            pdf_labels, xbrl_concepts, include_confidence=True
        )
        
        rows = []
        for pdf_label, result in mapping_results.items():
            if isinstance(result, dict):
                rows.append({
                    'pdf_label': pdf_label,
                    'preprocessed_label': self.preprocess_label(pdf_label),
                    'xbrl_concept': result.get('concept'),
                    'confidence': result.get('confidence', 0),
                    'mapping_method': result.get('method', 'unknown'),
                    'mapped': result.get('concept') is not None
                })
            else:
                # Backward compatibility
                rows.append({
                    'pdf_label': pdf_label,
                    'preprocessed_label': self.preprocess_label(pdf_label),
                    'xbrl_concept': result,
                    'confidence': 100 if result else 0,
                    'mapping_method': 'exact' if result else 'none',
                    'mapped': result is not None
                })
        
        return pd.DataFrame(rows)
    
    def get_mapping_statistics(self, mapping_df: pd.DataFrame) -> Dict[str, any]:
        """
        Get statistics about mapping results.
        
        Args:
            mapping_df: DataFrame from create_mapping_dataframe
            
        Returns:
            Dictionary with mapping statistics
        """
        if mapping_df.empty:
            return {}
        
        total_labels = len(mapping_df)
        mapped_labels = len(mapping_df[mapping_df['mapped'] == True])
        unmapped_labels = total_labels - mapped_labels
        
        stats = {
            'total_labels': total_labels,
            'mapped_labels': mapped_labels,
            'unmapped_labels': unmapped_labels,
            'mapping_rate': mapped_labels / total_labels if total_labels > 0 else 0,
            'avg_confidence': mapping_df[mapping_df['mapped'] == True]['confidence'].mean() if mapped_labels > 0 else 0,
            'method_counts': mapping_df['mapping_method'].value_counts().to_dict(),
            'unmapped_labels_list': mapping_df[mapping_df['mapped'] == False]['pdf_label'].tolist()
        }
        
        return stats
    
    def save_mapping_results(self, mapping_df: pd.DataFrame, 
                           output_path: str, format: str = 'csv') -> None:
        """
        Save mapping results to file.
        
        Args:
            mapping_df: DataFrame with mapping results
            output_path: Output file path
            format: Output format ('csv', 'json', 'xlsx')
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format.lower() == 'csv':
            mapping_df.to_csv(output_path, index=False)
        elif format.lower() == 'json':
            mapping_df.to_json(output_path, orient='records', indent=2)
        elif format.lower() == 'xlsx':
            mapping_df.to_excel(output_path, index=False)
        else:
            raise ValueError(f"Unsupported format: {format}")
        
        logger.info(f"Saved mapping results to {output_path}")
    
    def add_custom_mapping(self, pdf_label: str, xbrl_concept: str) -> None:
        """
        Add a custom mapping rule.
        
        Args:
            pdf_label: PDF table label
            xbrl_concept: Corresponding XBRL concept
        """
        cleaned_label = self.preprocess_label(pdf_label)
        self.concept_mappings[cleaned_label] = xbrl_concept
        logger.info(f"Added custom mapping: '{pdf_label}' -> '{xbrl_concept}'")
    
    def export_mappings(self, output_path: str) -> None:
        """
        Export current mappings to JSON file.
        
        Args:
            output_path: Path to save mappings
        """
        mappings_data = {
            'concept_mappings': self.concept_mappings,
            'synonym_mappings': self.synonym_mappings,
            'xbrl_concepts': self.xbrl_concepts,
            'config': self.config
        }
        
        with open(output_path, 'w') as f:
            json.dump(mappings_data, f, indent=2)
        
        logger.info(f"Exported mappings to {output_path}")
    
    def load_mappings(self, mappings_path: str) -> None:
        """
        Load mappings from JSON file.
        
        Args:
            mappings_path: Path to mappings file
        """
        with open(mappings_path, 'r') as f:
            mappings_data = json.load(f)
        
        self.concept_mappings.update(mappings_data.get('concept_mappings', {}))
        self.synonym_mappings.update(mappings_data.get('synonym_mappings', {}))
        
        if 'xbrl_concepts' in mappings_data:
            self.xbrl_concepts.extend(mappings_data['xbrl_concepts'])
            self.xbrl_concepts = list(set(self.xbrl_concepts))  # Remove duplicates
        
        logger.info(f"Loaded mappings from {mappings_path}")


def main():
    """
    Example usage of PDFXBRLMapper.
    """
    mapper = PDFXBRLMapper()
    
    # Example PDF labels
    sample_labels = [
        "Total Revenue",
        "Net Income",
        "Total Assets",
        "Stockholders' Equity",
        "Cost of Sales",
        "R&D Expenses"
    ]
    
    # Create mapping
    mapping_df = mapper.create_mapping_dataframe(sample_labels)
    print("Mapping Results:")
    print(mapping_df)
    
    # Get statistics
    stats = mapper.get_mapping_statistics(mapping_df)
    print(f"\nMapping Statistics:")
    print(f"Total Labels: {stats['total_labels']}")
    print(f"Mapped: {stats['mapped_labels']} ({stats['mapping_rate']:.1%})")
    print(f"Average Confidence: {stats['avg_confidence']:.1f}")


if __name__ == "__main__":
    main()