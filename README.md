# DAMG7245 Assignment-1: Complete PDF Processing Pipeline

**Team 5 – Big Data IA Fall 2025** | 
[![DVC Pipeline](https://img.shields.io/badge/DVC-Pipeline%20Ready-brightgreen.svg)](https://dvc.org) 
[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://www.python.org)
[![Tests](https://img.shields.io/badge/Tests-Passing-success.svg)](https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5)

## 🎯 **QUICK DEMO - One Command Per Component**
---

## **🎬 Demo Links**

- **CodedLab Demo**: (https://codelabs-preview.appspot.com/?file_id=1JBeq54zlgnJY6900jnok6JHRmja4hB-EeP6qXQKRBe8#0)
- **YouTube Demo**: (https://youtu.be/_xDNnss3a0c)
### **📋 Presentation Flow**: Complete Pipeline → Lab 7 → DVC → Lab 11

```bash
# SETUP (One Time Only)
git clone https://github.com/Big-Data-IA-Team-5/Assignment-1---DAMG7245-Team-5.git
cd Assignment-1---DAMG7245-Team-5
python3 setup/smart_setup.py && source setup/.venv/bin/activate

# PART 1: Complete Pipeline Demo (Labs 1-6)
python3 run_complete_pipeline.py --out demo_output

# PART 2: Lab 7 - Google AI vs Open Source  
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2

# PART 3: DVC Pipeline & CI/CD (MAIN FOCUS)
dvc repro  # Complete reproducible pipeline

# PART 4: Lab 11 - XBRL Integration
python3 src/xbrl/lab11_xbrl.py --pdf data/raw/tesla.pdf
```

## **Expected Results**
- **Pipeline**: 21,287+ metadata records, 3 output formats (JSON 11.7MB, MD 830KB, TXT 517KB)
- **Lab 7**: AI vs open-source comparison analysis
- **DVC**: 5-stage pipeline (parse→tables→layout→docling→export) with full reproducibility  
- **Lab 11**: XBRL financial data validation and cross-verification

---

## **Table of Contents**

* [Quick Demo](#quick-demo---one-command-per-component)
* [Complete Pipeline (Labs 1-6)](#complete-pipeline-labs-1-6)
* [Lab 7: Google AI Integration](#lab-7-google-ai-integration)
* [DVC Pipeline & CI/CD](#dvc-pipeline--cicd)
* [Lab 11: XBRL Integration](#lab-11-xbrl-integration)
* [Setup & Requirements](#setup--requirements)
* [Output Structure](#output-structure)
* [Testing & Validation](#testing--validation)
* [Team](#team)

---

## **Complete Pipeline (Labs 1-6)**

### **What It Does**: End-to-End PDF Processing with 6 Extraction Methods
**Demo Time**: 3-5 minutes | **One Command Execution**

```bash
# Complete integrated pipeline
python3 run_complete_pipeline.py

# View results
ls -la data/parsed/ && find data/parsed/ -name "*.md" | head -1 | xargs cat
```

### **Pipeline Components**:
| Lab | Method | Output | Performance |
|-----|--------|--------|-------------|
| Lab 1 | **Text Extraction** | 39 pages processed | pdfplumber + OCR fallback |
| Lab 2 | **Table Extraction** | 28 tables found | Camelot + pdfplumber hybrid |
| Lab 3 | **Layout Detection** | 1,855 blocks detected | LayoutParser (1,733 text + 45 table + 77 title) |
| Lab 4 | **Docling AI** | 46 tables detected | Advanced AI processing (87 seconds) |
| Lab 5 | **Metadata Integration** | 21,287 total records | All extraction methods combined |
| Lab 6 | **Format Conversion** | JSON/MD/TXT outputs | Multiple format exports |

**Key Results**: 
- **Scale**: 21,287+ metadata records from multiple extraction methods
- **Formats**: JSON (11.7MB), Markdown (830KB), TXT (517KB) 
- **Speed**: Complete pipeline in ~2 minutes

---

## **Lab 7: Google AI Integration**

### **What It Does**: AI-Powered Document Intelligence Comparison
**Demo Time**: 4-6 minutes | **Google Cloud Document AI**

```bash
# Run Google AI document processing
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2

# View comparison analysis
cat Lab7_GoogleAI_vs_OpenSource_Comparison_Report.md
```

### **Key Features**:
- **Google Document AI**: Advanced OCR and layout understanding
- **Performance Comparison**: Speed, accuracy, cost analysis  
- **Multi-Modal Processing**: Text + images + tables + forms
- **Business Insights**: When to use AI vs open-source tools

**Prerequisites**: Google Cloud credentials in `credentials/google-credentials.json`

---

## **DVC Pipeline & CI/CD**

### **What It Does**: Data Version Control & Reproducible ML Pipeline
**Demo Time**: 6-8 minutes | **MAIN PRESENTATION FOCUS**

### **Quick Verification**:
```bash
# Check DVC is ready
dvc --version && dvc dag --ascii
```

### **Core Demo Commands**:

#### **🔄 Run Complete Pipeline**:
```bash
# Execute full reproducible pipeline
dvc repro

# Check execution status  
dvc status && python3 scripts/check_data_versioning.py
```

#### **🧪 Testing & CI/CD**:
```bash
# Run smoke tests locally
python3 tests/test_dvc_pipeline.py

# Show GitHub Actions workflow
cat .github/workflows/dvc-smoke-test.yml
```

### **Pipeline Architecture**:
```
Raw PDF → Parse (39 pages) → Tables (28 tables) → Layout (1,855 blocks) 
       → Docling (46 tables) → Export (21,287 records) → 3 Output Formats
```

### **DVC Checkpoints Completed**:
- **Working DVC pipeline** that reproduces parsed outputs from raw PDFs
- **Data and model artifacts** are stored and versioned  
- **GitHub Actions workflow** runs smoke test on every pull request
- **Git preserves data lineage** via dvc.lock and .dvc files

### **Key Advantages**:
- **Reproducibility**: Exact same outputs every time via `dvc.lock`
- **Version Control**: Git tracks pipeline config, DVC tracks data
- **CI/CD Integration**: Automatic testing on every PR
- **Data Lineage**: Complete audit trail of data transformations
- **Caching**: Only changed stages rerun (80-85% efficiency)

---

## **Lab 11: XBRL Integration**

### **What It Does**: Financial Document Analysis & Validation  
**Demo Time**: 3-4 minutes | **SEC Filing Intelligence**

```bash
# Run XBRL mapping and validation
python3 src/xbrl/lab11_xbrl.py --pdf data/raw/tesla.pdf

# View results
cat Lab11_XBRL_Mapping_Analysis.md && ls reports/xbrl/
```

### **Key Features**:
- **Financial Intelligence**: SEC filing analysis
- **XBRL Mapping**: Connect extracted data to financial taxonomies
- **Validation Pipeline**: Ensure compliance with reporting standards  
- **Cross-Verification**: PDF content vs XBRL structured data

---

## **Setup & Requirements**

### **System Requirements**:
- **Python**: 3.11+ (recommended)
- **RAM**: 4GB minimum (8GB+ for large PDFs)
- **OS**: Windows/macOS/Linux

### **One-Command Setup**:
```bash
# Smart cross-platform setup
python3 setup/smart_setup.py && source setup/.venv/bin/activate

# Verify installation
python3 setup/verify_setup.py
```

### **Manual Setup** (if needed):
```bash
python3 -m venv setup/.venv
source setup/.venv/bin/activate  # Windows: setup\.venv\Scripts\activate
pip install -r requirements.txt
```

---

## **Output Structure**

### **Complete Pipeline Outputs**:
```
data/parsed/                       # Integrated pipeline results
├── tesla_[timestamp]/             # Timestamped output directory
│   ├── text/                      # Text extraction results
│   ├── tables/                    # Table extraction results
│   ├── layout/                    # Layout detection results
│   ├── docling/                   # Docling processing results
│   ├── metadata/                  # Metadata integration
│   └── formats/                   # Multi-format outputs

data/intermediate/                 # DVC pipeline stages
├── text/         # Lab 1: Text extraction (39 pages)
├── tables/       # Lab 2: Table extraction (28 tables)  
├── layout/       # Lab 3: Layout detection (1,855 blocks)
├── docling/      # Lab 4: Docling AI (46 tables)
├── metadata/     # Lab 5: Metadata integration (21,287 records)
└── formats/      # Lab 6: Format conversion (JSON/MD/TXT)

reports/                          # Analysis reports
├── google_ai/    # Lab 7: Google AI comparison
└── xbrl/         # Lab 11: XBRL validation

.github/workflows/                # CI/CD configuration
└── dvc-smoke-test.yml            # Automated testing
```

---

## **Testing & Validation**

### **Automated Testing**:
```bash
# Run comprehensive smoke tests
python3 tests/test_dvc_pipeline.py

# Check data versioning status  
python3 scripts/check_data_versioning.py

# Verify DVC pipeline integrity
dvc dag --ascii && dvc status
```

### **CI/CD Pipeline**:
- ✅ **GitHub Actions**: Automated testing on every PR
- ✅ **Smoke Tests**: Validate pipeline structure and outputs
- ✅ **Data Versioning**: Track all artifacts with DVC
- ✅ **Reproducibility**: Ensure consistent results across environments

### **Performance Metrics**:
- **Processing Speed**: ~2 minutes for complete pipeline
- **Memory Usage**: ~4GB RAM for typical PDFs
- **Cache Efficiency**: 80-85% stage skip on reruns
- **Test Coverage**: 6 comprehensive validation methods

---

## 🎯 **Quick Commands Reference**

### **Essential Demo Commands**:
```bash
# Setup & Activation
source setup/.venv/bin/activate

# Complete Pipeline Demo  
python3 run_complete_pipeline.py --out demo_output --hybrid-tables

# DVC Pipeline Execution
dvc repro

# Testing & Validation
python3 tests/test_dvc_pipeline.py

# Individual Components
python3 google_ai/run_lab7.py --pdf data/raw/tesla.pdf --random 2    # Lab 7
python3 src/xbrl/lab11_xbrl.py --pdf data/raw/tesla.pdf             # Lab 11
```

### **Presentation Flow Timing**:
- **Setup**: 30 seconds
- **Pipeline Demo**: 4 minutes  
- **DVC & CI/CD**: 7 minutes ⭐ (Main focus)
- **Lab 7 & 11**: 5 minutes
- **Q&A**: 5 minutes

---

## **Team**

**Team 5 – DAMG7245 Big Data Analytics (Fall 2025)**  
*SEC Filing Processing Pipeline with DVC Integration*

**Project Focus**: Data Version Control, Reproducible ML Pipelines, CI/CD Integration

---

## **Additional Resources**

- **[PRESENTATION_GUIDE.md](PRESENTATION_GUIDE.md)**: Complete presentation walkthrough
- **[DVC_WORKFLOW_GUIDE.md](DVC_WORKFLOW_GUIDE.md)**: Detailed DVC documentation  
- **[GOOGLE_CLOUD_SETUP.md](GOOGLE_CLOUD_SETUP.md)**: Lab 7 configuration
- **[XBRL_INTEGRATION_GUIDE.md](XBRL_INTEGRATION_GUIDE.md)**: Lab 11 setup

---

## **Project Highlights**

- **21,287+ metadata records** from comprehensive extraction
- **5-stage DVC pipeline** with full reproducibility
- **Automated CI/CD testing** via GitHub Actions  
- **Multi-format outputs** (JSON/Markdown/TXT)
- **Enterprise-grade** data versioning and lineage

---

*Ready to demonstrate advanced data engineering with DVC!*
