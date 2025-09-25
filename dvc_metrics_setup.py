#!/usr/bin/env python3
"""
DVC Metrics Setup and Management
Team 5 - DAMG7245 Fall 2025

This script sets up and manages metrics tracking for the LANTERN pipeline
and Lab 7 Google AI integration using DVC.

Usage:
    python dvc_metrics_setup.py --add-existing
    python dvc_metrics_setup.py --create-config
    python dvc_metrics_setup.py --compare
"""

import argparse
import datetime
import json
import re
import subprocess
import sys
from pathlib import Path


class DVCMetricsManager:
    """Manages DVC metrics tracking for pipeline outputs."""

    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.data_parsed = self.project_root / "data" / "parsed"
        self.reports_dir = self.project_root / "reports" / "google_ai"

    def find_pipeline_metrics(self):
        """Find existing pipeline summary JSON files."""
        metrics_files = []

        # Find pipeline summary files in data/parsed
        if self.data_parsed.exists():
            for json_file in self.data_parsed.glob("**/*.json"):
                if "pipeline_summary" in json_file.name or "summary" in json_file.name:
                    relative_path = json_file.relative_to(self.project_root)
                    metrics_files.append(
                        {
                            "file": str(relative_path),
                            "type": "pipeline_summary",
                            "source": "full_pipeline",
                        }
                    )

        # Find Lab 7 metrics in reports/google_ai
        if self.reports_dir.exists():
            for json_file in self.reports_dir.glob("**/parsed_results/*.json"):
                if "summary" in json_file.name:
                    relative_path = json_file.relative_to(self.project_root)
                    metrics_files.append(
                        {
                            "file": str(relative_path),
                            "type": "lab7_summary",
                            "source": "lab7_processing",
                        }
                    )

        return metrics_files

    def add_metrics_to_dvc(self, metrics_files):
        """Add metrics files to DVC tracking."""
        commands = []
        for metric in metrics_files:
            cmd = f"dvc metrics add {metric['file']}"
            commands.append(
                {"command": cmd, "file": metric["file"], "type": metric["type"]}
            )
        return commands

    def execute_dvc_commands(self, commands):
        """Execute DVC metrics commands."""
        results = []
        for cmd_info in commands:
            try:
                result = subprocess.run(
                    cmd_info["command"].split(),
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                )
                results.append(
                    {
                        "command": cmd_info["command"],
                        "success": result.returncode == 0,
                        "stdout": result.stdout.strip(),
                        "stderr": result.stderr.strip(),
                        "file": cmd_info["file"],
                    }
                )
            except Exception as e:
                results.append(
                    {
                        "command": cmd_info["command"],
                        "success": False,
                        "error": str(e),
                        "file": cmd_info["file"],
                    }
                )
        return results

    def create_metrics_config(self):
        """Create a dvc.yaml metrics configuration."""
        metrics_config = {
            "metrics": [
                {"data/parsed/pipeline_summary_*.json": {"cache": False}},
                {"reports/google_ai/*/parsed_results/summary*.json": {"cache": False}},
            ]
        }
        return metrics_config

    def update_dvc_yaml_with_metrics(self):
        """Update dvc.yaml to include metrics configuration."""
        dvc_yaml_path = self.project_root / "dvc.yaml"

        if not dvc_yaml_path.exists():
            print("Warning: dvc.yaml not found. Create pipeline first.")
            return False

        try:
            import yaml

            # Read existing dvc.yaml
            with open(dvc_yaml_path, "r") as f:
                dvc_config = yaml.safe_load(f)

            # Add metrics configuration to each stage
            if "stages" in dvc_config:
                # Add metrics to full_pipeline stage
                if "full_pipeline" in dvc_config["stages"]:
                    dvc_config["stages"]["full_pipeline"]["metrics"] = [
                        "data/parsed/pipeline_summary_*.json"
                    ]

                # Add metrics to lab7_processing stage
                if "lab7_processing" in dvc_config["stages"]:
                    dvc_config["stages"]["lab7_processing"]["metrics"] = [
                        "reports/google_ai/*/parsed_results/summary*.json"
                    ]

            # Write updated configuration
            with open(dvc_yaml_path, "w") as f:
                yaml.dump(dvc_config, f, default_flow_style=False, sort_keys=False)

            print(f"✓ Updated {dvc_yaml_path} with metrics configuration")
            return True

        except Exception as e:
            print(f"Error updating dvc.yaml: {e}")
            return False

    def show_metrics_diff(self):
        """Show metrics differences between runs."""
        try:
            result = subprocess.run(
                ["dvc", "metrics", "diff"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
            )

            if result.returncode == 0:
                return result.stdout
            else:
                return f"Error running metrics diff: {result.stderr}"

        except Exception as e:
            return f"Error: {e}"

    def create_metrics_summary_script(self):
        """Create a script to generate metrics summaries."""
        script_content = '''#!/usr/bin/env python3
"""
Pipeline Metrics Summary Generator
Generates standardized metrics summaries for LANTERN pipeline runs.
"""

import json
import datetime
from pathlib import Path

def create_pipeline_metrics_summary(output_dir, processing_stats=None):
    """Create a standardized metrics summary for pipeline output."""
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    
    summary = {
        "run_timestamp": timestamp,
        "pipeline_version": "LANTERN-v1.0",
        "processing_stats": processing_stats or {},
        "outputs_generated": {
            "text_files": len(list(Path(output_dir).glob("**/text/*.txt"))),
            "json_files": len(list(Path(output_dir).glob("**/*.json"))),
            "markdown_files": len(list(Path(output_dir).glob("**/*.md"))),
            "layout_files": len(list(Path(output_dir).glob("**/layout/*.json"))),
            "table_files": len(list(Path(output_dir).glob("**/tables/*.csv")))
        },
        "total_files_processed": 1,  # Assuming single PDF for now
        "execution_time_seconds": processing_stats.get("execution_time", 0) if processing_stats else 0
    }
    
    # Save summary
    summary_file = Path(output_dir) / f"pipeline_summary_{timestamp}.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary_file

def create_lab7_metrics_summary(reports_dir, session_id, processing_stats=None):
    """Create a standardized metrics summary for Lab 7 output."""
    summary = {
        "session_id": session_id,
        "lab7_version": "v1.0",
        "google_ai_integration": True,
        "processing_stats": processing_stats or {},
        "outputs_generated": {
            "parsed_documents": len(list(Path(reports_dir).glob("*/parsed_results/*.json"))),
            "comparison_files": len(list(Path(reports_dir).glob("*/parsed_data_comparison/*.md"))),
            "final_reports": len(list(Path(reports_dir).glob("*/final_reports/*.md")))
        }
    }
    
    # Save summary
    summary_file = Path(reports_dir) / session_id / "parsed_results" / "summary.json"
    summary_file.parent.mkdir(parents=True, exist_ok=True)
    
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    return summary_file

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        if sys.argv[1] == "pipeline":
            create_pipeline_metrics_summary(sys.argv[2])
        elif sys.argv[1] == "lab7":
            create_lab7_metrics_summary(sys.argv[2], sys.argv[3])
'''

        script_path = self.project_root / "utils" / "generate_metrics.py"
        script_path.parent.mkdir(exist_ok=True)

        with open(script_path, "w") as f:
            f.write(script_content)

        # Make executable
        script_path.chmod(0o755)

        return script_path


def main():
    parser = argparse.ArgumentParser(description="DVC Metrics Setup and Management")
    parser.add_argument(
        "--add-existing",
        action="store_true",
        help="Add existing metrics files to DVC tracking",
    )
    parser.add_argument(
        "--create-config",
        action="store_true",
        help="Update dvc.yaml with metrics configuration",
    )
    parser.add_argument(
        "--compare", action="store_true", help="Show metrics differences between runs"
    )
    parser.add_argument(
        "--create-generator",
        action="store_true",
        help="Create metrics summary generator script",
    )
    parser.add_argument(
        "--show-files", action="store_true", help="Show discovered metrics files"
    )

    args = parser.parse_args()

    # Initialize metrics manager
    manager = DVCMetricsManager()

    # Find existing metrics files
    metrics_files = manager.find_pipeline_metrics()

    if args.show_files or not any(
        [args.add_existing, args.create_config, args.compare, args.create_generator]
    ):
        print("Discovered Metrics Files:")
        print("=" * 40)
        for metric in metrics_files:
            print(f"  {metric['file']} ({metric['type']})")

        if not metrics_files:
            print("  No metrics files found yet.")
            print("\n  Run the pipeline first to generate metrics:")
            print("    dvc repro")

    # Add existing metrics to DVC
    if args.add_existing and metrics_files:
        print("\nAdding existing metrics to DVC:")
        commands = manager.add_metrics_to_dvc(metrics_files)
        results = manager.execute_dvc_commands(commands)

        for result in results:
            status = "✓" if result["success"] else "✗"
            print(f"  {status} {result['file']}")
            if not result["success"]:
                print(
                    f"    Error: {result.get('stderr', result.get('error', 'Unknown error'))}"
                )

    # Update dvc.yaml configuration
    if args.create_config:
        print("\nUpdating dvc.yaml with metrics configuration:")
        success = manager.update_dvc_yaml_with_metrics()
        if success:
            print("✓ Metrics configuration added to dvc.yaml")
        else:
            print("✗ Failed to update dvc.yaml")

    # Show metrics comparison
    if args.compare:
        print("\nMetrics Comparison:")
        print("=" * 40)
        diff_output = manager.show_metrics_diff()
        print(diff_output)

    # Create metrics generator script
    if args.create_generator:
        script_path = manager.create_metrics_summary_script()
        print(f"\n✓ Created metrics generator script: {script_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
