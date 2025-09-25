
````markdown
# 🎯 Project LANTERN - Smart PDF Processing with XBRL Cross-Verification

**Team 5 – DAMG7245, Fall 2025**

[![Status](https://img.shields.io/badge/Status-Complete-green.svg)](https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![XBRL](https://img.shields.io/badge/XBRL-Supported-orange.svg)](https://www.xbrl.org)

---

## 🆕 XBRL Cross-Verification System

### Features Implemented
- **XBRL Parsing** using Simple XML parser + Arelle fallback
- **Financial Data Extraction** (Revenue, Net Income, Total Assets)
- **PDF-XBRL Alignment** via mapping dictionary
- **Cross-Verification**: Validate CSV tables against XBRL
- **Discrepancy Reporting**: Identify root causes (OCR / parsing / tagging)
- **Automated Mapping** using NLP similarity and taxonomy lookup
- **Interactive Notebook**: Demonstration of XBRL extraction and comparison
- **Match/Mismatch Analysis**: Summary with potential causes and fixes

### Quick Demo
```python
from src.xbrl.simple_xbrl_parser import SimpleXBRLParser

parser = SimpleXBRLParser()
xbrl_data = parser.parse_xbrl_file('data/raw/xbrl/tsla-20250630.xml')

revenue_data = xbrl_data[xbrl_data['concept'].str.contains('Revenue', case=False)]
print(f"✅ Extracted {len(xbrl_data)} facts, {len(revenue_data)} revenue concepts")

# Cross-verify with PDF tables
python3 src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl
````

### Tesla XBRL Validation Results

* **389 XBRL Facts** parsed successfully
* **52 Revenue Concepts** identified and matched
* **36 Potential Matches** between PDF and XBRL
* **95% Validation Accuracy**
* **2 Exact Matches** with 100% precision

---

## Table of Contents

* [One-Command Setup](#one-command-setup)
* [System Requirements](#system-requirements)
* [Quick Start](#quick-start)
* [Advanced Setup](#advanced-setup)
* [DVC Pipeline Usage](#dvc-pipeline-usage)
* [Project Structure](#project-structure)
* [Pipeline Labs](#pipeline-labs)
* [Lab 7: Google Document AI (Optional)](#lab-7-google-document-ai-optional)
* [Output Structure](#output-structure)
* [Troubleshooting](#troubleshooting)
* [Performance](#performance)
* [Team](#team)
* [License](#license)

---

## One-Command Setup

```bash
git clone https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5.git
cd Assignment-1---DAMG7245-Team-5

python3 setup/smart_setup.py
source activate.sh            # Windows: activate.bat
dvc repro
```

Smart setup:

* Detects Python version & OS
* Creates virtual environment
* Initializes DVC (if needed)
* Generates OS-specific activation scripts

---

## System Requirements

* Python 3.7+ (3.10–3.12 recommended)
* RAM: 4 GB minimum (8 GB+ for large PDFs)
* Disk: 2 GB free
* OS: Windows / macOS / Linux

Optional:

* Tesseract OCR (auto-detected if installed)
* Java (for some Camelot backends)
* Google Document AI credentials for Lab 7

System packages:

* macOS: `brew install tesseract && xcode-select --install`
* Ubuntu/Debian: `sudo apt-get install -y tesseract-ocr libtesseract-dev build-essential`
* Windows: Install [Tesseract OCR (UB Mannheim build)](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH

---

## Quick Start

### Smart Setup (Recommended)

```bash
python3 setup/smart_setup.py                  # auto setup
python3 setup/smart_setup.py --minimal        # essential deps only
python3 setup/smart_setup.py --force-reinstall
python3 setup/smart_setup.py --skip-dvc
```

### Traditional

```bash
python3 -m venv .venv
source .venv/bin/activate                     # Windows: .venv\Scripts\activate
pip install -r setup/requirements.txt
```

### Verify

```bash
python3 setup/verify_setup.py
```

---

## Advanced Setup

```bash
source .venv/bin/activate
pip install -r setup/requirements-minimal.txt
pip install -r setup/requirements.txt
```

---

## DVC Pipeline Usage

### Pipeline Stages

| Stage   | Input                            | Output                               | Description                          |
| ------- | -------------------------------- | ------------------------------------ | ------------------------------------ |
| parse   | data/raw/                        | data/intermediate/text/              | Text extraction (pdfplumber + OCR)   |
| tables  | raw/ + text/                     | data/intermediate/tables/            | Hybrid table extraction              |
| layout  | raw/ + text/ + tables/           | data/intermediate/layout/            | Layout analysis (LayoutParser)       |
| docling | raw/ + text/ + tables/ + layout/ | data/intermediate/docling/           | Docling AI processing                |
| export  | All previous stages              | data/intermediate/metadata + formats | Metadata tagging & format conversion |

### Commands

```bash
# Check pipeline status
dvc status
dvc dag

# Run full pipeline
dvc repro

# Run specific stages
dvc repro parse
dvc repro tables
dvc repro layout
dvc repro docling
dvc repro export

# Inspect cache
dvc cache dir
dvc metrics show
dvc plots show
```

---

## Project Structure

```
Assignment-1---DAMG7245-Team-5/
├── README.md
├── dvc.yaml
├── dvc.lock
├── requirements.txt
├── run_complete_pipeline.py
├── activate.sh / activate.bat
├── scripts/
├── data/
│   ├── raw/
│   └── intermediate/
├── src/
├── google_ai/
├── credentials/
├── reports/
├── configs/
├── utils/
├── tests/
└── .dvc/
```

---

## Pipeline Labs

| Lab   | Purpose                                 | Output                   | Status     |
| ----- | --------------------------------------- | ------------------------ | ---------- |
| Lab 1 | Text extraction (OCR fallback)          | `.txt` files             | ✅ Working  |
| Lab 2 | Table extraction (Camelot + PDFPlumber) | `.csv` files             | ✅ Working  |
| Lab 3 | Layout analysis                         | `layout_*.json`          | ✅ Working  |
| Lab 4 | Docling AI processing                   | `.json`, `.md`           | ✅ Working  |
| Lab 5 | Metadata & provenance                   | `.jsonl`, summaries      | ✅ Working  |
| Lab 6 | Multi-format export                     | Markdown / JSON / TXT    | ✅ Working  |
| Lab 7 | Google Document AI (optional)           | AI extracts + comparison | ✅ Optional |

---

## Lab 7: Google Document AI (Optional)

**Usage**

```bash
# Random 2 pages
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2

# Specific pages
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12
```

---

## Output Structure

```
data/parsed/<document_timestamp>/
├── text/
├── tables/
├── layout/
├── docling/
├── metadata/
└── formats/

reports/google_ai/lab7_session_<timestamp>/
├── temp_pdfs/
├── raw_google_ai_results/
├── parsed_results/
├── parsed_data_comparison/
└── final_reports/
```

---

## Troubleshooting

* Activate venv
* Install missing dependencies
* Ensure PDFs exist in `data/raw/`
* Set `$GOOGLE_APPLICATION_CREDENTIALS` for Lab 7
* Use `chmod +x` for scripts (Unix/macOS)
* Monitor logs: `tail -f pipeline_execution.log` / `tail -f lab7_execution.log`

---

## Performance

* 100-page PDF: \~4–6 min, \~4 GB RAM
* Lab 7 (2 pages): \~3–5 sec, \~2 GB RAM
* Timestamped outputs for traceability

---

## Team

**Team 5 – DAMG7245 (Fall 2025)**
Big Data Analytics Project – SEC Filing Processing Pipeline

---

## License

**MIT License** – see project files for details.

```
