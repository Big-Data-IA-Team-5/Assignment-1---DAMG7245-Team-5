@echo off
REM Activation script for PDF Processing Pipeline
echo 🚀 Activating PDF Processing Pipeline Environment...
call "/Users/pranavpatel/Downloads/untitled folder 2/Assignment-1---DAMG7245-Team-5/setup/.venv\Scripts\activate.bat"
echo ✅ Environment activated!
echo 📂 Project root: /Users/pranavpatel/Downloads/untitled folder 2/Assignment-1---DAMG7245-Team-5/setup
python --version
echo.
echo Quick commands:
echo   dvc status              - Check pipeline status
echo   dvc repro              - Run full pipeline
echo   python run_complete_pipeline.py  - Alternative pipeline run
