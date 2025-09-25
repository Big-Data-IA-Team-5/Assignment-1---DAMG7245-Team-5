#!/bin/bash

# Smart Dynamic Setup Script - Wrapper for Python setup
# Automatically detects Python version and installs compatible packages

set -e  # Exit on any error

echo "🚀 Starting Smart Dynamic Setup..."
echo "============================================"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3.7+ first."
    exit 1
fi

PYTHON_VERSION=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
echo "🐍 Detected Python $PYTHON_VERSION"

# Check minimum Python version
if python3 -c "import sys; exit(0 if sys.version_info >= (3, 7) else 1)"; then
    echo "✅ Python version is compatible"
else
    echo "❌ Python 3.7+ is required. Current version: $PYTHON_VERSION"
    exit 1
fi

# Run the smart setup script with arguments
echo "🔄 Running intelligent setup..."

# Pass through any command line arguments
python3 smart_setup.py "$@"

# Check if setup was successful
if [ $? -eq 0 ]; then
    echo ""
    echo "🎉 Smart setup completed successfully!"
    echo "============================================"
    echo ""
    echo "📋 Quick start:"
    echo "1. Activate environment: source activate.sh"
    echo "2. Place PDFs in: data/raw/"
    echo "3. Run pipeline: dvc repro"
    echo ""
    echo "🔧 System recommendations:"
    
    # Check for Tesseract
    if command -v tesseract &> /dev/null; then
        echo "  ✅ Tesseract OCR found"
    else
        echo "  📦 Install Tesseract for better OCR:"
        case "$(uname -s)" in
            Darwin*)
                echo "     brew install tesseract"
                ;;
            Linux*)
                if command -v apt-get &> /dev/null; then
                    echo "     sudo apt-get install tesseract-ocr"
                elif command -v yum &> /dev/null; then
                    echo "     sudo yum install tesseract"
                else
                    echo "     Install tesseract using your package manager"
                fi
                ;;
            *)
                echo "     Check tesseract installation for your OS"
                ;;
        esac
    fi
    
    # Check for Java (for tabula-py)
    if command -v java &> /dev/null; then
        echo "  ✅ Java found (good for table extraction)"
    else
        echo "  📦 Consider installing Java for enhanced table extraction"
    fi
    
else
    echo "❌ Setup failed. Please check the output above for errors."
    exit 1
fi