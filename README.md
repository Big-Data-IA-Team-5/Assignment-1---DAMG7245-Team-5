# Project LANTERN – PDF Processing Pipeline

**Team 5 – DAMG7245, Fall 2025**

A production-ready pipeline to extract text, tables, layout, and metadata from PDFs. Outputs structured data in multiple formats suitable for RAG systems, financial analysis, and ML applications.

## Table of Contents

- [Overview](#overview)
- [System Requirements](#system-requirements)
- [Environment Setup](#environment-setup)
- [Project Structure](#project-structure)
- [Pipeline Labs](#pipeline-labs)
- [Usage Examples](#usage-examples)
- [Output Structure](#output-structure)
- [Troubleshooting](#troubleshooting)
- [Performance](#performance)
- [Team & License](#team--license)

## Overview

Project LANTERN provides end-to-end extraction, analysis, and conversion of PDF documents. Features include:

- Text extraction with OCR fallback
- Hybrid table extraction (Camelot + pdfplumber)
- Layout analysis and semantic classification
- AI-powered document understanding (Docling)
- Metadata & provenance tagging
- Multi-format conversion (JSON, Markdown, TXT)

The pipeline handles SEC filings and other structured/unstructured PDFs efficiently.

## System Requirements

- **Python**: 3.8+
- **RAM**: 4GB minimum (8GB recommended)
- **Disk Space**: 2GB free
- **OS**: Windows, macOS, Linux

### Key Dependencies

- `pdfplumber` – PDF text extraction
- `camelot-py` – Table extraction
- `pytesseract` – OCR
- `pandas`, `numpy` – Data processing
- `layoutparser` – Layout detection (optional)
- `docling` – AI PDF understanding (optional)
- `torch` – ML features

### System Dependencies

- **macOS**: `brew install tesseract`, `xcode-select --install`
- **Linux**: `sudo apt-get install tesseract-ocr libtesseract-dev python3-dev build-essential`
- **Windows**: Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH

## Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

### Optional automatic setup

```bash
# Linux/macOS
chmod +x setup.sh && ./setup.sh

# Windows
setup.bat
```

## Project Structure

```
Assignment-1---DAMG7245-Team-5/
├── run_complete_pipeline.py      # Main script
├── requirements.txt              # Python dependencies
├── data/
│   ├── raw/      # Input PDFs
│   └── parsed/   # Pipeline outputs
├── src/                          # 6 lab modules
│   ├── text/      # Lab 1
│   ├── tables/    # Lab 2
│   ├── layout/    # Lab 3
│   ├── docling/   # Lab 4
│   ├── metadata/  # Lab 5
│   └── formats/   # Lab 6
├── configs/      # Config files
├── utils/        # Helper scripts
├── tests/        # Test files
└── docs/         # Documentation
```

## Pipeline Labs

| Lab | Purpose | Output |
|-----|---------|--------|
| **Lab 1** | Text Extraction | .txt files |
| **Lab 2** | Table Extraction | .csv files |
| **Lab 3** | Layout Analysis | Layout structure .json |
| **Lab 4** | AI Processing | .json & .md outputs |
| **Lab 5** | Metadata Tagging | .jsonl metadata |
| **Lab 6** | Format Conversion | JSON, Markdown, TXT |

### Features

- One-click pipeline execution or individual lab runs
- Timestamped folders for outputs
- Error recovery if one lab fails
- Flexible execution options

## Usage Examples

### Complete Pipeline
```bash
# Copy PDFs to raw folder
cp your_file.pdf data/raw/

# Run pipeline
python3 run_complete_pipeline.py --out data/parsed --hybrid-tables --verbose
```

### Individual Labs
```bash
# Lab 1
python3 src/text/extract_text.py --in data/raw/your_file.pdf --out data/parsed/

# Lab 2
python3 src/tables/extract_tables.py --in data/raw/your_file.pdf --out data/parsed/ --hybrid

# Lab 3
python3 src/layout/extract_layout.py --in data/raw/your_file.pdf --out data/parsed/

# Lab 4
python3 src/docling/extract_docling.py --in data/raw/your_file.pdf --out data/parsed/

# Lab 5
python3 src/metadata/extract_metadata.py --in data/raw/your_file.pdf --out data/parsed/

# Lab 6
python3 src/formats/convert_formats.py --in data/parsed/metadata/doc.jsonl --out data/parsed/
```

### Utility Scripts
```bash
python utils/check_system.py         # Verify environment
python utils/download_filings.py     # Download SEC filings
python utils/fix_directory_naming.py # Fix directory issues
```

## Output Structure

```
data/parsed/
├── your_document_<timestamp>/
│   ├── text/       # Lab 1
│   ├── tables/     # Lab 2
│   ├── layout/     # Lab 3
│   ├── docling/    # Lab 4
│   ├── metadata/   # Lab 5
│   └── formats/    # Lab 6
├── LANTERN_Pipeline_Report_<timestamp>.md
└── pipeline_summary_<timestamp>.json
```

## Troubleshooting

### Common Issues

- **Command not found**: Use `python3` and activate virtual environment
- **Module not found**: `pip install -r requirements.txt`
- **No PDFs found**: Ensure PDFs are in `data/raw/`
- **Permission denied**: `chmod +x run_complete_pipeline.py setup.sh`
- **Out of memory**: Close other applications, process smaller PDFs first

### Logs
```bash
# Monitor execution
tail -f pipeline_execution.log
```

## Performance

- **Processing Time**: ~4-6 min for 100-page PDF
- **Memory Usage**: ~4GB RAM
- **Success Rate**: Reliable for most PDF types
- **Output Quality**: Structured, production-ready
- **Scalability**: Handles multiple PDFs with timestamped organization

## Team

**Team 5 – DAMG7245, Fall 2025**  
Big Data Analytics Project – SEC Filing Processing Pipeline

## License

MIT License – See project files for details