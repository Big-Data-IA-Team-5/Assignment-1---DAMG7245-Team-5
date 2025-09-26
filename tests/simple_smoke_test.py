#!/usr/bin/env python3
"""
Simple smoke test runner that doesn't require pytest
Tests basic DVC pipeline structure without hardcoded assumptions
"""

import yaml
import json
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent

def test_basic_dvc_structure():
    """Test basic DVC structure exists."""
    print("Testing DVC pipeline structure...")
    
    # Test 1: Required files exist
    required_files = ['dvc.yaml', 'dvc.lock']
    for filename in required_files:
        file_path = PROJECT_ROOT / filename
        if file_path.exists():
            print(f"[PASS] Found: {filename}")
        else:
            print(f"[FAIL] Missing: {filename}")
            return False
    
    # Test 2: DVC pipeline has stages
    try:
        with open(PROJECT_ROOT / "dvc.yaml", 'r') as f:
            dvc_config = yaml.safe_load(f)
        
        stages = dvc_config.get('stages', {})
        if len(stages) > 0:
            print(f"[PASS] Found {len(stages)} pipeline stages: {list(stages.keys())}")
        else:
            print("[FAIL] No pipeline stages found")
            return False
    except Exception as e:
        print(f"[FAIL] Error reading dvc.yaml: {e}")
        return False
    
    # Test 3: Check pipeline outputs (optional)
    data_dirs = ['data/intermediate', 'data/parsed', 'data/raw']
    found_data = False
    for dirname in data_dirs:
        dir_path = PROJECT_ROOT / dirname
        if dir_path.exists():
            print(f"[PASS] Found data directory: {dirname}")
            found_data = True
    
    if not found_data:
        print("[WARN] No data directories found - pipeline may not have run yet")
    
    return True

def main():
    """Run the smoke test."""
    print("Running DVC Pipeline Smoke Test (Non-hardcoded)")
    print("=" * 60)
    
    if test_basic_dvc_structure():
        print("\nSmoke Test PASSED!")
        print("[PASS] Pipeline structure is valid and configurable")
        return 0
    else:
        print("\nSmoke Test FAILED!")
        print("[INFO] Check your DVC configuration")
        return 1

if __name__ == "__main__":
    exit(main())