#!/usr/bin/env python3
"""
DVC Versioned Output Manager
Handles versioned outputs to prevent overlapping and enable run comparison.

This script creates timestamped output directories and maintains a registry
of all pipeline runs for easy comparison and reproducibility.

Usage:
    python3 scripts/setup_versioned_outputs.py --run-id $(date +%Y%m%d_%H%M%S)
"""

import argparse
import json
import os
import shutil
from datetime import datetime
from pathlib import Path


class VersionedOutputManager:
    """Manages versioned outputs for DVC pipeline runs."""
    
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.runs_registry = self.base_dir / "runs_registry.json"
        self.versioned_outputs_dir = self.base_dir / "versioned_outputs"
        
    def create_run_directory(self, run_id=None):
        """Create a new versioned run directory."""
        if run_id is None:
            run_id = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        run_dir = self.versioned_outputs_dir / f"run_{run_id}"
        run_dir.mkdir(parents=True, exist_ok=True)
        
        # Create subdirectories for each stage output
        subdirs = [
            "intermediate/text",
            "intermediate/tables", 
            "intermediate/layout",
            "intermediate/docling",
            "intermediate/metadata",
            "intermediate/formats",
            "metrics",
            "reports"
        ]
        
        for subdir in subdirs:
            (run_dir / subdir).mkdir(parents=True, exist_ok=True)
        
        return run_dir, run_id
    
    def register_run(self, run_id, run_dir, metadata=None):
        """Register a new run in the registry."""
        if self.runs_registry.exists():
            with open(self.runs_registry, 'r') as f:
                registry = json.load(f)
        else:
            registry = {"runs": []}
        
        run_info = {
            "run_id": run_id,
            "timestamp": datetime.now().isoformat(),
            "run_directory": str(run_dir),
            "status": "running",
            "metadata": metadata or {}
        }
        
        registry["runs"].append(run_info)
        
        with open(self.runs_registry, 'w') as f:
            json.dump(registry, f, indent=2)
        
        return run_info
    
    def update_run_status(self, run_id, status, summary=None):
        """Update the status of a run."""
        if not self.runs_registry.exists():
            return
        
        with open(self.runs_registry, 'r') as f:
            registry = json.load(f)
        
        for run in registry["runs"]:
            if run["run_id"] == run_id:
                run["status"] = status
                run["completion_time"] = datetime.now().isoformat()
                if summary:
                    run["summary"] = summary
                break
        
        with open(self.runs_registry, 'w') as f:
            json.dump(registry, f, indent=2)
    
    def list_runs(self, limit=10):
        """List recent runs."""
        if not self.runs_registry.exists():
            return []
        
        with open(self.runs_registry, 'r') as f:
            registry = json.load(f)
        
        # Return most recent runs
        return sorted(registry["runs"], key=lambda x: x["timestamp"], reverse=True)[:limit]
    
    def archive_old_outputs(self, keep_recent=5):
        """Archive old output directories to save space."""
        runs = self.list_runs()
        
        if len(runs) <= keep_recent:
            return
        
        archive_dir = self.versioned_outputs_dir / "archived"
        archive_dir.mkdir(exist_ok=True)
        
        runs_to_archive = runs[keep_recent:]
        
        for run in runs_to_archive:
            run_dir = Path(run["run_directory"])
            if run_dir.exists():
                archive_path = archive_dir / f"{run['run_id']}.tar.gz"
                shutil.make_archive(archive_path.with_suffix(''), 'gztar', run_dir)
                shutil.rmtree(run_dir)
                print(f"Archived run {run['run_id']} to {archive_path}")


def setup_dvc_versioned_config(run_id):
    """Create DVC configuration for versioned outputs."""
    dvc_config = {
        "vars": {
            "run_id": run_id,
            "timestamp": datetime.now().strftime("%Y%m%d_%H%M%S"),
            "output_base": f"versioned_outputs/run_{run_id}"
        }
    }
    
    # Write to dvc.yaml vars section
    config_file = Path("dvc_vars.yaml")
    with open(config_file, 'w') as f:
        import yaml
        yaml.dump(dvc_config, f, default_flow_style=False)
    
    print(f"DVC variables configuration saved to: {config_file}")
    return dvc_config


def main():
    parser = argparse.ArgumentParser(description="Setup versioned outputs for DVC pipeline")
    parser.add_argument("--run-id", help="Custom run ID (default: timestamp)")
    parser.add_argument("--archive-old", action="store_true", help="Archive old runs")
    parser.add_argument("--list-runs", action="store_true", help="List recent runs")
    
    args = parser.parse_args()
    
    manager = VersionedOutputManager()
    
    if args.list_runs:
        runs = manager.list_runs()
        print("Recent Pipeline Runs:")
        print("-" * 50)
        for run in runs:
            print(f"Run ID: {run['run_id']}")
            print(f"Status: {run['status']}")
            print(f"Timestamp: {run['timestamp']}")
            if 'summary' in run:
                summary = run['summary']
                print(f"Success Rate: {summary.get('overall_success_rate', 'N/A')}")
                print(f"Processing Time: {summary.get('total_processing_time', 'N/A')}s")
            print("-" * 30)
        return
    
    if args.archive_old:
        manager.archive_old_outputs()
        return
    
    # Create new versioned run
    run_dir, run_id = manager.create_run_directory(args.run_id)
    run_info = manager.register_run(run_id, run_dir)
    
    # Setup DVC configuration
    dvc_config = setup_dvc_versioned_config(run_id)
    
    print(f"Created versioned run: {run_id}")
    print(f"Run directory: {run_dir}")
    print(f"Registry updated with run info")
    print("\nTo use this run with DVC:")
    print(f"export DVC_RUN_ID={run_id}")
    print(f"dvc repro")


if __name__ == "__main__":
    main()