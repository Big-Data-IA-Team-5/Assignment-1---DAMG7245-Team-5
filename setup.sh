#!/bin/bash
# Project LANTERN - Automatic Setup Script for Linux/macOS
# This script sets up the complete Project LANTERN environment

set -e  # Exit on any error

echo "🚀 Project LANTERN - Automatic Setup"
echo "===================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    print_status "Checking Python installation..."
    
    if command -v python3 &> /dev/null; then
        PYTHON_VERSION=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
        print_success "Python $PYTHON_VERSION found"
        
        # Check if version is 3.8+
        if python3 -c 'import sys; exit(0 if sys.version_info >= (3, 8) else 1)'; then
            print_success "Python version is compatible (3.8+)"
        else
            print_error "Python 3.8+ required. Please upgrade Python."
            exit 1
        fi
    else
        print_error "Python 3 not found. Please install Python 3.8+ first."
        exit 1
    fi
}

# Install system dependencies
install_system_deps() {
    print_status "Installing system dependencies..."
    
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        print_status "Detected macOS"
        
        # Check if Homebrew is installed
        if ! command -v brew &> /dev/null; then
            print_warning "Homebrew not found. Installing Homebrew..."
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
        fi
        
        # Install Tesseract
        print_status "Installing Tesseract OCR..."
        brew install tesseract || print_warning "Tesseract may already be installed"
        
        # Install Xcode Command Line Tools if needed
        if ! xcode-select -p &> /dev/null; then
            print_status "Installing Xcode Command Line Tools..."
            xcode-select --install
        fi
        
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        print_status "Detected Linux"
        
        # Update package list
        print_status "Updating package list..."
        sudo apt-get update
        
        # Install system dependencies
        print_status "Installing system dependencies..."
        sudo apt-get install -y python3-dev python3-pip python3-venv build-essential cmake
        sudo apt-get install -y tesseract-ocr libtesseract-dev
        sudo apt-get install -y libgl1-mesa-glx libglib2.0-0 libsm6 libxext6 libxrender-dev libgomp1
        
    else
        print_warning "Unknown OS. Please install Tesseract OCR manually."
    fi
}

# Create virtual environment
setup_venv() {
    print_status "Setting up virtual environment..."
    
    if [ -d ".venv" ]; then
        print_warning "Virtual environment already exists. Removing old one..."
        rm -rf .venv
    fi
    
    python3 -m venv .venv
    source .venv/bin/activate
    
    # Upgrade pip
    print_status "Upgrading pip and core tools..."
    pip install --upgrade pip setuptools wheel
    
    print_success "Virtual environment created and activated"
}

# Install Python dependencies
install_dependencies() {
    print_status "Installing Python dependencies..."
    
    # Activate virtual environment
    source .venv/bin/activate
    
    # Choose installation type
    echo ""
    echo "Choose installation type:"
    echo "1) Full installation (all features) - Recommended"
    echo "2) Minimal installation (basic features only)"
    echo "3) Development installation (includes dev tools)"
    echo ""
    read -p "Enter choice (1-3) [default: 1]: " choice
    choice=${choice:-1}
    
    case $choice in
        1)
            print_status "Installing full dependencies..."
            pip install -r requirements.txt
            ;;
        2)
            print_status "Installing minimal dependencies..."
            pip install -r requirements-minimal.txt
            ;;
        3)
            print_status "Installing development dependencies..."
            pip install -r requirements.txt
            if [ -f "requirements-dev.txt" ]; then
                pip install -r requirements-dev.txt
            fi
            ;;
        *)
            print_error "Invalid choice. Using full installation."
            pip install -r requirements.txt
            ;;
    esac
    
    print_success "Dependencies installed successfully"
}

# Verify installation
verify_installation() {
    print_status "Verifying installation..."
    
    source .venv/bin/activate
    
    # Test core dependencies
    python3 -c "
import pdfplumber
import pandas
import numpy
import camelot
print('✅ Core dependencies working')
"
    
    # Test optional dependencies
    python3 -c "
try:
    import torch
    import layoutparser
    print('✅ Advanced features available')
except ImportError:
    print('⚠️  Some advanced features may not be available')
" 2>/dev/null || true
    
    # Test pipeline
    if python3 run_complete_pipeline.py --help > /dev/null 2>&1; then
        print_success "Pipeline script is working"
    else
        print_warning "Pipeline script may have issues"
    fi
    
    print_success "Installation verification complete"
}

# Create test data directory
setup_directories() {
    print_status "Setting up directory structure..."
    
    mkdir -p data/raw
    mkdir -p data/parsed
    
    print_success "Directory structure created"
}

# Main installation flow
main() {
    echo ""
    print_status "Starting Project LANTERN setup..."
    echo ""
    
    check_python
    echo ""
    
    # Ask for system dependencies installation
    read -p "Install system dependencies? (y/n) [default: y]: " install_sys
    install_sys=${install_sys:-y}
    
    if [[ $install_sys == "y" || $install_sys == "Y" ]]; then
        install_system_deps
        echo ""
    fi
    
    setup_venv
    echo ""
    
    install_dependencies
    echo ""
    
    setup_directories
    echo ""
    
    verify_installation
    echo ""
    
    print_success "🎉 Project LANTERN setup complete!"
    echo ""
    echo "Next steps:"
    echo "1. Activate virtual environment: source .venv/bin/activate"
    echo "2. Place PDF files in data/raw/ directory"
    echo "3. Run pipeline: python3 run_complete_pipeline.py --out data/parsed --hybrid-tables"
    echo ""
    echo "For help: python3 run_complete_pipeline.py --help"
}

# Run main function
main "$@"