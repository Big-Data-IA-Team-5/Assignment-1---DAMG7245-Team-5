#!/usr/bin/env python3
"""
DVC Workflow Utilities
Team 5 - DAMG7245 Fall 2025

Convenient utilities for common DVC operations in the LANTERN pipeline.

Usage:
    python dvc_utils.py status          # Show pipeline status
    python dvc_utils.py run             # Run complete pipeline
    python dvc_utils.py metrics         # Show metrics
    python dvc_utils.py compare         # Compare with previous run
    python dvc_utils.py setup MODE      # Setup pipeline configuration
"""

import argparse
import json
import subprocess
import sys
from pathlib import Path


class DVCUtils:
    """Utility functions for common DVC operations."""

    def __init__(self):
        self.project_root = Path.cwd()

    def run_command(self, cmd, description=""):
        """Execute a command and return the result."""
        print(f"📝 {description}" if description else f"Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(
                cmd, capture_output=True, text=True, cwd=self.project_root
            )
            return result
        except Exception as e:
            print(f"❌ Error: {e}")
            return None

    def show_status(self):
        """Show DVC pipeline status."""
        print("🔍 DVC Pipeline Status")
        print("=" * 40)

        result = self.run_command(["dvc", "status"], "Checking pipeline status...")
        if result and result.returncode == 0:
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("✅ All stages are up to date")
        else:
            print(
                f"❌ Error checking status: {result.stderr if result else 'Unknown error'}"
            )

        # Also show DAG
        print("\n📊 Pipeline Structure:")
        dag_result = self.run_command(["dvc", "dag"], "")
        if dag_result and dag_result.returncode == 0:
            print(dag_result.stdout)

    def run_pipeline(self, force=False, stage=None):
        """Run the DVC pipeline."""
        cmd = ["dvc", "repro"]
        if force:
            cmd.append("--force")
        if stage:
            cmd.append(stage)

        description = f"Running {'all stages' if not stage else f'stage: {stage}'}"
        if force:
            description += " (forced)"

        result = self.run_command(cmd, description)

        if result and result.returncode == 0:
            print("✅ Pipeline completed successfully!")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"❌ Pipeline failed: {result.stderr if result else 'Unknown error'}")
            return False

        return True

    def show_metrics(self, json_format=False):
        """Show pipeline metrics."""
        print("📈 Pipeline Metrics")
        print("=" * 40)

        cmd = ["dvc", "metrics", "show"]
        if json_format:
            cmd.append("--json")

        result = self.run_command(cmd, "Retrieving metrics...")

        if result and result.returncode == 0:
            if result.stdout.strip():
                if json_format:
                    try:
                        metrics = json.loads(result.stdout)
                        print(json.dumps(metrics, indent=2))
                    except json.JSONDecodeError:
                        print(result.stdout)
                else:
                    print(result.stdout)
            else:
                print("📊 No metrics available yet. Run the pipeline first:")
                print("   python dvc_utils.py run")
        else:
            print(
                f"❌ Error retrieving metrics: {result.stderr if result else 'Unknown error'}"
            )

    def compare_metrics(self, revision="HEAD~1"):
        """Compare metrics with previous run."""
        print(f"🔄 Comparing metrics with {revision}")
        print("=" * 40)

        result = self.run_command(
            ["dvc", "metrics", "diff", revision], f"Comparing with {revision}..."
        )

        if result and result.returncode == 0:
            if result.stdout.strip():
                print(result.stdout)
            else:
                print("📊 No differences found")
        else:
            print(
                f"❌ Error comparing metrics: {result.stderr if result else 'Unknown error'}"
            )

    def setup_pipeline(self, mode="separate"):
        """Setup pipeline configuration."""
        print(f"⚙️ Setting up pipeline in '{mode}' mode")
        print("=" * 40)

        result = self.run_command(
            ["python", "dvc_pipeline_setup.py", "--mode", mode, "--write-config"],
            f"Configuring pipeline for {mode} mode...",
        )

        if result and result.returncode == 0:
            print("✅ Pipeline configuration updated!")
            print(result.stdout)
        else:
            print(f"❌ Setup failed: {result.stderr if result else 'Unknown error'}")

    def clean_outputs(self):
        """Remove pipeline outputs (use with caution)."""
        print("🧹 Cleaning pipeline outputs")
        print("=" * 40)
        print("⚠️  This will remove all generated outputs!")

        confirm = input("Are you sure? (yes/no): ")
        if confirm.lower() != "yes":
            print("❌ Cancelled")
            return

        # Remove DVC-managed outputs
        outputs = ["data/parsed", "reports/google_ai"]
        for output in outputs:
            output_path = self.project_root / output
            if output_path.exists():
                import shutil

                shutil.rmtree(output_path)
                print(f"🗑️  Removed {output}")
            else:
                print(f"ℹ️  {output} not found")

        print("✅ Cleanup completed")

    def show_help(self):
        """Show help information."""
        help_text = """
🚀 DVC Utils - LANTERN Pipeline Management

Available Commands:
  status          Show pipeline status and structure
  run             Run the complete pipeline
  run-force       Force re-run the pipeline
  run-stage NAME  Run specific stage (full_pipeline or lab7_processing)
  metrics         Show current metrics
  metrics-json    Show metrics in JSON format
  compare         Compare metrics with previous run
  setup MODE      Setup pipeline (modes: separate, full, lab7-only, full-with-lab7)
  clean           Remove all pipeline outputs (CAUTION!)
  help            Show this help message

Examples:
  python dvc_utils.py status
  python dvc_utils.py run
  python dvc_utils.py run-stage full_pipeline
  python dvc_utils.py setup separate
  python dvc_utils.py compare
  python dvc_utils.py metrics-json

Quick Workflow:
  1. python dvc_utils.py status     # Check what needs to run
  2. python dvc_utils.py run        # Execute pipeline
  3. python dvc_utils.py metrics    # View results
  4. python dvc_utils.py compare    # Compare with previous run
"""
        print(help_text)


def main():
    parser = argparse.ArgumentParser(description="DVC Workflow Utilities")
    parser.add_argument("command", nargs="?", default="help", help="Command to execute")
    parser.add_argument("args", nargs="*", help="Additional arguments")

    args = parser.parse_args()
    utils = DVCUtils()

    if args.command == "status":
        utils.show_status()
    elif args.command == "run":
        utils.run_pipeline()
    elif args.command == "run-force":
        utils.run_pipeline(force=True)
    elif args.command == "run-stage":
        if args.args:
            utils.run_pipeline(stage=args.args[0])
        else:
            print("❌ Please specify stage name (full_pipeline or lab7_processing)")
    elif args.command == "metrics":
        utils.show_metrics()
    elif args.command == "metrics-json":
        utils.show_metrics(json_format=True)
    elif args.command == "compare":
        revision = args.args[0] if args.args else "HEAD~1"
        utils.compare_metrics(revision)
    elif args.command == "setup":
        mode = args.args[0] if args.args else "separate"
        utils.setup_pipeline(mode)
    elif args.command == "clean":
        utils.clean_outputs()
    elif args.command == "help":
        utils.show_help()
    else:
        print(f"❌ Unknown command: {args.command}")
        utils.show_help()
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
