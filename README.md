
---

# Project LANTERN – PDF Processing Pipeline

**Team 5 – DAMG7245, Fall 2025**

A production-ready pipeline to extract text, tables, layout, and metadata from PDFs. Outputs structured data in multiple formats suitable for RAG systems, financial analysis, and ML applications.

---

## Table of Contents

* [System Requirements](#system-requirements)
* [Dependencies](#dependencies)
* [Environment Setup](#environment-setup)
* [Project Structure](#project-structure)
* [Pipeline Labs](#pipeline-labs)
* [Lab 7: Google Document AI Integration](#lab-7-google-document-ai-integration)
* [Usage Examples](#usage-examples)
* [Output Structure](#output-structure)
* [Troubleshooting](#troubleshooting)
* [Performance](#performance)
* [Team](#team)
* [License](#license)

---

## System Requirements

* **Python:** 3.8+
* **RAM:** 4GB minimum (8GB recommended)
* **Disk Space:** 2GB free
* **OS:** Windows, macOS, Linux

---

## Dependencies

* `pdfplumber` – PDF text extraction
* `camelot-py` – Table extraction
* `pytesseract` – OCR
* `pandas`, `numpy` – Data manipulation
* `layoutparser` (optional) – Layout detection
* `docling` (optional) – AI PDF understanding
* `torch` – ML features

---

## Environment Setup

```bash
# Create virtual environment
python3 -m venv venv
source venv/bin/activate       # macOS/Linux
venv\Scripts\activate          # Windows

# Install dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt
```

**Install Tesseract for OCR:**

* macOS: `brew install tesseract && xcode-select --install`
* Linux: `sudo apt-get install tesseract-ocr libtesseract-dev python3-dev build-essential`
* Windows: Install [Tesseract OCR](https://github.com/UB-Mannheim/tesseract/wiki) and add to PATH

---

## Project Structure

```
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
```

---

## Pipeline Labs

| Lab   | Purpose            | Output                             | Status     |
| ----- | ------------------ | ---------------------------------- | ---------- |
| Lab 1 | Text Extraction    | `.txt` files                       | ✅ Working  |
| Lab 2 | Table Extraction   | `.csv` files                       | ✅ Working  |
| Lab 3 | Layout Analysis    | `.json` structure                  | ✅ Working  |
| Lab 4 | AI Processing      | `.json`, `.md`                     | ✅ Working  |
| Lab 5 | Metadata Tagging   | `.jsonl` metadata                  | ✅ Working  |
| Lab 6 | Format Conversion  | JSON, Markdown, TXT                | ✅ Working  |
| Lab 7 | Google Document AI | AI-powered extraction & comparison | ✅ Optional |

---

## Lab 7: Google Document AI Integration

**🚀 Enhanced AI-Powered PDF Analysis**

Lab 7 integrates Google's Document AI for advanced PDF processing and intelligent comparison with traditional parsing methods.

### ✨ Features

- **Smart Page Selection**: Choose specific pages or random sampling
- **AI-Powered Extraction**: Advanced text, table, and layout detection
- **Comparative Analysis**: Compare Google AI vs. traditional parsing results
- **Comprehensive Reporting**: Detailed analysis with metrics and insights
- **Organized Output**: Structured folder hierarchy for easy navigation

### 🔧 Setup Requirements

1. **Google Cloud Credentials**: Place your service account JSON in `credentials/google-credentials.json`
2. **Processor Configuration**: Update `configs/google_ai_config.json` with your processor ID
3. **Environment Variables** (optional but recommended):
   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="path/to/your/credentials.json"
   ```

### 📋 Usage Options

**Option 1: Random Page Processing (Recommended)**
```bash
# Process 2 random pages - best for quick testing
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2

# Process 3 random pages with reproducible seed
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 3 --seed 42
```

**Option 2: Specific Page Processing**
```bash
# Process specific pages (e.g., pages 5 and 12)
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12

# Process single page
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 8
```

**Option 3: Direct Script Execution**
```bash
# Run from google_ai directory
cd google_ai
python3 lab7_google_ai_integration.py --pdf ../data/raw/tesla.pdf --random 2
```

### 📊 Output Structure

Lab 7 creates organized output in `reports/google_ai/lab7_session_<timestamp>/`:

```
reports/google_ai/lab7_session_20250924_150404/
├── temp_pdfs/                     # Extracted page PDFs
│   └── tesla_pages_2_8.pdf
├── raw_google_ai_results/         # Raw Google AI JSON responses
│   └── tesla_pages_2_8_google_ai.json
├── parsed_results/                # Structured extraction results
│   ├── tesla_pages_2_8_google_text.txt
│   ├── tesla_pages_2_8_google_p1_t0.csv    # Table data
│   ├── tesla_pages_2_8_google_entities.json
│   ├── tesla_pages_2_8_google_forms.json
│   └── tesla_pages_2_8_google_summary.md
├── parsed_data_comparison/        # Traditional vs AI comparison
│   └── parsed_data_vs_google_ai_comparison.json
└── final_reports/                 # Comprehensive analysis
    └── lab7_comprehensive_report_20250924_150409.md
```

### 🎯 What Lab 7 Analyzes

**Document Content Detection:**
- **Text Extraction**: Full text with confidence scores
- **Table Recognition**: Advanced table detection and structure analysis
- **Named Entities**: Person names, organizations, dates, locations
- **Form Fields**: Key-value pairs and structured data
- **Layout Analysis**: Document structure and hierarchy

**Comparison Metrics:**
- **Text Similarity**: Character-level comparison with existing extractions
- **Table Count**: Number of tables detected by different methods
- **Processing Speed**: Performance benchmarks
- **Accuracy Assessment**: Quality metrics and confidence scores

### 📈 Sample Output

When you run Lab 7, you'll see output like:
```
INFO: Randomly selected pages: [2, 8] (1-indexed)
INFO: Google AI processing completed
INFO: Found:
  - Pages: 2
  - Tables: 4 
  - Entities: 2
  - Form Fields: 6
INFO: Workflow completed successfully!
Report: reports/google_ai/lab7_session_20250924_150404/final_reports/lab7_comprehensive_report_20250924_150409.md
```

### ⚠️ Important Notes

- **Page Limits**: Google Document AI has a 15-page limit for non-imageless mode
- **Random Pages**: The `--random` option selects different pages each time (use `--seed` for reproducibility)
- **Processing Time**: Typically 3-5 seconds for 2 pages
- **Credentials**: Ensure your Google Cloud credentials are properly configured

### 🔍 Recent Example Run

**Command Used:**
```bash
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2
```

**Pages Selected:** Pages 2 and 8 (randomly selected from 39 total pages)

**Results Found:**
- ✅ 2 pages processed successfully
- ✅ 4 tables detected and extracted to CSV files
- ✅ 2 named entities identified
- ✅ 6 form fields extracted
- ✅ Complete comparative analysis with existing parsed data
- ⚡ Total processing time: ~4.7 seconds

**Generated Report:** `reports/google_ai/lab7_session_20250924_150643/final_reports/lab7_comprehensive_report_20250924_150648.md`

---

## Usage Examples

**Run full pipeline:**

```bash
python3 run_complete_pipeline.py --out data/parsed --hybrid-tables --verbose
```

**Run individual labs:**

```bash
python3 src/text/extract_text.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/tables/extract_tables.py --in data/raw/your_file.pdf --out data/parsed/ --hybrid
python3 src/layout/extract_layout.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/docling/extract_docling.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/metadata/extract_metadata.py --in data/raw/your_file.pdf --out data/parsed/
python3 src/formats/convert_formats.py --in data/parsed/metadata/doc.jsonl --out data/parsed/
```

**Lab 7 (Google Document AI Integration):**

```bash
# 🎯 RECOMMENDED: Process 2 random pages for quick AI analysis
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2

# Process specific pages if you need particular sections
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12

# Use seed for reproducible random selection
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 3 --seed 42
```

---

## Output Structure

**Pipeline results:**

```
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
```

**Lab 7 AI results (optional):**

```
reports/google_ai/lab7_session_<timestamp>/
├── temp_pdfs/
├── raw_google_ai_results/
├── parsed_results/
├── parsed_data_comparison/
└── final_reports/
```

---

## Troubleshooting

* **Command not found:** Use `python3` and activate virtual environment
* **Module not found:** `pip install -r requirements.txt`
* **No PDFs found:** Ensure files exist in `data/raw/`
* **Permission denied:** `chmod +x run_complete_pipeline.py setup.sh`
* **Out of memory:** Close other apps, process smaller PDFs
* **Credentials issues:** Ensure `$GOOGLE_APPLICATION_CREDENTIALS` is set

**Monitor logs:**

```bash
tail -f pipeline_execution.log
tail -f lab7_execution.log
```

---

## Performance

* 100-page PDF: \~4–6 min, \~4GB RAM
* 2-page Lab 7 AI extraction: \~3–5 sec, \~2GB RAM
* High success rate and output quality
* Timestamped folders for traceability

---

## Team

**Team 5 – DAMG7245, Fall 2025**
Big Data Analytics Project – SEC Filing Processing Pipeline

**Lab 7 Contributors:**

* Google Document AI integration
* Page selection & processing
* AI analysis & reporting
* Security implementation
* Code quality & testing

---

## License

MIT License – see project files for details

---
