"""
Lab 6: Storage Formats - Markdown vs JSON vs TXT

Converts JSONL metadata to three different storage formats and analyzes trade-offs.
Demonstrates format selection for different use cases, especially RAG pipelines.
"""

import argparse
import json
from pathlib import Path
import logging
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def convert_metadata_to_formats(jsonl_path, output_dir):
    """
    Convert JSONL metadata to three different storage formats:
    - Markdown: Human-readable with structure preservation (best for RAG)
    - JSON: Machine-readable structured data (best for programmatic access)
    - TXT: Plain text baseline (structure lost, universal compatibility)
    """
    jsonl_path = Path(jsonl_path)
    output_dir = Path(output_dir)
    
    if not jsonl_path.exists():
        logger.error(f"JSONL file not found: {jsonl_path}")
        return None
    
    # Extract doc_id from path or filename
    doc_id = jsonl_path.stem
    if jsonl_path.parent.name == "metadata":
        # Extract doc_id from the JSONL filename
        doc_id = jsonl_path.stem  # e.g., "goog_2024" from "goog_2024.jsonl"
    
    # Create output directory structure: <unified_output_dir>/formats/
    formats_dir = output_dir / "formats"
    formats_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting metadata to multiple formats for document: {doc_id}")

    # Load and parse JSONL data
    records = []
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON on line {line_num}: {e}")
                        continue
    except Exception as e:
        logger.error(f"Error reading JSONL file: {e}")
        return None

    if not records:
        logger.warning("No valid records found in JSONL file")
        return None

    logger.info(f"Loaded {len(records)} metadata records")

    # Extract document metadata from first record
    doc_metadata = extract_document_metadata(records)

    # Group records by page for structured processing
    grouped_by_page = group_records_by_page(records)

    # Generate all three formats
    results = {}
    
    # 1. Generate Markdown format (optimized for RAG)
    results['markdown'] = generate_markdown_format(
        doc_id, doc_metadata, grouped_by_page, formats_dir
    )
    
    # 2. Generate JSON format (optimized for programmatic access)
    results['json'] = generate_json_format(
        doc_id, doc_metadata, records, grouped_by_page, formats_dir
    )
    
    # 3. Generate TXT format (baseline, structure lost)
    results['txt'] = generate_txt_format(
        doc_id, doc_metadata, grouped_by_page, formats_dir
    )
    
    # 4. Generate comprehensive format analysis
    results['analysis'] = generate_format_analysis(
        doc_id, results, formats_dir
    )

    # Create conversion summary
    summary = create_conversion_summary(doc_id, records, results)
    summary_path = formats_dir / "_conversion_summary.json"
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Format conversion completed for {doc_id}")
    print(f"Total records processed: {len(records)}")
    print(f"Formats created:")
    for format_name, file_path in results.items():
        if file_path and file_path.exists():
            size_kb = file_path.stat().st_size / 1024
            print(f"  📄 {format_name.upper()}: {file_path.name} ({size_kb:.1f} KB)")

    return results

def extract_document_metadata(records):
    """Extract document-level metadata from records."""
    if not records:
        return {}
    
    first_record = records[0]
    return {
        'company': first_record.get('company', 'Unknown Company'),
        'fiscal_year': first_record.get('fiscal_year', 'Unknown Year'),
        'doc_id': first_record.get('doc_id', 'unknown'),
        'source_path': first_record.get('source_path', 'Unknown Source'),
        'total_pages': len(set(r.get('page', 1) for r in records)),
        'extraction_date': first_record.get('extraction_timestamp', 'Unknown Date')
    }

def group_records_by_page(records):
    """Group records by page and section for structured processing."""
    grouped = {}
    
    for record in records:
        page = record.get('page', 1)
        section = record.get('section', 'Unknown Section')
        
        if page not in grouped:
            grouped[page] = {'sections': {}, 'page_metadata': {}}
        
        if section not in grouped[page]['sections']:
            grouped[page]['sections'][section] = []
        
        grouped[page]['sections'][section].append(record)
        
        # Store page-level metadata
        if not grouped[page]['page_metadata']:
            grouped[page]['page_metadata'] = {
                'page': page,
                'section': section
            }
    
    return grouped

def generate_markdown_format(doc_id, doc_metadata, grouped_by_page, output_dir):
    """
    Generate Markdown format optimized for RAG (Retrieval-Augmented Generation).
    Preserves semantic structure, headings, and context.
    """
    md_file = output_dir / f"{doc_id}.md"
    
    try:
        with open(md_file, 'w', encoding='utf-8') as f:
            # Document header with metadata
            f.write(f"# {doc_metadata['company']} - {doc_metadata['fiscal_year']}\n\n")
            f.write(f"**Document ID:** {doc_id}\n")
            f.write(f"**Source:** {doc_metadata.get('source_path', 'N/A')}\n")
            f.write(f"**Pages:** {doc_metadata.get('total_pages', 'N/A')}\n")
            f.write(f"**Extraction Date:** {doc_metadata.get('extraction_date', 'N/A')}\n\n")
            f.write("---\n\n")
            
            # Process each page with proper structure
            for page_num in sorted(grouped_by_page.keys()):
                page_data = grouped_by_page[page_num]
                
                f.write(f"## Page {page_num}\n\n")
                
                # Process each section on the page
                for section_name, section_records in page_data['sections'].items():
                    if section_name != f"Page {page_num}":
                        f.write(f"### {section_name}\n\n")
                    
                    # Group by block type for better structure
                    block_groups = group_records_by_block_type(section_records)
                    
                    # Process different block types with appropriate formatting in logical order
                    block_order = [
                        'financial_statement_title', 'section_header', 'table_header', 
                        'executive_summary', 'management_discussion', 'table', 
                        'financial_data', 'paragraph', 'footnote', 'text_fragment'
                    ]
                    
                    for block_type in block_order:
                        if block_type in block_groups:
                            format_blocks_for_markdown(f, block_type, block_groups[block_type])
                
                f.write("\n---\n\n")
        
        logger.info(f"Generated Markdown format: {md_file}")
        return md_file
        
    except Exception as e:
        logger.error(f"Error generating Markdown format: {e}")
        return None

def generate_json_format(doc_id, doc_metadata, records, grouped_by_page, output_dir):
    """
    Generate JSON format optimized for programmatic access.
    Maintains all metadata and structure for querying and analysis.
    """
    json_file = output_dir / f"{doc_id}.json"
    
    try:
        # Create comprehensive JSON structure
        json_data = {
            'document_metadata': doc_metadata,
            'conversion_info': {
                'format': 'JSON',
                'purpose': 'Programmatic access and data analysis',
                'created_at': datetime.now().isoformat(),
                'total_records': len(records)
            },
            'structure': {
                'pages': {},
                'block_types': get_block_type_summary(records),
                'sections': list(set(r.get('section', 'Unknown') for r in records))
            },
            'records': records,
            'page_structure': {str(k): v for k, v in grouped_by_page.items()}
        }
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(json_data, f, indent=2, ensure_ascii=False)
        
        logger.info(f"Generated JSON format: {json_file}")
        return json_file
        
    except Exception as e:
        logger.error(f"Error generating JSON format: {e}")
        return None

def generate_txt_format(doc_id, doc_metadata, grouped_by_page, output_dir):
    """
    Generate plain text format (baseline).
    Structure is lost but provides universal compatibility.
    """
    txt_file = output_dir / f"{doc_id}.txt"
    
    try:
        with open(txt_file, 'w', encoding='utf-8') as f:
            # Simple header
            f.write(f"{doc_metadata['company']} - {doc_metadata['fiscal_year']}\n")
            f.write("=" * 50 + "\n\n")
            
            # Process pages sequentially, concatenating all text
            for page_num in sorted(grouped_by_page.keys()):
                page_data = grouped_by_page[page_num]
                
                f.write(f"Page {page_num}:\n")
                
                # Concatenate all text from the page
                page_text_parts = []
                for section_name, section_records in page_data['sections'].items():
                    for record in section_records:
                        text = record.get('text', '').strip()
                        if text:
                            page_text_parts.append(text)
                
                page_text = ' '.join(page_text_parts)
                f.write(page_text)
                f.write("\n\n")
        
        logger.info(f"Generated TXT format: {txt_file}")
        return txt_file
        
    except Exception as e:
        logger.error(f"Error generating TXT format: {e}")
        return None

def generate_format_analysis(doc_id, results, output_dir):
    """Generate comprehensive analysis comparing all three formats."""
    analysis_file = output_dir / "_format_analysis.md"
    
    # Calculate file sizes
    file_sizes = {}
    for format_name, file_path in results.items():
        if file_path and file_path.exists():
            file_sizes[format_name] = file_path.stat().st_size / 1024  # KB

    analysis_content = f"""# Storage Format Analysis for {doc_id}

## Executive Summary

This analysis compares three storage formats for the extracted document content:
- **Markdown (.md)**: Optimized for human reading and RAG pipelines
- **JSON (.json)**: Optimized for programmatic access and analysis
- **Plain Text (.txt)**: Baseline format with universal compatibility

## Format Comparison

### 📄 Markdown Format
- **File Size**: {file_sizes.get('markdown', 0):.1f} KB
- **Structure Preservation**: ✅ Excellent
- **Human Readability**: ✅ Excellent  
- **LLM Compatibility**: ✅ Excellent for RAG
- **Use Case**: **RECOMMENDED** for retrieval-augmented generation (RAG) pipelines
- **Pros**: 
  - Preserves semantic structure (headings, sections, tables)
  - Natural language context maintained
  - LLMs understand semantic markup intuitively
  - Good balance of human and machine readability
- **Cons**: 
  - Requires parsing for programmatic access
  - Some metadata lost in favor of readability

### 🔧 JSON Format
- **File Size**: {file_sizes.get('json', 0):.1f} KB
- **Structure Preservation**: ✅ Perfect (all metadata preserved)
- **Human Readability**: ⚠️ Moderate (requires tools)
- **LLM Compatibility**: ✅ Good with proper parsing
- **Use Case**: **RECOMMENDED** for data analysis and programmatic access
- **Pros**: 
  - Complete metadata and provenance preservation
  - Queryable structure for complex analysis
  - Perfect for API integrations
  - Maintains all extraction confidence scores
- **Cons**: 
  - Verbose and harder to read directly
  - Requires JSON parsing libraries
  - Not ideal for direct LLM consumption

### 📝 Plain Text Format
- **File Size**: {file_sizes.get('txt', 0):.1f} KB
- **Structure Preservation**: ❌ Structure lost
- **Human Readability**: ✅ Good (simple)
- **LLM Compatibility**: ⚠️ Limited (no structure context)
- **Use Case**: Simple text analysis, baseline comparison
- **Pros**: 
  - Universal compatibility across all systems
  - Smallest file size
  - No parsing requirements
  - Direct text search capability
- **Cons**: 
  - Complete loss of document structure
  - No metadata or provenance information
  - Context relationships lost
  - Poor for complex document understanding

## Use Case Recommendations

### For RAG (Retrieval-Augmented Generation) Systems
**🎯 Use Markdown Format**
- Preserves semantic structure that LLMs understand
- Maintains section context and hierarchical information
- Optimal balance for both retrieval and generation phases
- Headers and formatting provide natural chunk boundaries

### For Data Analysis and Processing
**🎯 Use JSON Format**
- Complete access to all extracted metadata
- Enables complex queries and filtering
- Preserves confidence scores for quality assessment
- Structured data for statistical analysis

### For Simple Text Operations
**🎯 Use Plain Text Format**
- Quick text search and basic analysis
- Integration with simple text processing tools
- Baseline for comparison with other methods
- Universal compatibility across platforms

## Technical Considerations

### File Size Efficiency
1. **Plain Text**: Smallest (baseline)
2. **Markdown**: ~{(file_sizes.get('markdown', 0) / file_sizes.get('txt', 1)):.1f}x larger than TXT
3. **JSON**: ~{(file_sizes.get('json', 0) / file_sizes.get('txt', 1)):.1f}x larger than TXT

### Processing Speed
- **TXT**: Fastest to read and process
- **Markdown**: Fast, with minor parsing overhead
- **JSON**: Slower, requires deserialization

### Maintenance and Updates
- **JSON**: Easiest to update programmatically
- **Markdown**: Moderate complexity for updates
- **TXT**: Simple but structure changes require full regeneration

## Final Recommendation

**For this project's RAG pipeline: Use Markdown format as primary, with JSON as secondary**

**Rationale:**
1. Markdown provides optimal structure preservation for document understanding
2. LLMs can leverage semantic markup for better context comprehension
3. Section headers and formatting aid in retrieval accuracy
4. Human readability enables easy validation and debugging
5. JSON backup ensures all metadata is preserved for analysis

The combination approach leverages the strengths of both formats while mitigating their individual weaknesses.
"""

    try:
        with open(analysis_file, 'w', encoding='utf-8') as f:
            f.write(analysis_content)
        logger.info(f"Generated format analysis: {analysis_file}")
        return analysis_file
    except Exception as e:
        logger.error(f"Error generating format analysis: {e}")
        return None

def group_records_by_block_type(records):
    """Group records by block type for structured formatting. Handles both old content_type and new block_type fields."""
    groups = {}
    for record in records:
        # Support both new block_type and legacy content_type fields
        block_type = record.get('block_type') or record.get('content_type', 'text_fragment')
        
        # Map legacy content_type values to new block_type values
        legacy_mapping = {
            'page_content': 'paragraph',
            'table': 'table'
        }
        
        if block_type in legacy_mapping:
            block_type = legacy_mapping[block_type]
        
        if block_type not in groups:
            groups[block_type] = []
        groups[block_type].append(record)
    return groups

def format_blocks_for_markdown(file_handle, block_type, blocks):
    """Format blocks appropriately for Markdown based on their type."""
    if not blocks:
        return
    
    if block_type == 'financial_statement_title':
        for block in blocks:
            file_handle.write(f"#### {block.get('text', '')}\n\n")
    
    elif block_type == 'section_header':
        for block in blocks:
            file_handle.write(f"##### {block.get('text', '')}\n\n")
    
    elif block_type == 'table_header':
        for block in blocks:
            file_handle.write(f"**{block.get('text', '')}**\n\n")
    
    elif block_type == 'table':
        file_handle.write("**Table Data:**\n\n")
        for block in blocks:
            text = block.get('text', '')
            if '|' in text:  # Already formatted as table
                file_handle.write(text + "\n\n")
            else:
                file_handle.write("```\n")
                file_handle.write(text)
                file_handle.write("\n```\n\n")
    
    elif block_type == 'financial_data':
        file_handle.write("**Financial Data:**\n\n")
        for block in blocks:
            file_handle.write(f"- {block.get('text', '')}\n")
        file_handle.write("\n")
    
    elif block_type == 'footnote':
        file_handle.write("**Notes:**\n\n")
        for block in blocks:
            file_handle.write(f"> {block.get('text', '')}\n\n")
    
    else:  # paragraph, text_fragment
        for block in blocks:
            text = block.get('text', '').strip()
            if text:
                file_handle.write(f"{text}\n\n")

def get_block_type_summary(records):
    """Get summary of block types in the records."""
    block_types = {}
    for record in records:
        block_type = record.get('block_type', 'unknown')
        block_types[block_type] = block_types.get(block_type, 0) + 1
    return block_types

def create_conversion_summary(doc_id, records, results):
    """Create a summary of the conversion process."""
    return {
        'document_id': doc_id,
        'conversion_timestamp': datetime.now().isoformat(),
        'input_records': len(records),
        'formats_generated': {
            format_name: str(file_path) if file_path else None 
            for format_name, file_path in results.items()
        },
        'block_type_distribution': get_block_type_summary(records),
        'quality_metrics': {
            'total_characters': sum(len(r.get('text', '')) for r in records),
            'total_words': sum(len(r.get('text', '').split()) for r in records),
            'pages_covered': len(set(r.get('page', 1) for r in records)),
            'sections_identified': len(set(r.get('section', 'Unknown') for r in records))
        }
    }

def main():
    parser = argparse.ArgumentParser(description="Lab 6: Storage Formats - Markdown vs JSON vs TXT")
    parser.add_argument('--in', dest='input_jsonl', required=True, help='Input JSONL metadata file')
    parser.add_argument('--out', dest='output_dir', required=True, help='Output directory for format conversions')
    
    args = parser.parse_args()
    
    result = convert_metadata_to_formats(args.input_jsonl, args.output_dir)
    
    if result and any(result.values()):
        logger.info("✅ Lab 6 completed successfully")
        return 0
    else:
        logger.error("❌ Lab 6 failed")
        return 1

if __name__ == "__main__":
    exit(main())