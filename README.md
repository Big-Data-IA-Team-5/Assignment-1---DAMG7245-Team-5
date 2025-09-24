Project LANTERN – PDF Processing Pipeline

Team 5 – DAMG7245, Fall 2025

A production-ready pipeline to extract text, tables, layout, and metadata from PDFs. Outputs structured data in multiple formats suitable for RAG systems, financial analysis, and machine learning applications.

Table of Contents

System Requirements

Dependencies

Environment Setup

Project Structure

Pipeline Labs

Lab 7: Google Document AI Integration

Usage Examples

Output Structure

Troubleshooting

Performance

Team

License

System Requirements

Python: 3.8+

RAM: 4GB minimum (8GB recommended)

Disk Space: 2GB free

OS: Windows, macOS, Linux

Dependencies
Core Dependencies

pdfplumber – PDF text extraction

camelot-py – Table extraction

pytesseract – OCR

pandas, numpy – Data manipulation

layoutparser (optional) – Layout detection

docling (optional) – AI PDF understanding

torch – ML features

Pipeline Management

dvc – Data Version Control

git – Version control integration

Environment Setup

Create virtual environment

python3 -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows


Install dependencies

pip install --upgrade pip setuptools wheel
pip install -r requirements.txt


Install Tesseract for OCR

macOS: brew install tesseract && xcode-select --install

Linux: sudo apt-get install tesseract-ocr libtesseract-dev python3-dev build-essential

Windows: Install Tesseract OCR
 and add to PATH

Project Structure
Assignment-1---DAMG7245-Team-5/
├── run_complete_pipeline.py      # Main script
├── requirements.txt
├── data/
│   ├── raw/      # Input PDFs
│   └── parsed/   # Pipeline outputs
├── src/
│   ├── text/      # Lab 1
│   ├── tables/    # Lab 2
│   ├── layout/    # Lab 3
│   ├── docling/   # Lab 4
│   ├── metadata/  # Lab 5
│   ├── formats/   # Lab 6
│   └── google_ai/ # Lab 7 (optional)
├── credentials/   # Secure keys
├── reports/       # AI analysis reports
├── configs/
├── utils/
├── tests/
└── docs/

Pipeline Labs
Lab	Purpose	Output	Status
Lab 1	Text Extraction	.txt files	✅ Working
Lab 2	Table Extraction	.csv files	✅ Working
Lab 3	Layout Analysis	.json structure	✅ Working
Lab 4	AI Processing	.json, .md	✅ Working
Lab 5	Metadata Tagging	.jsonl metadata	✅ Working
Lab 6	Format Conversion	JSON, Markdown, TXT	✅ Working
Lab 7	Google Document AI	AI-powered extraction & comparison	✅ Optional
Lab 7: Google Document AI Integration

Enhanced AI-Powered PDF Analysis

Lab 7 integrates Google's Document AI for advanced PDF processing and comparison with traditional parsing results.

Key Features

Smart page selection (specific pages or random sampling)

AI-powered extraction: text, tables, entities, forms

Comparative analysis with Lab 1–6 outputs

Comprehensive reporting with metrics

Organized folder hierarchy

Setup Requirements

Place service account JSON in credentials/google-credentials.json

Configure configs/google_ai_config.json with processor ID

Optional environment variable:

export GOOGLE_APPLICATION_CREDENTIALS="path/to/credentials.json"


Usage Examples

Random pages:

python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2


Specific pages:

python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12

Usage Examples

Run full pipeline:

python3 run_complete_pipeline.py --out data/parsed --hybrid-tables --verbose


Run individual labs:

python3 src/text/extract_text.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/tables/extract_tables.py --in data/raw/your_file.pdf --out data/parsed/ --hybrid
python3 src/layout/extract_layout.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/docling/extract_docling.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/metadata/extract_metadata.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/formats/convert_formats.py --in data/parsed/metadata/doc.jsonl --out data/parsed/


Lab 7 Google AI:

python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12

Output Structure

Pipeline results:

data/parsed/
├── your_document_<timestamp>/
│   ├── text/
│   ├── tables/
│   ├── layout/
│   ├── docling/
│   ├── metadata/
│   └── formats/
├── LANTERN_Pipeline_Report_<timestamp>.md
└── pipeline_summary_<timestamp>.json


Lab 7 AI results:

reports/google_ai/lab7_session_<timestamp>/
├── temp_pdfs/
├── raw_google_ai_results/
├── parsed_results/
├── parsed_data_comparison/
└── final_reports/

Troubleshooting

Ensure python3 and virtual environment are active

Install missing packages: pip install -r requirements.txt

PDFs must exist in data/raw/

Use chmod +x run_complete_pipeline.py setup.sh on macOS/Linux

Monitor logs:

tail -f pipeline_execution.log
tail -f lab7_execution.log

Performance

100-page PDF: ~4–6 min, ~4GB RAM

2-page Lab 7 AI extraction: ~3–5 sec, ~2GB RAM

High success rate and output quality

Timestamped folders for traceability

Team

Team 5 – DAMG7245, Fall 2025
Big Data Analytics Project – SEC Filing Processing Pipeline

Lab 7 Contributors: Google Document AI integration, page selection, AI analysis, security, testing

License

MIT License – see project files for details