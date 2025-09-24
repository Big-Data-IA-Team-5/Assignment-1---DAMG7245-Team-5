"""
Lab 7: Google Document AI Integration with Page Selection
Team 5 - DAMG7245 Fall 2025

This script demonstrates the complete workflow for:
1. Extracting specific pages from a multi-page PDF
2. Sending the temporary PDF to Google Document AI
3. Parsing the results and comparing with existing parsed data
4. Generating comprehensive analysis reports

Usage:
    python lab7_google_ai_integration.py --pdf data/raw/tesla.pdf --pages 5 12 --config configs/google_ai_config.yaml
    python lab7_google_ai_integration.py --pdf data/raw/tesla.pdf --random 2 --seed 42
"""

import argparse
import sys
import json
from pathlib import Path
from datetime import datetime

import logging

# Add current directory to Python path
sys.path.append(str(Path(__file__).parent))

try:
    from page_extractor import PDFPageExtractor
    from document_processor import process_pdf_with_google_ai
    from result_parser import parse_google_ai_result
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure you're running from the project root directory or the google_ai folder.")
    sys.exit(1)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('lab7_execution.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class Lab7GoogleAIWorkflow:
    """
    Complete workflow manager for Google Document AI integration.
    """
    
    def __init__(self, config_path="configs/google_ai_config.json"):
        """
        Initialize the workflow with configuration.
        
        Args:
            config_path: Path to the Google AI configuration file
        """
        self.config = self._load_config(config_path)
        self.google_ai_config = self.config.get('google_document_ai', {})
        
        # Create organized output structure
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.session_name = f"lab7_session_{timestamp}"
        
        # Main reports folder
        self.reports_base = Path("reports/google_ai")
        self.session_dir = self.reports_base / self.session_name
        
        # Sub-folders for organized output
        self.temp_pdfs_dir = self.session_dir / "temp_pdfs"
        self.raw_results_dir = self.session_dir / "raw_google_ai_results"
        self.parsed_results_dir = self.session_dir / "parsed_results"
        self.comparison_dir = self.session_dir / "parsed_data_comparison"
        self.final_report_dir = self.session_dir / "final_reports"
        
        # Create all directories
        for directory in [self.temp_pdfs_dir, self.raw_results_dir, 
                         self.parsed_results_dir, self.comparison_dir, self.final_report_dir]:
            directory.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized Lab 7 workflow - Session: {self.session_name}")
        logger.info(f"All outputs will be saved to: {self.session_dir}")
    
    def _load_config(self, config_path):
        """Load configuration file with fallback to default values."""
        config_path_obj = Path(config_path)
        
        if not config_path_obj.exists():
            logger.warning(f"Config file not found: {config_path}. Creating default config.")
            return self._create_default_config(config_path_obj)
        
        try:
            # Try JSON first (more reliable)
            with open(config_path_obj, 'r') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            # JSON failed, create default config
            logger.warning(f"Failed to parse config file: {config_path}")
            return self._create_default_config(config_path_obj)
    
    def _create_default_config(self, config_path):
        """Create a default configuration file."""
        default_config = {
            "google_document_ai": {
                "project_id": "your-project-id",
                "location": "us",
                "processor_id": "your-processor-id",
                "credentials_path": "path/to/service-account-key.json"
            },
            "output_settings": {
                "save_temp_pdfs": True,
                "save_json_results": True,
                "save_parsed_results": True,
                "generate_comparison": True
            },
            "page_selection": {
                "default_pages": [5, 12],
                "random_seed": 42,
                "max_random_pages": 5
            }
        }
        
        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, 'w') as f:
            json.dump(default_config, f, indent=2)
        
        logger.info(f"Created default config at: {config_path}")
        logger.warning("Please update the configuration with your Google Cloud credentials!")
        
        return default_config
    
    def extract_pages(self, pdf_path, page_numbers=None, random_pages=None, seed=None):
        """
        Extract specific or random pages from the PDF.
        
        Args:
            pdf_path: Path to the original PDF
            page_numbers: Specific pages to extract (1-indexed)
            random_pages: Number of random pages to extract
            seed: Random seed for reproducibility
        
        Returns:
            (temp_pdf_path, selected_page_numbers)
        """
        logger.info(f"Starting page extraction from: {pdf_path}")
        
        extractor = PDFPageExtractor(pdf_path)
        pdf_info = extractor.get_page_info()
        logger.info(f"PDF has {pdf_info['total_pages']} pages, size: {pdf_info['file_size_mb']:.2f} MB")
        
        if random_pages:
            # Extract random pages
            temp_pdf_path, selected_pages = extractor.extract_random_pages(
                num_pages=random_pages,
                seed=seed or self.config.get('page_selection', {}).get('random_seed', 42)
            )
            # Convert to proper types
            temp_pdf_path = str(temp_pdf_path)
            selected_pages = list(selected_pages) if selected_pages else []
            selected_pages_1indexed = [int(p) + 1 for p in selected_pages]  # Convert to 1-indexed
        else:
            # Extract specific pages
            if not page_numbers:
                page_numbers = self.config.get('page_selection', {}).get('default_pages', [5, 12])
            
            # Ensure page_numbers is a List[int]
            if page_numbers is None:
                page_numbers = [5, 12]  # fallback default
                
            temp_pdf_path = str(extractor.extract_specific_pages(page_numbers))
            selected_pages_1indexed = list(page_numbers)
        
        logger.info(f"Created temporary PDF with pages {selected_pages_1indexed}: {temp_pdf_path}")
        
        # Copy temp PDF to organized reports structure
        temp_pdf_name = Path(temp_pdf_path).name
        organized_temp_pdf = self.temp_pdfs_dir / temp_pdf_name
        import shutil
        shutil.copy2(temp_pdf_path, organized_temp_pdf)
        
        logger.info(f"Copied to reports folder: {organized_temp_pdf}")
        return str(organized_temp_pdf), selected_pages_1indexed
    
    def process_with_google_ai(self, temp_pdf_path):
        """
        Process the temporary PDF with Google Document AI.
        
        Args:
            temp_pdf_path: Path to the temporary PDF file
        
        Returns:
            (result_dict, output_json_path)
        """
        logger.info("Starting Google Document AI processing...")
        
        project_id = self.google_ai_config.get('project_id')
        processor_id = self.google_ai_config.get('processor_id')
        location = self.google_ai_config.get('location', 'us')
        
        if not project_id or not processor_id:
            raise ValueError("Google Cloud project_id and processor_id must be configured!")
        
        # Check if credentials path is set
        credentials_path = self.google_ai_config.get('credentials_path')
        if credentials_path:
            import os
            os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = credentials_path
        
        try:
            result = process_pdf_with_google_ai(  # type: ignore
                pdf_path=temp_pdf_path,
                project_id=project_id,
                processor_id=processor_id,
                location=location,
                output_dir=str(self.raw_results_dir)
            )
            
            logger.info(f"Google AI processing completed: {result['output_file']}")
            return result['result'], result['output_file']
            
        except Exception as e:
            logger.error(f"Google Document AI processing failed: {e}")
            raise
    
    def parse_results(self, json_path):
        """
        Parse Google Document AI results.
        
        Args:
            json_path (str): Path to the JSON result file
        
        Returns:
            Dict: Parsed results
        """
        logger.info(f"Parsing Google AI results: {json_path}")
        
        parsed_results = parse_google_ai_result(json_path, str(self.parsed_results_dir))
        
        logger.info(f"Parsing completed. Found:")
        logger.info(f"  - Pages: {parsed_results['document_info']['total_pages']}")
        logger.info(f"  - Tables: {len(parsed_results['tables'])}")
        logger.info(f"  - Entities: {len(parsed_results['entities'])}")
        logger.info(f"  - Form Fields: {len(parsed_results['form_fields'])}")
        
        return parsed_results
    
    def _get_parsed_data_for_pages(self, parsed_dir, pages_processed):
        """Extract parsed data only for the specific pages processed by Google AI."""
        logger.info(f"Extracting parsed data for pages: {pages_processed}")
        
        parsed_summary = {
            "pages_analyzed": pages_processed,
            "tables_found": 0,
            "text_length": 0,
            "docling_files": 0,
            "layout_files": 0,
            "metadata_files": 0,
            "page_specific_data": {}
        }
        
        # Read metadata to find page-specific data
        metadata_dir = parsed_dir / "metadata"
        if metadata_dir.exists():
            metadata_files = list(metadata_dir.glob("*.jsonl"))
            if metadata_files:
                page_data_map = {}
                
                # Parse metadata to map page numbers to data
                with open(metadata_files[0], 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.strip():
                            try:
                                record = json.loads(line)
                                page_num = record.get('page')
                                if page_num in pages_processed:
                                    if page_num not in page_data_map:
                                        page_data_map[page_num] = {'tables': 0, 'text_length': 0}
                                    
                                    if record.get('block_type') == 'table':
                                        page_data_map[page_num]['tables'] += 1
                                        parsed_summary['tables_found'] += 1
                                    
                                    if 'text' in record:
                                        text_length = len(record['text'])
                                        page_data_map[page_num]['text_length'] += text_length
                                        parsed_summary['text_length'] += text_length
                                        
                            except json.JSONDecodeError:
                                continue
                
                parsed_summary['page_specific_data'] = page_data_map
                parsed_summary['metadata_files'] = len(metadata_files)
        
        # Count other file types for completeness
        docling_dir = parsed_dir / "docling"
        if docling_dir.exists():
            parsed_summary['docling_files'] = len(list(docling_dir.glob("*.json")))
        
        layout_dir = parsed_dir / "layout"
        if layout_dir.exists():
            parsed_summary['layout_files'] = len(list(layout_dir.glob("*.json")))
        
        logger.info(f"Parsed data page-specific analysis: {parsed_summary['tables_found']} tables, {parsed_summary['text_length']} characters")
        return parsed_summary
    
    def _create_page_comparison(self, google_ai_summary, parsed_summary, pages_processed):
        """Create detailed page-to-page comparison."""
        comparison = {
            "google_ai_summary": google_ai_summary,
            "parsed_data_summary": parsed_summary,
            "comparison_results": {
                "pages_analyzed": pages_processed,
                "text_length_ratio": (google_ai_summary["total_text_length"] / max(parsed_summary["text_length"], 1)),
                "table_detection": {
                    "google_ai_tables": google_ai_summary["tables_found"],
                    "parsed_data_tables": parsed_summary["tables_found"],
                    "difference": google_ai_summary["tables_found"] - parsed_summary["tables_found"],
                    "note": f"Both processed same pages: {pages_processed}"
                },
                "text_analysis": {
                    "google_ai_text_length": google_ai_summary["total_text_length"],
                    "parsed_data_text_length": parsed_summary["text_length"],
                    "ratio": (google_ai_summary["total_text_length"] / max(parsed_summary["text_length"], 1)),
                    "coverage": f"Page-to-page comparison for pages {pages_processed}"
                },
                "page_breakdown": {}
            },
            "analysis": []
        }
        
        # Add per-page breakdown if available
        if "page_specific_data" in parsed_summary:
            for page in pages_processed:
                page_data = parsed_summary["page_specific_data"].get(page, {"tables": 0, "text_length": 0})
                comparison["comparison_results"]["page_breakdown"][f"page_{page}"] = {
                    "parsed_data_tables": page_data["tables"],
                    "parsed_data_text_length": page_data["text_length"],
                    "google_ai_contribution": f"Part of {google_ai_summary['total_text_length']} total characters"
                }
        
        # Generate analysis insights
        if google_ai_summary["tables_found"] == 0 and parsed_summary["tables_found"] == 0:
            comparison["analysis"].append(f"Neither Google AI nor your parsed data detected tables in pages {pages_processed}")
        elif google_ai_summary["tables_found"] == 0 and parsed_summary["tables_found"] > 0:
            comparison["analysis"].append(f"Your parsed data detected {parsed_summary['tables_found']} tables in pages {pages_processed}, Google AI detected none")
        elif google_ai_summary["tables_found"] > 0 and parsed_summary["tables_found"] == 0:
            comparison["analysis"].append(f"Google AI detected {google_ai_summary['tables_found']} tables in pages {pages_processed}, your parsed data detected none")
        else:
            comparison["analysis"].append(f"Both detected tables: Google AI ({google_ai_summary['tables_found']}) vs Your parsed data ({parsed_summary['tables_found']})")
        
        text_ratio = comparison["comparison_results"]["text_analysis"]["ratio"]
        if text_ratio < 0.5:
            comparison["analysis"].append(f"Google AI extracted {text_ratio*100:.1f}% of your parsed data's text from same pages - may indicate different extraction methods")
        elif text_ratio > 1.5:
            comparison["analysis"].append(f"Google AI extracted {text_ratio*100:.1f}% more text than your parsed data from same pages")
        else:
            comparison["analysis"].append(f"Text extraction similar: Google AI vs your parsed data ratio = {text_ratio:.2f}")
        
        return comparison
    
    def compare_with_parsed_data(self, google_results, original_pdf, selected_pages):
        """
        Compare Google AI results with existing parsed data using page-specific matching.
        
        Args:
            google_results (Dict): Parsed Google AI results
            original_pdf (str): Path to the original PDF
            selected_pages (List[int]): Pages that were processed
        
        Returns:
            Dict: Comparison results with page-to-page analysis
        """
        logger.info("Comparing Google AI results with your parsed data using page-specific matching...")
        
        # Look for existing parsed data results
        pdf_name = Path(original_pdf).stem
        parsed_data_dir = Path("data/parsed")
        
        google_ai_summary = {
            "pages_processed": selected_pages,
            "total_text_length": google_results['document_info']['total_text_length'],
            "tables_found": len(google_results['tables']),
            "entities_found": len(google_results['entities']),
            "form_fields_found": len(google_results['form_fields'])
        }
        
        # Try to find parsed data results - look for directories containing the PDF name
        parsed_result_dirs = []
        
        # Look for directories that contain the PDF name
        for item in parsed_data_dir.iterdir():
            if item.is_dir() and pdf_name.lower() in item.name.lower():
                parsed_result_dirs.append(item)
        
        if parsed_result_dirs:
            # Use the most recent parsed data result directory
            parsed_dir = sorted(parsed_result_dirs, key=lambda x: x.name)[-1]
            logger.info(f"Found parsed data results directory: {parsed_dir}")
            
            # Get page-specific parsed data for matching pages
            parsed_summary = self._get_parsed_data_for_pages(parsed_dir, selected_pages)
            
            # Create page-to-page comparison
            comparison = self._create_page_comparison(google_ai_summary, parsed_summary, selected_pages)
            
        else:
            logger.warning("No parsed data results found for comparison")
            comparison = {
                "google_ai_summary": google_ai_summary,
                "parsed_data_summary": {
                    "pages_analyzed": selected_pages,
                    "tables_found": 0,
                    "text_length": 0,
                    "error": "No parsed data found"
                },
                "comparison_results": {
                    "pages_analyzed": selected_pages,
                    "text_length_ratio": 0,
                    "table_detection": {
                        "google_ai_tables": google_ai_summary["tables_found"],
                        "parsed_data_tables": 0,
                        "difference": google_ai_summary["tables_found"],
                        "note": "No parsed data available for comparison"
                    }
                },
                "analysis": ["No parsed data results available for comparison"]
            }
        
        # Save comparison results to organized folder
        comparison_file = self.comparison_dir / f"parsed_data_vs_google_ai_comparison.json"
        with open(comparison_file, 'w', encoding='utf-8') as f:
            json.dump(comparison, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Comparison results saved to: {comparison_file}")
        return comparison
    
    def generate_report(self, workflow_results):
        """
        Generate a comprehensive workflow report.
        
        Args:
            workflow_results (Dict): Complete workflow results
        
        Returns:
            str: Path to the generated report
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_path = self.final_report_dir / f"lab7_comprehensive_report_{timestamp}.md"
        
        report_content = f"""# Lab 7: Google Document AI Integration Report

**Generated**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Workflow Summary

### Input
- **Original PDF**: {workflow_results['original_pdf']}
- **Pages Selected**: {workflow_results['selected_pages']}
- **Selection Method**: {'Random' if workflow_results['random_selection'] else 'Specific'}

### Processing Results
- **Temporary PDF**: {workflow_results['temp_pdf']}
- **Google AI JSON**: {workflow_results['google_json']}
- **Processing Time**: {workflow_results.get('processing_time', 'N/A')}

## Google Document AI Analysis

### Document Information
- **Total Pages Processed**: {workflow_results['parsed_results']['document_info']['total_pages']}
- **Total Text Length**: {workflow_results['parsed_results']['document_info']['total_text_length']:,} characters
- **Processor Used**: {workflow_results['parsed_results']['document_info']['processor_id']}

### Content Detected
- **Tables**: {len(workflow_results['parsed_results']['tables'])}
- **Named Entities**: {len(workflow_results['parsed_results']['entities'])}
- **Form Fields**: {len(workflow_results['parsed_results']['form_fields'])}

"""
        
        # Add table details if any
        if workflow_results['parsed_results']['tables']:
            report_content += "\n### Table Analysis\n"
            for table in workflow_results['parsed_results']['tables']:
                report_content += f"""
**{table['table_id']}** (Page {table['page_number']})
- Dimensions: {table['row_count']} rows × {table['col_count']} columns
- Header rows: {len(table['header_rows'])}
- Body rows: {len(table['body_rows'])}
"""
        
        # Add entity analysis if any
        if workflow_results['parsed_results']['entities']:
            report_content += "\n### Named Entities\n"
            entity_summary = {}
            for entity in workflow_results['parsed_results']['entities']:
                entity_type = entity['type']
                if entity_type not in entity_summary:
                    entity_summary[entity_type] = []
                entity_summary[entity_type].append(entity['mention_text'])
            
            for entity_type, mentions in entity_summary.items():
                report_content += f"- **{entity_type}**: {', '.join(mentions[:5])}{'...' if len(mentions) > 5 else ''}\n"
        
        # Add comparison results
        if 'comparison' in workflow_results:
            comparison = workflow_results['comparison']
            report_content += f"""

## Comparison with Existing Parsed Data

### Summary
- **Google AI Text Length**: {comparison['google_ai_summary']['total_text_length']:,} characters
- **Google AI Tables**: {comparison['google_ai_summary']['tables_found']}
- **Parsed Data Tables**: {comparison['parsed_data_summary'].get('tables_found', 'N/A')}

### Analysis Insights
"""
            for insight in comparison['analysis']:
                report_content += f"- {insight}\n"
        
        # Add file outputs
        if 'saved_files' in workflow_results['parsed_results']:
            report_content += "\n## Generated Files\n"
            for file_type, file_path in workflow_results['parsed_results']['saved_files'].items():
                report_content += f"- **{file_type.title()}**: `{file_path}`\n"
        
        report_content += f"""

## File Organization

All outputs have been organized in the reports folder:

### Session Directory: `{self.session_dir}`

#### Temporary PDFs
- **Location**: `{self.temp_pdfs_dir}`
- **Contents**: Extracted pages from original PDF

#### Raw Google AI Results  
- **Location**: `{self.raw_results_dir}`
- **Contents**: JSON responses from Google Document AI

#### Parsed Results
- **Location**: `{self.parsed_results_dir}` 
- **Contents**: Structured text, tables, entities, layouts

#### Parsed Data Comparison
- **Location**: `{self.comparison_dir}`
- **Contents**: Comparison analysis with existing parsed data

#### Final Reports
- **Location**: `{self.final_report_dir}`
- **Contents**: This comprehensive report and summaries

## Technical Details

### Configuration Used
```json
{json.dumps(self.google_ai_config, indent=2)}
```

### Workflow Steps Completed
1. PDF page extraction -> `{self.temp_pdfs_dir}`
2. Google Document AI processing -> `{self.raw_results_dir}`
3. Result parsing and analysis -> `{self.parsed_results_dir}`
4. Comparison with existing parsed data -> `{self.comparison_dir}`
5. Report generation -> `{self.final_report_dir}`

---

*Report generated by Lab 7 Google Document AI Integration Workflow*
*All files organized in: {self.session_dir}*
"""
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Generated comprehensive report: {report_path}")
        return str(report_path)
    
    def run_complete_workflow(self, pdf_path, page_numbers=None, random_pages=None, seed=None):
        """
        Execute the complete Google Document AI workflow.
        
        Args:
            pdf_path (str): Path to the original PDF
            page_numbers (Optional[List[int]]): Specific pages to process
            random_pages (Optional[int]): Number of random pages to process
            seed (Optional[int]): Random seed for reproducibility
        
        Returns:
            Dict: Complete workflow results
        """
        start_time = datetime.now()
        logger.info("=" * 50)
        logger.info("STARTING LAB 7 GOOGLE DOCUMENT AI WORKFLOW")
        logger.info("=" * 50)
        
        try:
            # Step 1: Extract pages
            temp_pdf, selected_pages = self.extract_pages(pdf_path, page_numbers, random_pages, seed)
            
            # Step 2: Process with Google Document AI
            result_dict, json_path = self.process_with_google_ai(temp_pdf)
            
            # Step 3: Parse results
            parsed_results = self.parse_results(json_path)
            
            # Step 4: Compare with existing parsed data
            comparison_results = self.compare_with_parsed_data(parsed_results, pdf_path, selected_pages)
            
            # Step 5: Compile workflow results
            workflow_results = {
                "success": True,
                "timestamp": datetime.now().isoformat(),
                "processing_time": str(datetime.now() - start_time),
                "original_pdf": pdf_path,
                "selected_pages": selected_pages,
                "random_selection": random_pages is not None,
                "temp_pdf": temp_pdf,
                "google_json": json_path,
                "parsed_results": parsed_results,
                "comparison": comparison_results,
                "config_used": self.google_ai_config
            }
            
            # Step 6: Generate report
            report_path = self.generate_report(workflow_results)
            workflow_results['report'] = report_path
            
            end_time = datetime.now()
            logger.info("=" * 50)
            logger.info("WORKFLOW COMPLETED SUCCESSFULLY")
            logger.info(f"Total time: {end_time - start_time}")
            logger.info(f"Report: {report_path}")
            logger.info("=" * 50)
            
            return workflow_results
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
                "processing_time": str(datetime.now() - start_time)
            }


def main():
    """Main function to run the Lab 7 workflow."""
    parser = argparse.ArgumentParser(
        description="Lab 7: Google Document AI Integration with Page Selection"
    )
    
    parser.add_argument(
        '--pdf',
        required=True,
        help='Path to the input PDF file'
    )
    
    parser.add_argument(
        '--pages',
        nargs='+',
        type=int,
        help='Specific page numbers to extract (1-indexed). Example: --pages 5 12'
    )
    
    parser.add_argument(
        '--random',
        type=int,
        help='Number of random pages to extract. Example: --random 2'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducible random page selection'
    )
    
    parser.add_argument(
        '--config',
        default='configs/google_ai_config.json',
        help='Path to Google AI configuration file'
    )
    
    parser.add_argument(
        '--output-dir',
        default='data/lab7_results',
        help='Output directory for results'
    )
    
    args = parser.parse_args()
    
    # Validate arguments
    if args.pages and args.random:
        print("Error: Cannot specify both --pages and --random. Choose one.")
        return 1
    
    if not args.pages and not args.random:
        print("Using default pages [5, 12]. Use --pages or --random to specify different selection.")
    
    # Check if PDF exists
    if not Path(args.pdf).exists():
        print(f"Error: PDF file not found: {args.pdf}")
        return 1
    
    try:
        # Initialize workflow
        workflow = Lab7GoogleAIWorkflow(args.config)
        
        # Run workflow
        results = workflow.run_complete_workflow(
            pdf_path=args.pdf,
            page_numbers=args.pages,
            random_pages=args.random,
            seed=args.seed
        )
        
        if results['success']:
            print("\\nWorkflow completed successfully!")
            print(f"Report: {results['report']}")
            print(f"Processed {len(results['selected_pages'])} pages")
            print(f"Found {len(results['parsed_results']['tables'])} tables")
            print(f"Found {len(results['parsed_results']['entities'])} entities")
            return 0
        else:
            print(f"\\nWorkflow failed: {results['error']}")
            return 1
            
    except KeyboardInterrupt:
        print("\\nWorkflow interrupted by user.")
        return 1
    except Exception as e:
        print(f"\\nUnexpected error: {e}")
        logger.exception("Unexpected error in main workflow")
        return 1


if __name__ == "__main__":
    exit(main())