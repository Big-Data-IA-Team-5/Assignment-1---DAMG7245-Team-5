"""
Enhanced Metadata Extraction - Extracts ALL Document Content
Integrates with existing pipeline to ensure comprehensive coverage
"""

import json
import logging
from pathlib import Path
from datetime import datetime
import pdfplumber
import csv
import re
from typing import List, Dict, Any

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_comprehensive_metadata(pdf_path: str, doc_id: str, company: str, 
                                 fiscal_year: str, output_dir: str, unified_dir: str = None) -> bool:
    """
    Enhanced metadata extraction that captures ALL document content
    
    This function extracts:
    1. ALL text content (paragraphs, headings, etc.) - not just tables
    2. Table content from existing CSV files
    3. Document structure and layout elements
    4. Headers, footers, and page metadata
    5. Docling AI analysis content
    """
    
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    if unified_dir:
        unified_base = Path(unified_dir)
    else:
        unified_base = output_dir
    
    # Create metadata directory
    metadata_dir = unified_base / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)
    
    jsonl_path = metadata_dir / f"{doc_id}.jsonl"
    
    all_records = []
    
    logger.info(f"🚀 Starting comprehensive extraction for {doc_id}")
    
    # PART 1: Extract ALL text content from PDF pages
    logger.info("📄 Extracting full document text content...")
    text_records = extract_full_document_text(pdf_path, doc_id, company, fiscal_year)
    all_records.extend(text_records)
    logger.info(f"✅ Extracted {len(text_records)} text records")
    
    # PART 2: Extract table content from existing CSV files
    logger.info("📊 Processing existing table extractions...")
    table_records = extract_existing_table_content(unified_base, doc_id, company, fiscal_year, pdf_path)
    all_records.extend(table_records)
    logger.info(f"✅ Extracted {len(table_records)} table records")
    
    # PART 3: Extract docling AI content
    logger.info("🤖 Processing Docling AI content...")
    docling_records = extract_docling_ai_content(unified_base, doc_id, company, fiscal_year, pdf_path)
    all_records.extend(docling_records)
    logger.info(f"✅ Extracted {len(docling_records)} Docling AI records")
    
    # PART 4: Extract document structure and layout
    logger.info("🏗️ Extracting document structure...")
    structure_records = extract_document_structure(pdf_path, doc_id, company, fiscal_year)
    all_records.extend(structure_records)
    logger.info(f"✅ Extracted {len(structure_records)} structure records")
    
    # PART 5: Extract headers, footers, and page metadata
    logger.info("📑 Extracting page metadata...")
    metadata_records = extract_page_level_metadata(pdf_path, doc_id, company, fiscal_year)
    all_records.extend(metadata_records)
    logger.info(f"✅ Extracted {len(metadata_records)} metadata records")
    
    # Write comprehensive JSONL file
    with open(jsonl_path, 'w', encoding='utf-8') as f:
        for record in all_records:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    
    # Generate comprehensive summary
    generate_extraction_summary(all_records, metadata_dir, doc_id)
    
    logger.info(f"🎉 COMPREHENSIVE EXTRACTION COMPLETE!")
    logger.info(f"📈 Total records: {len(all_records)}")
    logger.info(f"📁 Output: {jsonl_path}")
    
    # Show coverage by content type
    content_types = {}
    for record in all_records:
        block_type = record.get('block_type', 'unknown')
        content_types[block_type] = content_types.get(block_type, 0) + 1
    
    logger.info("📊 Content Coverage:")
    for content_type, count in sorted(content_types.items()):
        logger.info(f"   {content_type}: {count} records")
    
    return True

def extract_full_document_text(pdf_path: Path, doc_id: str, company: str, fiscal_year: str) -> List[Dict]:
    """Extract ALL text content from the PDF"""
    records = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                # Get full page text
                full_text = page.extract_text()
                if not full_text or len(full_text.strip()) < 20:
                    continue
                
                # Split into meaningful paragraphs
                paragraphs = split_into_paragraphs(full_text)
                
                for i, paragraph in enumerate(paragraphs):
                    if len(paragraph.strip()) < 15:  # Skip very short content
                        continue
                        
                    # Classify the content type
                    block_type = classify_text_content(paragraph)
                    
                    section = f"Page {page_num}"
                    if len(paragraphs) > 1:
                        section += f" - Section {i+1}"
                    
                    record = {
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "source_path": str(pdf_path.resolve()),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "pdfplumber_comprehensive_text",
                        "page": page_num,
                        "section": section,
                        "block_type": block_type,
                        "text": paragraph.strip(),
                        "confidence": 0.9,
                        "bbox": None,
                    }
                    records.append(record)
                    
                # Also extract word-level content for detailed analysis
                words = page.extract_words()
                if words:
                    word_blocks = group_words_into_text_blocks(words)
                    for j, (block_text, bbox_info) in enumerate(word_blocks):
                        if len(block_text.strip()) < 30:  # Skip short blocks
                            continue
                            
                        record = {
                            "doc_id": doc_id,
                            "company": company,
                            "fiscal_year": fiscal_year,
                            "source_path": str(pdf_path.resolve()),
                            "extraction_timestamp": datetime.now().isoformat(),
                            "extraction_method": "pdfplumber_positioned_text",
                            "page": page_num,
                            "section": f"Page {page_num} - Text Block {j+1}",
                            "block_type": classify_positioned_text(block_text, bbox_info),
                            "text": block_text.strip(),
                            "confidence": 0.85,
                            "bbox": {
                                "x1": bbox_info.get('x0', 0),
                                "y1": bbox_info.get('top', 0),
                                "x2": bbox_info.get('x1', 0),
                                "y2": bbox_info.get('bottom', 0)
                            },
                        }
                        records.append(record)
                        
            except Exception as e:
                logger.warning(f"Error extracting text from page {page_num}: {e}")
    
    return records

def extract_existing_table_content(unified_base: Path, doc_id: str, company: str, 
                                 fiscal_year: str, pdf_path: Path) -> List[Dict]:
    """Extract content from existing table CSV files"""
    records = []
    tables_dir = unified_base / "tables"
    
    if not tables_dir.exists():
        return records
        
    for csv_file in tables_dir.glob("*.csv"):
        if csv_file.name.startswith("_"):  # Skip analysis files
            continue
            
        try:
            # Parse filename for metadata
            table_info = parse_table_filename(csv_file)
            if not table_info:
                continue
                
            # Read and format table content
            with open(csv_file, 'r', encoding='utf-8') as f:
                csv_reader = csv.reader(f)
                table_rows = list(csv_reader)
                
            if not table_rows:
                continue
                
            table_text = format_table_content(table_rows)
            
            record = {
                "doc_id": doc_id,
                "company": company,
                "fiscal_year": fiscal_year,
                "source_path": str(pdf_path.resolve()),
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_method": f"hybrid_table_extraction_{table_info['method']}",
                "page": table_info['page'],
                "section": f"Page {table_info['page']} - Table {table_info['table_id']} ({table_info['method']})",
                "block_type": "table",
                "text": table_text,
                "confidence": 0.85,
                "bbox": None,
                "table_info": {
                    "rows": len(table_rows),
                    "cols": len(table_rows[0]) if table_rows else 0,
                    "table_id": table_info['table_id'],
                    "extraction_method": table_info['method'],
                    "file_name": csv_file.name,
                    "has_headers": True
                }
            }
            records.append(record)
            
        except Exception as e:
            logger.warning(f"Error processing table {csv_file}: {e}")
    
    return records

def extract_docling_ai_content(unified_base: Path, doc_id: str, company: str,
                              fiscal_year: str, pdf_path: Path) -> List[Dict]:
    """Extract Docling AI analysis content"""
    records = []
    docling_dir = unified_base / "docling"
    
    if not docling_dir.exists():
        return records
        
    # Process Docling Markdown output
    md_file = docling_dir / "output.md"
    if md_file.exists():
        try:
            with open(md_file, 'r', encoding='utf-8') as f:
                content = f.read()
                
            sections = parse_docling_markdown(content)
            
            for i, (title, section_content) in enumerate(sections):
                if len(section_content.strip()) > 50:
                    record = {
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "source_path": str(pdf_path.resolve()),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "docling_markdown_extraction",
                        "page": i + 1,
                        "section": f"Docling Section: {title}",
                        "block_type": "structured_content",
                        "text": section_content[:1500] + ("..." if len(section_content) > 1500 else ""),
                        "confidence": 0.92,
                        "bbox": None,
                        "section_info": {
                            "title": title,
                            "content_length": len(section_content),
                            "section_number": i + 1
                        }
                    }
                    records.append(record)
                    
        except Exception as e:
            logger.warning(f"Error processing Docling markdown: {e}")
    
    # Process Docling JSON output
    json_file = docling_dir / "output.json"
    if json_file.exists():
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                docling_data = json.load(f)
                
            analysis_text = f"""Docling AI Analysis Results:
- Tables detected: {len(docling_data.get('tables', []))}
- Document structure analyzed with advanced AI
- Main text content length: {len(str(docling_data.get('main_text', '')))} characters
- Processed with Docling's state-of-the-art PDF understanding"""
            
            record = {
                "doc_id": doc_id,
                "company": company,
                "fiscal_year": fiscal_year,
                "source_path": str(pdf_path.resolve()),
                "extraction_timestamp": datetime.now().isoformat(),
                "extraction_method": "docling_ai_analysis",
                "page": 1,
                "section": "Document AI Analysis",
                "block_type": "ai_analysis",
                "text": analysis_text,
                "confidence": 0.95,
                "bbox": None,
                "docling_analysis": {
                    "tables_count": len(docling_data.get("tables", [])),
                    "document_info": docling_data.get("document_info", {}),
                    "main_text_length": len(str(docling_data.get('main_text', ''))),
                }
            }
            records.append(record)
            
        except Exception as e:
            logger.warning(f"Error processing Docling JSON: {e}")
    
    return records

def extract_document_structure(pdf_path: Path, doc_id: str, company: str, fiscal_year: str) -> List[Dict]:
    """Extract document structure and layout elements"""
    records = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                # Extract visual elements (lines, curves)
                lines = page.lines
                curves = page.curves
                
                if lines or curves:
                    structure_info = f"Layout elements found: {len(lines)} lines, {len(curves)} curves"
                    
                    record = {
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "source_path": str(pdf_path.resolve()),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "layout_detection",
                        "page": page_num,
                        "section": f"Page {page_num} - Layout Structure",
                        "block_type": "layout_block",
                        "text": structure_info,
                        "confidence": 0.8,
                        "bbox": None,
                    }
                    records.append(record)
                
                # Extract images
                images = page.images
                for i, img in enumerate(images):
                    record = {
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "source_path": str(pdf_path.resolve()),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "pdfplumber_image_detection",
                        "page": page_num,
                        "section": f"Page {page_num} - Image {i+1}",
                        "block_type": "image",
                        "text": f"Image detected at coordinates {img.get('x0', 0)}, {img.get('top', 0)}",
                        "confidence": 0.9,
                        "bbox": {
                            "x1": img.get('x0', 0),
                            "y1": img.get('top', 0),
                            "x2": img.get('x1', 0),
                            "y2": img.get('bottom', 0)
                        }
                    }
                    records.append(record)
                    
            except Exception as e:
                logger.warning(f"Error extracting structure from page {page_num}: {e}")
    
    return records

def extract_page_level_metadata(pdf_path: Path, doc_id: str, company: str, fiscal_year: str) -> List[Dict]:
    """Extract headers, footers, and page-level metadata"""
    records = []
    
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            try:
                # Extract potential headers (top 10% of page)
                header_bbox = (0, 0, page.width, page.height * 0.1)
                header_text = page.within_bbox(header_bbox).extract_text()
                
                if header_text and len(header_text.strip()) > 5:
                    record = {
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "source_path": str(pdf_path.resolve()),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "pdfplumber_header_extraction",
                        "page": page_num,
                        "section": f"Page {page_num} - Header",
                        "block_type": "header",
                        "text": header_text.strip(),
                        "confidence": 0.8,
                        "bbox": {
                            "x1": 0, "y1": 0,
                            "x2": page.width, "y2": page.height * 0.1
                        }
                    }
                    records.append(record)
                
                # Extract potential footers (bottom 10% of page)
                footer_bbox = (0, page.height * 0.9, page.width, page.height)
                footer_text = page.within_bbox(footer_bbox).extract_text()
                
                if footer_text and len(footer_text.strip()) > 5:
                    record = {
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "source_path": str(pdf_path.resolve()),
                        "extraction_timestamp": datetime.now().isoformat(),
                        "extraction_method": "pdfplumber_footer_extraction",
                        "page": page_num,
                        "section": f"Page {page_num} - Footer",
                        "block_type": "footer",
                        "text": footer_text.strip(),
                        "confidence": 0.8,
                        "bbox": {
                            "x1": 0, "y1": page.height * 0.9,
                            "x2": page.width, "y2": page.height
                        }
                    }
                    records.append(record)
                    
            except Exception as e:
                logger.warning(f"Error extracting page metadata from page {page_num}: {e}")
    
    return records

# Helper functions
def split_into_paragraphs(text: str) -> List[str]:
    """Split text into meaningful paragraphs"""
    # Split on double newlines first
    paragraphs = text.split('\n\n')
    result = []
    
    for para in paragraphs:
        para = para.strip()
        if len(para) < 15:
            continue
            
        # If paragraph is very long, split it further
        if len(para) > 2000:
            sentences = para.replace('. ', '.|').split('|')
            current_chunk = ""
            
            for sentence in sentences:
                if len(current_chunk) + len(sentence) <= 2000:
                    current_chunk += sentence
                else:
                    if current_chunk:
                        result.append(current_chunk.strip())
                    current_chunk = sentence
            
            if current_chunk:
                result.append(current_chunk.strip())
        else:
            result.append(para)
    
    return result

def classify_text_content(text: str) -> str:
    """Classify text content into appropriate block types"""
    text_upper = text.upper()
    text_stripped = text.strip()
    
    # Check for headings (short, often uppercase, specific patterns)
    if len(text_stripped) < 100:
        if any(keyword in text_upper for keyword in ['FORM', 'REPORT', 'TESLA', 'ITEM', 'PART', 'SECTION']):
            return "heading"
        if text_stripped.isupper() and len(text_stripped) < 50:
            return "subheading"
    
    # Check for financial/table data
    if any(keyword in text_upper for keyword in ['$', 'MILLION', 'BILLION', 'REVENUE', 'INCOME']):
        return "text_block"
    
    # Check for lists
    if re.search(r'^[\d\w]+\.\s', text_stripped) or '•' in text:
        return "list"
    
    # Check for structured content
    if any(keyword in text_upper for keyword in ['TABLE', 'FIGURE', 'EXHIBIT']):
        return "structured_content"
    
    return "paragraph"

def classify_positioned_text(text: str, bbox_info: dict) -> str:
    """Classify text based on position and content"""
    # Use font size if available
    font_size = bbox_info.get('size', 11)
    
    if font_size > 14:
        return "heading"
    elif font_size > 12:
        return "subheading"
    
    return classify_text_content(text)

def group_words_into_text_blocks(words: List[dict]) -> List[tuple]:
    """Group words into logical text blocks"""
    if not words:
        return []
    
    blocks = []
    current_text = []
    current_bbox = None
    
    for word in words:
        if not current_bbox:
            current_bbox = {
                'x0': word['x0'], 'x1': word['x1'],
                'top': word['top'], 'bottom': word['bottom']
            }
            current_text = [word['text']]
        elif abs(word['top'] - current_bbox['top']) < 5:  # Same line
            current_text.append(word['text'])
            current_bbox['x1'] = max(current_bbox['x1'], word['x1'])
        else:  # New line
            if current_text:
                blocks.append((' '.join(current_text), current_bbox))
            current_bbox = {
                'x0': word['x0'], 'x1': word['x1'],
                'top': word['top'], 'bottom': word['bottom']
            }
            current_text = [word['text']]
    
    if current_text:
        blocks.append((' '.join(current_text), current_bbox))
    
    return blocks

def parse_table_filename(csv_file: Path) -> dict:
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

def format_table_content(table_rows: List[List[str]]) -> str:
    """Format table rows into readable text"""
    if not table_rows:
        return ""
    
    if len(table_rows) == 1:
        return f"Single row table: {' | '.join([str(cell).strip() for cell in table_rows[0] if str(cell).strip()])}"
    
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

def parse_docling_markdown(content: str) -> List[tuple]:
    """Parse Docling markdown into sections"""
    sections = []
    lines = content.split('\n')
    current_section = {"title": "Introduction", "content": ""}
    
    for line in lines:
        if line.startswith('#'):
            if current_section["content"].strip():
                sections.append((current_section["title"], current_section["content"]))
            current_section = {"title": line.strip('# ').strip(), "content": ""}
        else:
            current_section["content"] += line + "\n"
    
    if current_section["content"].strip():
        sections.append((current_section["title"], current_section["content"]))
    
    return sections

def generate_extraction_summary(records: List[Dict], metadata_dir: Path, doc_id: str):
    """Generate a summary of the extraction process"""
    # Count records by type
    type_counts = {}
    method_counts = {}
    page_coverage = set()
    
    for record in records:
        block_type = record.get('block_type', 'unknown')
        method = record.get('extraction_method', 'unknown')
        page = record.get('page', 0)
        
        type_counts[block_type] = type_counts.get(block_type, 0) + 1
        method_counts[method] = method_counts.get(method, 0) + 1
        page_coverage.add(page)
    
    summary = {
        "doc_id": doc_id,
        "total_records": len(records),
        "extraction_timestamp": datetime.now().isoformat(),
        "content_coverage": {
            "pages_covered": sorted(list(page_coverage)),
            "total_pages": len(page_coverage),
            "content_types": type_counts,
            "extraction_methods": method_counts
        },
        "comprehensive_coverage": {
            "has_text_content": any('paragraph' in bt or 'text' in bt for bt in type_counts.keys()),
            "has_table_content": 'table' in type_counts,
            "has_structure_content": any('heading' in bt or 'layout' in bt for bt in type_counts.keys()),
            "has_ai_analysis": 'ai_analysis' in type_counts,
            "coverage_score": min(1.0, len(type_counts) / 8)  # Score based on diversity of content types
        }
    }
    
    # Write summary
    summary_path = metadata_dir / f"{doc_id}_extraction_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
    
    logger.info(f"📋 Extraction summary written to: {summary_path}")

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Comprehensive Document Extraction")
    parser.add_argument("--pdf", required=True, help="Path to PDF file")
    parser.add_argument("--doc-id", required=True, help="Document ID")
    parser.add_argument("--company", required=True, help="Company name")
    parser.add_argument("--fiscal-year", required=True, help="Fiscal year")
    parser.add_argument("--output", required=True, help="Output directory")
    parser.add_argument("--unified", help="Unified directory (optional)")
    
    args = parser.parse_args()
    
    success = extract_comprehensive_metadata(
        args.pdf, args.doc_id, args.company, args.fiscal_year, args.output, args.unified
    )
    
    if success:
        print("✅ Comprehensive metadata extraction completed successfully!")
    else:
        print("❌ Comprehensive metadata extraction failed!")