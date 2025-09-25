"""
Google Document AI Integration Module
Team 5 - DAMG7245 Fall 2025

This module provides functionality to send PDFs to Google Document AI
and process the results for text, tables, and layout information.
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

try:
    from google.api_core import exceptions as google_exceptions
    from google.cloud import documentai_v1 as documentai

    GOOGLE_AI_AVAILABLE = True
except ImportError:
    GOOGLE_AI_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleDocumentAIProcessor:
    """
    A processor class for Google Document AI operations.
    """

    def __init__(
        self, project_id: str, location: str = "us", processor_id: Optional[str] = None
    ):
        """
        Initialize the Google Document AI processor.

        Args:
            project_id (str): Google Cloud Project ID
            location (str): Processing location (default: "us")
            processor_id (Optional[str]): Specific processor ID to use
        """
        if not GOOGLE_AI_AVAILABLE:
            raise ImportError(
                "Google Document AI client library not available. Install with: pip install google-cloud-documentai"
            )

        self.project_id = project_id
        self.location = location
        self.processor_id = processor_id
        self.client = None
        self.processor_name = None

        self._initialize_client()

    def _initialize_client(self):
        """Initialize the Document AI client and processor name."""
        try:
            self.client = documentai.DocumentProcessorServiceClient()

            if self.processor_id:
                self.processor_name = f"projects/{self.project_id}/locations/{self.location}/processors/{self.processor_id}"
            else:
                # List available processors and use the first general processor
                parent = f"projects/{self.project_id}/locations/{self.location}"
                processors = self.client.list_processors(parent=parent)

                for processor in processors:
                    if (
                        "general" in processor.type_.lower()
                        or "document" in processor.type_.lower()
                    ):
                        self.processor_name = processor.name
                        self.processor_id = processor.name.split("/")[-1]
                        break

                if not self.processor_name:
                    raise ValueError(
                        "No suitable processor found. Please specify a processor_id."
                    )

            logger.info(
                f"Initialized Google Document AI client with processor: {self.processor_id}"
            )

        except Exception as e:
            logger.error(f"Failed to initialize Google Document AI client: {e}")
            raise

    def process_pdf(
        self, pdf_path: str, output_dir: Optional[str] = None
    ) -> Tuple[Dict, str]:
        """
        Process a PDF file with Google Document AI.

        Args:
            pdf_path (str): Path to the PDF file to process
            output_dir (Optional[str]): Directory to save the JSON output

        Returns:
            Tuple[Dict, str]: (processed_result_dict, output_json_path)
        """
        pdf_path = Path(pdf_path)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")

        # Prepare output path
        if output_dir:
            output_dir = Path(output_dir)
            output_dir.mkdir(parents=True, exist_ok=True)
            output_json = output_dir / f"{pdf_path.stem}_google_ai.json"
        else:
            output_json = pdf_path.parent / f"{pdf_path.stem}_google_ai.json"

        try:
            # Read PDF file
            with open(pdf_path, "rb") as pdf_file:
                document = documentai.RawDocument(
                    content=pdf_file.read(), mime_type="application/pdf"
                )

            # Process document
            logger.info(f"Sending PDF to Google Document AI: {pdf_path.name}")
            request = documentai.ProcessRequest(
                name=self.processor_name, raw_document=document
            )

            result = self.client.process_document(request=request)

            # Convert result to dictionary
            result_dict = {
                "document": self._document_to_dict(result.document),
                "processing_metadata": {
                    "processor_id": self.processor_id,
                    "project_id": self.project_id,
                    "location": self.location,
                    "processed_at": datetime.now().isoformat(),
                    "original_pdf": str(pdf_path),
                    "pdf_size_mb": pdf_path.stat().st_size / (1024 * 1024),
                },
            }

            # Save JSON output
            with open(output_json, "w", encoding="utf-8") as json_file:
                json.dump(result_dict, json_file, indent=2, ensure_ascii=False)

            logger.info(
                f"Google Document AI processing completed. Output saved to: {output_json}"
            )

            return result_dict, str(output_json)

        except google_exceptions.GoogleAPIError as e:
            logger.error(f"Google API error: {e}")
            raise
        except Exception as e:
            logger.error(f"Failed to process PDF with Google Document AI: {e}")
            raise

    def _document_to_dict(self, document) -> Dict:
        """
        Convert a Google Document AI Document object to a dictionary.

        Args:
            document: Google Document AI Document object

        Returns:
            Dict: Document data as dictionary
        """
        doc_dict = {
            "text": document.text,
            "pages": [],
            "entities": [],
            "text_styles": [],
        }

        # Process pages
        for page_idx, page in enumerate(document.pages):
            page_dict = {
                "page_number": page_idx + 1,
                "dimensions": {
                    "width": page.dimension.width if page.dimension else None,
                    "height": page.dimension.height if page.dimension else None,
                    "unit": page.dimension.unit if page.dimension else None,
                },
                "blocks": [],
                "paragraphs": [],
                "lines": [],
                "tokens": [],
                "tables": [],
                "form_fields": [],
            }

            # Process blocks
            for block in page.blocks:
                page_dict["blocks"].append(self._layout_to_dict(block.layout, "block"))

            # Process paragraphs
            for paragraph in page.paragraphs:
                page_dict["paragraphs"].append(
                    self._layout_to_dict(paragraph.layout, "paragraph")
                )

            # Process lines
            for line in page.lines:
                page_dict["lines"].append(self._layout_to_dict(line.layout, "line"))

            # Process tokens
            for token in page.tokens:
                page_dict["tokens"].append(self._layout_to_dict(token.layout, "token"))

            # Process tables
            for table_idx, table in enumerate(page.tables):
                table_dict = {
                    "table_id": table_idx,
                    "header_rows": [],
                    "body_rows": [],
                    "layout": (
                        self._layout_to_dict(table.layout, "table")
                        if table.layout
                        else None
                    ),
                }

                # Process header rows
                for row in table.header_rows:
                    table_dict["header_rows"].append(
                        self._process_table_row(row, document.text)
                    )

                # Process body rows
                for row in table.body_rows:
                    table_dict["body_rows"].append(
                        self._process_table_row(row, document.text)
                    )

                page_dict["tables"].append(table_dict)

            # Process form fields
            for form_field in page.form_fields:
                field_dict = {
                    "field_name": (
                        self._extract_text_from_layout(
                            form_field.field_name, document.text
                        )
                        if form_field.field_name
                        else ""
                    ),
                    "field_value": (
                        self._extract_text_from_layout(
                            form_field.field_value, document.text
                        )
                        if form_field.field_value
                        else ""
                    ),
                    "name_layout": (
                        self._layout_to_dict(form_field.field_name, "form_field_name")
                        if form_field.field_name
                        else None
                    ),
                    "value_layout": (
                        self._layout_to_dict(form_field.field_value, "form_field_value")
                        if form_field.field_value
                        else None
                    ),
                }
                page_dict["form_fields"].append(field_dict)

            doc_dict["pages"].append(page_dict)

        # Process entities
        for entity in document.entities:
            entity_dict = {
                "type": entity.type_,
                "mention_text": entity.mention_text,
                "normalized_value": (
                    entity.normalized_value.text if entity.normalized_value else None
                ),
                "confidence": entity.confidence,
                "page_refs": [],
            }

            for page_ref in entity.page_anchor.page_refs:
                entity_dict["page_refs"].append(
                    {
                        "page": page_ref.page,
                        "layout_type": page_ref.layout_type,
                        "layout_id": page_ref.layout_id,
                    }
                )

            doc_dict["entities"].append(entity_dict)

        return doc_dict

    def _layout_to_dict(self, layout, element_type: str) -> Dict:
        """Convert layout information to dictionary."""
        if not layout:
            return None

        layout_dict = {
            "element_type": element_type,
            "text": "",
            "confidence": layout.confidence if hasattr(layout, "confidence") else None,
            "bounding_poly": None,
            "orientation": (
                layout.orientation if hasattr(layout, "orientation") else None
            ),
        }

        # Extract text if text_anchor exists
        if hasattr(layout, "text_anchor") and layout.text_anchor:
            layout_dict["text"] = self._extract_text_from_layout(layout, "")

        # Extract bounding polygon
        if hasattr(layout, "bounding_poly") and layout.bounding_poly:
            layout_dict["bounding_poly"] = {
                "vertices": [
                    {"x": v.x, "y": v.y} for v in layout.bounding_poly.vertices
                ]
            }

        return layout_dict

    def _extract_text_from_layout(self, layout, document_text: str) -> str:
        """Extract text from layout using text anchors."""
        if not layout or not hasattr(layout, "text_anchor"):
            return ""

        text_segments = []
        for segment in layout.text_anchor.text_segments:
            start_idx = segment.start_index if segment.start_index else 0
            end_idx = segment.end_index if segment.end_index else len(document_text)
            text_segments.append(document_text[start_idx:end_idx])

        return "".join(text_segments)

    def _process_table_row(self, row, document_text: str) -> List[Dict]:
        """Process a table row and return cell information."""
        cells = []
        for cell in row.cells:
            cell_dict = {
                "text": (
                    self._extract_text_from_layout(cell.layout, document_text)
                    if cell.layout
                    else ""
                ),
                "row_span": cell.row_span,
                "col_span": cell.col_span,
                "layout": (
                    self._layout_to_dict(cell.layout, "table_cell")
                    if cell.layout
                    else None
                ),
            }
            cells.append(cell_dict)
        return cells

    def get_available_processors(self) -> List[Dict]:
        """
        Get list of available processors in the project.

        Returns:
            List[Dict]: List of available processors with their details
        """
        try:
            parent = f"projects/{self.project_id}/locations/{self.location}"
            processors = self.client.list_processors(parent=parent)

            processor_list = []
            for processor in processors:
                processor_list.append(
                    {
                        "name": processor.name,
                        "display_name": processor.display_name,
                        "type": processor.type_,
                        "state": processor.state.name,
                        "default_processor_version": processor.default_processor_version,
                        "processor_version_aliases": list(
                            processor.processor_version_aliases
                        ),
                    }
                )

            return processor_list

        except Exception as e:
            logger.error(f"Failed to get available processors: {e}")
            return []


# Configuration and utility functions
def load_google_ai_config(config_path: str = "configs/google_ai_config.yaml") -> Dict:
    """
    Load Google Document AI configuration from YAML file.

    Args:
        config_path (str): Path to the configuration file

    Returns:
        Dict: Configuration dictionary
    """
    import yaml

    config_path = Path(config_path)
    if not config_path.exists():
        # Create default config
        default_config = {
            "google_document_ai": {
                "project_id": "your-project-id",
                "location": "us",
                "processor_id": "your-processor-id",
                "credentials_path": "path/to/service-account-key.json",
            }
        }

        config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(config_path, "w") as f:
            yaml.dump(default_config, f, indent=2)

        logger.warning(
            f"Created default config at {config_path}. Please update with your credentials."
        )
        return default_config

    with open(config_path, "r") as f:
        return yaml.safe_load(f)


def process_pdf_with_google_ai(
    pdf_path: str,
    project_id: str,
    processor_id: str,
    location: str = "us",
    output_dir: Optional[str] = None,
) -> Dict:
    """
    Convenience function to process a PDF with Google Document AI.

    Args:
        pdf_path (str): Path to the PDF file
        project_id (str): Google Cloud Project ID
        processor_id (str): Document AI Processor ID
        location (str): Processing location
        output_dir (Optional[str]): Output directory for results

    Returns:
        Dict: Processing results with metadata
    """
    processor = GoogleDocumentAIProcessor(project_id, location, processor_id)
    result_dict, output_json = processor.process_pdf(pdf_path, output_dir)

    return {
        "success": True,
        "result": result_dict,
        "output_file": output_json,
        "processor_info": {
            "project_id": project_id,
            "processor_id": processor_id,
            "location": location,
        },
    }


# Example usage
if __name__ == "__main__":
    # Example configuration (replace with your actual values)
    PROJECT_ID = "your-project-id"
    PROCESSOR_ID = "your-processor-id"
    LOCATION = "us"

    # Example: Process a temporary PDF created by page extractor
    temp_pdf = "data/temp/tesla_pages_5_12.pdf"
    output_dir = "data/google_ai_results"

    try:
        if GOOGLE_AI_AVAILABLE:
            result = process_pdf_with_google_ai(
                pdf_path=temp_pdf,
                project_id=PROJECT_ID,
                processor_id=PROCESSOR_ID,
                location=LOCATION,
                output_dir=output_dir,
            )
            print(f"Processing completed: {result['output_file']}")
        else:
            print(
                "Google Document AI library not available. Install with: pip install google-cloud-documentai"
            )

    except Exception as e:
        print(f"Error: {e}")
