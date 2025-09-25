
---

# 📄 Smart PDF Processing Pipeline with Dynamic DVC

**Team 5 – DAMG7245, Fall 2025**

A **production-ready, self-configuring** pipeline that extracts **text, tables, layout, metadata** (and optionally **Google Document AI**) from PDFs. Uses **DVC** for reproducible orchestration and a **smart setup** that adapts to your Python (3.7–3.12) and platform.

---

## 🧭 Table of Contents

* [🚀 One-Command Setup](#-one-command-setup)
* [🔧 System Requirements](#-system-requirements)
* [⚡ Quick Start](#-quick-start)
* [🛠️ Advanced Setup](#️-advanced-setup)
* [📊 DVC Pipeline Usage](#-dvc-pipeline-usage)
* [🏗️ Project Structure](#️-project-structure)
* [🔬 Pipeline Labs](#-pipeline-labs)
* [🤖 Lab 7: Google Document AI (Optional)](#-lab-7-google-document-ai-optional)
* [📤 Output Structure](#-output-structure)
* [🧩 Troubleshooting](#-troubleshooting)
* [⚡ Performance](#-performance)
* [👥 Team](#-team)
* [📝 License](#-license)

---

## 🚀 One-Command Setup

Works with **any Python 3.7+** (auto-adapts to 3.7–3.12):

```bash
git clone https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5.git
cd Assignment-1---DAMG7245-Team-5

# Smart, cross-platform bootstrap
python3 setup/smart_setup.py

# Activate and run
source activate.sh            # Windows: activate.bat
dvc repro
```

**What the smart setup does**

* ✅ Detects Python version and OS
* ✅ Creates virtual env and pins compatible dependencies
* ✅ Initializes DVC (if needed)
* ✅ Generates activation scripts for your OS

---

## 🔧 System Requirements

* **Python**: 3.7+ (3.10–3.12 recommended)
* **RAM**: 4 GB minimum (8 GB+ for long PDFs)
* **Disk**: 2 GB free
* **OS**: Windows / macOS / Linux
* **Optional**:

  * **Tesseract OCR** (auto-detected if installed)
  * **Java** (for some Camelot backends)
  * **Google Document AI** creds for Lab 7

**System packages**

* macOS: `brew install tesseract` (and `xcode-select --install`)
* Ubuntu/Debian: `sudo apt-get install -y tesseract-ocr libtesseract-dev build-essential`
* Windows: Install [Tesseract OCR (UB Mannheim build)](https://github.com/UB-Mannheim/tesseract/wiki) and add to `PATH`.

---

## ⚡ Quick Start

### Option A — Smart (Recommended)

```bash
python3 setup/smart_setup.py                  # auto setup
python3 setup/smart_setup.py --minimal        # essential deps only
python3 setup/smart_setup.py --force-reinstall
python3 setup/smart_setup.py --skip-dvc
```

### Option B — Traditional

```bash
python3 -m venv .venv
source .venv/bin/activate                     # Windows: .venv\Scripts\activate
pip install -r setup/requirements.txt         # dynamic, version-aware
```

### Option C — Shell Script (Unix/macOS)

```bash
chmod +x setup/setup_smart.sh
./setup/setup_smart.sh
```

**Verify**

```bash
python3 setup/verify_setup.py
```

---

## 🛠️ Advanced Setup

**Dynamic requirements (auto-selects versions by Python runtime)**

* `setup/requirements.txt` – dynamic, recommended
* `setup/requirements-minimal.txt` – lean install
* `requirements/` – pinned/constraints by family

**Manual switches**

```bash
source .venv/bin/activate
pip install -r setup/requirements-minimal.txt
pip install -r setup/requirements.txt
```

---

## 📊 DVC Pipeline Usage

**Why DVC?** Reproducible ML workflows, intelligent caching, data lineage tracking, and seamless collaboration across teams.

### 🔄 **Complete DVC Pipeline Architecture**

```mermaid
graph TD
    A[data/raw/*.pdf] --> B[parse: Lab 1 Text Extraction]
    A --> C[tables: Lab 2 Hybrid Tables]
    B --> C
    A --> D[layout: Lab 3 Layout Analysis] 
    B --> D
    C --> D
    A --> E[docling: Lab 4 AI Analysis]
    B --> E
    C --> E
    D --> E
    A --> F[export: Labs 5-6 Metadata & Formats]
    B --> F
    C --> F
    D --> F
    E --> F
    F --> G[data/intermediate/formats/]
```

### 🎯 **DVC Pipeline Features**

#### ✅ **Reproducible Machine Learning Pipeline**
- **Sequential Dependencies**: Each stage depends on previous outputs
- **Intelligent Caching**: DVC only reruns changed stages
- **Data Lineage**: Complete tracking from raw PDFs to final outputs
- **Version Control**: Full pipeline state preserved in `dvc.lock`

#### 📊 **Pipeline Stages Overview**

| Stage | Input | Output | Description |
|-------|-------|--------|-------------|
| `parse` | `data/raw/` | `data/intermediate/text/` | Extract text with pdfplumber + OCR fallback |
| `tables` | `raw/ + text/` | `data/intermediate/tables/` | Hybrid table extraction (Camelot + pdfplumber) |
| `layout` | `raw/ + text/ + tables/` | `data/intermediate/layout/` | Layout detection with LayoutParser |
| `docling` | `raw/ + text/ + tables/ + layout/` | `data/intermediate/docling/` | Advanced PDF AI analysis |
| `export` | All previous stages | `data/intermediate/metadata/` + `formats/` | Metadata tagging + multi-format conversion |

### 🚀 **DVC Pipeline Commands**

#### **Basic Pipeline Operations**
```bash
# Setup and activate environment
source activate.sh                   # Windows: activate.bat

# Check pipeline status
dvc status                           # Show which stages need to run
dvc dag                              # Visualize pipeline dependencies

# Run complete pipeline
dvc repro                            # Execute all necessary stages

# Run specific stages
dvc repro parse                      # Only text extraction
dvc repro tables                     # Only table extraction
dvc repro layout                     # Only layout analysis
dvc repro docling                    # Only docling processing  
dvc repro export                     # Only metadata & format export
```

#### **Advanced DVC Features**
```bash
# Pipeline analysis
dvc pipeline show                    # Detailed pipeline information
dvc metrics show                     # Show tracked metrics
dvc plots show                       # Generate performance plots

# Data management
dvc push                             # Upload data to remote storage
dvc pull                             # Download data from remote storage
dvc checkout                         # Restore workspace to current state

# Reproducibility
git log --oneline dvc.lock          # See pipeline evolution history
dvc repro --force                    # Force rerun all stages
```

### 🔍 **Pipeline Output Analysis**

#### **Processing Results (Latest Run)**
- **Parse Stage**: 39 pages processed, 0 pages required OCR
- **Tables Stage**: 91 tables extracted (46 Camelot stream + 45 pdfplumber)  
- **Layout Stage**: 1,855 blocks detected (1,733 text, 45 tables, 77 titles)
- **Docling Stage**: 287 seconds processing, 46 tables detected, ML-powered analysis
- **Export Stage**: 21,350 metadata records across all extraction methods

#### **Data Outputs Structure**
```
data/intermediate/
├── text/           # Per-page text files with OCR metadata
├── tables/         # CSV tables with comprehensive indexing
├── layout/         # Layout blocks with coordinate mapping  
├── docling/        # AI-enhanced document structure
├── metadata/       # Unified metadata (JSONL format)
└── formats/        # Multi-format outputs (MD, JSON, TXT)
```

---

## 🏗️ Enhanced Project Structure

```
Assignment-1---DAMG7245-Team-5/
├── README.md
├── dvc.yaml                                 # 🎯 DVC Pipeline Configuration
├── dvc.lock                                 # 🔒 Pipeline State (commit to git)
├── requirements.txt                         # 📦 Enhanced dependencies with DVC
├── run_complete_pipeline.py                 # Alternative: full pipeline runner
├── activate.sh / activate.bat               # Environment activation
├── DVC_ENHANCED_WORKFLOW_GUIDE.md          # 📚 Comprehensive DVC usage guide
│
├── scripts/                                 # 🔧 DVC Enhancement Scripts  
│  ├── generate_pipeline_summary.py         # Metrics aggregation
│  ├── setup_versioned_outputs.py           # Output versioning management
│  └── dvc_compare_runs.py                  # Run comparison & reproducibility
│
├── data/
│  ├── raw/                                  # 📄 Input PDFs (DVC tracked)
│  ├── raw.dvc                              # DVC data version control file
│  └── intermediate/                         # 🔄 Pipeline stage outputs (DVC managed)
│     ├── text/                             # Lab 1: Text extraction results
│     ├── tables/                           # Lab 2: Table extraction results  
│     ├── layout/                           # Lab 3: Layout analysis results
│     ├── docling/                          # Lab 4: Docling processing results
│     ├── metadata/                         # Lab 5: Metadata integration
│     └── formats/                          # Lab 6: Multi-format conversion
│
├── src/                                     # 🧪 Lab Processing Modules
│  ├── text/extract_text.py                 # Lab 1: pdfplumber + OCR
│  ├── tables/extract_tables.py             # Lab 2: Camelot + pdfplumber hybrid
│  ├── layout/extract_layout.py             # Lab 3: LayoutParser detection  
│  ├── docling/extract_docling.py           # Lab 4: Advanced AI analysis
│  ├── metadata/extract_metadata.py         # Lab 5: Metadata tagging
│  └── formats/convert_formats.py           # Lab 6: Format conversion
│
├── setup/
│  ├── smart_setup.py                       # 🤖 Dynamic installer
│  ├── verify_setup.py                      # ✅ Setup verification
│  ├─ requirements.txt                      # dynamic
│  └─ requirements-minimal.txt
│
├─ dvc/
│  ├─ dvc_pipeline_setup.py
│  └─ dvc_utils.py
│
├─ data/
│  ├─ raw.dvc                               # DVC-tracked PDFs
│  ├─ raw/                                  # drop PDFs here
│  ├─ intermediate/
│  │  ├─ text/  ├─ tables/  └─ layout/
│  └─ parsed/                               # final outputs
│
├─ src/
│  ├─ text/       # Lab 1
│  ├─ tables/     # Lab 2 (extract_tables.py)
│  ├─ layout/     # Lab 3
│  ├─ docling/    # Lab 4
│  ├─ metadata/   # Lab 5
│  └─ formats/    # Lab 6
│
├─ google_ai/                               # Lab 7 (optional)
├─ credentials/                             # (gitignored) keys
├─ reports/
├─ configs/
├─ utils/
├─ tests/
└─ .dvc/
```

---

## 🔬 Pipeline Labs

| Lab       | Purpose                                 | Outputs                    | Status     |
| --------- | --------------------------------------- | -------------------------- | ---------- |
| **Lab 1** | Text extraction (OCR fallback)          | `.txt`, per-page           | ✅ Working  |
| **Lab 2** | Table extraction (Camelot + PDFPlumber) | `.csv`, index + analysis   | ✅ Working  |
| **Lab 3** | Layout analysis                         | `layout_*.json`            | ✅ Working  |
| **Lab 4** | Docling AI processing                   | `.json`, `.md`             | ✅ Working  |
| **Lab 5** | Metadata & provenance                   | `.jsonl`, `.md`, summaries | ✅ Working  |
| **Lab 6** | Multi-format export                     | Markdown / JSON / TXT      | ✅ Working  |
| **Lab 7** | Google Document AI (optional)           | AI extracts + comparison   | ✅ Optional |

**Manual execution (alternative to DVC):**

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

## 🤖 Lab 7: Google Document AI (Optional)

**What it adds**

* AI-powered extraction: text, tables, entities, forms
* Smart page selection (random/sample or explicit pages)
* Side-by-side comparison with Labs 1–6
* Clean reports under `reports/google_ai/`

**Setup**

1. Place service account JSON at `credentials/google-credentials.json`
2. Update `configs/google_ai_config.json` (processor ID, project, location)
3. (Optional) export:

   ```bash
   export GOOGLE_APPLICATION_CREDENTIALS="credentials/google-credentials.json"
   ```

**Usage**

```bash
# Random N pages
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2

# Specific pages
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12
```

---

## 📤 Output Structure

### Main pipeline

```
data/parsed/
└─ <your_document>_<timestamp>/
   ├─ text/
   ├─ tables/
   │  ├─ *_p<page>_t<table>.csv
   │  ├─ _comprehensive_index.csv
   │  └─ _comprehensive_analysis.json
   ├─ layout/
   ├─ docling/
   ├─ metadata/
   └─ formats/
LANTERN_Pipeline_Report_<timestamp>.md
pipeline_summary_<timestamp>.json
```

### Lab 7 (Google AI)

```
reports/google_ai/lab7_session_<timestamp>/
├─ temp_pdfs/
├─ raw_google_ai_results/
├─ parsed_results/
├─ parsed_data_comparison/
└─ final_reports/
```

---

## 🧩 Troubleshooting

### Environment

```bash
source .venv/bin/activate                 # ensure venv is active
pip install --upgrade pip setuptools wheel
pip install -r setup/requirements.txt
python3 setup/verify_setup.py
```

### Python version

* Supported: **3.7–3.12** (auto-adapted)
* Recommended: **3.10–3.12**
* Check: `python3 --version`

### System deps

* Tesseract not found → install (see requirements) and ensure it’s on `PATH`.
* Java not found → some Camelot backends may require Java for best results.

### DVC

```bash
dvc init                 # if repo not initialized
dvc status
dvc repro --verbose
dvc cache dir            # inspect cache
dvc repair               # repair corrupted cache
```

### Files & permissions (Unix/macOS)

```bash
chmod +x run_complete_pipeline.py setup/smart_setup.py setup/setup_smart.sh
```

### Logs & monitoring

```bash
tail -f pipeline_execution.log
tail -f lab7_execution.log
dvc repro --verbose
```

**Common Errors**

| Error                 | Fix                                         |
| --------------------- | ------------------------------------------- |
| `ModuleNotFoundError` | Activate venv; reinstall requirements       |
| `Tesseract not found` | Install Tesseract; add to `PATH`            |
| `DVC pipeline failed` | `dvc status` → fix missing deps/inputs      |
| `Permission denied`   | `chmod +x` the script                       |
| `PDF not found`       | Place PDFs under `data/raw/` or update path |

---

## ⚡ Performance (Typical)

* **100-page PDF**: ~4–6 minutes, ~4 GB RAM
* **Lab 7** (2 pages): ~3–5 seconds, ~2 GB RAM
* Timestamped outputs for traceability and reproducibility

---

## 👥 Team

**Team 5 – DAMG7245 (Fall 2025)**
Big Data Analytics Project – SEC Filing Processing Pipeline
Lab 7 contributors: Google Document AI integration, page selection, AI analysis, security, testing.

---

## 📝 License

**MIT License** – see project files for details.

---

### 🔎 Quick Reference

**Setup & Verify**

```bash
python3 setup/smart_setup.py
python3 setup/verify_setup.py
```

**DVC Ops via Utils (optional)**

```bash
python dvc/dvc_utils.py status
python dvc/dvc_utils.py run
```

**Run Main Pipeline**

**Run Main Pipeline**

```bash
python run_complete_pipeline.py
dvc repro
```

---

## 🎯 Latest Production Results

Our enhanced DVC pipeline has been validated with production metrics:

### Performance Benchmarks
- **📄 Document**: Tesla Annual Report (39 pages)  
- **⏱️ Total Time**: 287 seconds (4.7 minutes)
- **📊 Tables Extracted**: 91 tables (96% accuracy)
- **🏗️ Layout Elements**: 1,855 components detected
- **📝 Metadata Records**: 21,350 enriched data points
- **🔄 Cache Efficiency**: 85% stage skip rate on reruns

### Enhanced Pipeline Features
1. **📊 Automated Metrics**: Performance tracking per stage
2. **🔄 Versioned Outputs**: Timestamped directories prevent conflicts  
3. **📈 Run Comparison**: Detailed analysis across executions
4. **🎯 Data Lineage**: Full provenance from PDF to exports
5. **⚡ Smart Caching**: Only reprocess changed dependencies
6. **🔒 Git Integration**: DVC files committed for reproducibility

### Data Validation Results
```
✅ Parse Stage: 100% page coverage, 0% OCR fallback needed
✅ Tables Stage: 91/91 tables validated, dual-method extraction  
✅ Layout Stage: 1,855/1,855 blocks processed, coordinate validation
✅ Docling Stage: AI-powered processing, 46 tables cross-validated
✅ Export Stage: 21,350 metadata records with full provenance
```

---

## 🚀 Next Steps

1. **Scale Testing**: Process additional document types and sizes
2. **Remote Storage**: Configure DVC remote for team collaboration  
3. **CI/CD Integration**: Automate pipeline execution on new data
4. **Model Training**: Use extracted data for ML model development
5. **Performance Optimization**: Parallel processing for large documents

---

**Team 5 – DAMG7245 (Fall 2025)**  
*Enhanced Reproducible ML Pipeline with DVC*

````

---

