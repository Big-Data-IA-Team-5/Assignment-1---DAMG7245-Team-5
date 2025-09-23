@echo off
REM Project LANTERN - Automatic Setup Script for Windows
REM This script sets up the complete Project LANTERN environment

echo.
echo 🚀 Project LANTERN - Automatic Setup for Windows
echo =============================================
echo.

REM Check Python installation
echo [INFO] Checking Python installation...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python not found. Please install Python 3.8+ from python.org
    pause
    exit /b 1
)

python -c "import sys; exit(0 if sys.version_info >= (3, 8) else 1)" >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python 3.8+ required. Please upgrade Python.
    pause
    exit /b 1
)

echo [SUCCESS] Python installation verified

REM Check for Visual C++ Build Tools
echo [INFO] Checking for Visual C++ Build Tools...
echo [WARNING] If you encounter compilation errors, install Visual C++ Build Tools
echo           Download from: https://visualstudio.microsoft.com/visual-cpp-build-tools/
echo.

REM Check for Tesseract
echo [INFO] Checking for Tesseract OCR...
tesseract --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Tesseract OCR not found. Please install from:
    echo           https://github.com/UB-Mannheim/tesseract/wiki
    echo           And add to PATH: C:\Program Files\Tesseract-OCR
    echo.
)

REM Create virtual environment
echo [INFO] Setting up virtual environment...
if exist .venv (
    echo [WARNING] Virtual environment already exists. Removing old one...
    rmdir /s /q .venv
)

python -m venv .venv
call .venv\Scripts\activate.bat

REM Upgrade pip
echo [INFO] Upgrading pip and core tools...
python -m pip install --upgrade pip setuptools wheel

REM Choose installation type
echo.
echo Choose installation type:
echo 1) Full installation (all features) - Recommended
echo 2) Minimal installation (basic features only)
echo 3) Development installation (includes dev tools)
echo.
set /p choice="Enter choice (1-3) [default: 1]: "
if "%choice%"=="" set choice=1

if "%choice%"=="1" (
    echo [INFO] Installing full dependencies...
    pip install -r requirements.txt
) else if "%choice%"=="2" (
    echo [INFO] Installing minimal dependencies...
    pip install -r requirements-minimal.txt
) else if "%choice%"=="3" (
    echo [INFO] Installing development dependencies...
    pip install -r requirements.txt
    if exist requirements-dev.txt (
        pip install -r requirements-dev.txt
    )
) else (
    echo [ERROR] Invalid choice. Using full installation.
    pip install -r requirements.txt
)

if %errorlevel% neq 0 (
    echo [ERROR] Dependency installation failed.
    echo [INFO] Try using pre-built wheels: pip install --only-binary=all -r requirements.txt
    pause
    exit /b 1
)

echo [SUCCESS] Dependencies installed successfully

REM Setup directories
echo [INFO] Setting up directory structure...
if not exist "data\raw" mkdir "data\raw"
if not exist "data\parsed" mkdir "data\parsed"
echo [SUCCESS] Directory structure created

REM Verify installation
echo [INFO] Verifying installation...
python -c "import pdfplumber, pandas, numpy, camelot; print('✅ Core dependencies working')"
if %errorlevel% neq 0 (
    echo [ERROR] Core dependencies verification failed
    pause
    exit /b 1
)

python -c "import torch, layoutparser; print('✅ Advanced features available')" 2>nul || echo [WARNING] Some advanced features may not be available

python run_complete_pipeline.py --help >nul 2>&1
if %errorlevel% neq 0 (
    echo [WARNING] Pipeline script may have issues
) else (
    echo [SUCCESS] Pipeline script is working
)

echo.
echo [SUCCESS] 🎉 Project LANTERN setup complete!
echo.
echo Next steps:
echo 1. Activate virtual environment: .venv\Scripts\activate.bat
echo 2. Place PDF files in data\raw\ directory
echo 3. Run pipeline: python run_complete_pipeline.py --out data/parsed --hybrid-tables
echo.
echo For help: python run_complete_pipeline.py --help
echo.
pause