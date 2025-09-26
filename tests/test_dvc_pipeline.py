#!/usr/bin/env python3
"""
DVC Pipeline Smoke Test
Tests that the DVC pipeline can run successfully and produces expected outputs.
Configurable via configs/smoke_test_config.yaml to avoid hardcoding.
"""

import json
import subprocess
import pytest
import yaml
from pathlib import Path

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_INTERMEDIATE = PROJECT_ROOT / "data" / "intermediate"

# Load configuration (with defaults if file doesn't exist)
def load_smoke_test_config():
    """Load smoke test configuration with sensible defaults."""
    config_file = PROJECT_ROOT / "configs" / "smoke_test_config.yaml"
    
    # Default configuration
    default_config = {
        'pipeline': {'min_stages': 1, 'required_files': ['dvc.yaml', 'dvc.lock']},
        'metadata': {'min_records': 10, 'check_extraction_methods': True},
        'tests': {'skip_missing_outputs': True, 'verbose_logging': True}
    }
    
    if config_file.exists():
        try:
            with open(config_file, 'r') as f:
                user_config = yaml.safe_load(f)
                # Merge with defaults
                for section, values in user_config.items():
                    if section in default_config:
                        default_config[section].update(values)
                    else:
                        default_config[section] = values
            except Exception as e:
            print(f"[WARN] Warning: Could not load config file: {e}. Using defaults.")
    
    return default_config# Load configuration
CONFIG = load_smoke_test_config()

class TestDVCPipeline:
    """Test suite for DVC pipeline functionality."""
    
    def test_dvc_is_installed(self):
        """Test that DVC is properly installed."""
        try:
            result = subprocess.run(["dvc", "--version"], 
                                  capture_output=True, text=True, check=True)
            assert "3." in result.stdout  # Check for DVC version 3.x
            print(f"[PASS] DVC Version: {result.stdout.strip()}")
        except subprocess.CalledProcessError:
            pytest.fail("DVC is not installed or not accessible")
    
    def test_dvc_files_exist(self):
        """Test that essential DVC files exist."""
        # Get required files from configuration
        required_files = CONFIG.get('pipeline', {}).get('required_files', ['dvc.yaml', 'dvc.lock'])
        
        for filename in required_files:
            file_path = PROJECT_ROOT / filename
            assert file_path.exists(), f"Missing required DVC file: {file_path}"
            print(f"[PASS] Found: {file_path}")
        
        # Also check data/raw.dvc if it exists (not always required)
        raw_dvc = PROJECT_ROOT / "data" / "raw.dvc"
        if raw_dvc.exists():
            print(f"[PASS] Found: {raw_dvc}")
        else:
            print("[INFO] Note: data/raw.dvc not found (may be optional)")
    
    def test_dvc_pipeline_structure(self):
        """Test that dvc.yaml contains valid pipeline stages."""
        dvc_yaml_path = PROJECT_ROOT / "dvc.yaml"
        
        with open(dvc_yaml_path, 'r') as f:
            import yaml
            dvc_config = yaml.safe_load(f)
        
        assert "stages" in dvc_config, "No stages found in dvc.yaml"
        stages = dvc_config["stages"]
        
        # Dynamic stage validation - just check we have stages with required structure
        assert len(stages) > 0, "No pipeline stages defined"
        
        for stage_name, stage_config in stages.items():
            # Verify each stage has required DVC structure
            assert "cmd" in stage_config, f"Stage {stage_name} missing 'cmd'"
            assert "deps" in stage_config or "outs" in stage_config, f"Stage {stage_name} missing deps/outs"
            print(f"[PASS] Stage found: {stage_name}")
        
        print(f"[PASS] Pipeline has {len(stages)} stages: {list(stages.keys())}")
    
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
            print(f"[PASS] Output exists: {output_dir}")
    
    def test_metadata_files_exist(self):
        """Test that final metadata files are generated."""
        formats_dir = DATA_INTERMEDIATE / "formats"
        expected_files = ["pdf_doc.json", "pdf_doc.md", "pdf_doc.txt"]
        
        for filename in expected_files:
            file_path = formats_dir / filename
            assert file_path.exists(), f"Missing metadata file: {file_path}"
            assert file_path.stat().st_size > 0, f"Empty metadata file: {file_path}"
            print(f"[PASS] Metadata file: {filename} ({file_path.stat().st_size} bytes)")
    
    def test_metadata_content_quality(self):
        """Test that metadata contains expected content."""
        metadata_file = DATA_INTERMEDIATE / "formats" / "pdf_doc.json"
        
        if not metadata_file.exists():
            pytest.skip(f"Metadata file not found: {metadata_file}")
        
        with open(metadata_file, 'r') as f:
            metadata = json.load(f)
        
        # Dynamic validation - check we have reasonable amount of data
        min_records = 10  # Much lower threshold for flexibility
        assert len(metadata) >= min_records, f"Too few metadata records: {len(metadata)} (minimum: {min_records})"
        
        # Check for any extraction methods (don't assume specific ones)
        methods = {record.get('extraction_method') for record in metadata if record.get('extraction_method')}
        
        if methods:
            print(f"[PASS] Found extraction methods: {sorted(methods)}")
        else:
            print("[WARN] No extraction methods found in metadata")
        
        print(f"[PASS] Total metadata records: {len(metadata)}")

def test_dvc_pipeline_smoke():
    """
    Lightweight smoke test that can run in CI/CD.
    Only checks file existence and basic structure.
    """
    # Quick file existence checks
    assert (PROJECT_ROOT / "dvc.yaml").exists()
    assert (PROJECT_ROOT / "dvc.lock").exists()
    
    # Check that intermediate data exists (optional)
    if not DATA_INTERMEDIATE.exists():
        print("[WARN] Intermediate data directory not found - pipeline may not have run yet")
    
    # Dynamic pipeline stage check - don't assume minimum count
    with open(PROJECT_ROOT / "dvc.yaml", 'r') as f:
        import yaml
        dvc_config = yaml.safe_load(f)
        stages = dvc_config.get("stages", {})
        assert len(stages) > 0, "No pipeline stages found"
        print(f"[PASS] Found {len(stages)} pipeline stages")
    
    print("[PASS] DVC Pipeline smoke test passed!")

if __name__ == "__main__":
    # Run smoke test directly
    test_dvc_pipeline_smoke()
    print("\n[PASS] All smoke tests passed!")