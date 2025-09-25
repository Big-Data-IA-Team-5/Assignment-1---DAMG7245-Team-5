
---

# Project LANTERN – Smart PDF & XBRL Processing Pipeline (Enhanced Visuals)

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

Project LANTERN processes **PDF filings** and **XBRL data** to extract and validate:

* Text, tables, layout, metadata
* AI-enhanced PDF understanding (Docling)
* Optional Google Document AI extraction
* XBRL cross-verification for key financial metrics

---

## System Requirements

* **Python:** 3.7+ (3.10–3.12 recommended)
* **RAM:** 4 GB minimum (8 GB+ for large PDFs)
* **Disk Space:** 2 GB free
* **OS:** Windows, macOS, Linux
* **Optional:** Tesseract OCR, Java, Google AI credentials

---

## Setup & Quick Start

```bash
git clone https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5.git
cd Assignment-1---DAMG7245-Team-5
python3 setup/smart_setup.py
source activate.sh  # Windows: activate.bat
dvc repro
```

**Verify Installation**

```bash
python3 setup/verify_setup.py
```

---

## Pipeline Labs

| Lab    | Purpose                                 | Output                   | Status     |
| ------ | --------------------------------------- | ------------------------ | ---------- |
| Lab 1  | Text extraction (OCR fallback)          | `.txt`                   | ✅ Working  |
| Lab 2  | Table extraction (Camelot + PDFPlumber) | `.csv`                   | ✅ Working  |
| Lab 3  | Layout analysis                         | `layout_*.json`          | ✅ Working  |
| Lab 4  | Docling AI                              | `.json` / `.md`          | ✅ Working  |
| Lab 5  | Metadata & Provenance                   | `.jsonl`                 | ✅ Working  |
| Lab 6  | Multi-format Export                     | Markdown / JSON / TXT    | ✅ Working  |
| Lab 7  | Google Document AI (Optional)           | AI extracts + comparison | ✅ Optional |
| Lab 11 | XBRL Verification                       | CSV / summary            | ✅ Working  |

---

## DVC Pipeline

* **Full reproducibility** and caching
* Track dependencies and outputs automatically
* Supports rerun of only changed stages

**Example Commands**

```bash
dvc status
dvc dag
dvc repro
dvc repro parse
dvc repro tables
dvc repro layout
dvc repro docling
dvc repro export
```

---

## XBRL Cross-Verification

* Parse XBRL using **Simple XML parser** or **Arelle**
* Extract Revenue, Net Income, Total Assets
* Map PDF tables to XBRL taxonomy using **mapping dictionary**
* Validate numerical values, report mismatches

**Example**

```bash
python3 src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl
```

---

## Optional Google Document AI

* Text, table, entity, and form extraction
* Random or selected pages
* Compare with Labs 1–6

**Usage**

```bash
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12
```

---

## Architecture Diagram

```python
# lantern_architecture.py
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

**Result:** Generates a professional **SVG architecture diagram** with custom icons for PDFPlumber, Camelot, Docling, Google AI, and XBRL.

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
* Tesseract OCR must be on PATH
* Check `dvc status` and repair cache if needed

---

## Performance

* 100-page PDF: \~4–6 min, \~4 GB RAM
* Lab 7 (2 pages): \~3–5 sec, \~2 GB RAM
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


