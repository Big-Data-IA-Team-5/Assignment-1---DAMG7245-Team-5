#!/usr/bin/env python3
"""
Smart Dynamic Setup for PDF Processing Pipeline
===============================================

This script automatically detects your Python version and system configuration,
then installs the most compatible versions of all required packages.

Features:
- Auto-detects Python version (3.7-3.12+)
- Handles virtual environment creation
- Installs version-specific compatible packages
- Provides fallbacks for problematic packages
- Sets up DVC with appropriate configuration

Usage:
    python3 smart_setup.py [--force-reinstall] [--skip-dvc] [--minimal]
"""

import sys
import subprocess
import platform
import os
import argparse
from pathlib import Path
import json

class SmartInstaller:
    def __init__(self, force_reinstall=False, skip_dvc=False, minimal=False):
        self.python_version = sys.version_info
        self.platform_system = platform.system()
        self.platform_machine = platform.machine()
        self.force_reinstall = force_reinstall
        self.skip_dvc = skip_dvc
        self.minimal = minimal
        self.project_root = Path(__file__).parent
        self.venv_path = self.project_root / ".venv"
        
        print(f"🐍 Python {self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}")
        print(f"💻 {self.platform_system} {self.platform_machine}")
        print(f"📁 Project: {self.project_root}")

    def run_command(self, command, check=True, capture_output=False):
        """Run shell command with error handling"""
        try:
            if isinstance(command, str):
                command = command.split()
            
            result = subprocess.run(
                command, 
                check=check, 
                capture_output=capture_output,
                text=True,
                cwd=self.project_root
            )
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Command failed: {' '.join(command)}")
            print(f"Error: {e}")
            if not capture_output:
                return None
            raise

    def create_virtual_environment(self):
        """Create or recreate virtual environment"""
        print("\n🔧 Setting up virtual environment...")
        
        if self.venv_path.exists() and self.force_reinstall:
            print("  Removing existing virtual environment...")
            import shutil
            shutil.rmtree(self.venv_path)
        
        if not self.venv_path.exists():
            print("  Creating new virtual environment...")
            self.run_command([sys.executable, "-m", "venv", str(self.venv_path)])
            print("  ✅ Virtual environment created")
        else:
            print("  ✅ Using existing virtual environment")

    def get_pip_executable(self):
        """Get the pip executable path for the virtual environment"""
        if self.platform_system == "Windows":
            return str(self.venv_path / "Scripts" / "pip.exe")
        else:
            return str(self.venv_path / "bin" / "pip")

    def get_python_executable(self):
        """Get the python executable path for the virtual environment"""
        if self.platform_system == "Windows":
            return str(self.venv_path / "Scripts" / "python.exe")
        else:
            return str(self.venv_path / "bin" / "python")

    def upgrade_pip(self):
        """Upgrade pip to latest version"""
        print("\n📦 Upgrading pip...")
        pip_exe = self.get_pip_executable()
        self.run_command([pip_exe, "install", "--upgrade", "pip"])
        print("  ✅ Pip upgraded")

    def get_dynamic_requirements(self):
        """Generate requirements based on Python version and system"""
        requirements = []
        
        # Core packages - always install these
        core_packages = [
            "pdfplumber>=0.7.0",
            "pytesseract>=0.3.8", 
            "tqdm>=4.60.0",
            "requests>=2.25.0",
            "beautifulsoup4>=4.9.0",
            "pyyaml>=6.0",
            "jsonlines>=2.0.0",
            "PyPDF2>=2.12.0",
        ]
        requirements.extend(core_packages)

        # Python version specific packages
        if self.python_version >= (3, 8):
            requirements.extend([
                "pandas>=1.5.0",
                "numpy>=1.21.0",
                "Pillow>=9.0.0",
            ])
        else:
            requirements.extend([
                "pandas>=1.3.0,<2.0.0",
                "numpy>=1.19.0,<1.22.0", 
                "Pillow>=8.0.0,<9.0.0",
            ])

        # Table extraction
        if self.python_version >= (3, 8):
            requirements.append("camelot-py[base]>=0.10.1")
        else:
            requirements.append("camelot-py[cv]>=0.9.0")
        
        requirements.append("tabula-py>=2.5.0")

        # Visualization
        if self.python_version >= (3, 10):
            requirements.append("matplotlib>=3.5.0")
        else:
            requirements.append("matplotlib>=3.3.0,<3.8.0")

        # Computer Vision
        requirements.append("opencv-python-headless>=4.5.0")
        
        if self.python_version >= (3, 10):
            requirements.append("scikit-image>=0.19.0")
        else:
            requirements.append("scikit-image>=0.18.0,<0.22.0")

        # Testing
        requirements.append("pytest>=6.2.0")

        # DVC - Version control for data
        if not self.skip_dvc:
            if self.python_version >= (3, 9):
                requirements.append("dvc>=3.0.0")
            else:
                requirements.append("dvc>=2.55.0,<3.0.0")

        # Google Cloud (optional)
        if not self.minimal:
            google_packages = [
                "google-cloud-documentai>=2.15.0",
                "google-cloud-storage>=2.7.0",
                "google-auth>=2.15.0",
                "google-api-python-client>=2.70.0",
            ]
            requirements.extend(google_packages)

        return requirements

    def install_packages_with_fallbacks(self):
        """Install packages from unified requirements.txt with smart fallbacks"""
        print("\n📦 Installing packages from requirements.txt...")
        pip_exe = self.get_pip_executable()
        
        requirements_file = self.project_root / "requirements.txt"
        if not requirements_file.exists():
            print("❌ requirements.txt not found, falling back to dynamic generation")
            requirements = self.get_dynamic_requirements()
        else:
            # Use unified requirements.txt with constraints if minimal install
            install_cmd = [pip_exe, "install", "-r", str(requirements_file)]
            
            if self.minimal:
                constraints_file = self.project_root / "constraints-minimal.txt"
                if constraints_file.exists():
                    install_cmd.extend(["--constraint", str(constraints_file)])
                    print("  Using minimal installation constraints...")
            
            # Try to install from requirements file first
            print("  Attempting installation from requirements.txt...")
            try:
                self.run_command(install_cmd, check=True)
                print("  ✅ All packages installed successfully from requirements.txt")
                return
            except subprocess.CalledProcessError:
                print("  ⚠️  Requirements.txt installation failed, trying fallback method...")
                requirements = self.get_dynamic_requirements()

        # Fallback: Install packages individually with fallbacks
        print("  Falling back to individual package installation...")
        failed_packages = []
        for package in requirements:
            try:
                print(f"    Installing {package}...")
                self.run_command([pip_exe, "install", package], check=True)
                print(f"    ✅ {package}")
            except subprocess.CalledProcessError:
                print(f"    ❌ Failed: {package}")
                failed_packages.append(package)
                
                # Try fallback for specific packages
                if "camelot-py" in package:
                    try:
                        fallback = "camelot-py[cv]>=0.9.0"
                        print(f"    🔄 Trying fallback: {fallback}")
                        self.run_command([pip_exe, "install", fallback], check=True)
                        print(f"    ✅ Fallback succeeded: {fallback}")
                    except subprocess.CalledProcessError:
                        print(f"    ❌ Fallback also failed for camelot-py")

        if failed_packages:
            print(f"\n⚠️  Some packages failed to install: {failed_packages}")
            print("The core functionality should still work!")
        else:
            print("\n✅ All packages installed successfully!")

    def setup_dvc(self):
        """Initialize DVC if not already done"""
        if self.skip_dvc:
            print("\n⏭️  Skipping DVC setup")
            return
            
        print("\n🗂️  Setting up DVC...")
        
        dvc_dir = self.project_root / ".dvc"
        if not dvc_dir.exists():
            python_exe = self.get_python_executable()
            try:
                self.run_command([python_exe, "-m", "dvc", "init"])
                print("  ✅ DVC initialized")
            except subprocess.CalledProcessError:
                print("  ⚠️  DVC initialization failed (this is okay if already initialized)")
        else:
            print("  ✅ DVC already initialized")

    def verify_installation(self):
        """Verify that key packages are working"""
        print("\n🔍 Verifying installation...")
        python_exe = self.get_python_executable()
        
        test_imports = [
            "import pandas as pd; print(f'✅ Pandas {pd.__version__}')",
            "import numpy as np; print(f'✅ NumPy {np.__version__}')",
            "import pdfplumber; print('✅ PDFplumber')",
            "import requests; print('✅ Requests')",
            "import yaml; print('✅ PyYAML')",
        ]
        
        if not self.skip_dvc:
            test_imports.append("import dvc; print('✅ DVC')")

        for test in test_imports:
            try:
                result = self.run_command([python_exe, "-c", test], capture_output=True)
                if result and result.stdout:
                    print(f"  {result.stdout.strip()}")
            except subprocess.CalledProcessError:
                package_name = test.split()[1].split('.')[0]
                print(f"  ❌ {package_name} verification failed")

    def create_activation_scripts(self):
        """Create easy activation scripts"""
        print("\n📝 Creating activation scripts...")
        
        # Create activate script for Unix-like systems
        activate_script = self.project_root / "activate.sh"
        activate_content = f"""#!/bin/bash
# Activation script for PDF Processing Pipeline
echo "🚀 Activating PDF Processing Pipeline Environment..."
source "{self.venv_path}/bin/activate"
echo "✅ Environment activated!"
echo "📂 Project root: {self.project_root}"
echo "🐍 Python: $(python --version)"
echo ""
echo "Quick commands:"
echo "  dvc status              - Check pipeline status"
echo "  dvc repro              - Run full pipeline"
echo "  python run_complete_pipeline.py  - Alternative pipeline run"
"""
        
        with open(activate_script, 'w') as f:
            f.write(activate_content)
        
        # Make executable
        activate_script.chmod(0o755)
        
        # Create Windows batch script
        activate_bat = self.project_root / "activate.bat"
        activate_bat_content = f"""@echo off
REM Activation script for PDF Processing Pipeline
echo 🚀 Activating PDF Processing Pipeline Environment...
call "{self.venv_path}\\Scripts\\activate.bat"
echo ✅ Environment activated!
echo 📂 Project root: {self.project_root}
python --version
echo.
echo Quick commands:
echo   dvc status              - Check pipeline status
echo   dvc repro              - Run full pipeline
echo   python run_complete_pipeline.py  - Alternative pipeline run
"""
        
        with open(activate_bat, 'w') as f:
            f.write(activate_bat_content)
            
        print(f"  ✅ Created {activate_script}")
        print(f"  ✅ Created {activate_bat}")

    def save_installation_info(self):
        """Save information about the installation"""
        info = {
            "python_version": f"{self.python_version.major}.{self.python_version.minor}.{self.python_version.micro}",
            "platform": f"{self.platform_system} {self.platform_machine}",
            "installation_date": str(Path(__file__).stat().st_mtime),
            "venv_path": str(self.venv_path),
            "options": {
                "force_reinstall": self.force_reinstall,
                "skip_dvc": self.skip_dvc,
                "minimal": self.minimal
            }
        }
        
        info_file = self.project_root / ".setup_info.json"
        with open(info_file, 'w') as f:
            json.dump(info, f, indent=2)

    def run_full_setup(self):
        """Run the complete setup process"""
        print("🚀 Starting Smart Dynamic Setup...")
        print("=" * 50)
        
        try:
            self.create_virtual_environment()
            self.upgrade_pip()
            self.install_packages_with_fallbacks()
            self.setup_dvc()
            self.verify_installation()
            self.create_activation_scripts()
            self.save_installation_info()
            
            print("\n" + "=" * 50)
            print("🎉 Setup completed successfully!")
            print("\nNext steps:")
            print("1. Activate the environment:")
            if self.platform_system == "Windows":
                print("   .\\activate.bat")
            else:
                print("   source activate.sh")
            print("2. Run the pipeline:")
            print("   dvc repro")
            print("   # OR")
            print("   python run_complete_pipeline.py")
            
        except Exception as e:
            print(f"\n❌ Setup failed with error: {e}")
            sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Smart Dynamic Setup for PDF Processing Pipeline")
    parser.add_argument("--force-reinstall", action="store_true", 
                       help="Force reinstallation of virtual environment")
    parser.add_argument("--skip-dvc", action="store_true",
                       help="Skip DVC installation and setup")
    parser.add_argument("--minimal", action="store_true",
                       help="Minimal installation (skip optional packages)")
    
    args = parser.parse_args()
    
    installer = SmartInstaller(
        force_reinstall=args.force_reinstall,
        skip_dvc=args.skip_dvc,
        minimal=args.minimal
    )
    
    installer.run_full_setup()

if __name__ == "__main__":
    main()