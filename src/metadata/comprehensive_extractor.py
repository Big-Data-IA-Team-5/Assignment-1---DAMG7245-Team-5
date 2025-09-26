"""
Comprehensive Document Extraction Pipeline
Extracts ALL document elements: text, tables, headings, paragraphs, etc.
Uses the metadata schema to ensure complete coverage.
"""

import json
import logging
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pdfplumber
import pandas as pd
import csv
import re

# Import our schema definitions
import sys
sys.path.append(str(Path(__file__).parent.parent.parent / "configs"))
try:
    from metadata_schema import (
        MetadataRecord, BlockType, ExtractionMethod, 
        create_text_record, create_table_record, TableInfo,
        MetadataValidator, BoundingBox
    )
except ImportError:
    # Fallback - define simplified schema inline
    class BlockType:
        PARAGRAPH = "paragraph"
        HEADING = "heading"
        SUBHEADING = "subheading"
        HEADER = "header"
        FOOTER = "footer"
        TABLE = "table"
        STRUCTURED_CONTENT = "structured_content"
        LAYOUT_BLOCK = "layout_block"
        IMAGE = "image"
        AI_ANALYSIS = "ai_analysis"
        TEXT_BLOCK = "text_block"
        LIST = "list"
    
    class ExtractionMethod:
        PDFPLUMBER_TEXT = "pdfplumber_text"
        DOCLING_MARKDOWN_EXTRACTION = "docling_markdown_extraction"
        DOCLING_AI_ANALYSIS = "docling_ai_analysis"
        LAYOUT_DETECTION = "layout_detection"
        
    def create_metadata_record(doc_id, company, fiscal_year, source_path, page, 
                             text, section, block_type, method, confidence=0.9, bbox=None,
                             table_info=None):
        return {
            "doc_id": doc_id,
            "company": company,
            "fiscal_year": fiscal_year,
            "source_path": source_path,
            "extraction_timestamp": datetime.now().isoformat(),
            "page": page,
            "section": section,
            "block_type": block_type,
            "text": text,
            "extraction_method": method,
            "confidence": confidence,
            "bbox": bbox,
            "table_info": table_info
        }

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ComprehensiveExtractor:
    """Extracts ALL document content according to metadata schema"""
    
    def __init__(self, pdf_path: str, doc_id: str, company: str, fiscal_year: str):
        self.pdf_path = Path(pdf_path)
        self.doc_id = doc_id
        self.company = company
        self.fiscal_year = fiscal_year
        self.records = []
        
    def extract_all_content(self, output_dir: Path) -> List[MetadataRecord]:
        """Extract ALL document content - text, tables, structure, etc."""
        logger.info(f"Starting comprehensive extraction for {self.doc_id}")
        
        # 1. Extract full text content (paragraphs, headings, etc.)
        self._extract_full_text()
        
        # 2. Extract table content from existing CSV files
        self._extract_existing_tables(output_dir)
        
        # 3. Extract docling content if available
        self._extract_docling_content(output_dir)
        
        # 4. Extract layout and structural elements
        self._extract_layout_structure()
        
        # 5. Extract headers, footers, and page metadata
        self._extract_page_metadata()
        
        logger.info(f"Comprehensive extraction complete: {len(self.records)} records")
        return self.records
    
    def _extract_full_text(self):
        """Extract ALL text content from PDF - not just tables"""
        logger.info("Extracting full text content...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    # Get full page text
                    full_text = page.extract_text()
                    if not full_text or len(full_text.strip()) < 10:
                        continue
                        
                    # Split into meaningful chunks
                    chunks = self._split_text_into_chunks(full_text)
                    
                    for i, chunk in enumerate(chunks):
                        if len(chunk.strip()) < 10:
                            continue
                            
                        # Determine block type based on content
                        block_type = self._classify_text_block(chunk)
                        
                        # Create section identifier
                        if len(chunks) > 1:
                            section = f"Page {page_num} - Part {i+1}"
                        else:
                            section = f"Page {page_num} - Content"
                            
                        record = create_text_record(
                            doc_id=self.doc_id,
                            company=self.company,
                            fiscal_year=self.fiscal_year,
                            source_path=str(self.pdf_path.resolve()),
                            page=page_num,
                            text=chunk.strip(),
                            section=section,
                            block_type=block_type,
                            method=ExtractionMethod.PDFPLUMBER_TEXT,
                            confidence=0.9
                        )
                        self.records.append(record)
                        
                    # Extract words with positions for more detailed analysis
                    self._extract_positioned_words(page, page_num)
                    
                except Exception as e:
                    logger.warning(f"Error extracting text from page {page_num}: {e}")
                    
    def _extract_positioned_words(self, page, page_num: int):
        """Extract words with position information for detailed analysis"""
        try:
            words = page.extract_words()
            if not words:
                return
                
            # Group words into logical text blocks
            text_blocks = self._group_words_into_blocks(words)
            
            for i, (text_block, bbox_info) in enumerate(text_blocks):
                if len(text_block.strip()) < 20:  # Skip very short blocks
                    continue
                    
                # Determine if this is a heading, paragraph, etc.
                block_type = self._classify_positioned_text(text_block, bbox_info)
                
                bbox = BoundingBox(
                    x1=bbox_info['x0'], y1=bbox_info['top'],
                    x2=bbox_info['x1'], y2=bbox_info['bottom']
                )
                
                record = create_text_record(
                    doc_id=self.doc_id,
                    company=self.company,
                    fiscal_year=self.fiscal_year,
                    source_path=str(self.pdf_path.resolve()),
                    page=page_num,
                    text=text_block.strip(),
                    section=f"Page {page_num} - Positioned Block {i+1}",
                    block_type=block_type,
                    method=ExtractionMethod.PDFPLUMBER_TEXT,
                    confidence=0.85,
                    bbox=bbox
                )
                self.records.append(record)
                
        except Exception as e:
            logger.warning(f"Error extracting positioned words from page {page_num}: {e}")
    
    def _extract_existing_tables(self, output_dir: Path):
        """Extract table content from existing CSV files"""
        logger.info("Processing existing table extractions...")
        
        tables_dir = output_dir / "tables"
        if not tables_dir.exists():
            return
            
        for csv_file in tables_dir.glob("*.csv"):
            if csv_file.name.startswith("_"):  # Skip analysis files
                continue
                
            try:
                # Parse filename to get metadata
                table_info = self._parse_table_filename(csv_file)
                if not table_info:
                    continue
                    
                # Read CSV content
                with open(csv_file, 'r', encoding='utf-8') as f:
                    csv_reader = csv.reader(f)
                    table_rows = list(csv_reader)
                    
                if not table_rows:
                    continue
                    
                # Format table text
                table_text = self._format_table_text(table_rows)
                
                # Create table record
                record = create_table_record(
                    doc_id=self.doc_id,
                    company=self.company,
                    fiscal_year=self.fiscal_year,
                    source_path=str(self.pdf_path.resolve()),
                    page=table_info['page'],
                    text=table_text,
                    table_info=TableInfo(
                        rows=len(table_rows),
                        cols=len(table_rows[0]) if table_rows else 0,
                        table_id=table_info['table_id'],
                        extraction_method=table_info['method'],
                        file_name=csv_file.name,
                        has_headers=True
                    ),
                    section=f"Page {table_info['page']} - Table {table_info['table_id']} ({table_info['method']})"
                )
                self.records.append(record)
                
            except Exception as e:
                logger.warning(f"Error processing table file {csv_file}: {e}")
    
    def _extract_docling_content(self, output_dir: Path):
        """Extract Docling AI analysis content"""
        logger.info("Processing Docling content...")
        
        docling_dir = output_dir / "docling"
        if not docling_dir.exists():
            return
            
        # Process Docling markdown output
        md_file = docling_dir / "output.md"
        if md_file.exists():
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    
                # Split into sections
                sections = self._parse_docling_markdown(content)
                
                for i, (title, text_content) in enumerate(sections):
                    if len(text_content.strip()) > 50:
                        record = MetadataRecord(
                            doc_id=self.doc_id,
                            company=self.company,
                            fiscal_year=self.fiscal_year,
                            source_path=str(self.pdf_path.resolve()),
                            extraction_timestamp=datetime.now().isoformat(),
                            page=i + 1,  # Approximate page mapping
                            section=f"Docling Section: {title}",
                            block_type=BlockType.STRUCTURED_CONTENT,
                            text=text_content[:1500] + ("..." if len(text_content) > 1500 else ""),
                            extraction_method=ExtractionMethod.DOCLING_MARKDOWN_EXTRACTION,
                            confidence=0.92
                        )
                        self.records.append(record)
                        
            except Exception as e:
                logger.warning(f"Error processing Docling markdown: {e}")
        
        # Process Docling JSON output
        json_file = docling_dir / "output.json"
        if json_file.exists():
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    docling_data = json.load(f)
                    
                # Create AI analysis record
                analysis_text = self._format_docling_analysis(docling_data)
                
                record = MetadataRecord(
                    doc_id=self.doc_id,
                    company=self.company,
                    fiscal_year=self.fiscal_year,
                    source_path=str(self.pdf_path.resolve()),
                    extraction_timestamp=datetime.now().isoformat(),
                    page=1,
                    section="Document AI Analysis",
                    block_type=BlockType.AI_ANALYSIS,
                    text=analysis_text,
                    extraction_method=ExtractionMethod.DOCLING_AI_ANALYSIS,
                    confidence=0.95
                )
                self.records.append(record)
                
            except Exception as e:
                logger.warning(f"Error processing Docling JSON: {e}")
    
    def _extract_layout_structure(self):
        """Extract document layout and structural elements"""
        logger.info("Extracting layout structure...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    # Extract lines and curves (visual elements)
                    lines = page.lines
                    curves = page.curves
                    
                    if lines or curves:
                        structure_info = f"Layout elements found: {len(lines)} lines, {len(curves)} curves"
                        
                        record = MetadataRecord(
                            doc_id=self.doc_id,
                            company=self.company,
                            fiscal_year=self.fiscal_year,
                            source_path=str(self.pdf_path.resolve()),
                            extraction_timestamp=datetime.now().isoformat(),
                            page=page_num,
                            section=f"Page {page_num} - Layout Structure",
                            block_type=BlockType.LAYOUT_BLOCK,
                            text=structure_info,
                            extraction_method=ExtractionMethod.LAYOUT_DETECTION,
                            confidence=0.8
                        )
                        self.records.append(record)
                        
                    # Extract images if present
                    images = page.images
                    for i, img in enumerate(images):
                        record = MetadataRecord(
                            doc_id=self.doc_id,
                            company=self.company,
                            fiscal_year=self.fiscal_year,
                            source_path=str(self.pdf_path.resolve()),
                            extraction_timestamp=datetime.now().isoformat(),
                            page=page_num,
                            section=f"Page {page_num} - Image {i+1}",
                            block_type=BlockType.IMAGE,
                            text=f"Image detected at coordinates {img.get('x0', 0)}, {img.get('top', 0)}",
                            extraction_method=ExtractionMethod.PDFPLUMBER_TEXT,
                            confidence=0.9
                        )
                        self.records.append(record)
                        
                except Exception as e:
                    logger.warning(f"Error extracting layout from page {page_num}: {e}")
    
    def _extract_page_metadata(self):
        """Extract page-level metadata, headers, footers"""
        logger.info("Extracting page metadata...")
        
        with pdfplumber.open(self.pdf_path) as pdf:
            for page_num, page in enumerate(pdf.pages, start=1):
                try:
                    # Extract potential headers (top 10% of page)
                    header_bbox = (0, 0, page.width, page.height * 0.1)
                    header_text = page.within_bbox(header_bbox).extract_text()
                    
                    if header_text and len(header_text.strip()) > 5:
                        record = create_text_record(
                            doc_id=self.doc_id,
                            company=self.company,
                            fiscal_year=self.fiscal_year,
                            source_path=str(self.pdf_path.resolve()),
                            page=page_num,
                            text=header_text.strip(),
                            section=f"Page {page_num} - Header",
                            block_type=BlockType.HEADER,
                            method=ExtractionMethod.PDFPLUMBER_TEXT,
                            confidence=0.8
                        )
                        self.records.append(record)
                    
                    # Extract potential footers (bottom 10% of page)
                    footer_bbox = (0, page.height * 0.9, page.width, page.height)
                    footer_text = page.within_bbox(footer_bbox).extract_text()
                    
                    if footer_text and len(footer_text.strip()) > 5:
                        record = create_text_record(
                            doc_id=self.doc_id,
                            company=self.company,
                            fiscal_year=self.fiscal_year,
                            source_path=str(self.pdf_path.resolve()),
                            page=page_num,
                            text=footer_text.strip(),
                            section=f"Page {page_num} - Footer",
                            block_type=BlockType.FOOTER,
                            method=ExtractionMethod.PDFPLUMBER_TEXT,
                            confidence=0.8
                        )
                        self.records.append(record)
                        
                except Exception as e:
                    logger.warning(f"Error extracting page metadata from page {page_num}: {e}")
    
    # Helper methods
    def _split_text_into_chunks(self, text: str, max_size: int = 2000) -> List[str]:
        """Split text into manageable chunks"""
        if len(text) <= max_size:
            return [text]
            
        # Split on double newlines (paragraph breaks) first
        paragraphs = text.split('\n\n')
        chunks = []
        current_chunk = ""
        
        for para in paragraphs:
            if len(current_chunk) + len(para) <= max_size:
                current_chunk += para + "\n\n"
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = para + "\n\n"
        
        if current_chunk:
            chunks.append(current_chunk.strip())
            
        return chunks
    
    def _classify_text_block(self, text: str) -> str:
        """Classify text block type based on content"""
        text_upper = text.upper()
        text_stripped = text.strip()
        
        # Check for headings (short, often uppercase, specific patterns)
        if len(text_stripped) < 100 and any(keyword in text_upper for keyword in 
                                          ['FORM', 'REPORT', 'TESLA', 'ITEM', 'PART']):
            return BlockType.HEADING
            
        # Check for financial data patterns
        if any(keyword in text_upper for keyword in 
               ['$', 'MILLION', 'BILLION', 'REVENUE', 'INCOME', 'CASH']):
            return BlockType.TEXT_BLOCK
            
        # Check for lists
        if re.search(r'^[\d\w]+\.\s', text_stripped) or '•' in text:
            return BlockType.LIST
            
        # Default to paragraph
        return BlockType.PARAGRAPH
    
    def _classify_positioned_text(self, text: str, bbox_info: dict) -> str:
        """Classify text based on content and position"""
        # Use font size and position to determine type
        font_size = bbox_info.get('size', 11)
        
        if font_size > 14:
            return BlockType.HEADING
        elif font_size > 12:
            return BlockType.SUBHEADING
        else:
            return self._classify_text_block(text)
    
    def _group_words_into_blocks(self, words: List[dict]) -> List[tuple]:
        """Group words into logical text blocks"""
        if not words:
            return []
            
        blocks = []
        current_text = []
        current_bbox = None
        
        for word in words:
            # Simple grouping by vertical position
            if not current_bbox:
                current_bbox = {
                    'x0': word['x0'], 'x1': word['x1'],
                    'top': word['top'], 'bottom': word['bottom']
                }
                current_text = [word['text']]
            elif abs(word['top'] - current_bbox['top']) < 5:  # Same line
                current_text.append(word['text'])
                current_bbox['x1'] = max(current_bbox['x1'], word['x1'])
            else:  # New line/block
                if current_text:
                    blocks.append((' '.join(current_text), current_bbox))
                current_bbox = {
                    'x0': word['x0'], 'x1': word['x1'],
                    'top': word['top'], 'bottom': word['bottom']
                }
                current_text = [word['text']]
        
        # Add final block
        if current_text:
            blocks.append((' '.join(current_text), current_bbox))
            
        return blocks
    
    def _parse_table_filename(self, csv_file: Path) -> Optional[dict]:
        """Parse table CSV filename to extract metadata"""
        try:
            filename_parts = csv_file.stem.split("_")
            if len(filename_parts) >= 4:
                if filename_parts[1] == "camelot" and len(filename_parts) >= 5:
                    method = "camelot_stream"
                    page_num = int(filename_parts[3][1:])
                    table_num = int(filename_parts[4][1:])
                else:
                    method = filename_parts[1]
                    page_num = int(filename_parts[2][1:])
                    table_num = int(filename_parts[3][1:])
                    
                return {
                    'page': page_num,
                    'table_id': table_num,
                    'method': method
                }
        except (ValueError, IndexError):
            pass
        return None
    
    def _format_table_text(self, table_rows: List[List[str]]) -> str:
        """Format table rows into readable text"""
        if not table_rows:
            return ""
            
        if len(table_rows) == 1:
            return f"Single row table: {' | '.join([str(cell).strip() for cell in table_rows[0] if str(cell).strip()])}"
            
        # Format with headers and data
        headers = table_rows[0]
        data_rows = table_rows[1:]
        
        text = f"Table Headers: {', '.join([str(h) for h in headers if str(h).strip()])}\n"
        
        for i, row in enumerate(data_rows[:10]):  # Limit to first 10 rows
            clean_row = [str(cell).strip() for cell in row if str(cell).strip()]
            if clean_row:
                text += f"Row {i+1}: {' | '.join(clean_row)}\n"
        
        if len(data_rows) > 10:
            text += f"... ({len(data_rows) - 10} more rows)\n"
            
        return text
    
    def _parse_docling_markdown(self, content: str) -> List[tuple]:
        """Parse Docling markdown into sections"""
        sections = []
        current_section = {"title": "", "content": ""}
        
        for line in content.split('\n'):
            if line.startswith('#'):
                if current_section["content"]:
                    sections.append((current_section["title"], current_section["content"]))
                current_section = {"title": line.strip('# '), "content": ""}
            else:
                current_section["content"] += line + "\n"
        
        if current_section["content"]:
            sections.append((current_section["title"], current_section["content"]))
            
        return sections
    
    def _format_docling_analysis(self, docling_data: dict) -> str:
        """Format Docling JSON analysis into readable text"""
        return f"""Docling AI Analysis Results:
- Tables detected: {len(docling_data.get('tables', []))}
- Document structure analyzed with advanced AI
- Main text content length: {len(str(docling_data.get('main_text', '')))} characters
- Processed with Docling's state-of-the-art PDF understanding"""

def extract_comprehensive_metadata(pdf_path: str, doc_id: str, company: str, 
                                 fiscal_year: str, output_dir: str) -> str:
    """
    Main function to extract comprehensive metadata using the new schema
    
    Args:
        pdf_path: Path to the PDF file
        doc_id: Document identifier 
        company: Company name
        fiscal_year: Fiscal year
        output_dir: Output directory path
        
    Returns:
        Path to the generated JSONL metadata file
    """
    output_path = Path(output_dir)
    
    # Initialize extractor
    extractor = ComprehensiveExtractor(pdf_path, doc_id, company, fiscal_year)
    
    # Extract all content
    records = extractor.extract_all_content(output_path)
    
    # Validate extraction completeness
    validator = MetadataValidator()
    record_dicts = [record.to_dict() for record in records]
    
    # Check for validation errors
    all_errors = []
    for i, record_dict in enumerate(record_dicts):
        errors = validator.validate_record(record_dict)
        if errors:
            all_errors.extend([f"Record {i}: {error}" for error in errors])
    
    if all_errors:
        logger.warning(f"Validation errors found: {len(all_errors)}")
        for error in all_errors[:5]:  # Show first 5 errors
            logger.warning(error)
    
    # Generate completeness report
    completeness_stats = validator.validate_completeness(record_dicts)
    logger.info(f"Extraction completeness: {json.dumps(completeness_stats, indent=2)}")
    
    # Write JSONL file
    metadata_dir = output_path / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    jsonl_file = metadata_dir / f"{doc_id}.jsonl"
    with open(jsonl_file, 'w', encoding='utf-8') as f:
        for record in records:
            f.write(record.to_jsonl() + '\n')
    
    logger.info(f"✅ Comprehensive extraction complete!")
    logger.info(f"📄 Total records: {len(records)}")
    logger.info(f"📄 Pages covered: {len(completeness_stats['pages_covered'])}")
    logger.info(f"📄 Block types: {list(completeness_stats['block_types'].keys())}")
    logger.info(f"📁 Output file: {jsonl_file}")
    
    return str(jsonl_file)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Document Extraction")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--doc-id", required=True, help="Document ID")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--fiscal-year", required=True, help="Fiscal year")
    parser.add_argument("--output", required=True, help="Output directory")
    
    args = parser.parse_args()
    
    result = extract_comprehensive_metadata(
        args.pdf, args.doc_id, args.company, args.fiscal_year, args.output
    )
    
    print(f"Comprehensive metadata extraction complete: {result}")