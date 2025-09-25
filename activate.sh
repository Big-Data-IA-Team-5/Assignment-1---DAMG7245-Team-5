#!/bin/bash
# Activation script for PDF Processing Pipeline
echo "Activating PDF Processing Pipeline Environment..."
source "/Users/pranavpatel/Downloads/Big_data_1.1/untitled folder/untitled folder/Assignment-1---DAMG7245-Team-5/.venv/bin/activate"
echo "Environment activated!"
echo "Project root: /Users/pranavpatel/Downloads/Big_data_1.1/untitled folder/untitled folder/Assignment-1---DAMG7245-Team-5"
echo "Python: $(python --version)"
echo ""
echo "Quick commands:"
echo "  dvc status              - Check pipeline status"
echo "  dvc repro              - Run full pipeline"
echo "  python run_complete_pipeline.py  - Alternative pipeline run"
echo "  python setup/verify_setup.py     - Verify setup"
echo "  python dvc/dvc_utils.py status   - DVC utilities"
