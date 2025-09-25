#!/usr/bin/env python3
"""
DVC Pipeline Summary Generator
Aggregates metrics from all pipeline stages and creates comprehensive summaries
for run comparison and reproducibility tracking.

Usage:
    python3 scripts/generate_pipeline_summary.py --metrics-dir metrics/ --out metrics/pipeline_summary.json
"""

import argparse
import json
import os
import time
from datetime import datetime
from pathlib import Path


def load_stage_metrics(metrics_dir):
    """Load all stage metrics files."""
    metrics = {}
    metrics_path = Path(metrics_dir)
    
    for metrics_file in metrics_path.glob("*_metrics.json"):
        stage_name = metrics_file.stem.replace("_metrics", "")
        try:
            with open(metrics_file, 'r') as f:
                metrics[stage_name] = json.load(f)
        except Exception as e:
            print(f"Warning: Could not load {metrics_file}: {e}")
            metrics[stage_name] = {"error": str(e)}
    
    return metrics


def calculate_pipeline_summary(stage_metrics):
    """Calculate overall pipeline statistics."""
    summary = {
        "run_timestamp": datetime.now().isoformat(),
        "total_stages": len(stage_metrics),
        "successful_stages": 0,
        "failed_stages": 0,
        "total_processing_time": 0,
        "total_files_processed": 0,
        "stages": [],
        "overall_success_rate": 0
    }
    
    for stage_name, metrics in stage_metrics.items():
        if "error" not in metrics:
            summary["successful_stages"] += 1
            
            # Extract common metrics
            stage_summary = {
                "stage_name": stage_name,
                "processing_time_seconds": metrics.get("processing_time_seconds", 0),
                "files_processed": metrics.get("files_processed", 0),
                "success_rate": metrics.get("success_rate", 1.0),
                "output_size_mb": metrics.get("output_size_mb", 0),
                "memory_usage_mb": metrics.get("memory_usage_mb", 0)
            }
            
            summary["total_processing_time"] += stage_summary["processing_time_seconds"]
            summary["total_files_processed"] += stage_summary["files_processed"]
            summary["stages"].append(stage_summary)
        else:
            summary["failed_stages"] += 1
            summary["stages"].append({
                "stage_name": stage_name,
                "error": metrics["error"],
                "success_rate": 0.0
            })
    
    if summary["total_stages"] > 0:
        summary["overall_success_rate"] = summary["successful_stages"] / summary["total_stages"]
    
    return summary


def save_summary(summary, output_path):
    """Save pipeline summary to JSON file."""
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(output_path, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print(f"Pipeline summary saved to: {output_path}")


def create_comparison_report(metrics_dir, summary):
    """Create a comparison report if previous runs exist."""
    comparison_file = Path(metrics_dir) / "run_comparisons.json"
    
    # Load previous comparisons if they exist
    if comparison_file.exists():
        with open(comparison_file, 'r') as f:
            comparisons = json.load(f)
    else:
        comparisons = {"runs": []}
    
    # Add current run
    current_run = {
        "timestamp": summary["run_timestamp"],
        "total_processing_time": summary["total_processing_time"],
        "success_rate": summary["overall_success_rate"],
        "files_processed": summary["total_files_processed"],
        "stages_count": summary["total_stages"]
    }
    
    comparisons["runs"].append(current_run)
    
    # Keep only last 10 runs for comparison
    if len(comparisons["runs"]) > 10:
        comparisons["runs"] = comparisons["runs"][-10:]
    
    # Calculate trends if we have multiple runs
    if len(comparisons["runs"]) > 1:
        latest = comparisons["runs"][-1]
        previous = comparisons["runs"][-2]
        
        comparisons["trends"] = {
            "processing_time_change": latest["total_processing_time"] - previous["total_processing_time"],
            "success_rate_change": latest["success_rate"] - previous["success_rate"],
            "performance_improving": latest["total_processing_time"] < previous["total_processing_time"]
        }
    
    # Save updated comparisons
    with open(comparison_file, 'w') as f:
        json.dump(comparisons, f, indent=2)
    
    print(f"Run comparison data updated: {comparison_file}")


def main():
    parser = argparse.ArgumentParser(description="Generate DVC pipeline summary")
    parser.add_argument("--metrics-dir", required=True, help="Directory containing stage metrics")
    parser.add_argument("--out", required=True, help="Output file for pipeline summary")
    parser.add_argument("--create-reports", action="store_true", help="Create detailed reports")
    
    args = parser.parse_args()
    
    # Load metrics from all stages
    print(f"Loading metrics from: {args.metrics_dir}")
    stage_metrics = load_stage_metrics(args.metrics_dir)
    
    # Generate pipeline summary
    print("Calculating pipeline summary...")
    summary = calculate_pipeline_summary(stage_metrics)
    
    # Save summary
    save_summary(summary, args.out)
    
    # Create comparison reports
    create_comparison_report(args.metrics_dir, summary)
    
    # Print brief summary to console
    print("\n" + "="*50)
    print("PIPELINE EXECUTION SUMMARY")
    print("="*50)
    print(f"Timestamp: {summary['run_timestamp']}")
    print(f"Total Stages: {summary['total_stages']}")
    print(f"Successful: {summary['successful_stages']}")
    print(f"Failed: {summary['failed_stages']}")
    print(f"Success Rate: {summary['overall_success_rate']:.2%}")
    print(f"Total Processing Time: {summary['total_processing_time']:.2f} seconds")
    print(f"Files Processed: {summary['total_files_processed']}")
    print("="*50)


if __name__ == "__main__":
    main()