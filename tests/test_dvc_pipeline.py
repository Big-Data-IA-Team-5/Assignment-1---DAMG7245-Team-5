#!/usr/bin/env python3
"""
DVC Pipeline Smoke Test
Tests that the DVC pipeline can run successfully and produces expected outputs.
"""

import json
import subprocess
import pytest
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_INTERMEDIATE = PROJECT_ROOT / "data" / "intermediate"

class TestDVCPipeline:
    """Test suite for DVC pipeline functionality."""
    
    def test_dvc_is_installed(self):
        """Test that DVC is properly installed."""
        try:
            result = subprocess.run(["dvc", "--version"], 
                                  capture_output=True, text=True, check=True)
            assert "3." in result.stdout  # Check for DVC version 3.x
            print(f"✅ DVC Version: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            pytest.fail("DVC is not installed or not accessible")
    
    def test_dvc_files_exist(self):
        """Test that essential DVC files exist."""
        required_files = [
            PROJECT_ROOT / "dvc.yaml",
            PROJECT_ROOT / "dvc.lock", 
            PROJECT_ROOT / "data" / "raw.dvc"
        ]
        
        for file_path in required_files:
            assert file_path.exists(), f"Missing required DVC file: {file_path}"
            print(f"✅ Found: {file_path}")
    
    def test_dvc_pipeline_structure(self):
        """Test that dvc.yaml contains expected pipeline stages."""
        dvc_yaml_path = PROJECT_ROOT / "dvc.yaml"
        
        with open(dvc_yaml_path, 'r') as f:
            import yaml
            dvc_config = yaml.safe_load(f)
        
        expected_stages = ["parse", "tables", "layout", "docling", "export"]
        
        assert "stages" in dvc_config, "No stages found in dvc.yaml"
        
        for stage in expected_stages:
            assert stage in dvc_config["stages"], f"Missing stage: {stage}"
            print(f"✅ Stage found: {stage}")
    
    def test_pipeline_outputs_exist(self):
        """Test that pipeline outputs exist after running."""
        expected_outputs = [
            DATA_INTERMEDIATE / "text",
            DATA_INTERMEDIATE / "tables", 
            DATA_INTERMEDIATE / "layout",
            DATA_INTERMEDIATE / "docling",
            DATA_INTERMEDIATE / "formats"
        ]
        
        for output_dir in expected_outputs:
            assert output_dir.exists(), f"Missing pipeline output: {output_dir}"
            assert any(output_dir.iterdir()), f"Empty output directory: {output_dir}"
            print(f"✅ Output exists: {output_dir}")
    
    def test_metadata_files_exist(self):
        """Test that final metadata files are generated."""
        formats_dir = DATA_INTERMEDIATE / "formats"
        expected_files = ["pdf_doc.json", "pdf_doc.md", "pdf_doc.txt"]
        
        for filename in expected_files:
            file_path = formats_dir / filename
            assert file_path.exists(), f"Missing metadata file: {file_path}"
            assert file_path.stat().st_size > 0, f"Empty metadata file: {file_path}"
            print(f"✅ Metadata file: {filename} ({file_path.stat().st_size} bytes)")
    
    def test_metadata_content_quality(self):
        """Test that metadata contains expected content."""
        metadata_file = DATA_INTERMEDIATE / "formats" / "pdf_doc.json"
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Check that we have substantial metadata records
        assert len(metadata) > 1000, f"Too few metadata records: {len(metadata)}"
        
        # Check for different extraction methods
        methods = {record.get('extraction_method') for record in metadata}
        expected_methods = ['pdfplumber_word_level', 'lab1_pdfplumber', 'layoutparser', 'docling_unified']
        
        for method in expected_methods:
            assert method in methods, f"Missing extraction method: {method}"
            print(f"✅ Extraction method found: {method}")
        
        print(f"✅ Total metadata records: {len(metadata)}")

def test_dvc_pipeline_smoke():
    """
    Lightweight smoke test that can run in CI/CD.
    Only checks file existence and basic structure.
    """
    # Quick file existence checks
    assert (PROJECT_ROOT / "dvc.yaml").exists()
    assert (PROJECT_ROOT / "dvc.lock").exists()
    
    # Check that intermediate data exists
    assert (DATA_INTERMEDIATE).exists()
    
    # Basic pipeline stage check
    with open(PROJECT_ROOT / "dvc.yaml", 'r') as f:
        import yaml
        dvc_config = yaml.safe_load(f)
        assert len(dvc_config.get("stages", {})) >= 5
    
    print("✅ DVC Pipeline smoke test passed!")

if __name__ == "__main__":
    # Run smoke test directly
    test_dvc_pipeline_smoke()
    print("\n🎯 All smoke tests passed!")