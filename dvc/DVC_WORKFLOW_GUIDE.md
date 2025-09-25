# DVC Pipeline Documentation
## LANTERN Project - Team 5 - DAMG7245 Fall 2025

This document provides comprehensive instructions for using DVC (Data Version Control) with the LANTERN pipeline project. The DVC setup enables reproducible data processing workflows, experiment tracking, and efficient collaboration.

## 🎯 Overview

Our DVC implementation provides:
- **Pipeline Management**: Automated execution of LANTERN pipeline (Labs 1-6) and Lab 7 Google AI integration
- **Metrics Tracking**: Standardized metrics collection and comparison across pipeline runs
- **Reproducibility**: Consistent execution environment and dependency tracking
- **Flexibility**: Multiple pipeline configurations for different use cases

## 📋 Table of Contents

1. [Quick Start](#quick-start)
2. [Pipeline Configurations](#pipeline-configurations)
3. [Running Pipelines](#running-pipelines)
4. [Metrics and Monitoring](#metrics-and-monitoring)
5. [Advanced Usage](#advanced-usage)
6. [Troubleshooting](#troubleshooting)

## 🚀 Quick Start

### Prerequisites
- Python 3.11+ with virtual environment activated
- Git repository initialized
- DVC installed (`pip install dvc`)

### Basic Workflow
```bash
# 1. Check pipeline status
dvc status

# 2. Run the complete pipeline
dvc repro

# 3. Check results
dvc metrics show

# 4. Compare with previous runs
dvc metrics diff
```

## ⚙️ Pipeline Configurations

Our DVC setup supports multiple pipeline configurations:

### 1. Separate Stages (Default)
Two independent stages that can be run separately or together:
- `full_pipeline`: Complete LANTERN processing (Labs 1-6)
- `lab7_processing`: Google Document AI integration

### 2. Full Pipeline Only
Just the LANTERN pipeline without Lab 7:
```bash
python dvc_pipeline_setup.py --mode full --write-config
```

### 3. Lab 7 Only
Only Google AI processing:
```bash
python dvc_pipeline_setup.py --mode lab7-only --write-config
```

### 4. Combined Pipeline
Single stage running both pipelines sequentially:
```bash
python dvc_pipeline_setup.py --mode full-with-lab7 --write-config
```

## 🔄 Running Pipelines

### Complete Pipeline Execution
```bash
# Run all stages
dvc repro

# Run specific stage only
dvc repro full_pipeline
dvc repro lab7_processing
```

### Pipeline Status
```bash
# Check what needs to be run
dvc status

# View pipeline structure
dvc dag

# Show pipeline details
dvc stage list
```

### Force Re-execution
```bash
# Force re-run all stages
dvc repro --force

# Force re-run specific stage
dvc repro --force full_pipeline
```

## 📊 Metrics and Monitoring

### Metrics Configuration
Our pipeline automatically tracks:
- **Pipeline Summary**: Processing statistics, file counts, execution times
- **Lab 7 Results**: Google AI processing metrics and comparisons

### Viewing Metrics
```bash
# Show current metrics
dvc metrics show

# Show metrics in JSON format
dvc metrics show --json

# Compare with previous commit
dvc metrics diff

# Compare with specific commit
dvc metrics diff HEAD~1
```

### Metrics Files Location
- **Full Pipeline**: `data/parsed/pipeline_summary_*.json`
- **Lab 7**: `reports/google_ai/*/parsed_results/summary*.json`

## 🛠️ Advanced Usage

### Custom Pipeline Configuration
```bash
# Create custom pipeline with specific parameters
python dvc_pipeline_setup.py \
  --mode separate \
  --output-dir custom_output \
  --pdf-file data/raw/custom.pdf \
  --pages "10 15" \
  --lab7-mode pages \
  --write-config
```

### Pipeline Parameters
- `--output-dir`: Custom output directory (default: `data/parsed`)
- `--pdf-file`: PDF file for Lab 7 processing (default: `data/raw/tesla.pdf`)
- `--pages`: Page range for Lab 7 (default: `"5 12"`)
- `--lab7-mode`: Processing mode - `pages`, `random`, or `all`
- `--hybrid-tables`: Enable hybrid table extraction (default: true)

### Metrics Management
```bash
# Set up metrics tracking for existing files
python dvc_metrics_setup.py --add-existing --create-config

# Show discovered metrics files
python dvc_metrics_setup.py --show-files

# Compare metrics between runs
python dvc_metrics_setup.py --compare

# Generate metrics summary script
python dvc_metrics_setup.py --create-generator
```

### Git Integration
```bash
# Commit pipeline changes
git add dvc.yaml dvc.lock
git commit -m "Update pipeline configuration"

# Track changes without committing outputs
git add dvc.yaml .dvc/ .dvcignore .gitignore
git commit -m "Update DVC configuration"
```

## 🏗️ Project Structure

```
├── dvc.yaml                    # DVC pipeline configuration
├── dvc_pipeline_setup.py       # Pipeline configuration script
├── dvc_metrics_setup.py        # Metrics management script
├── .dvc/                       # DVC internal files
├── .dvcignore                  # DVC ignore patterns
├── .gitignore                  # Git ignore patterns (includes DVC outputs)
├── data/
│   ├── raw/                    # Input data (Git-tracked)
│   └── parsed/                 # Pipeline outputs (DVC-managed)
├── reports/
│   └── google_ai/              # Lab 7 outputs (DVC-managed)
├── src/                        # Source code (dependencies)
└── google_ai/                  # Lab 7 source code
```

## 🔍 Troubleshooting

### Common Issues

#### Pipeline Fails to Start
```bash
# Check dependencies
dvc status

# Verify file paths
ls -la data/raw/
ls -la src/
```

#### Metrics Not Showing
```bash
# Ensure pipeline has run at least once
dvc repro

# Check metrics configuration
grep -A 5 "metrics:" dvc.yaml
```

#### Output Directories Missing
```bash
# Create required directories
mkdir -p data/parsed reports/google_ai

# Check .gitignore excludes outputs
cat .gitignore | grep -E "(parsed|reports)"
```

#### Permission Issues
```bash
# Make scripts executable
chmod +x dvc_pipeline_setup.py
chmod +x dvc_metrics_setup.py
```

### Debug Information
```bash
# Verbose DVC output
dvc repro --verbose

# Check DVC version
dvc version

# Validate dvc.yaml syntax
dvc stage list
```

## 🔄 Typical Workflow

### Daily Development
```bash
# 1. Check current status
dvc status

# 2. Run pipeline if changes detected
dvc repro

# 3. Review results
dvc metrics show

# 4. Compare with previous run
dvc metrics diff

# 5. Commit changes if satisfied
git add dvc.yaml dvc.lock
git commit -m "Pipeline run: $(date)"
```

### Adding New Data
```bash
# 1. Add new PDF to data/raw/
cp new_document.pdf data/raw/

# 2. Update pipeline configuration if needed
python dvc_pipeline_setup.py --pdf-file data/raw/new_document.pdf --write-config

# 3. Run pipeline
dvc repro

# 4. Commit configuration changes
git add dvc.yaml
git commit -m "Add processing for new_document.pdf"
```

### Experiment Tracking
```bash
# 1. Create experiment branch
git checkout -b experiment/new-feature

# 2. Modify pipeline configuration
python dvc_pipeline_setup.py --mode full-with-lab7 --pages "1 5" --write-config

# 3. Run experiment
dvc repro

# 4. Compare results
dvc metrics diff main

# 5. Merge if successful
git checkout main
git merge experiment/new-feature
```

## 📚 Additional Resources

- [DVC Documentation](https://dvc.org/doc)
- [DVC Tutorials](https://dvc.org/doc/tutorials)
- [Pipeline Configuration Reference](https://dvc.org/doc/user-guide/project-structure/dvcyaml-files)
- [Metrics Reference](https://dvc.org/doc/command-reference/metrics)

## 🤝 Contributing

When contributing to the pipeline:
1. Always test changes with `dvc repro`
2. Update metrics configuration if adding new outputs
3. Document any new parameters or modes
4. Commit both code changes and DVC configuration updates

---

**Team 5 - DAMG7245 Fall 2025**  
*Dynamic DVC Pipeline for LANTERN Project*