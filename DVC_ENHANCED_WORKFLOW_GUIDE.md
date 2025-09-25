# Enhanced DVC Pipeline Workflow Guide

## Overview
This enhanced DVC pipeline provides comprehensive versioning, metrics tracking, and reproducibility features for your machine learning workflow.

## Key Features Added

### 1. Versioned Outputs (Prevents Overlapping)
- Each pipeline run creates a timestamped output directory
- Previous run outputs are preserved for comparison
- Automatic archiving of old runs to save storage space

### 2. Comprehensive Metrics Tracking
- Stage-level metrics for each processing step
- Pipeline-wide performance summaries
- Cross-run comparison and trend analysis
- Reproducibility validation

### 3. Enhanced Pipeline Stages
```
data/raw → parse → tables → layout → docling → export → summary
```

Each stage now generates:
- Processing outputs (cached by DVC)
- Metrics files (for comparison)
- Performance statistics

## Usage Instructions

### Initial Setup
```bash
# Create a new versioned run
python3 scripts/setup_versioned_outputs.py --run-id $(date +%Y%m%d_%H%M%S)

# Export the run ID for this session
export DVC_RUN_ID=$(date +%Y%m%d_%H%M%S)
```

### Running the Pipeline
```bash
# Execute the complete pipeline
export PATH="/Users/pranavpatel/Library/Python/3.9/bin:$PATH"
dvc repro

# Check pipeline status
dvc status

# View pipeline dependencies
dvc dag
```

### Comparing Runs
```bash
# Compare two specific runs
python3 scripts/dvc_compare_runs.py --run1 20240925_143022 --run2 20240925_150145

# Compare current run with best previous run
python3 scripts/dvc_compare_runs.py --compare-with-best

# Generate reproducibility report
python3 scripts/dvc_compare_runs.py --reproducibility-report

# Show performance trends over time
python3 scripts/dvc_compare_runs.py --show-trends --last-n-runs 10
```

### Metrics Analysis
```bash
# View DVC metrics
dvc metrics show

# Compare metrics between commits/branches
dvc metrics diff

# Show metrics in table format
dvc metrics show --show-md

# Plot performance trends
dvc plots show metrics/pipeline_summary.json
```

### Managing Outputs
```bash
# List all pipeline runs
python3 scripts/setup_versioned_outputs.py --list-runs

# Archive old runs to save space
python3 scripts/setup_versioned_outputs.py --archive-old

# View current run registry
cat runs_registry.json | jq '.'
```

## File Structure After Enhancement

```
├── dvc.yaml                    # Enhanced pipeline configuration
├── dvc.lock                    # Execution state (commit to git)
├── metrics/                    # Current run metrics
│   ├── pipeline_summary.json
│   ├── parse_metrics.json
│   ├── tables_metrics.json
│   ├── layout_metrics.json
│   ├── docling_metrics.json
│   ├── metadata_metrics.json
│   └── formats_metrics.json
├── versioned_outputs/          # Timestamped run outputs
│   ├── run_20240925_143022/
│   ├── run_20240925_150145/
│   └── archived/               # Compressed old runs
├── runs_registry.json          # Complete run history
└── scripts/                    # Enhancement scripts
    ├── generate_pipeline_summary.py
    ├── setup_versioned_outputs.py
    └── dvc_compare_runs.py
```

## Reproducibility Workflow

### 1. Data Lineage Tracking
```bash
# Commit DVC files for data lineage
git add dvc.yaml dvc.lock data/raw.dvc
git commit -m "Pipeline configuration and data lineage"

# Push to preserve lineage
git push
```

### 2. Reproducing Results
```bash
# Reproduce exact run from git commit
git checkout <commit_hash>
dvc repro

# Compare with original results
python3 scripts/dvc_compare_runs.py --compare-with-best
```

### 3. Validating Consistency
```bash
# Run reproducibility report
python3 scripts/dvc_compare_runs.py --reproducibility-report

# This will show:
# - Cross-run consistency metrics
# - Performance stability analysis
# - Data drift detection
# - Quality assurance recommendations
```

## Advanced Features

### Pipeline Customization
You can modify `dvc.yaml` to:
- Add new processing stages
- Include custom parameters
- Configure different output formats
- Add experiment tracking

### Metrics Customization
Each script can be enhanced to track:
- Custom business metrics
- Model performance indicators
- Data quality scores
- Resource utilization stats

### Integration with MLOps Tools
The pipeline integrates with:
- MLflow for experiment tracking
- Weights & Biases for visualization
- TensorBoard for monitoring
- Custom dashboards via the metrics JSON files

## Best Practices

1. **Always run versioned outputs** for production pipelines
2. **Commit dvc.lock after successful runs** to preserve exact state
3. **Regular reproducibility validation** using comparison scripts
4. **Archive old runs periodically** to manage storage
5. **Use meaningful run IDs** for easier tracking
6. **Monitor metrics trends** to detect performance degradation

## Troubleshooting

### Pipeline Fails
```bash
# Check which stage failed
dvc status

# Re-run specific stage
dvc repro <stage_name>

# Debug with verbose output
dvc repro --verbose
```

### Metrics Issues
```bash
# Verify metrics files exist
ls -la metrics/

# Check metrics format
cat metrics/pipeline_summary.json | jq '.'

# Validate DVC metrics configuration
dvc metrics show --show-md
```

This enhanced pipeline provides production-ready ML workflow management with comprehensive tracking, comparison, and reproducibility features.