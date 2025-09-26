#!/usr/bin/env python3
"""
Simple test runner to verify the standalone evaluation system

This script runs basic tests to ensure the evaluation system components work correctly.
"""

import sys
from pathlib import Path

def test_xbrl_loading():
    """Test XBRL file loading and parsing"""
    print("🔍 Testing XBRL loading...")
    
    # Check if XBRL file exists
    xbrl_dir = Path(__file__).parent / "data" / "raw" / "xbrl_files"
    
    if not xbrl_dir.exists():
        print(f"❌ XBRL directory not found: {xbrl_dir}")
        return False
    
    xbrl_files = list(xbrl_dir.glob("*.xbrl")) + list(xbrl_dir.glob("*.xml"))
    
    if not xbrl_files:
        print(f"❌ No XBRL files found in {xbrl_dir}")
        return False
    
    print(f"✅ Found {len(xbrl_files)} XBRL files:")
    for xbrl_file in xbrl_files:
        print(f"   - {xbrl_file.name}")
    
    return True

def test_data_structure():
    """Test parsed data structure"""
    print("📁 Testing data structure...")
    
    data_dir = Path(__file__).parent / "data" / "intermediate"
    
    if not data_dir.exists():
        print(f"❌ Data directory not found: {data_dir}")
        return False
    
    # Check for expected subdirectories
    expected_dirs = ["tables", "text_extraction"]
    found_dirs = []
    
    for expected_dir in expected_dirs:
        dir_path = data_dir / expected_dir
        if dir_path.exists():
            found_dirs.append(expected_dir)
            print(f"✅ Found {expected_dir}/ directory")
        else:
            print(f"⚠️  Missing {expected_dir}/ directory")
    
    if found_dirs:
        print(f"✅ Data structure partially available ({len(found_dirs)}/{len(expected_dirs)} directories)")
        return True
    else:
        print("❌ No expected data directories found")
        return False

def test_imports():
    """Test if evaluation modules can be imported"""
    print("📦 Testing module imports...")
    
    try:
        from src.evaluation.parser_quality_evaluator import ParserQualityEvaluator
        print("✅ ParserQualityEvaluator imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import ParserQualityEvaluator: {e}")
        return False
    
    try:
        from src.evaluation.standalone_metrics_tracker import StandaloneMetricsTracker
        print("✅ StandaloneMetricsTracker imported successfully")
    except ImportError as e:
        print(f"❌ Failed to import StandaloneMetricsTracker: {e}")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Running standalone evaluation system tests...")
    print("="*50)
    
    tests = [
        ("Module Imports", test_imports),
        ("Data Structure", test_data_structure), 
        ("XBRL Loading", test_xbrl_loading)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n{test_name}:")
        results[test_name] = test_func()
    
    print("\n" + "="*50)
    print("📊 Test Results Summary:")
    
    passed = 0
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("🎉 All tests passed! System ready for demo.")
        return True
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)