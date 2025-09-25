#!/usr/bin/env python3
"""
Verification Script for Dynamic PDF Processing Pipeline
=====================================================

This script verifies that the dynamic setup worked correctly and all
components are properly installed and functional.

Usage:
    python3 verify_setup.py [--verbose] [--test-dvc]
"""

import sys
import subprocess
import importlib
from pathlib import Path

def check_python_version():
    """Check Python version compatibility"""
    version = sys.version_info
    print(f"🐍 Python {version.major}.{version.minor}.{version.micro}")
    
    if version >= (3, 7):
        print("✅ Python version is compatible")
        return True
    else:
        print(f"❌ Python 3.7+ required, found {version.major}.{version.minor}")
        return False

def check_package(package_name, import_name=None):
    """Check if a package is installed and importable"""
    if import_name is None:
        import_name = package_name.replace('-', '_')
    
    try:
        module = importlib.import_module(import_name)
        if hasattr(module, '__version__'):
            version = getattr(module, '__version__')
            print(f"✅ {package_name}: {version}")
        else:
            print(f"✅ {package_name}: installed")
        return True
    except ImportError:
        print(f"❌ {package_name}: not found")
        return False

def check_essential_packages():
    """Check essential packages"""
    print("\n📦 Checking Essential Packages:")
    essential = [
        ('pandas', 'pandas'),
        ('numpy', 'numpy'), 
        ('pdfplumber', 'pdfplumber'),
        ('requests', 'requests'),
        ('pyyaml', 'yaml'),
        ('tqdm', 'tqdm'),
        ('PyPDF2', 'PyPDF2')
    ]
    
    results = []
    for pkg_name, import_name in essential:
        results.append(check_package(pkg_name, import_name))
    
    return all(results)

def check_advanced_packages():
    """Check advanced packages"""
    print("\n🔬 Checking Advanced Packages:")
    advanced = [
        ('camelot-py', 'camelot'),
        ('tabula-py', 'tabula'),
        ('matplotlib', 'matplotlib'),
        ('opencv-python', 'cv2'),
        ('pytesseract', 'pytesseract'),
        ('beautifulsoup4', 'bs4')
    ]
    
    results = []
    for pkg_name, import_name in advanced:
        results.append(check_package(pkg_name, import_name))
    
    return results

def check_dvc():
    """Check DVC installation and setup"""
    print("\n📊 Checking DVC:")
    
    # Check DVC package
    if not check_package('dvc', 'dvc'):
        return False
    
    # Check DVC initialization
    dvc_dir = Path('.dvc')
    if dvc_dir.exists():
        print("✅ DVC initialized")
    else:
        print("⚠️  DVC not initialized (run: dvc init)")
    
    # Check DVC files
    dvc_yaml = Path('dvc.yaml')
    if dvc_yaml.exists():
        print("✅ DVC pipeline configuration found")
    else:
        print("❌ dvc.yaml not found")
    
    return True

def check_project_structure():
    """Check project directory structure"""
    print("\n📁 Checking Project Structure:")
    
    required_dirs = ['data/raw', 'data/intermediate', 'src', 'configs']
    results = []
    
    for dir_name in required_dirs:
        dir_path = Path(dir_name)
        if dir_path.exists():
            print(f"✅ {dir_name}/")
            results.append(True)
        else:
            print(f"❌ {dir_name}/ missing")
            results.append(False)
    
    return all(results)

def test_dvc_pipeline():
    """Test DVC pipeline status"""
    print("\n🔄 Testing DVC Pipeline:")
    
    try:
        # Check if we're in a virtual environment
        venv_path = Path('.venv/bin/dvc')
        if venv_path.exists():
            dvc_cmd = str(venv_path)
        else:
            dvc_cmd = 'dvc'
        
        # Test dvc status
        result = subprocess.run([dvc_cmd, 'status'], capture_output=True, text=True)
        if result.returncode == 0:
            print("✅ DVC pipeline accessible")
            if result.stdout.strip():
                print(f"📊 Pipeline status: Changes detected")
            else:
                print("📊 Pipeline status: Up to date")
            return True
        else:
            print(f"❌ DVC pipeline error: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ DVC command not found")
        return False

def check_activation_scripts():
    """Check if activation scripts were created"""
    print("\n🚀 Checking Activation Scripts:")
    
    scripts = ['activate.sh', 'activate.bat']
    for script in scripts:
        script_path = Path(script)
        if script_path.exists():
            print(f"✅ {script}")
        else:
            print(f"❌ {script} missing")

def main():
    """Run complete verification"""
    print("🔍 Dynamic Setup Verification")
    print("=" * 40)
    
    results = []
    
    # Check Python version
    results.append(check_python_version())
    
    # Check packages
    results.append(check_essential_packages())
    check_advanced_packages()  # Don't fail on advanced packages
    
    # Check DVC
    results.append(check_dvc())
    
    # Check project structure
    results.append(check_project_structure())
    
    # Test DVC pipeline
    test_dvc_pipeline()  # Don't fail on pipeline test
    
    # Check activation scripts
    check_activation_scripts()
    
    # Final summary
    print("\n" + "=" * 40)
    if all(results):
        print("🎉 Verification PASSED!")
        print("\n✅ Your dynamic setup is working correctly!")
        print("\nNext steps:")
        print("1. source activate.sh (or activate.bat on Windows)")
        print("2. dvc repro")
        print("3. Place PDFs in data/raw/ and run the pipeline")
    else:
        print("⚠️  Verification had some issues")
        print("\nSome components may not be working correctly.")
        print("Try running: python3 smart_setup.py --force-reinstall")
    
    return 0 if all(results) else 1

if __name__ == "__main__":
    sys.exit(main())