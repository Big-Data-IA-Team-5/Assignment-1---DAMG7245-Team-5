#!/usr/bin/env python3
"""
Lab 11 - XBRL Cross-Verification Script for Project LANTERN

This is the main entry point for the XBRL cross-verification workflow.
It integrates PDF table extraction with XBRL filing validation to identify
discrepancies and ensure data accuracy.

Usage:
    python src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl
    python src/xbrl/lab11_xbrl.py --config configs/xbrl_config.yaml
"""

import argparse
import sys
import os
import glob
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import pandas as pd
import warnings

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from src.xbrl.parse_xbrl import XBRLParser
    from src.xbrl.simple_xbrl_parser import SimpleXBRLParser
    from src.xbrl.map_pdf_to_xbrl import PDFXBRLMapper
    from src.xbrl.enhanced_pdf_xbrl_mapper import EnhancedPDFXBRLMapper
    from src.xbrl.validate_xbrl import XBRLValidator
    from src.xbrl.report_xbrl import XBRLReporter
except ImportError as e:
    print(f"Warning: Could not import XBRL modules: {e}")
    print("Some functionality may not be available until dependencies are installed.")

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/lab11_xbrl.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Suppress warnings for cleaner output
warnings.filterwarnings("ignore", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)


class Lab11XBRLWorkflow:
    """
    Main workflow class for XBRL cross-verification (Lab 11).
    
    This class orchestrates the entire XBRL validation process including:
    1. Loading and parsing XBRL files
    2. Loading PDF table data
    3. Mapping PDF labels to XBRL concepts
    4. Cross-validation and discrepancy detection
    5. Report generation
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the XBRL workflow.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.session_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Initialize enhanced mapper with fallback to basic mapper
        mapper_config = self.config.get('mapper', {})
        try:
            self.mapper = EnhancedPDFXBRLMapper(mapper_config)
            logger.info("Using EnhancedPDFXBRLMapper with NLP capabilities")
        except Exception as e:
            logger.warning(f"Could not initialize EnhancedPDFXBRLMapper: {e}")
            try:
                self.mapper = PDFXBRLMapper(mapper_config)
                logger.info("Falling back to basic PDFXBRLMapper")
            except Exception as e2:
                logger.warning(f"Could not initialize PDFXBRLMapper: {e2}")
                self.mapper = None
        
        # Data storage
        self.pdf_data = {}
        self.xbrl_data = {}
        self.mappings = {}
        self.validation_results = {}
        
        self._initialize_components()
    
    def _initialize_components(self):
        """Initialize XBRL processing components."""
        try:
            parser_config = self.config.get('parser', {})
            
            # Use SimpleXBRLParser directly for better compatibility
            logger.info("Using SimpleXBRLParser for XBRL processing")
            self.parser = SimpleXBRLParser(parser_config)
            
            mapper_config = self.config.get('mapper', {})
            self.mapper = PDFXBRLMapper(mapper_config)
            
            validator_config = self.config.get('validator', {})
            self.validator = XBRLValidator(validator_config)
            
            reporter_config = self.config.get('reporter', {})
            self.reporter = XBRLReporter(reporter_config)
            
            logger.info("XBRL components initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing XBRL components: {str(e)}")
            raise
    
    def load_pdf_tables(self, tables_directory: str) -> Dict[str, pd.DataFrame]:
        """
        Load PDF table data from the tables directory.
        
        Args:
            tables_directory: Path to directory containing PDF table data
            
        Returns:
            Dictionary mapping file names to DataFrames
        """
        logger.info(f"Loading PDF table data from {tables_directory}")
        
        tables_path = Path(tables_directory)
        if not tables_path.exists():
            raise FileNotFoundError(f"Tables directory not found: {tables_directory}")
        
        pdf_tables = {}
        
        # Look for CSV files (common output from table extraction)
        csv_files = list(tables_path.glob("**/*.csv"))
        
        for csv_file in csv_files:
            try:
                df = pd.read_csv(csv_file)
                if not df.empty:
                    pdf_tables[csv_file.name] = df
                    logger.info(f"Loaded PDF table: {csv_file.name} ({len(df)} rows)")
                else:
                    logger.warning(f"Empty table file: {csv_file.name}")
                    
            except Exception as e:
                logger.error(f"Error loading {csv_file.name}: {str(e)}")
        
        # Also look for Excel files
        excel_files = list(tables_path.glob("**/*.xlsx")) + list(tables_path.glob("**/*.xls"))
        
        for excel_file in excel_files:
            try:
                df = pd.read_excel(excel_file)
                if not df.empty:
                    pdf_tables[excel_file.name] = df
                    logger.info(f"Loaded PDF table: {excel_file.name} ({len(df)} rows)")
                    
            except Exception as e:
                logger.error(f"Error loading {excel_file.name}: {str(e)}")
        
        if not pdf_tables:
            logger.warning(f"No PDF table files found in {tables_directory}")
        
        self.pdf_data = pdf_tables
        return pdf_tables
    
    def load_xbrl_files(self, xbrl_dir: str) -> List[Dict[str, Any]]:
        """
        Load and parse XBRL files from specified directory.
        
        Args:
            xbrl_dir: Directory containing XBRL files
            
        Returns:
            List of parsed XBRL data dictionaries
        """
        xbrl_files = []
        
        # Dynamically detect XBRL files with multiple extensions
        xbrl_extensions = ['.xml', '.xbrl']
        found_files = []
        
        for ext in xbrl_extensions:
            pattern = os.path.join(xbrl_dir, f"*{ext}")
            matching_files = glob.glob(pattern)
            found_files.extend(matching_files)
        
        logger.info(f"Found {len(found_files)} XBRL files in {xbrl_dir}")
        
        if not found_files:
            logger.warning(f"No XBRL files found in {xbrl_dir}")
            return []
        
        # Process each XBRL file
        for xbrl_file in found_files:
            try:
                logger.info(f"Processing XBRL file: {xbrl_file}")
                parsed_data = self.parser.parse_xbrl_file(xbrl_file)
                # Create a proper dictionary structure for xbrl_files
                xbrl_data_dict = {
                    'file': xbrl_file,
                    'data': parsed_data
                }
                xbrl_files.append(xbrl_data_dict)
                logger.info(f"Successfully parsed {xbrl_file}")
            except Exception as e:
                logger.error(f"Error processing {xbrl_file}: {str(e)}")
                continue
        
        logger.info(f"Total XBRL files processed: {len(xbrl_files)}")
        return xbrl_files
    
    def create_mappings(self) -> Dict[str, Dict[str, str]]:
        """
        Create mappings between PDF table labels and XBRL concepts.
        
        Returns:
            Dictionary mapping file names to label-concept mappings
        """
        logger.info("Creating PDF-to-XBRL mappings")
        
        if self.mapper is None:
            raise RuntimeError("XBRL mapper not initialized")
        
        mappings = {}
        
        for pdf_file, pdf_df in self.pdf_data.items():
            try:
                # Extract labels from PDF table columns
                pdf_labels = pdf_df.columns.tolist()
                
                # Get available XBRL concepts from all loaded XBRL files
                all_xbrl_concepts = set()
                for xbrl_df in self.xbrl_data.values():
                    if 'concept' in xbrl_df.columns:
                        all_xbrl_concepts.update(xbrl_df['concept'].unique())
                
                # Create enhanced mappings with analysis
                if hasattr(self.mapper, 'generate_mapping_analysis'):
                    # Use enhanced mapper with detailed analysis
                    mapping_analysis = self.mapper.generate_mapping_analysis(
                        pdf_labels, list(all_xbrl_concepts)
                    )
                    mappings[pdf_file] = mapping_analysis['detailed_mappings']
                    
                    # Log enhanced mapping statistics
                    mapped_count = mapping_analysis['mapped_labels']
                    total_count = mapping_analysis['total_labels']
                    mapping_rate = mapping_analysis['mapping_rate']
                    logger.info(f"Enhanced mapping for {pdf_file}: {mapped_count}/{total_count} labels mapped ({mapping_rate:.1%})")
                    
                    # Log confidence distribution
                    conf_dist = mapping_analysis['confidence_distribution']
                    logger.info(f"  High confidence: {conf_dist['high_confidence']}, Medium: {conf_dist['medium_confidence']}, Low: {conf_dist['low_confidence']}")
                    
                else:
                    # Fallback to basic mapping
                    file_mapping = self.mapper.map_pdf_labels_to_xbrl(
                        pdf_labels, list(all_xbrl_concepts)
                    )
                    mappings[pdf_file] = file_mapping
                    
                    # Log basic mapping statistics
                    mapped_count = sum(1 for v in file_mapping.values() if v is not None)
                    logger.info(f"Basic mapping for {pdf_file}: {mapped_count}/{len(pdf_labels)} labels mapped")
                
            except Exception as e:
                logger.error(f"Error creating mappings for {pdf_file}: {str(e)}")
        
        self.mappings = mappings
        return mappings
    
    def validate_data(self) -> Dict[str, Any]:
        """
        Perform cross-validation between PDF and XBRL data.
        
        Returns:
            Dictionary with validation results
        """
        logger.info("Starting XBRL cross-validation")
        
        if self.validator is None:
            raise RuntimeError("XBRL validator not initialized")
        
        validation_results = {
            'session_id': self.session_id,
            'validation_timestamp': datetime.now().isoformat(),
            'file_results': {},
            'summary': {}
        }
        
        all_discrepancies = []
        
        for pdf_file in self.pdf_data.keys():
            try:
                pdf_df = self.pdf_data[pdf_file]
                file_mapping = self.mappings.get(pdf_file, {})
                
                # Find corresponding XBRL data (simple matching by file name patterns)
                corresponding_xbrl = self._find_corresponding_xbrl(pdf_file)
                
                if corresponding_xbrl is None:
                    logger.warning(f"No corresponding XBRL data found for {pdf_file}")
                    continue
                
                # Perform validation
                discrepancies = self.validator.validate_pdf_vs_xbrl(
                    pdf_df, corresponding_xbrl, file_mapping
                )
                
                # Store file-specific results
                validation_results['file_results'][pdf_file] = {
                    'discrepancies': discrepancies,
                    'discrepancy_count': len(discrepancies),
                    'mapping_count': len(file_mapping)
                }
                
                all_discrepancies.extend(discrepancies)
                
                logger.info(f"Validation complete for {pdf_file}: {len(discrepancies)} discrepancies found")
                
            except Exception as e:
                logger.error(f"Error validating {pdf_file}: {str(e)}")
        
        # Generate overall summary
        if all_discrepancies:
            validation_results['summary'] = self.validator.generate_validation_summary(all_discrepancies)
            validation_results['categorized_discrepancies'] = self.validator.categorize_discrepancies(all_discrepancies)
        else:
            validation_results['summary'] = {
                'total_discrepancies': 0,
                'validation_timestamp': datetime.now().isoformat()
            }
            validation_results['categorized_discrepancies'] = {}
        
        validation_results['all_discrepancies'] = all_discrepancies
        
        self.validation_results = validation_results
        logger.info(f"Overall validation complete: {len(all_discrepancies)} total discrepancies")
        
        return validation_results
    
    def _find_corresponding_xbrl(self, pdf_file: str) -> Optional[pd.DataFrame]:
        """
        Find corresponding XBRL data for a PDF file.
        
        Args:
            pdf_file: Name of the PDF file
            
        Returns:
            Corresponding XBRL DataFrame or None
        """
        # Simple heuristic: look for similar file names or combine all XBRL data
        pdf_name_parts = pdf_file.lower().replace('.csv', '').replace('.xlsx', '').split('_')
        
        # First, try to find exact or partial matches
        for xbrl_file, xbrl_df in self.xbrl_data.items():
            xbrl_name_parts = xbrl_file.lower().replace('.xml', '').replace('.xbrl', '').split('_')
            
            # Check for common elements in file names
            common_parts = set(pdf_name_parts) & set(xbrl_name_parts)
            if len(common_parts) > 0:
                logger.info(f"Matched {pdf_file} with {xbrl_file} based on common name parts: {common_parts}")
                return xbrl_df
        
        # If no specific match found, combine all XBRL data
        if self.xbrl_data:
            combined_xbrl = pd.concat(self.xbrl_data.values(), ignore_index=True)
            logger.info(f"Using combined XBRL data for {pdf_file}")
            return combined_xbrl
        
        return None
    
    def generate_reports(self, output_directory: str) -> Dict[str, str]:
        """
        Generate comprehensive validation reports.
        
        Args:
            output_directory: Directory to save reports
            
        Returns:
            Dictionary with paths to generated reports
        """
        # Create timestamped session directory
        session_output_dir = Path(output_directory) / f"xbrl_session_{self.session_id}"
        session_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create organized subdirectories for this session
        subdirs = {
            'mapping': session_output_dir / 'mapping',
            'validation': session_output_dir / 'validation', 
            'analysis': session_output_dir / 'analysis',
            'reports': session_output_dir / 'reports',
            'extracted_data': session_output_dir / 'extracted_data'
        }
        
        for subdir in subdirs.values():
            subdir.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Generating XBRL validation reports in {session_output_dir}")
        
        if self.reporter is None:
            raise RuntimeError("XBRL reporter not initialized")
        
        report_files = {}
        
        try:
            validation_summary = self.validation_results.get('summary', {})
            all_discrepancies = self.validation_results.get('all_discrepancies', [])
            categorized_discrepancies = self.validation_results.get('categorized_discrepancies', {})
            
            # Prepare metadata
            metadata = {
                'session_id': self.session_id,
                'pdf_files_processed': len(self.pdf_data),
                'xbrl_files_processed': len(self.xbrl_data),
                'total_mappings': sum(len(m) for m in self.mappings.values()),
                'processing_timestamp': datetime.now().isoformat()
            }
            
            # Generate Markdown report
            markdown_content = self.reporter.generate_markdown_report(
                validation_summary, all_discrepancies, categorized_discrepancies, metadata
            )
            
            markdown_file = subdirs['reports'] / f"XBRL_Validation_Report_{self.session_id}.md"
            self.reporter.save_markdown_report(markdown_content, str(markdown_file))
            report_files['markdown_report'] = str(markdown_file)
            
            # Generate JSON report
            json_report = self.reporter.generate_json_report(
                validation_summary, all_discrepancies, categorized_discrepancies, metadata
            )
            
            json_file = subdirs['reports'] / f"XBRL_Validation_Report_{self.session_id}.json"
            self.reporter.save_json_report(json_report, str(json_file))
            report_files['json_report'] = str(json_file)
            
            # Save detailed validation results
            detailed_file = subdirs['validation'] / f"XBRL_Validation_Detailed_{self.session_id}.json"
            with open(detailed_file, 'w') as f:
                json.dump(self.validation_results, f, indent=2, default=str)
            report_files['detailed_results'] = str(detailed_file)
            
            # Save mappings
            mappings_file = subdirs['mapping'] / f"XBRL_Mappings_{self.session_id}.json"
            with open(mappings_file, 'w') as f:
                json.dump(self.mappings, f, indent=2)
            report_files['mappings'] = str(mappings_file)
            
            # Save extracted data (if any)
            if hasattr(self, 'pdf_data') and self.pdf_data:
                extracted_data_file = subdirs['extracted_data'] / f"PDF_Extracted_Data_{self.session_id}.json"
                with open(extracted_data_file, 'w') as f:
                    # Convert DataFrames to JSON-serializable format
                    serializable_data = {}
                    for filename, df in self.pdf_data.items():
                        serializable_data[filename] = df.to_dict('records')
                    json.dump(serializable_data, f, indent=2, default=str)
                report_files['extracted_data'] = str(extracted_data_file)
            
            logger.info("Reports generated successfully")
            
        except Exception as e:
            logger.error(f"Error generating reports: {str(e)}")
            raise
        
        return report_files
    
    def run_full_workflow(self, tables_dir: str, xbrl_dir: str, 
                         output_dir: str = "data/xbrl_outputs") -> Dict[str, Any]:
        """
        Run the complete XBRL cross-verification workflow.
        
        Args:
            tables_dir: Directory containing PDF table data
            xbrl_dir: Directory containing XBRL files
            output_dir: Directory for output reports
            
        Returns:
            Dictionary with workflow results
        """
        logger.info(f"Starting Lab 11 XBRL Cross-Verification Workflow (Session: {self.session_id})")
        
        try:
            # Step 1: Load PDF tables
            pdf_data = self.load_pdf_tables(tables_dir)
            if not pdf_data:
                raise ValueError("No PDF table data loaded")
            
            # Step 2: Load XBRL files
            xbrl_files_list = self.load_xbrl_files(xbrl_dir)
            if not xbrl_files_list:
                raise ValueError("No XBRL data loaded")
            
            # Convert list to dictionary format expected by other methods
            self.xbrl_data = {}
            for xbrl_item in xbrl_files_list:
                file_path = xbrl_item['file']
                file_name = os.path.basename(file_path)
                # Store the parsed DataFrame data
                self.xbrl_data[file_name] = xbrl_item['data']
            
            # Step 3: Create mappings
            mappings = self.create_mappings()
            
            # Step 4: Validate data
            validation_results = self.validate_data()
            

            
            # Step 5: Generate reports
            report_files = self.generate_reports(output_dir)
            
            # Prepare final results
            workflow_results = {
                'session_id': self.session_id,
                'success': True,
                'pdf_files_processed': len(pdf_data),
                'xbrl_files_processed': len(self.xbrl_data),
                'total_discrepancies': len(validation_results.get('all_discrepancies', [])),
                'report_files': report_files,
                'validation_summary': validation_results.get('summary', {}),
                'completion_timestamp': datetime.now().isoformat()
            }
            
            logger.info("XBRL Cross-Verification Workflow completed successfully")
            return workflow_results
            
        except Exception as e:
            logger.error(f"Workflow failed: {str(e)}")
            raise


def load_config(config_path: str) -> Dict[str, Any]:
    """
    Load configuration from YAML or JSON file.
    
    Args:
        config_path: Path to configuration file
        
    Returns:
        Configuration dictionary
    """
    config_file = Path(config_path)
    
    if not config_file.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    try:
        if config_path.endswith('.yaml') or config_path.endswith('.yml'):
            import yaml
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        elif config_path.endswith('.json'):
            with open(config_file, 'r') as f:
                return json.load(f)
        else:
            raise ValueError(f"Unsupported config format: {config_path}")
            
    except Exception as e:
        logger.error(f"Error loading config: {str(e)}")
        raise


def main():
    """
    Main entry point for Lab 11 XBRL Cross-Verification.
    """
    parser = argparse.ArgumentParser(
        description="Lab 11 - XBRL Cross-Verification for Project LANTERN",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl
  python src/xbrl/lab11_xbrl.py --config configs/xbrl_config.yaml
  python src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl --output reports/xbrl
        """
    )
    
    parser.add_argument(
        '--tables', 
        type=str, 
        help='Directory containing PDF table data'
    )
    
    parser.add_argument(
        '--xbrl', 
        type=str, 
        help='Directory containing XBRL files'
    )
    
    parser.add_argument(
        '--output', 
        type=str, 
        default=None,
        help='Output directory for reports (default: data/xbrl_outputs)'
    )
    
    parser.add_argument(
        '--config', 
        type=str, 
        help='Configuration file path (YAML or JSON)'
    )
    
    parser.add_argument(
        '--verbose', 
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        # Load configuration if provided
        config = {}
        if args.config:
            config = load_config(args.config)
        
        # Initialize and run workflow
        workflow = Lab11XBRLWorkflow(config)
        
        # Use hardcoded paths as defaults
        tables_dir = args.tables or "data/parsed/tesla_20250926_023933/tables"
        xbrl_dir = args.xbrl or "data/raw/xbrl_files"
        output_dir = args.output or "data/xbrl_outputs"
        
        results = workflow.run_full_workflow(tables_dir, xbrl_dir, output_dir)
        
        # Print summary
        print("\\n" + "="*60)
        print("XBRL CROSS-VERIFICATION COMPLETED")
        print("="*60)
        print(f"Session ID: {results['session_id']}")
        print(f"PDF Files Processed: {results['pdf_files_processed']}")
        print(f"XBRL Files Processed: {results['xbrl_files_processed']}")
        print(f"Total Discrepancies: {results['total_discrepancies']}")
        print(f"Reports Generated:")
        for report_type, path in results['report_files'].items():
            print(f"  - {report_type}: {path}")
        print("="*60)
        
        return 0
        
    except Exception as e:
        logger.error(f"Lab 11 XBRL workflow failed: {str(e)}")
        return 1


if __name__ == "__main__":
    sys.exit(main())