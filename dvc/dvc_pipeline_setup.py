#!/usr/bin/env python3
"""
Dynamic DVC Pipeline Setup Script
Team 5 - DAMG7245 Fall 2025

This script creates flexible DVC pipeline configurations that can handle:
- Full LANTERN pipeline only
- Full pipeline + Lab 7 Google AI integration
- Lab 7 only mode
- Custom configurations

Usage:
    python dvc_pipeline_setup.py --mode full
    python dvc_pipeline_setup.py --mode full-with-lab7
    python dvc_pipeline_setup.py --mode lab7-only
    python dvc_pipeline_setup.py --mode custom --stages "stage1,stage2"
"""

import argparse
import datetime
import json
import subprocess
import sys
from pathlib import Path

import yaml


class DVCPipelineManager:
    """Manages DVC pipeline configuration and execution."""

    def __init__(self, project_root=None):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.dvc_yaml_path = self.project_root / "dvc.yaml"
        self.data_raw = self.project_root / "data" / "raw"
        self.data_parsed = self.project_root / "data" / "parsed"
        self.reports_dir = self.project_root / "reports" / "google_ai"

    def create_full_pipeline_stage(
        self, output_dir="data/parsed", use_hybrid_tables=True
    ):
        """Create the full LANTERN pipeline stage."""
        cmd = ["python3", "run_complete_pipeline.py", "--out", output_dir]
        if use_hybrid_tables:
            cmd.append("--hybrid-tables")

        stage = {
            "cmd": " ".join(cmd),
            "deps": ["run_complete_pipeline.py", "src/", "data/raw/"],
            "outs": [output_dir + "/"],
            "desc": "Complete LANTERN pipeline processing (Labs 1-6)",
        }
        return stage

    def create_lab7_stage(
        self, pdf_file="data/raw/tesla.pdf", pages="5 12", mode="pages"
    ):
        """Create Lab 7 Google AI integration stage."""
        if mode == "pages":
            cmd = f"python3 google_ai/run_lab7.py --pdf {pdf_file} --pages {pages}"
        elif mode == "random":
            cmd = f"python3 google_ai/run_lab7.py --pdf {pdf_file} --random 2 --seed 42"
        else:
            cmd = f"python3 google_ai/run_lab7.py --pdf {pdf_file} --all-pages"

        stage = {
            "cmd": cmd,
            "deps": [
                "google_ai/run_lab7.py",
                "google_ai/lab7_google_ai_integration.py",
                "google_ai/",
                pdf_file,
            ],
            "outs": ["reports/google_ai/"],
            "desc": f"Lab 7 Google Document AI processing ({mode} mode)",
        }
        return stage

    def create_combined_stage(
        self,
        output_dir="data/parsed",
        pdf_file="data/raw/tesla.pdf",
        pages="5 12",
        use_hybrid_tables=True,
    ):
        """Create a combined stage that runs both full pipeline and Lab 7."""
        full_cmd = ["python3", "run_complete_pipeline.py", "--out", output_dir]
        if use_hybrid_tables:
            full_cmd.append("--hybrid-tables")

        lab7_cmd = f"python3 google_ai/run_lab7.py --pdf {pdf_file} --pages {pages}"

        combined_cmd = f"({' '.join(full_cmd)}) && ({lab7_cmd})"

        stage = {
            "cmd": combined_cmd,
            "deps": [
                "run_complete_pipeline.py",
                "src/",
                "google_ai/run_lab7.py",
                "google_ai/lab7_google_ai_integration.py",
                "google_ai/",
                "data/raw/",
            ],
            "outs": [output_dir + "/", "reports/google_ai/"],
            "desc": "Combined LANTERN pipeline + Lab 7 Google AI processing",
        }
        return stage

    def create_pipeline_config(self, mode="full", **kwargs):
        """Create the DVC pipeline configuration based on mode."""
        stages = {}

        if mode == "full":
            stages["full_pipeline"] = self.create_full_pipeline_stage(
                output_dir=kwargs.get("output_dir", "data/parsed"),
                use_hybrid_tables=kwargs.get("use_hybrid_tables", True),
            )

        elif mode == "lab7-only":
            stages["lab7_processing"] = self.create_lab7_stage(
                pdf_file=kwargs.get("pdf_file", "data/raw/tesla.pdf"),
                pages=kwargs.get("pages", "5 12"),
                mode=kwargs.get("lab7_mode", "pages"),
            )

        elif mode == "full-with-lab7":
            stages["full_pipeline_with_lab7"] = self.create_combined_stage(
                output_dir=kwargs.get("output_dir", "data/parsed"),
                pdf_file=kwargs.get("pdf_file", "data/raw/tesla.pdf"),
                pages=kwargs.get("pages", "5 12"),
                use_hybrid_tables=kwargs.get("use_hybrid_tables", True),
            )

        elif mode == "separate":
            # Create separate stages for full pipeline and lab7
            stages["full_pipeline"] = self.create_full_pipeline_stage(
                output_dir=kwargs.get("output_dir", "data/parsed"),
                use_hybrid_tables=kwargs.get("use_hybrid_tables", True),
            )
            stages["lab7_processing"] = self.create_lab7_stage(
                pdf_file=kwargs.get("pdf_file", "data/raw/tesla.pdf"),
                pages=kwargs.get("pages", "5 12"),
                mode=kwargs.get("lab7_mode", "pages"),
            )

        return {"stages": stages}

    def write_dvc_yaml(self, config):
        """Write the DVC configuration to dvc.yaml file."""
        try:
            with open(self.dvc_yaml_path, "w") as f:
                yaml.dump(config, f, default_flow_style=False, sort_keys=False)
            print(f"✓ DVC pipeline configuration written to {self.dvc_yaml_path}")
            return True
        except Exception as e:
            print(f"Error writing DVC configuration: {e}")
            return False

    def setup_metrics_tracking(self):
        """Set up metrics tracking for pipeline outputs."""
        metrics_commands = []

        # Add metrics for parsed data summaries
        parsed_metrics = self.data_parsed.glob("*/pipeline_summary*.json")
        for metric_file in parsed_metrics:
            relative_path = metric_file.relative_to(self.project_root)
            metrics_commands.append(f"dvc metrics add {relative_path}")

        # Add metrics for Lab 7 results
        lab7_metrics = self.reports_dir.glob("*/parsed_results/summary*.json")
        for metric_file in lab7_metrics:
            relative_path = metric_file.relative_to(self.project_root)
            metrics_commands.append(f"dvc metrics add {relative_path}")

        return metrics_commands

    def create_gitignore_updates(self):
        """Create .gitignore updates for DVC-managed outputs."""
        gitignore_entries = [
            "# DVC-managed pipeline outputs",
            "/data/parsed/",
            "/reports/google_ai/",
            "*.dvc",
            "",
        ]
        return gitignore_entries


def main():
    parser = argparse.ArgumentParser(description="Dynamic DVC Pipeline Setup")
    parser.add_argument(
        "--mode",
        choices=["full", "lab7-only", "full-with-lab7", "separate"],
        default="separate",
        help="Pipeline mode to configure",
    )
    parser.add_argument(
        "--output-dir", default="data/parsed", help="Output directory for parsed data"
    )
    parser.add_argument(
        "--pdf-file",
        default="data/raw/tesla.pdf",
        help="PDF file to process with Lab 7",
    )
    parser.add_argument(
        "--pages", default="5 12", help="Page range for Lab 7 processing"
    )
    parser.add_argument(
        "--lab7-mode",
        choices=["pages", "random", "all"],
        default="pages",
        help="Lab 7 processing mode",
    )
    parser.add_argument(
        "--hybrid-tables",
        action="store_true",
        default=True,
        help="Use hybrid table extraction",
    )
    parser.add_argument(
        "--write-config",
        action="store_true",
        default=True,
        help="Write configuration to dvc.yaml",
    )
    parser.add_argument(
        "--setup-metrics", action="store_true", help="Set up metrics tracking"
    )

    args = parser.parse_args()

    # Initialize pipeline manager
    manager = DVCPipelineManager()

    # Create pipeline configuration
    config = manager.create_pipeline_config(
        mode=args.mode,
        output_dir=args.output_dir,
        pdf_file=args.pdf_file,
        pages=args.pages,
        lab7_mode=args.lab7_mode,
        use_hybrid_tables=args.hybrid_tables,
    )

    # Display configuration
    print("Generated DVC Pipeline Configuration:")
    print("=" * 50)
    print(yaml.dump(config, default_flow_style=False))

    # Write configuration if requested
    if args.write_config:
        success = manager.write_dvc_yaml(config)
        if success:
            print("\n✓ Pipeline configuration saved successfully!")
            print("\nNext steps:")
            print("1. Run: dvc repro")
            print("2. Check status: dvc status")
            print("3. View pipeline: dvc dag")
        else:
            print("\n✗ Failed to save pipeline configuration")
            return 1

    # Setup metrics tracking if requested
    if args.setup_metrics:
        metrics_commands = manager.setup_metrics_tracking()
        if metrics_commands:
            print("\nMetrics tracking commands:")
            for cmd in metrics_commands:
                print(f"  {cmd}")
        else:
            print("\nNo existing metrics files found to track")

    # Display gitignore suggestions
    gitignore_entries = manager.create_gitignore_updates()
    print("\nSuggested .gitignore entries:")
    for entry in gitignore_entries:
        print(f"  {entry}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
