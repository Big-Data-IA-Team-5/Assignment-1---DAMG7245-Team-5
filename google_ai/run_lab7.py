#!/usr/bin/env python3
"""
Lab 7 Google Document AI Integration Launcher
Team 5 - DAMG7245 Fall 2025

This script provides an easy way to run the Lab 7 workflow from the project root.
All outputs will be organized in the reports/google_ai/ folder.

Usage:
    python run_lab7.py --pdf data/raw/tesla.pdf --pages 5 12
    python run_lab7.py --pdf data/raw/tesla.pdf --random 2 --seed 42
"""

import subprocess
import sys
from pathlib import Path


def main():
    """Launch the Lab 7 workflow script."""
    # Path to the actual Lab 7 script in the google_ai folder
    lab7_script = Path(__file__).parent / "lab7_google_ai_integration.py"

    if not lab7_script.exists():
        print(f"Error: Lab 7 script not found: {lab7_script}")
        print("Please ensure the project structure is correct.")
        return 1

    # Pass all command line arguments to the Lab 7 script
    cmd = [sys.executable, str(lab7_script)] + sys.argv[1:]

    print("Starting Lab 7 Google Document AI Integration...")
    print(f"All outputs will be organized in: reports/google_ai/")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)

    # Run the Lab 7 script
    try:
        result = subprocess.run(cmd, check=False)
        return result.returncode
    except KeyboardInterrupt:
        print("\\nProcess interrupted by user.")
        return 1
    except Exception as e:
        print(f"Error launching Lab 7: {e}")
        return 1


if __name__ == "__main__":
    exit(main())
