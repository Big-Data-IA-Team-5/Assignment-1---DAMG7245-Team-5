"""
XBRL Validation Module for Project LANTERN

This module performs cross-verification between PDF table data and XBRL filings
to identify discrepancies and validate data accuracy.

Dependencies:
    - pandas: Data manipulation
    - numpy: Numerical computations
    - datetime: Date handling
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import json
from datetime import datetime, date
from pathlib import Path
import warnings

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class XBRLValidator:
    """
    XBRL Validator for cross-verification of PDF table data against XBRL filings.
    
    This class provides methods to compare extracted PDF table data with
    authoritative XBRL data and identify discrepancies for validation.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize XBRL Validator.
        
        Args:
            config: Optional configuration dictionary with validation parameters
        """
        self.config = config or {}
        
        # Validation tolerances
        self.numeric_tolerance = self.config.get('numeric_tolerance', 0.01)  # 1 cent
        self.percentage_tolerance = self.config.get('percentage_tolerance', 0.001)  # 0.1%
        self.relative_tolerance = self.config.get('relative_tolerance', 1e-6)  # Relative tolerance
        
        # Validation settings
        self.ignore_unmapped = self.config.get('ignore_unmapped', True)
        self.strict_matching = self.config.get('strict_matching', False)
        self.aggregate_method = self.config.get('aggregate_method', 'sum')  # sum, mean, latest
        
        # Scale factors for common unit mismatches
        self.scale_factors = self.config.get('scale_factors', {
            'thousands': 1000,
            'millions': 1000000,
            'billions': 1000000000
        })
    
    def validate_pdf_vs_xbrl(self, pdf_df: pd.DataFrame, xbrl_df: pd.DataFrame, 
                           mapping: Dict[str, str]) -> List[Dict[str, Any]]:
        """
        Compare PDF table data against XBRL data using provided mapping.
        
        Args:
            pdf_df: DataFrame with PDF table data
            xbrl_df: DataFrame with XBRL facts
            mapping: Dictionary mapping PDF labels to XBRL concepts
            
        Returns:
            List of discrepancy dictionaries
        """
        discrepancies = []
        
        if pdf_df.empty or xbrl_df.empty:
            logger.warning("Empty dataframes provided for validation")
            return discrepancies
        
        logger.info(f"Starting validation with {len(mapping)} mapped concepts")
        
        for pdf_label, xbrl_concept in mapping.items():
            if xbrl_concept is None and self.ignore_unmapped:
                continue
            
            try:
                discrepancy = self._compare_single_concept(
                    pdf_df, xbrl_df, pdf_label, xbrl_concept
                )
                if discrepancy:
                    discrepancies.append(discrepancy)
                    
            except Exception as e:
                logger.error(f"Error comparing '{pdf_label}' to '{xbrl_concept}': {str(e)}")
                discrepancies.append({
                    'pdf_label': pdf_label,
                    'xbrl_concept': xbrl_concept,
                    'error': str(e),
                    'status': 'error',
                    'validation_timestamp': datetime.now().isoformat()
                })
        
        logger.info(f"Validation complete. Found {len(discrepancies)} discrepancies")
        return discrepancies
    
    def _compare_single_concept(self, pdf_df: pd.DataFrame, xbrl_df: pd.DataFrame,
                              pdf_label: str, xbrl_concept: Optional[str]) -> Optional[Dict[str, Any]]:
        """
        Compare a single PDF label against corresponding XBRL concept.
        
        Args:
            pdf_df: PDF DataFrame
            xbrl_df: XBRL DataFrame
            pdf_label: PDF table label
            xbrl_concept: Corresponding XBRL concept
            
        Returns:
            Discrepancy dictionary or None if no issues
        """
        if xbrl_concept is None:
            return {
                'pdf_label': pdf_label,
                'xbrl_concept': None,
                'pdf_value': self._extract_pdf_value(pdf_df, pdf_label),
                'xbrl_value': None,
                'discrepancy_type': 'no_xbrl_mapping',
                'status': 'unmapped',
                'validation_timestamp': datetime.now().isoformat()
            }
        
        # Extract values
        pdf_value = self._extract_pdf_value(pdf_df, pdf_label)
        xbrl_value = self._extract_xbrl_value(xbrl_df, xbrl_concept)
        
        # Check for missing values
        if pdf_value is None and xbrl_value is None:
            return None  # Both missing, no discrepancy
        
        if pdf_value is None:
            return {
                'pdf_label': pdf_label,
                'xbrl_concept': xbrl_concept,
                'pdf_value': None,
                'xbrl_value': xbrl_value,
                'discrepancy_type': 'missing_pdf_value',
                'status': 'discrepancy',
                'validation_timestamp': datetime.now().isoformat()
            }
        
        if xbrl_value is None:
            return {
                'pdf_label': pdf_label,
                'xbrl_concept': xbrl_concept,
                'pdf_value': pdf_value,
                'xbrl_value': None,
                'discrepancy_type': 'missing_xbrl_value',
                'status': 'discrepancy',
                'validation_timestamp': datetime.now().isoformat()
            }
        
        # Compare numeric values
        comparison_result = self._compare_numeric_values(pdf_value, xbrl_value)
        
        if comparison_result['match']:
            return None  # Values match within tolerance
        
        # Create discrepancy record
        discrepancy = {
            'pdf_label': pdf_label,
            'xbrl_concept': xbrl_concept,
            'pdf_value': pdf_value,
            'xbrl_value': xbrl_value,
            'difference': comparison_result['difference'],
            'percentage_difference': comparison_result['percentage_difference'],
            'scaled_match': comparison_result.get('scaled_match', False),
            'scale_factor': comparison_result.get('scale_factor'),
            'discrepancy_type': comparison_result['discrepancy_type'],
            'status': 'discrepancy',
            'validation_timestamp': datetime.now().isoformat()
        }
        
        return discrepancy
    
    def _extract_pdf_value(self, pdf_df: pd.DataFrame, pdf_label: str) -> Optional[float]:
        """
        Extract numeric value from PDF DataFrame for a given label.
        
        Args:
            pdf_df: PDF DataFrame
            pdf_label: Label/column name
            
        Returns:
            Extracted numeric value or None
        """
        try:
            # Check if label exists as column
            if pdf_label in pdf_df.columns:
                values = pd.to_numeric(pdf_df[pdf_label], errors='coerce').dropna()
                if not values.empty:
                    return self._aggregate_values(values)
            
            # Try to find similar column names
            similar_cols = [col for col in pdf_df.columns 
                          if pdf_label.lower() in col.lower() or col.lower() in pdf_label.lower()]
            
            if similar_cols:
                col = similar_cols[0]  # Take first match
                values = pd.to_numeric(pdf_df[col], errors='coerce').dropna()
                if not values.empty:
                    return self._aggregate_values(values)
            
            return None
            
        except Exception as e:
            logger.warning(f"Error extracting PDF value for '{pdf_label}': {str(e)}")
            return None
    
    def _extract_xbrl_value(self, xbrl_df: pd.DataFrame, xbrl_concept: str) -> Optional[float]:
        """
        Extract numeric value from XBRL DataFrame for a given concept.
        
        Args:
            xbrl_df: XBRL DataFrame
            xbrl_concept: XBRL concept name
            
        Returns:
            Extracted numeric value or None
        """
        try:
            # Filter by concept
            concept_data = xbrl_df[xbrl_df['concept'] == xbrl_concept]
            
            if concept_data.empty:
                return None
            
            # Get numeric values
            if 'numeric_value' in concept_data.columns:
                values = concept_data['numeric_value'].dropna()
            elif 'value' in concept_data.columns:
                values = pd.to_numeric(concept_data['value'], errors='coerce').dropna()
            else:
                return None
            
            if values.empty:
                return None
            
            # Filter for most recent or relevant period
            filtered_values = self._filter_xbrl_by_period(concept_data, values)
            
            return self._aggregate_values(filtered_values)
            
        except Exception as e:
            logger.warning(f"Error extracting XBRL value for '{xbrl_concept}': {str(e)}")
            return None
    
    def _filter_xbrl_by_period(self, concept_data: pd.DataFrame, 
                             values: pd.Series) -> pd.Series:
        """
        Filter XBRL data to get most relevant period values.
        
        Args:
            concept_data: DataFrame with concept data
            values: Series with numeric values
            
        Returns:
            Filtered values series
        """
        # If no period information, return all values
        if 'end_date' not in concept_data.columns and 'instant_date' not in concept_data.columns:
            return values
        
        # Prefer most recent period
        if 'end_date' in concept_data.columns:
            end_dates = pd.to_datetime(concept_data['end_date'], errors='coerce')
            if not end_dates.isna().all():
                latest_date = end_dates.max()
                latest_mask = end_dates == latest_date
                return values[latest_mask]
        
        if 'instant_date' in concept_data.columns:
            instant_dates = pd.to_datetime(concept_data['instant_date'], errors='coerce')
            if not instant_dates.isna().all():
                latest_date = instant_dates.max()
                latest_mask = instant_dates == latest_date
                return values[latest_mask]
        
        return values
    
    def _aggregate_values(self, values: pd.Series) -> float:
        """
        Aggregate multiple values using configured method.
        
        Args:
            values: Series of numeric values
            
        Returns:
            Aggregated value
        """
        if values.empty:
            return None
        
        if len(values) == 1:
            return float(values.iloc[0])
        
        if self.aggregate_method == 'sum':
            return float(values.sum())
        elif self.aggregate_method == 'mean':
            return float(values.mean())
        elif self.aggregate_method == 'latest':
            return float(values.iloc[-1])  # Last value
        else:
            return float(values.sum())  # Default to sum
    
    def _compare_numeric_values(self, pdf_value: float, xbrl_value: float) -> Dict[str, Any]:
        """
        Compare two numeric values with tolerance checking.
        
        Args:
            pdf_value: Value from PDF
            xbrl_value: Value from XBRL
            
        Returns:
            Comparison result dictionary
        """
        difference = abs(pdf_value - xbrl_value)
        percentage_diff = (difference / abs(xbrl_value)) * 100 if xbrl_value != 0 else float('inf')
        
        result = {
            'difference': difference,
            'percentage_difference': percentage_diff,
            'match': False,
            'discrepancy_type': 'value_mismatch'
        }
        
        # Check absolute tolerance
        if difference <= self.numeric_tolerance:
            result['match'] = True
            return result
        
        # Check percentage tolerance
        if percentage_diff <= self.percentage_tolerance * 100:
            result['match'] = True
            return result
        
        # Check relative tolerance
        relative_diff = difference / max(abs(pdf_value), abs(xbrl_value))
        if relative_diff <= self.relative_tolerance:
            result['match'] = True
            return result
        
        # Check for scale factor mismatches (thousands, millions, etc.)
        scale_result = self._check_scale_factors(pdf_value, xbrl_value)
        if scale_result['scaled_match']:
            result.update(scale_result)
            result['discrepancy_type'] = 'scale_mismatch'
        
        return result
    
    def _check_scale_factors(self, pdf_value: float, xbrl_value: float) -> Dict[str, Any]:
        """
        Check if values match with common scale factors.
        
        Args:
            pdf_value: Value from PDF
            xbrl_value: Value from XBRL
            
        Returns:
            Scale check result
        """
        result = {'scaled_match': False, 'scale_factor': None}
        
        for scale_name, scale_factor in self.scale_factors.items():
            # Check if PDF value scaled equals XBRL value
            scaled_pdf = pdf_value * scale_factor
            if abs(scaled_pdf - xbrl_value) <= self.numeric_tolerance:
                result['scaled_match'] = True
                result['scale_factor'] = scale_factor
                result['scale_name'] = scale_name
                result['scaled_direction'] = 'pdf_to_xbrl'
                break
            
            # Check if XBRL value scaled equals PDF value
            scaled_xbrl = xbrl_value * scale_factor
            if abs(scaled_xbrl - pdf_value) <= self.numeric_tolerance:
                result['scaled_match'] = True
                result['scale_factor'] = 1 / scale_factor
                result['scale_name'] = scale_name
                result['scaled_direction'] = 'xbrl_to_pdf'
                break
        
        return result
    
    def categorize_discrepancies(self, discrepancies: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
        """
        Categorize discrepancies by type and severity.
        
        Args:
            discrepancies: List of discrepancy dictionaries
            
        Returns:
            Dictionary with categorized discrepancies
        """
        categories = {
            'critical': [],      # Large value mismatches
            'moderate': [],      # Moderate mismatches or scale issues
            'minor': [],         # Small mismatches within reasonable bounds
            'missing_data': [],  # Missing values
            'unmapped': [],      # No XBRL mapping available
            'errors': []         # Processing errors
        }
        
        for discrepancy in discrepancies:
            try:
                category = self._classify_discrepancy_severity(discrepancy)
                categories[category].append(discrepancy)
            except Exception as e:
                logger.warning(f"Error categorizing discrepancy: {str(e)}")
                categories['errors'].append(discrepancy)
        
        return categories
    
    def _classify_discrepancy_severity(self, discrepancy: Dict[str, Any]) -> str:
        """
        Classify the severity of a discrepancy.
        
        Args:
            discrepancy: Discrepancy dictionary
            
        Returns:
            Severity category string
        """
        discrepancy_type = discrepancy.get('discrepancy_type', 'unknown')
        
        # Handle non-value discrepancies
        if discrepancy_type in ['no_xbrl_mapping']:
            return 'unmapped'
        
        if discrepancy_type in ['missing_pdf_value', 'missing_xbrl_value']:
            return 'missing_data'
        
        if discrepancy.get('error'):
            return 'errors'
        
        # Handle value mismatches
        percentage_diff = discrepancy.get('percentage_difference', 0)
        scaled_match = discrepancy.get('scaled_match', False)
        
        if scaled_match:
            return 'moderate'  # Scale factor issues are moderate
        
        if percentage_diff > 10:  # More than 10% difference
            return 'critical'
        elif percentage_diff > 1:  # 1-10% difference
            return 'moderate'
        else:
            return 'minor'
    
    def generate_validation_summary(self, discrepancies: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Generate summary statistics for validation results.
        
        Args:
            discrepancies: List of discrepancy dictionaries
            
        Returns:
            Summary dictionary
        """
        categorized = self.categorize_discrepancies(discrepancies)
        
        total_discrepancies = len(discrepancies)
        value_mismatches = len([d for d in discrepancies 
                               if d.get('discrepancy_type') == 'value_mismatch'])
        
        summary = {
            'validation_timestamp': datetime.now().isoformat(),
            'total_discrepancies': total_discrepancies,
            'value_mismatches': value_mismatches,
            'category_counts': {k: len(v) for k, v in categorized.items()},
            'severity_distribution': {
                'critical': len(categorized['critical']),
                'moderate': len(categorized['moderate']),
                'minor': len(categorized['minor']),
                'data_issues': len(categorized['missing_data']) + len(categorized['unmapped']),
                'errors': len(categorized['errors'])
            }
        }
        
        # Calculate percentage differences statistics
        percentage_diffs = [d.get('percentage_difference', 0) for d in discrepancies 
                           if d.get('percentage_difference') is not None and 
                           d.get('percentage_difference') != float('inf')]
        
        if percentage_diffs:
            summary['percentage_difference_stats'] = {
                'mean': np.mean(percentage_diffs),
                'median': np.median(percentage_diffs),
                'max': np.max(percentage_diffs),
                'min': np.min(percentage_diffs)
            }
        
        return summary
    
    def save_validation_results(self, discrepancies: List[Dict[str, Any]], 
                              output_dir: str, filename_prefix: str = "xbrl_validation") -> Dict[str, str]:
        """
        Save validation results to files.
        
        Args:
            discrepancies: List of discrepancy dictionaries
            output_dir: Output directory path
            filename_prefix: Prefix for output filenames
            
        Returns:
            Dictionary with paths of saved files
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Save detailed results as JSON
        json_path = output_path / f"{filename_prefix}_{timestamp}.json"
        with open(json_path, 'w') as f:
            json.dump(discrepancies, f, indent=2, default=str)
        
        # Save as CSV for analysis
        if discrepancies:
            csv_path = output_path / f"{filename_prefix}_{timestamp}.csv"
            df_results = pd.DataFrame(discrepancies)
            df_results.to_csv(csv_path, index=False)
        else:
            csv_path = None
        
        # Save summary
        summary = self.generate_validation_summary(discrepancies)
        summary_path = output_path / f"{filename_prefix}_summary_{timestamp}.json"
        with open(summary_path, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        saved_files = {
            'detailed_results': str(json_path),
            'summary': str(summary_path)
        }
        
        if csv_path:
            saved_files['csv_results'] = str(csv_path)
        
        logger.info(f"Validation results saved to {output_dir}")
        return saved_files
    
    def create_validation_dataframe(self, discrepancies: List[Dict[str, Any]]) -> pd.DataFrame:
        """
        Convert discrepancies to a structured DataFrame.
        
        Args:
            discrepancies: List of discrepancy dictionaries
            
        Returns:
            DataFrame with validation results
        """
        if not discrepancies:
            return pd.DataFrame()
        
        df = pd.DataFrame(discrepancies)
        
        # Add severity classification
        df['severity'] = df.apply(lambda row: self._classify_discrepancy_severity(row.to_dict()), axis=1)
        
        # Reorder columns for better readability
        column_order = [
            'pdf_label', 'xbrl_concept', 'pdf_value', 'xbrl_value',
            'difference', 'percentage_difference', 'discrepancy_type',
            'severity', 'status', 'validation_timestamp'
        ]
        
        # Only include columns that exist
        available_columns = [col for col in column_order if col in df.columns]
        remaining_columns = [col for col in df.columns if col not in available_columns]
        
        df = df[available_columns + remaining_columns]
        
        return df


def main():
    """
    Example usage of XBRLValidator.
    """
    validator = XBRLValidator()
    
    # Example data (normally would come from actual parsing)
    pdf_data = pd.DataFrame({
        'Total Revenue': [100000],
        'Net Income': [25000],
        'Total Assets': [500000]
    })
    
    xbrl_data = pd.DataFrame({
        'concept': ['Revenues', 'NetIncomeLoss', 'Assets'],
        'numeric_value': [100000, 25100, 500000],  # Slight difference in Net Income
        'currency': ['USD', 'USD', 'USD']
    })
    
    mapping = {
        'Total Revenue': 'Revenues',
        'Net Income': 'NetIncomeLoss',
        'Total Assets': 'Assets'
    }
    
    # Perform validation
    discrepancies = validator.validate_pdf_vs_xbrl(pdf_data, xbrl_data, mapping)
    
    print(f"Found {len(discrepancies)} discrepancies:")
    for d in discrepancies:
        print(f"  {d['pdf_label']}: PDF={d['pdf_value']}, XBRL={d['xbrl_value']}")


if __name__ == "__main__":
    main()