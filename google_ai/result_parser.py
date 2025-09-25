"""
Google Document AI Result Parser
Team 5 - DAMG7245 Fall 2025

This module provides functionality to parse Google Document AI JSON results
and extract text, tables, and layout information for analysis and comparison.
"""

# pyright: ignore
# pylint: disable-all

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import pandas as pd  # type: ignore

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class GoogleAIResultParser:
    """
    Parser for Google Document AI JSON results.
    """

    def __init__(self, json_path: str):
        """
        Initialize the parser with a Google Document AI JSON result file.

        Args:
            json_path: Path to the JSON result file from Google Document AI
        """
        self.json_path = Path(json_path)
        self.data: Any = None
        self.document: Any = None
        self.pages: Any = []

        if not self.json_path.exists():
            raise FileNotFoundError(f"JSON result file not found: {json_path}")

        self._load_json()

    def _load_json(self):
        """Load and parse the JSON result file."""
        try:
            with open(self.json_path, "r", encoding="utf-8") as f:
                self.data = json.load(f)

            self.document = self.data.get("document", {})
            self.pages = self.document.get("pages", [])

            logger.info(
                f"Loaded Google AI results: {len(self.pages)} pages from {self.json_path.name}"
            )

        except Exception as e:
            logger.error(f"Failed to load JSON file: {e}")
            raise

    def get_document_info(self):
        """
        Get basic information about the processed document.

        Returns:
            Document metadata and processing information
        """
        processing_meta = self.data.get("processing_metadata", {})

        return {
            "source_file": self.json_path.name,
            "original_pdf": processing_meta.get("original_pdf", ""),
            "total_pages": len(self.pages),
            "total_text_length": len(self.document.get("text", "")),
            "processor_id": processing_meta.get("processor_id", ""),
            "processed_at": processing_meta.get("processed_at", ""),
            "pdf_size_mb": processing_meta.get("pdf_size_mb", 0),
            "has_tables": any(len(page.get("tables", [])) > 0 for page in self.pages),
            "has_form_fields": any(
                len(page.get("form_fields", [])) > 0 for page in self.pages
            ),
            "total_entities": len(self.document.get("entities", [])),
        }

    def extract_full_text(self):
        """
        Extract the complete text content from the document.

        Returns:
            Full text content
        """
        return self.document.get("text", "")

    def extract_page_texts(self):
        """
        Extract text content organized by pages.

        Returns:
            List of page text data with metadata
        """
        page_texts = []
        full_text = self.document.get("text", "")

        for page_idx, page in enumerate(self.pages):
            page_text = ""

            # Extract text from paragraphs
            for paragraph in page.get("paragraphs", []):
                if paragraph.get("text"):
                    page_text += paragraph["text"] + "\n"

            # If no paragraph text, extract from lines
            if not page_text.strip():
                for line in page.get("lines", []):
                    if line.get("text"):
                        page_text += line["text"] + "\n"

            # If still no text, extract from tokens
            if not page_text.strip():
                for token in page.get("tokens", []):
                    if token.get("text"):
                        page_text += token["text"] + " "
                page_text = page_text.strip() + "\n"

            page_info = {
                "page_number": page_idx + 1,
                "text": page_text.strip(),
                "text_length": len(page_text.strip()),
                "paragraph_count": len(page.get("paragraphs", [])),
                "line_count": len(page.get("lines", [])),
                "token_count": len(page.get("tokens", [])),
                "table_count": len(page.get("tables", [])),
                "form_field_count": len(page.get("form_fields", [])),
                "dimensions": page.get("dimensions", {}),
            }

            page_texts.append(page_info)

        return page_texts

    def extract_tables(self):
        """
        Extract all tables from the document with their structure and content.

        Returns:
            List of table data with metadata
        """
        all_tables = []

        for page_idx, page in enumerate(self.pages):
            tables = page.get("tables", [])

            for table_idx, table in enumerate(tables):
                table_data = {
                    "page_number": page_idx + 1,
                    "table_index": table_idx,
                    "table_id": f"p{page_idx + 1}_t{table_idx}",
                    "header_rows": [],
                    "body_rows": [],
                    "all_rows": [],
                    "row_count": 0,
                    "col_count": 0,
                    "layout": table.get("layout"),
                }

                # Process header rows
                header_rows = table.get("header_rows", [])
                for row in header_rows:
                    row_data = [cell.get("text", "").strip() for cell in row]
                    table_data["header_rows"].append(row_data)
                    table_data["all_rows"].append(row_data)

                # Process body rows
                body_rows = table.get("body_rows", [])
                for row in body_rows:
                    row_data = [cell.get("text", "").strip() for cell in row]
                    table_data["body_rows"].append(row_data)
                    table_data["all_rows"].append(row_data)

                # Calculate dimensions
                table_data["row_count"] = len(table_data["all_rows"])
                if table_data["all_rows"]:
                    table_data["col_count"] = max(
                        len(row) for row in table_data["all_rows"]
                    )

                all_tables.append(table_data)

        return all_tables

    def extract_tables_as_dataframes(self):
        """
        Convert extracted tables to pandas DataFrames.

        Returns:
            List of (table_id, DataFrame) tuples
        """
        tables = self.extract_tables()
        dataframes = []

        for table in tables:
            table_id = table["table_id"]

            if table["all_rows"]:
                # Use header row if available, otherwise create generic column names
                if table["header_rows"]:
                    columns = (
                        table["header_rows"][0]
                        if table["header_rows"][0]
                        else [f"Col_{i}" for i in range(table["col_count"])]
                    )
                    data_rows = table["body_rows"]
                else:
                    columns = [f"Col_{i}" for i in range(table["col_count"])]
                    data_rows = table["all_rows"]

                # Ensure all rows have the same number of columns
                max_cols = len(columns)
                normalized_rows = []
                for row in data_rows:
                    normalized_row = row + [""] * (
                        max_cols - len(row)
                    )  # Pad with empty strings
                    normalized_rows.append(
                        normalized_row[:max_cols]
                    )  # Truncate if too long

                try:
                    df = pd.DataFrame(normalized_rows, columns=columns)
                    dataframes.append((table_id, df))
                except Exception as e:
                    logger.warning(
                        f"Failed to create DataFrame for table {table_id}: {e}"
                    )
                    # Create a simple DataFrame with the raw data
                    df = pd.DataFrame(data_rows)
                    dataframes.append((table_id, df))

        return dataframes

    def extract_form_fields(self):
        """
        Extract form fields from the document.

        Returns:
            List of form field data
        """
        all_form_fields = []

        for page_idx, page in enumerate(self.pages):
            form_fields = page.get("form_fields", [])

            for field_idx, field in enumerate(form_fields):
                field_data = {
                    "page_number": page_idx + 1,
                    "field_index": field_idx,
                    "field_id": f"p{page_idx + 1}_f{field_idx}",
                    "field_name": field.get("field_name", "").strip(),
                    "field_value": field.get("field_value", "").strip(),
                    "name_layout": field.get("name_layout"),
                    "value_layout": field.get("value_layout"),
                }
                all_form_fields.append(field_data)

        return all_form_fields

    def extract_entities(self):
        """
        Extract named entities from the document.

        Returns:
            List of entity data
        """
        entities = self.document.get("entities", [])

        processed_entities = []
        for entity in entities:
            entity_data = {
                "type": entity.get("type", ""),
                "mention_text": entity.get("mention_text", ""),
                "normalized_value": entity.get("normalized_value", ""),
                "confidence": entity.get("confidence", 0.0),
                "page_references": entity.get("page_refs", []),
            }
            processed_entities.append(entity_data)

        return processed_entities

    def get_layout_analysis(self):
        """
        Analyze the document layout and structure.

        Returns:
            Layout analysis results
        """
        layout_analysis = {"total_pages": len(self.pages), "pages": []}

        for page_idx, page in enumerate(self.pages):
            page_analysis = {
                "page_number": page_idx + 1,
                "dimensions": page.get("dimensions", {}),
                "elements": {
                    "blocks": len(page.get("blocks", [])),
                    "paragraphs": len(page.get("paragraphs", [])),
                    "lines": len(page.get("lines", [])),
                    "tokens": len(page.get("tokens", [])),
                    "tables": len(page.get("tables", [])),
                    "form_fields": len(page.get("form_fields", [])),
                },
                "bounding_boxes": [],
            }

            # Extract bounding box information
            for element_type in ["blocks", "paragraphs", "lines", "tokens"]:
                for element in page.get(element_type, []):
                    if element.get("bounding_poly"):
                        bbox_info = {
                            "element_type": element_type[:-1],  # Remove 's' from plural
                            "text": element.get("text", ""),
                            "confidence": element.get("confidence"),
                            "bounding_poly": element["bounding_poly"],
                        }
                        page_analysis["bounding_boxes"].append(bbox_info)

            layout_analysis["pages"].append(page_analysis)

        return layout_analysis

    def save_parsed_results(self, output_dir: Any):
        """
        Save all parsed results to separate files.

        Args:
            output_dir: Directory to save the parsed results

        Returns:
            Dictionary of saved file paths
        """
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        base_name = self.json_path.stem.replace("_google_ai", "")
        saved_files = {}

        # Save full text
        text_file = output_dir / f"{base_name}_google_text.txt"
        with open(text_file, "w", encoding="utf-8") as f:
            f.write(self.extract_full_text())
        saved_files["text"] = str(text_file)

        # Save page texts
        page_texts = self.extract_page_texts()
        pages_file = output_dir / f"{base_name}_google_pages.json"
        with open(pages_file, "w", encoding="utf-8") as f:
            json.dump(page_texts, f, indent=2, ensure_ascii=False)
        saved_files["pages"] = str(pages_file)

        # Save tables
        tables = self.extract_tables()
        if tables:
            tables_file = output_dir / f"{base_name}_google_tables.json"
            with open(tables_file, "w", encoding="utf-8") as f:
                json.dump(tables, f, indent=2, ensure_ascii=False)
            saved_files["tables"] = str(tables_file)

            # Save tables as CSV files
            dataframes = self.extract_tables_as_dataframes()
            for table_id, df in dataframes:
                csv_file = output_dir / f"{base_name}_google_{table_id}.csv"
                df.to_csv(csv_file, index=False)
                saved_files[f"table_{table_id}"] = str(csv_file)

        # Save form fields
        form_fields = self.extract_form_fields()
        if form_fields:
            forms_file = output_dir / f"{base_name}_google_forms.json"
            with open(forms_file, "w", encoding="utf-8") as f:
                json.dump(form_fields, f, indent=2, ensure_ascii=False)
            saved_files["forms"] = str(forms_file)

        # Save entities
        entities = self.extract_entities()
        if entities:
            entities_file = output_dir / f"{base_name}_google_entities.json"
            with open(entities_file, "w", encoding="utf-8") as f:
                json.dump(entities, f, indent=2, ensure_ascii=False)
            saved_files["entities"] = str(entities_file)

        # Save layout analysis
        layout = self.get_layout_analysis()
        layout_file = output_dir / f"{base_name}_google_layout.json"
        with open(layout_file, "w", encoding="utf-8") as f:
            json.dump(layout, f, indent=2, ensure_ascii=False)
        saved_files["layout"] = str(layout_file)

        # Save summary report
        summary = self.generate_summary_report()
        summary_file = output_dir / f"{base_name}_google_summary.md"
        with open(summary_file, "w", encoding="utf-8") as f:
            f.write(summary)
        saved_files["summary"] = str(summary_file)

        logger.info(f"Saved {len(saved_files)} parsed result files to {output_dir}")
        return saved_files

    def generate_summary_report(self):
        """
        Generate a comprehensive summary report of the parsed results.

        Returns:
            Markdown-formatted summary report
        """
        doc_info = self.get_document_info()
        page_texts = self.extract_page_texts()
        tables = self.extract_tables()
        form_fields = self.extract_form_fields()
        entities = self.extract_entities()

        report = f"""# Google Document AI Analysis Report
        
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Document Information
- **Source PDF**: {doc_info['original_pdf']}
- **Total Pages**: {doc_info['total_pages']}
- **Total Text Length**: {doc_info['total_text_length']:,} characters
- **PDF Size**: {doc_info['pdf_size_mb']:.2f} MB
- **Processor ID**: {doc_info['processor_id']}
- **Processed At**: {doc_info['processed_at']}

## Content Summary
- **Has Tables**: {doc_info['has_tables']}
- **Has Form Fields**: {doc_info['has_form_fields']}
- **Total Entities**: {doc_info['total_entities']}

## Page Analysis
"""

        for page in page_texts:
            report += f"""
### Page {page['page_number']}
- **Text Length**: {page['text_length']} characters
- **Paragraphs**: {page['paragraph_count']}
- **Lines**: {page['line_count']}
- **Tokens**: {page['token_count']}
- **Tables**: {page['table_count']}
- **Form Fields**: {page['form_field_count']}
"""

        if tables:
            report += "\n## Tables Detected\n"
            for table in tables:
                report += f"""
### {table['table_id']} (Page {table['page_number']})
- **Dimensions**: {table['row_count']} rows × {table['col_count']} columns
- **Header Rows**: {len(table['header_rows'])}
- **Body Rows**: {len(table['body_rows'])}
"""

        if form_fields:
            report += "\n## Form Fields\n"
            for field in form_fields:
                report += f"- **{field['field_name']}**: {field['field_value']} (Page {field['page_number']})\n"

        if entities:
            report += "\n## Named Entities\n"
            for entity in entities:
                report += f"- **{entity['type']}**: {entity['mention_text']} (Confidence: {entity['confidence']:.2f})\n"

        return report


def parse_google_ai_result(json_path: str, output_dir: Any = None):
    """
    Convenience function to parse Google Document AI results.

    Args:
        json_path: Path to the JSON result file
        output_dir: Directory to save parsed results

    Returns:
        Parsed results with metadata
    """
    parser = GoogleAIResultParser(json_path)

    results = {
        "document_info": parser.get_document_info(),
        "full_text": parser.extract_full_text(),
        "page_texts": parser.extract_page_texts(),
        "tables": parser.extract_tables(),
        "form_fields": parser.extract_form_fields(),
        "entities": parser.extract_entities(),
        "layout_analysis": parser.get_layout_analysis(),
    }

    if output_dir:
        saved_files = parser.save_parsed_results(output_dir)
        results["saved_files"] = saved_files

    return results


# Example usage
if __name__ == "__main__":
    # Example: Parse Google AI results
    json_file = "data/google_ai_results/tesla_pages_5_12_google_ai.json"
    output_dir = "data/parsed_google_ai"

    try:
        results = parse_google_ai_result(json_file, output_dir)
        print(f"Parsed Google AI results:")
        print(f"- Document: {results['document_info']['original_pdf']}")
        print(f"- Pages: {results['document_info']['total_pages']}")
        print(f"- Tables: {len(results['tables'])}")
        print(f"- Entities: {len(results['entities'])}")
        print(f"- Form Fields: {len(results['form_fields'])}")

        if "saved_files" in results:
            print(f"- Saved files: {len(results['saved_files'])}")

    except FileNotFoundError:
        print(f"JSON file not found: {json_file}")
        print("Please run Google Document AI processing first.")
    except Exception as e:
        print(f"Error: {e}")
