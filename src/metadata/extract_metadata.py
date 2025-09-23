import pdfplumber
import json
import pandas as pd
import argparse
from pathlib import Path

def extract_metadata(pdf_path, doc_id, company, fiscal_year, output_dir, unified_dir=None):
    pdf_path = Path(pdf_path)
    output_dir = Path(output_dir)
    
    # If unified_dir is provided, use it as the base for finding lab outputs
    if unified_dir:
        unified_base = Path(unified_dir)
    else:
        unified_base = output_dir
    
    # Create metadata output directory
    metadata_dir = unified_base / "metadata"
    metadata_dir.mkdir(parents=True, exist_ok=True)

    jsonl_path = metadata_dir / f"{doc_id}.jsonl"
    md_path = metadata_dir / f"{doc_id}.md"

    records = []
    markdown_lines = [f"# Document: {company} ({fiscal_year})\n"]

    # PART 1: Process word-level extraction (your original approach)
    print("Processing word-level extraction...")
    with pdfplumber.open(pdf_path) as pdf:
        for page_num, page in enumerate(pdf.pages, start=1):
            words = page.extract_words()
            section = f"Page {page_num}"

            # Markdown heading for section
            markdown_lines.append(f"\n## {section}\n")

            # Sort words top-down, left-right
            words_sorted = sorted(words, key=lambda w: (w["top"], w["x0"]))
            line_text = " ".join(word["text"] for word in words_sorted)
            markdown_lines.append(line_text)

            for word in words_sorted:
                record = {
                    "doc_id": doc_id,
                    "company": company,
                    "fiscal_year": fiscal_year,
                    "page": page_num,
                    "section": section,
                    "block_type": "text",
                    "extraction_method": "pdfplumber_word_level",
                    "bbox": [word["x0"], word["top"], word["x1"], word["bottom"]],
                    "text": word["text"],
                    "source_path": str(pdf_path.resolve()),
                    "extraction_stage": "lab5_word_level"
                }
                records.append(record)

    # PART 2: Process Lab 1 text extraction results
    print("Processing Lab 1 text extraction results...")
    lab1_records = process_lab1_results(doc_id, company, fiscal_year, pdf_path, unified_base)
    records.extend(lab1_records)
    
    # Add Lab 1 results to markdown
    if lab1_records:
        markdown_lines.append(f"\n# Lab 1 Text Extraction Results\n")
        for record in lab1_records[:5]:  # Show first 5 blocks
            markdown_lines.append(f"## Page {record['page']}\n")
            markdown_lines.append(f"{record['text'][:300]}...\n")

    # PART 3: Process Lab 2 table extraction results
    print("Processing Lab 2 table extraction results...")
    lab2_records = process_lab2_results(doc_id, company, fiscal_year, pdf_path, unified_base)
    records.extend(lab2_records)
    
    # Add Lab 2 results to markdown
    if lab2_records:
        markdown_lines.append(f"\n# Lab 2 Table Extraction Results\n")
        for record in lab2_records:
            markdown_lines.append(f"## Table from {record['extraction_method']}\n")
            markdown_lines.append(f"- Rows: {record.get('table_rows', 'unknown')}\n")
            markdown_lines.append(f"- Columns: {record.get('table_cols', 'unknown')}\n")
            markdown_lines.append(f"- Method: {record['extraction_method']}\n\n")

    # PART 4: Process Lab 3 layout detection results
    print("Processing Lab 3 layout detection results...")
    lab3_records = process_lab3_results(doc_id, company, fiscal_year, pdf_path, unified_base)
    records.extend(lab3_records)
    
    # Add Lab 3 results to markdown
    if lab3_records:
        markdown_lines.append(f"\n# Lab 3 Layout Detection Results\n")
        layout_summary = {}
        for record in lab3_records:
            block_type = record.get('block_type', 'unknown')
            layout_summary[block_type] = layout_summary.get(block_type, 0) + 1
        
        for block_type, count in layout_summary.items():
            markdown_lines.append(f"- {block_type.title()} blocks: {count}\n")

    # PART 5: Process Lab 4 Docling results
    print("Processing Lab 4 Docling results...")
    lab4_records = process_lab4_results(doc_id, company, fiscal_year, pdf_path, unified_base)
    records.extend(lab4_records)
    
    # Add Lab 4 results to markdown
    if lab4_records:
        markdown_lines.append(f"\n# Lab 4 Docling Results\n")
        markdown_lines.append(f"- Total Docling blocks: {len(lab4_records)}\n")
        markdown_lines.append(f"- Extraction method: Unified document understanding\n\n")

    # Save JSONL with ALL results
    with open(jsonl_path, "w", encoding="utf-8") as f_jsonl:
        for rec in records:
            f_jsonl.write(json.dumps(rec) + "\n")

    # Save comprehensive Markdown summary
    with open(md_path, "w", encoding="utf-8") as f_md:
        f_md.write("\n".join(markdown_lines))

    # Print summary by extraction method
    method_counts = {}
    for record in records:
        method = record.get('extraction_method', 'unknown')
        method_counts[method] = method_counts.get(method, 0) + 1

    # Create summary JSON
    summary_path = metadata_dir / f"{doc_id}_summary.json"
    summary_data = {
        "doc_id": doc_id,
        "company": company,
        "fiscal_year": fiscal_year,
        "total_records": len(records),
        "extraction_methods": method_counts,
        "source_pdf": str(pdf_path.resolve()),
        "metadata_files": {
            "jsonl": str(jsonl_path),
            "markdown": str(md_path),
            "summary": str(summary_path)
        },
        "extraction_timestamp": pd.Timestamp.now().isoformat()
    }
    
    with open(summary_path, "w", encoding="utf-8") as f_summary:
        json.dump(summary_data, f_summary, indent=2)

    print(f"\n COMPREHENSIVE LAB 5 COMPLETE!")
    print(f"-> JSONL with ALL lab results: {jsonl_path}")
    print(f"-> Markdown summary: {md_path}")
    print(f"-> Summary JSON: {summary_path}")
    print(f"-> Total metadata records: {len(records)}")
    
    print(f"\nExtraction methods included:")
    for method, count in method_counts.items():
        print(f"  - {method}: {count} records")

def process_lab1_results(doc_id, company, fiscal_year, pdf_path, unified_base):
    """Process Lab 1 text extraction files"""
    records = []
    
    # Look for Lab 1 text files in the unified directory structure
    text_dir = unified_base / "text"
    
    # Look for combined.txt
    combined_file = text_dir / "combined.txt"
    if combined_file.exists():
        try:
            with open(combined_file, 'r', encoding='utf-8') as f:
                text_content = f.read().strip()
            
            if text_content:
                record = {
                    "doc_id": doc_id,
                    "company": company,
                    "fiscal_year": fiscal_year,
                    "page": 1,
                    "section": f"Lab1_Combined_Text",
                    "block_type": "text_block",
                    "extraction_method": "lab1_pdfplumber_combined",
                    "bbox": [0, 0, 612, 792],  # Full page
                    "text": text_content,
                    "source_path": str(pdf_path.resolve()),
                    "extraction_stage": "lab1_text_extraction",
                    "word_count": len(text_content.split()),
                    "char_count": len(text_content)
                }
                records.append(record)
        except Exception as e:
            print(f"Error processing {combined_file}: {e}")
    
    # Look for individual page files in pages/ subdirectory
    pages_dir = text_dir / "pages"
    if pages_dir.exists():
        page_files = list(pages_dir.glob("page_*.txt"))
        
        for page_file in page_files:
            try:
                # Extract page number from filename
                page_num = int(page_file.stem.split('_')[1])
                
                with open(page_file, 'r', encoding='utf-8') as f:
                    text_content = f.read().strip()
                
                if text_content:
                    record = {
                        "doc_id": doc_id,
                        "company": company,
                        "fiscal_year": fiscal_year,
                        "page": page_num,
                        "section": f"Lab1_Page_{page_num}",
                        "block_type": "text_block",
                        "extraction_method": "lab1_pdfplumber",
                        "bbox": [0, 0, 612, 792],  # Full page
                        "text": text_content,
                        "source_path": str(pdf_path.resolve()),
                        "extraction_stage": "lab1_text_extraction",
                        "word_count": len(text_content.split()),
                        "char_count": len(text_content)
                    }
                    records.append(record)
            except Exception as e:
                print(f"Error processing {page_file}: {e}")
    
    return records

def process_lab2_results(doc_id, company, fiscal_year, pdf_path, unified_base):
    """Process Lab 2 table extraction CSV files"""
    records = []
    
    # Look for Lab 2 CSV files in the unified directory structure
    tables_dir = unified_base / "tables"
    
    if tables_dir.exists():
        csv_files = list(tables_dir.glob("*.csv"))
        
        for csv_file in csv_files:
            try:
                # Skip index files
                if "_tables_index.csv" in csv_file.name:
                    continue
                    
                df = pd.read_csv(csv_file)
                
                # Determine extraction method from filename
                if 'stream' in csv_file.name:
                    method = 'camelot_stream'
                elif 'lattice' in csv_file.name:
                    method = 'camelot_lattice'
                elif 'pdfplumber' in csv_file.name:
                    method = 'pdfplumber_table'
                else:
                    method = 'unknown_table_method'
                
                # Extract page if available in filename
                page_num = 1
                if '_p' in csv_file.stem:
                    try:
                        page_num = int(csv_file.stem.split('_p')[1].split('_')[0])
                    except:
                        pass
                
                table_text = df.to_string(index=False)
                
                record = {
                    "doc_id": doc_id,
                    "company": company,
                    "fiscal_year": fiscal_year,
                    "page": page_num,
                    "section": f"Lab2_Table_{csv_file.stem}",
                    "block_type": "table",
                    "extraction_method": method,
                    "bbox": [50, 100, 550, 400],  # Estimated table area
                    "text": table_text,
                    "source_path": str(pdf_path.resolve()),
                    "extraction_stage": "lab2_table_extraction",
                    "table_rows": len(df),
                    "table_cols": len(df.columns),
                    "table_file": str(csv_file),
                    "word_count": len(table_text.split()),
                    "char_count": len(table_text)
                }
                records.append(record)
                
            except Exception as e:
                print(f"Error processing {csv_file}: {e}")
    
    return records

def process_lab3_results(doc_id, company, fiscal_year, pdf_path, unified_base):
    """Process Lab 3 layout detection results"""
    records = []
    
    # Look for Lab 3 layout files in the unified directory structure
    layout_dir = unified_base / "layout"
    
    if layout_dir.exists():
        # Look for the main layout blocks file
        layout_file = layout_dir / "layout_blocks.json"
        
        if layout_file.exists():
            try:
                with open(layout_file, 'r', encoding='utf-8') as f:
                    layout_data = json.load(f)
                
                # Process pages from the layout data
                for page_data in layout_data.get('pages', []):
                    page_num = page_data.get('page_num', 1)
                    
                    for block in page_data.get('blocks', []):
                        bbox = block.get('bounding_box', {})
                        block_type = block.get('type', 'layout_block')
                        
                        record = {
                            "doc_id": doc_id,
                            "company": company,
                            "fiscal_year": fiscal_year,
                            "page": page_num,
                            "section": f"Lab3_Layout_Page_{page_num}",
                            "block_type": block_type,
                            "extraction_method": "layoutparser",
                            "bbox": [bbox.get('x1', 0), bbox.get('y1', 0), 
                                    bbox.get('x2', 0), bbox.get('y2', 0)],
                            "text": block.get('text', ''),
                            "source_path": str(pdf_path.resolve()),
                            "extraction_stage": "lab3_layout_detection",
                            "confidence": block.get('confidence', 0.8),
                            "layout_block_id": block.get('block_id', '')
                        }
                        records.append(record)
                        
            except Exception as e:
                print(f"Error processing {layout_file}: {e}")
    
    return records

def process_lab4_results(doc_id, company, fiscal_year, pdf_path, unified_base):
    """Process Lab 4 Docling results"""
    records = []
    
    # Look for Lab 4 Docling files in the unified directory structure
    docling_dir = unified_base / "docling"
    
    if docling_dir.exists():
        # Look for Docling markdown output
        md_file = docling_dir / "output.md"
        
        if md_file.exists():
            try:
                with open(md_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Split into sections
                sections = content.split('\n#')
                
                for i, section in enumerate(sections):
                    if section.strip():
                        lines = section.split('\n')
                        section_title = lines[0].strip('# ').strip()
                        section_text = '\n'.join(lines[1:]).strip()
                        
                        if section_text:
                            record = {
                                "doc_id": doc_id,
                                "company": company,
                                "fiscal_year": fiscal_year,
                                "page": 1,  # Docling doesn't preserve exact page mapping
                                "section": f"Lab4_Docling_{section_title}",
                                "block_type": "docling_section",
                                "extraction_method": "docling_unified",
                                "bbox": [0, 0, 612, 792],
                                "text": section_text,
                                "source_path": str(pdf_path.resolve()),
                                "extraction_stage": "lab4_docling",
                                "word_count": len(section_text.split()),
                                "char_count": len(section_text),
                                "docling_section_title": section_title
                            }
                            records.append(record)
                            
            except Exception as e:
                print(f"Error processing {md_file}: {e}")
    
    return records

# CONFIGURATION TO RUN
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lab 5: Extract comprehensive metadata from all lab outputs")
    parser.add_argument('--in', dest='input_path', required=True, help='Input PDF file')
    parser.add_argument('--out', dest='output_dir', required=True, help='Unified output directory')
    parser.add_argument('--doc-id', dest='doc_id', required=True, help='Document ID')
    parser.add_argument('--company', dest='company', required=True, help='Company name')
    parser.add_argument('--fiscal-year', dest='fiscal_year', required=True, help='Fiscal year')
    
    args = parser.parse_args()
    
    extract_metadata(
        pdf_path=args.input_path,
        doc_id=args.doc_id,
        company=args.company,
        fiscal_year=args.fiscal_year,
        output_dir=args.output_dir,
        unified_dir=args.output_dir
    )