"""
Lab 6: Storage Formats - Markdown vs JSON vs TXT

Converts JSONL metadata to three different storage formats and analyzes trade-offs.
Demonstrates format selection for different use cases, especially RAG pipelines.
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def convert_metadata_to_formats(jsonl_path, output_dir):
    """Convert JSONL metadata to three different storage formats."""
    jsonl_path = Path(jsonl_path)
    output_dir = Path(output_dir)

    if not jsonl_path.exists():
        logger.error(f"JSONL file not found: {jsonl_path}")
        return None

    # Extract doc_id from filename
    doc_id = jsonl_path.stem

    # Create output directory structure
    formats_dir = output_dir / "formats"
    formats_dir.mkdir(parents=True, exist_ok=True)

    logger.info(f"Converting metadata for document: {doc_id}")

    # Load JSONL data
    records = []
    try:
        with open(jsonl_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    try:
                        record = json.loads(line)
                        records.append(record)
                    except json.JSONDecodeError:
                        continue
    except Exception as e:
        logger.error(f"Error reading JSONL file: {e}")
        return None

    if not records:
        logger.warning("No valid records found")
        return None

    logger.info(f"Loaded {len(records)} records")

    # Generate formats
    results = {}
    
    # Markdown format
    md_file = formats_dir / f"{doc_id}.md"
    try:
        with open(md_file, "w", encoding="utf-8") as f:
            f.write(f"# Document: {doc_id}\n\n")
            for i, record in enumerate(records):
                text = record.get("text", "")
                if text:
                    f.write(f"## Record {i+1}\n\n{text}\n\n")
        results["markdown"] = md_file
        logger.info(f"Generated Markdown: {md_file}")
    except Exception as e:
        logger.error(f"Error generating Markdown: {e}")

    # JSON format  
    json_file = formats_dir / f"{doc_id}.json"
    try:
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump({"records": records}, f, indent=2)
        results["json"] = json_file  
        logger.info(f"Generated JSON: {json_file}")
    except Exception as e:
        logger.error(f"Error generating JSON: {e}")

    # TXT format
    txt_file = formats_dir / f"{doc_id}.txt"
    try:
        with open(txt_file, "w", encoding="utf-8") as f:
            f.write(f"Document: {doc_id}\n")
            f.write("=" * 50 + "\n\n")
            for record in records:
                text = record.get("text", "")
                if text:
                    f.write(text + "\n\n")
        results["txt"] = txt_file
        logger.info(f"Generated TXT: {txt_file}")
    except Exception as e:
        logger.error(f"Error generating TXT: {e}")

    # Analysis file
    analysis_file = formats_dir / "_format_analysis.md"
    try:
        file_sizes = {}
        for format_name, file_path in results.items():
            if file_path and file_path.exists():
                file_sizes[format_name] = file_path.stat().st_size / 1024

        with open(analysis_file, "w", encoding="utf-8") as f:
            f.write(f"# Format Analysis for {doc_id}\n\n")
            f.write("## File Sizes\n\n")
            for format_name, size in file_sizes.items():
                f.write(f"- {format_name.upper()}: {size:.1f} KB\n")
            f.write("\n## Recommendations\n\n")
            f.write("- **Markdown**: Best for RAG pipelines\n")
            f.write("- **JSON**: Best for programmatic access\n") 
            f.write("- **TXT**: Best for simple text processing\n")
        
        results["analysis"] = analysis_file
        logger.info(f"Generated analysis: {analysis_file}")
    except Exception as e:
        logger.error(f"Error generating analysis: {e}")

    return results


def main():
    parser = argparse.ArgumentParser(description="Lab 6: Storage Formats")
    parser.add_argument("--in", dest="input_jsonl", required=True, help="Input JSONL file")
    parser.add_argument("--out", dest="output_dir", required=True, help="Output directory")

    args = parser.parse_args()
    result = convert_metadata_to_formats(args.input_jsonl, args.output_dir)

    if result:
        logger.info("✅ Lab 6 completed successfully")
        return 0
    else:
        logger.error("❌ Lab 6 failed")
        return 1


if __name__ == "__main__":
    exit(main())
