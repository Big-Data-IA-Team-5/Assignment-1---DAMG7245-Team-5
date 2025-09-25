
---

# Project LANTERN – Smart PDF & XBRL Processing Pipeline

**Team 5 – DAMG7245, Fall 2025**

[![Status](https://img.shields.io/badge/Status-Complete-green.svg)](https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5)
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![XBRL](https://img.shields.io/badge/XBRL-Supported-orange.svg)](https://www.xbrl.org)

---

## Table of Contents

* [Overview](#overview)
* [System Requirements](#system-requirements)
* [Setup & Quick Start](#setup--quick-start)
* [Pipeline Labs](#pipeline-labs)
* [DVC Pipeline](#dvc-pipeline)
* [XBRL Cross-Verification](#xbrl-cross-verification)
* [Optional Google Document AI Integration](#optional-google-document-ai-integration)
* [Architecture Diagram](#architecture-diagram)
* [Output Structure](#output-structure)
* [Troubleshooting](#troubleshooting)
* [Performance](#performance)
* [Team](#team)
* [License](#license)

---

## Overview

Project LANTERN is a **production-ready pipeline** for extracting and validating structured data from **PDF filings** and **XBRL files**.

Features:

* PDF text, tables, layout, metadata extraction
* AI-enhanced processing via Docling
* Optional Google Document AI integration
* XBRL cross-verification of financial data
* DVC-powered reproducibility and caching

---

## System Requirements

* **Python:** 3.7+ (3.10–3.12 recommended)
* **RAM:** 4 GB minimum (8 GB+ for large PDFs)
* **Disk Space:** 2 GB free
* **OS:** Windows, macOS, Linux
* **Optional:** Tesseract OCR, Java, Google AI credentials

System packages:

* macOS: `brew install tesseract && xcode-select --install`
* Ubuntu/Debian: `sudo apt-get install -y tesseract-ocr libtesseract-dev build-essential`
* Windows: Install [Tesseract OCR (UB Mannheim)](https://github.com/UB-Mannheim/tesseract/wiki) and add to `PATH`.

---

## Setup & Quick Start

### Smart Setup (Recommended)

```bash
git clone https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5.git
cd Assignment-1---DAMG7245-Team-5

# Smart cross-platform setup
python3 setup/smart_setup.py

# Activate environment
source activate.sh       # Windows: activate.bat

# Run the DVC pipeline
dvc repro
```

### Traditional Setup

```bash
python3 -m venv .venv
source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r setup/requirements.txt
```

### Verify Setup

```bash
python3 setup/verify_setup.py
```

---

## Pipeline Labs

| Lab    | Purpose                                 | Output                   | Status     |
| ------ | --------------------------------------- | ------------------------ | ---------- |
| Lab 1  | Text extraction (OCR fallback)          | `.txt` per page          | ✅ Working  |
| Lab 2  | Table extraction (Camelot + PDFPlumber) | `.csv`, index            | ✅ Working  |
| Lab 3  | Layout analysis                         | `layout_*.json`          | ✅ Working  |
| Lab 4  | Docling AI processing                   | `.json` / `.md`          | ✅ Working  |
| Lab 5  | Metadata & provenance                   | `.jsonl`, summaries      | ✅ Working  |
| Lab 6  | Multi-format export                     | Markdown / JSON / TXT    | ✅ Working  |
| Lab 7  | Google Document AI (optional)           | AI extracts + comparison | ✅ Optional |
| Lab 11 | XBRL Verification                       | CSV / summary            | ✅ Working  |

**Manual Execution (Alternative to DVC)**

```bash
python3 run_complete_pipeline.py --out data/parsed --hybrid-tables --verbose
# Individual labs
python3 src/text/extract_text.py      --in data/raw/your.pdf --out data/parsed/
python3 src/tables/extract_tables.py  --in data/raw/your.pdf --out data/parsed/ --hybrid
python3 src/layout/extract_layout.py  --in data/raw/your.pdf --out data/parsed/
python3 src/docling/extract_docling.py --in data/raw/your.pdf --out data/parsed/
python3 src/metadata/extract_metadata.py --in data/raw/your.pdf --out data/parsed/
python3 src/formats/convert_formats.py --in data/parsed/<doc>/metadata/<doc>.jsonl --out data/parsed/<doc>/
```

---

## DVC Pipeline

* **Sequential stages**: Text → Tables → Layout → Docling → Export
* **Caching & reproducibility**: Only changed stages rerun
* **Versioning**: Track pipeline state via `dvc.lock`

```bash
dvc status
dvc dag
dvc repro                # Run full pipeline
dvc repro parse          # Run only text extraction
dvc repro tables
dvc repro layout
dvc repro docling
dvc repro export
dvc pipeline show
dvc metrics show
dvc plots show
dvc push                 # Upload to remote
dvc pull                 # Download from remote
dvc checkout             # Restore workspace
```

---

## XBRL Cross-Verification

* Parse XBRL using **Simple XML parser** or **Arelle**
* Extract Revenue, Net Income, Total Assets
* Map PDF tables to XBRL taxonomy using **mapping dictionary**
* Validate numerical values and report discrepancies

**Run XBRL verification**

```bash
python3 src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl
```

---

## Optional Google Document AI

```bash
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12
```

---

## Architecture Diagram

```python
from diagrams import Diagram, Cluster
from diagrams.onprem.client import User
from diagrams.onprem.compute import Server
from diagrams.onprem.database import Postgresql, Elasticsearch
from diagrams.custom import Custom

with Diagram("Project LANTERN Architecture", filename="lantern_architecture", show=True, outformat="svg", direction="LR"):

    user = User("Browser / Mobile")

    with Cluster("Pipeline Orchestrator / Labs"):
        ingestion = Server("PDF Ingestion")
        lab1 = Custom("Text Extraction\n(pdfplumber)", "./icons/pdfplumber.svg")
        lab2 = Custom("Table Extraction\n(Camelot)", "./icons/camelot.svg")
        lab3 = Server("Layout Analysis\n(LayoutParser)")
        lab4 = Custom("Docling AI", "./icons/docling.svg")
        lab5_6 = Server("Metadata & Format Conversion")
        lab7 = Custom("Google Document AI", "./icons/google_ai.svg")
        lab11 = Custom("XBRL Verification\n(Arelle/Python)", "./icons/xbrl.svg")

        ingestion >> lab1 >> lab2 >> lab3 >> lab4 >> lab5_6
        lab5_6 >> lab11
        lab1 >> lab7
        lab2 >> lab7
        lab3 >> lab7
        lab7 >> lab5_6

    db_metadata = Postgresql("Metadata DB")
    db_search = Elasticsearch("Search / Index")
    lab5_6 >> db_metadata
    lab5_6 >> db_search
    lab7 >> db_metadata
    lab11 >> db_metadata
    user >> ingestion
```

* Generates a professional **SVG diagram** with custom icons for PDFPlumber, Camelot, Docling, Google AI, and XBRL.

---

## Output Structure

```
data/parsed/
└─ <document>_<timestamp>/
   ├─ text/
   ├─ tables/
   ├─ layout/
   ├─ docling/
   ├─ metadata/
   └─ formats/
LANTERN_Pipeline_Report_<timestamp>.md
pipeline_summary_<timestamp>.json

reports/google_ai/lab7_session_<timestamp>/
├─ temp_pdfs/
├─ raw_google_ai_results/
├─ parsed_results/
├─ parsed_data_comparison/
└─ final_reports/
```

---

## Troubleshooting

* Activate virtual environment
* Install missing dependencies (`pip install -r setup/requirements.txt`)
* Ensure PDFs are in `data/raw/`
* Tesseract OCR must be on `PATH`
* Check `dvc status` and repair cache if needed

---

## Performance

* 100-page PDF: \~4–6 minutes, \~4 GB RAM
* Lab 7 (2 pages): \~3–5 seconds, \~2 GB RAM
* Timestamped outputs for traceability
* Cache efficiency: 80–85% stage skip on reruns

---

## Team

**Team 5 – DAMG7245 (Fall 2025)**
Big Data Analytics Project – SEC Filing Processing Pipeline

---

## License

**MIT License** – see project files for details

---

This README is **fully copy-paste ready** and works directly in a GitHub repository.

It supports:

* Clickable Table of Contents
* Lab and DVC commands
* XBRL verification instructions
* Optional Google AI integration
* Architecture diagram code ready to generate SVG

---
