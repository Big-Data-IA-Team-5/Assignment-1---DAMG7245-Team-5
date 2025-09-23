#!/usr/bin/env python3
"""
Project LANTERN - System Check Utility
Verifies system compatibility and dependency status
"""

import sys
import platform
import subprocess
import importlib
import pkg_resources
from pathlib import Path

def print_header():
    """Print system check header"""
    print("🔍 Project LANTERN - System Compatibility Check")
    print("=" * 50)
    print()

def check_python_version():
    """Check Python version compatibility"""
    print("📍 Python Environment")
    print("-" * 20)
    
    version = sys.version_info
    print(f"Python version: {version.major}.{version.minor}.{version.micro}")
    print(f"Platform: {platform.platform()}")
    print(f"Architecture: {platform.architecture()[0]}")
    
    if version >= (3, 8):
        print("✅ Python version is compatible (3.8+)")
        if version >= (3, 9):
            print("✅ Full features available (3.9+)")
        else:
            print("⚠️  Some advanced features require Python 3.9+")
    else:
        print("❌ Python 3.8+ required")
        return False
    
    print()
    return True

def check_system_dependencies():
    """Check system-level dependencies"""
    print("📍 System Dependencies")
    print("-" * 20)
    
    # Check Tesseract
    try:
        result = subprocess.run(['tesseract', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            version_line = result.stdout.split('\n')[0]
            print(f"✅ Tesseract OCR: {version_line}")
        else:
            print("❌ Tesseract OCR not found")
    except FileNotFoundError:
        print("❌ Tesseract OCR not found in PATH")
        print("   Install from: https://github.com/tesseract-ocr/tesseract")
    
    # Check Git (optional)
    try:
        result = subprocess.run(['git', '--version'], 
                              capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Git: {result.stdout.strip()}")
    except FileNotFoundError:
        print("⚠️  Git not found (optional)")
    
    print()

def check_core_dependencies():
    """Check core Python dependencies"""
    print("📍 Core Dependencies")
    print("-" * 20)
    
    core_packages = [
        ('pdfplumber', 'PDF processing'),
        ('pandas', 'Data manipulation'),
        ('numpy', 'Numerical computing'),
        ('camelot', 'Table extraction'),
        ('PIL', 'Image processing'),
        ('pytesseract', 'OCR interface'),
    ]
    
    all_good = True
    for package, description in core_packages:
        try:
            module = importlib.import_module(package)
            if hasattr(module, '__version__'):
                version = module.__version__
            else:
                try:
                    version = pkg_resources.get_distribution(package).version
                except:
                    version = "unknown"
            print(f"✅ {package}: {version} ({description})")
        except ImportError:
            print(f"❌ {package}: Not installed ({description})")
            all_good = False
    
    print()
    return all_good

def check_optional_dependencies():
    """Check optional dependencies"""
    print("📍 Optional Dependencies")
    print("-" * 20)
    
    optional_packages = [
        ('torch', 'PyTorch for ML features'),
        ('torchvision', 'Computer vision'),
        ('layoutparser', 'Layout detection'),
        ('detectron2', 'Advanced layout analysis'),
        ('docling', 'Advanced PDF understanding'),
        ('cv2', 'OpenCV for image processing'),
    ]
    
    available_features = []
    for package, description in optional_packages:
        try:
            module = importlib.import_module(package)
            if hasattr(module, '__version__'):
                version = module.__version__
            else:
                try:
                    version = pkg_resources.get_distribution(package).version
                except:
                    version = "unknown"
            print(f"✅ {package}: {version} ({description})")
            available_features.append(package)
        except ImportError:
            print(f"⚠️  {package}: Not available ({description})")
    
    print()
    return available_features

def check_memory_and_storage():
    """Check system resources"""
    print("📍 System Resources")
    print("-" * 20)
    
    try:
        import psutil
        
        # Memory
        memory = psutil.virtual_memory()
        memory_gb = memory.total / (1024**3)
        print(f"Total RAM: {memory_gb:.1f} GB")
        
        if memory_gb >= 8:
            print("✅ Excellent memory for large documents")
        elif memory_gb >= 4:
            print("✅ Good memory for medium documents")
        else:
            print("⚠️  Limited memory - consider processing smaller files")
        
        # Storage
        disk = psutil.disk_usage('.')
        disk_free_gb = disk.free / (1024**3)
        print(f"Free disk space: {disk_free_gb:.1f} GB")
        
        if disk_free_gb >= 5:
            print("✅ Sufficient storage available")
        else:
            print("⚠️  Limited storage - ensure adequate space for outputs")
        
    except ImportError:
        print("⚠️  psutil not available - cannot check system resources")
    
    print()

def check_project_structure():
    """Check project directory structure"""
    print("📍 Project Structure")
    print("-" * 20)
    
    required_files = [
        'run_complete_pipeline.py',
        'requirements.txt',
        'requirements-minimal.txt',
        'src/',
        'data/',
    ]
    
    all_present = True
    for item in required_files:
        path = Path(item)
        if path.exists():
            print(f"✅ {item}")
        else:
            print(f"❌ {item} (missing)")
            all_present = False
    
    # Check data directories
    data_dirs = ['data/raw', 'data/parsed']
    for dir_path in data_dirs:
        path = Path(dir_path)
        if path.exists():
            print(f"✅ {dir_path}/")
        else:
            print(f"⚠️  {dir_path}/ (will be created)")
    
    print()
    return all_present

def provide_recommendations(core_ok, optional_features):
    """Provide installation recommendations"""
    print("📍 Recommendations")
    print("-" * 20)
    
    if not core_ok:
        print("❌ Core dependencies missing:")
        print("   Run: pip install -r requirements-minimal.txt")
        print()
    
    missing_features = []
    if 'torch' not in optional_features:
        missing_features.append("PyTorch (ML features)")
    if 'layoutparser' not in optional_features:
        missing_features.append("LayoutParser (advanced layout)")
    if 'docling' not in optional_features:
        missing_features.append("Docling (advanced PDF processing)")
    
    if missing_features:
        print("⚠️  Optional features not available:")
        for feature in missing_features:
            print(f"   - {feature}")
        print("   For full features: pip install -r requirements.txt")
        print()
    
    if core_ok and len(optional_features) >= 3:
        print("✅ System is ready for full pipeline processing!")
    elif core_ok:
        print("✅ System is ready for basic pipeline processing!")
        print("   Use --skip-docling flag for missing features")
    
    print()

def main():
    """Main system check function"""
    print_header()
    
    # Run all checks
    python_ok = check_python_version()
    check_system_dependencies()
    core_ok = check_core_dependencies()
    optional_features = check_optional_dependencies()
    check_memory_and_storage()
    structure_ok = check_project_structure()
    
    # Summary
    print("📍 System Check Summary")
    print("-" * 20)
    
    if python_ok and core_ok and structure_ok:
        print("🎉 System check passed! Ready to run Project LANTERN.")
    else:
        print("⚠️  Some issues detected. See recommendations below.")
    
    print()
    
    # Provide recommendations
    provide_recommendations(core_ok, optional_features)
    
    # Quick start guide
    if core_ok:
        print("📍 Quick Start")
        print("-" * 20)
        print("1. Place PDF files in data/raw/")
        print("2. Run: python3 run_complete_pipeline.py --out data/parsed --hybrid-tables")
        print("3. Check outputs in data/parsed/")
        print()

if __name__ == "__main__":
    main()