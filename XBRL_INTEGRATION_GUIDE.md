# Lab 11: XBRL Cross-Verification System

## Overview

Lab 11 integrates **XBRL cross-verification** into Project LANTERN, providing authoritative validation of PDF table extractions against standardized XBRL filings. This ensures data accuracy and identifies potential discrepancies in financial data processing.

## 🎯 Key Features

- **📄 XBRL Parsing**: Extract financial data from XBRL filings using the `arelle` library
- **🔗 Intelligent Mapping**: Fuzzy matching between PDF table labels and XBRL concepts
- **⚖️ Cross-Verification**: Compare PDF extractions against authoritative XBRL data
- **📊 Comprehensive Reporting**: Generate detailed validation reports with recommendations
- **🔄 DVC Integration**: Fully reproducible validation pipeline

## 🚀 Quick Start

### 1. Install Dependencies
```bash
pip install arelle fuzzywuzzy python-Levenshtein
```

### 2. Place XBRL Files
Put your XBRL files in:
```
data/raw/xbrl/
├── TSLA_2023_10K.xml
├── AAPL_2023_Q4.xbrl
└── MSFT_2024_10Q.htm
```

### 3. Run Validation
```bash
# Basic validation
python src/xbrl/lab11_xbrl.py --tables data/intermediate/tables --xbrl data/raw/xbrl

# Using configuration file
python src/xbrl/lab11_xbrl.py --config configs/xbrl_config.yaml

# Using DVC pipeline
dvc repro xbrl_validation
```

## 📁 Directory Structure

```
src/xbrl/
├── __init__.py              # Module initialization
├── parse_xbrl.py           # XBRL parsing functionality
├── map_pdf_to_xbrl.py      # PDF-to-XBRL mapping system
├── validate_xbrl.py        # Cross-verification engine
├── report_xbrl.py          # Comprehensive reporting
└── lab11_xbrl.py           # Main entry point

data/
├── raw/xbrl/               # XBRL files input directory
├── intermediate/
│   ├── tables/            # PDF table extractions (from Lab 2)
│   └── xbrl_validation/   # Validation processing data
└── reports/xbrl/          # Generated validation reports

configs/
└── xbrl_config.yaml       # XBRL validation configuration
```

## 🔧 Configuration

Edit `configs/xbrl_config.yaml` to customize:

```yaml
# Validation tolerances
validator:
  numeric_tolerance: 0.01      # $0.01 tolerance
  percentage_tolerance: 0.001  # 0.1% tolerance
  
# Fuzzy matching settings
mapper:
  fuzzy_threshold: 80         # 80% confidence minimum
  
# Custom mappings for company-specific terms
custom_mappings:
  "total revenue": "Revenues"
  "net earnings": "NetIncomeLoss"
```

## 📋 Workflow Steps

### 1. **XBRL Parsing**
- Loads XBRL files from `data/raw/xbrl/`
- Extracts key financial concepts (Revenue, Assets, etc.)
- Converts to structured DataFrames

### 2. **Label Mapping**
- Maps PDF table headers to XBRL concepts
- Uses fuzzy string matching with predefined rules
- Handles synonyms and company-specific terminology

### 3. **Cross-Verification**
- Compares PDF values against XBRL facts
- Applies configurable tolerance thresholds
- Detects scale factor mismatches (thousands vs. millions)

### 4. **Report Generation**
- Creates comprehensive Markdown and JSON reports
- Categorizes discrepancies by severity (Critical, Moderate, Minor)
- Provides actionable recommendations

## 📊 Sample Output

### Executive Summary
```
✅ Validation Status: PASS
📊 Total Discrepancies: 3
🔴 Critical Issues: 0
🟡 Moderate Issues: 2  
🟢 Minor Issues: 1
```

### Detailed Analysis
| PDF Label | XBRL Concept | PDF Value | XBRL Value | Difference | Status |
|-----------|--------------|-----------|------------|------------|--------|
| Net Revenue | Revenues | $1,000,000 | $1,000,100 | 0.01% | Minor |
| Total Assets | Assets | $5,000 | $5,000,000 | Scale Issue | Moderate |

## 🔍 Discrepancy Categories

- **🔴 Critical**: Large value mismatches requiring immediate attention
- **🟡 Moderate**: Scale mismatches or moderate differences  
- **🟢 Minor**: Small differences within acceptable bounds
- **📊 Missing Data**: Values not found in PDF or XBRL
- **🔗 Unmapped**: PDF labels without XBRL concept mapping
- **⚠️ Errors**: Technical processing issues

## 🛠 Advanced Usage

### Custom Mapping Rules
```python
# Add custom mappings in your script
mapper = PDFXBRLMapper()
mapper.add_custom_mapping("company revenue", "Revenues")
```

### Programmatic Access
```python
from src.xbrl.lab11_xbrl import Lab11XBRLWorkflow

# Initialize workflow
workflow = Lab11XBRLWorkflow()

# Run validation
results = workflow.run_full_workflow(
    tables_dir="data/intermediate/tables",
    xbrl_dir="data/raw/xbrl"
)

# Access results
print(f"Total discrepancies: {results['total_discrepancies']}")
```

### Batch Processing
```bash
# Process multiple companies
for company in TSLA AAPL MSFT; do
    python src/xbrl/lab11_xbrl.py \\
        --tables "data/intermediate/tables/${company}" \\
        --xbrl "data/raw/xbrl/${company}" \\
        --output "reports/xbrl/${company}"
done
```

## 🔄 Integration with LANTERN Pipeline

### DVC Pipeline Integration
```bash
# Run complete pipeline including XBRL validation
dvc repro

# Run only XBRL validation stage
dvc repro xbrl_validation

# Check pipeline status
dvc dag
```

### After Lab 2 (Tables)
XBRL validation automatically processes table extraction results:
```bash
# Tables extracted → XBRL validation ready
dvc repro tables      # Extract PDF tables
dvc repro xbrl_validation  # Validate against XBRL
```

## 📈 Quality Assurance

### Tolerance Configuration
- **Numeric Tolerance**: Absolute difference threshold ($0.01)
- **Percentage Tolerance**: Relative difference threshold (0.1%)
- **Scale Detection**: Automatic thousands/millions/billions detection

### Validation Levels
1. **Exact Match**: Direct value comparison
2. **Tolerance Match**: Within configured thresholds  
3. **Scale Match**: After scale factor adjustment
4. **No Match**: Significant discrepancy requiring review

## 🚨 Common Issues & Solutions

### Issue: "arelle library not found"
```bash
pip install arelle
# or
conda install -c conda-forge arelle
```

### Issue: "No XBRL files found"
- Ensure XBRL files are in `data/raw/xbrl/`
- Supported formats: `.xml`, `.xbrl`, `.htm`
- Check file permissions and accessibility

### Issue: "High number of unmapped labels"
- Review and enhance custom mappings in config
- Lower fuzzy matching threshold for more matches
- Add company-specific terminology to mapping rules

### Issue: "Scale factor mismatches"
- Common when PDF shows "thousands" but XBRL has actual amounts
- System automatically detects and reports these
- Review unit specifications in source documents

## 🔧 Troubleshooting

### Enable Debug Logging
```bash
python src/xbrl/lab11_xbrl.py --verbose --tables data/intermediate/tables --xbrl data/raw/xbrl
```

### Check File Formats
```bash
# Verify XBRL file validity
python -c "from src.xbrl.parse_xbrl import XBRLParser; p=XBRLParser(); p.parse_xbrl_file('data/raw/xbrl/test.xml')"
```

### Validate Configuration
```bash
# Test configuration file
python -c "import yaml; print(yaml.safe_load(open('configs/xbrl_config.yaml')))"
```

## 📚 Technical Details

### Dependencies
- **arelle**: XBRL processing and validation
- **fuzzywuzzy**: Fuzzy string matching for label mapping
- **python-Levenshtein**: Fast string distance calculations
- **pandas/numpy**: Data manipulation and analysis

### Performance Considerations
- XBRL parsing can be memory-intensive for large filings
- Fuzzy matching scales linearly with label count
- Consider parallel processing for multiple files
- Memory usage configurable in `xbrl_config.yaml`

### Supported XBRL Formats
- **XML**: Standard XBRL instance documents (`.xml`, `.xbrl`)
- **HTML**: XBRL embedded in HTML format (`.htm`, `.html`)
- **Inline XBRL**: XBRL data within HTML documents

## 🤝 Contributing

### Adding New Financial Concepts
1. Edit `key_concepts` in `configs/xbrl_config.yaml`
2. Add corresponding mappings in `custom_mappings`
3. Test with sample XBRL files

### Improving Fuzzy Matching
1. Enhance preprocessing patterns in `map_pdf_to_xbrl.py`
2. Add synonym mappings for financial terms
3. Adjust fuzzy matching parameters

### Custom Validation Rules
1. Extend validation logic in `validate_xbrl.py`
2. Add new discrepancy categories as needed
3. Update reporting templates accordingly

---

## 📞 Support

For issues or questions:
1. Check the logs in `logs/lab11_xbrl.log`
2. Review configuration in `configs/xbrl_config.yaml`
3. Ensure all dependencies are properly installed
4. Verify XBRL file formats and accessibility

**Lab 11 XBRL Cross-Verification** ensures the highest level of data accuracy by validating PDF extractions against authoritative XBRL filings. This provides confidence in your financial data processing pipeline and identifies areas for improvement.