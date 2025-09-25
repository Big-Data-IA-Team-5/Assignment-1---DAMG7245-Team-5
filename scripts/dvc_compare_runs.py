#!/usr/bin/env python3
"""
DVC Metrics Comparison and Reproducibility Tool

This script provides comprehensive functionality for:
1. Comparing metrics across different pipeline runs
2. Generating reproducibility reports
3. Creating visualizations for performance analysis
4. Detecting data drift and model degradation

Usage:
    # Compare two specific runs
    python3 scripts/dvc_compare_runs.py --run1 20240925_143022 --run2 20240925_150145

    # Compare current run with previous best
    python3 scripts/dvc_compare_runs.py --compare-with-best

    # Generate reproducibility report
    python3 scripts/dvc_compare_runs.py --reproducibility-report

    # Show metrics trends over time
    python3 scripts/dvc_compare_runs.py --show-trends --last-n-runs 10
"""

import argparse
import json
import matplotlib.pyplot as plt
import pandas as pd
from datetime import datetime, timedelta
from pathlib import Path
import seaborn as sns


class DVCMetricsComparator:
    """Compare and analyze DVC pipeline runs for reproducibility."""
    
    def __init__(self, base_dir="."):
        self.base_dir = Path(base_dir)
        self.metrics_dir = self.base_dir / "metrics"
        self.runs_registry = self.base_dir / "runs_registry.json"
        self.versioned_outputs = self.base_dir / "versioned_outputs"
    
    def load_run_metrics(self, run_id):
        """Load metrics for a specific run."""
        if run_id == "current":
            # Load from current metrics directory
            metrics_path = self.metrics_dir
        else:
            # Load from versioned outputs
            metrics_path = self.versioned_outputs / f"run_{run_id}" / "metrics"
        
        if not metrics_path.exists():
            raise ValueError(f"Metrics not found for run: {run_id}")
        
        run_metrics = {}
        
        # Load pipeline summary
        summary_file = metrics_path / "pipeline_summary.json"
        if summary_file.exists():
            with open(summary_file, 'r') as f:
                run_metrics["summary"] = json.load(f)
        
        # Load individual stage metrics
        for metrics_file in metrics_path.glob("*_metrics.json"):
            if metrics_file.name != "pipeline_summary.json":
                stage_name = metrics_file.stem.replace("_metrics", "")
                with open(metrics_file, 'r') as f:
                    run_metrics[stage_name] = json.load(f)
        
        return run_metrics
    
    def compare_two_runs(self, run_id1, run_id2):
        """Compare metrics between two specific runs."""
        print(f"Comparing runs: {run_id1} vs {run_id2}")
        print("=" * 60)
        
        try:
            metrics1 = self.load_run_metrics(run_id1)
            metrics2 = self.load_run_metrics(run_id2)
        except ValueError as e:
            print(f"Error loading metrics: {e}")
            return None
        
        comparison = {
            "run1_id": run_id1,
            "run2_id": run_id2,
            "comparison_timestamp": datetime.now().isoformat(),
            "overall_comparison": {},
            "stage_comparisons": {}
        }
        
        # Compare overall metrics
        if "summary" in metrics1 and "summary" in metrics2:
            sum1, sum2 = metrics1["summary"], metrics2["summary"]
            
            comparison["overall_comparison"] = {
                "processing_time_change": sum2["total_processing_time"] - sum1["total_processing_time"],
                "success_rate_change": sum2["overall_success_rate"] - sum1["overall_success_rate"],
                "files_processed_change": sum2["total_files_processed"] - sum1["total_files_processed"],
                "performance_improved": sum2["total_processing_time"] < sum1["total_processing_time"],
                "quality_improved": sum2["overall_success_rate"] >= sum1["overall_success_rate"]
            }
            
            print(f"Processing Time: {sum1['total_processing_time']:.2f}s → {sum2['total_processing_time']:.2f}s "
                  f"({comparison['overall_comparison']['processing_time_change']:+.2f}s)")
            print(f"Success Rate: {sum1['overall_success_rate']:.2%} → {sum2['overall_success_rate']:.2%} "
                  f"({comparison['overall_comparison']['success_rate_change']:+.2%})")
            print(f"Files Processed: {sum1['total_files_processed']} → {sum2['total_files_processed']} "
                  f"({comparison['overall_comparison']['files_processed_change']:+d})")
        
        # Compare individual stages
        common_stages = set(metrics1.keys()) & set(metrics2.keys())
        common_stages.discard("summary")
        
        print(f"\nStage-by-Stage Comparison:")
        print("-" * 40)
        
        for stage in sorted(common_stages):
            stage1, stage2 = metrics1[stage], metrics2[stage]
            
            stage_comparison = {}
            
            if "processing_time_seconds" in stage1 and "processing_time_seconds" in stage2:
                time_change = stage2["processing_time_seconds"] - stage1["processing_time_seconds"]
                stage_comparison["processing_time_change"] = time_change
                print(f"{stage.upper()}: {stage1['processing_time_seconds']:.2f}s → {stage2['processing_time_seconds']:.2f}s "
                      f"({time_change:+.2f}s)")
            
            if "success_rate" in stage1 and "success_rate" in stage2:
                rate_change = stage2["success_rate"] - stage1["success_rate"]
                stage_comparison["success_rate_change"] = rate_change
                print(f"  Success Rate: {stage1['success_rate']:.2%} → {stage2['success_rate']:.2%} "
                      f"({rate_change:+.2%})")
            
            comparison["stage_comparisons"][stage] = stage_comparison
        
        # Save comparison results
        comparison_file = self.metrics_dir / f"comparison_{run_id1}_vs_{run_id2}.json"
        with open(comparison_file, 'w') as f:
            json.dump(comparison, f, indent=2)
        
        print(f"\nDetailed comparison saved to: {comparison_file}")
        return comparison
    
    def find_best_run(self, metric="overall_success_rate"):
        """Find the best performing run based on specified metric."""
        if not self.runs_registry.exists():
            return None
        
        with open(self.runs_registry, 'r') as f:
            registry = json.load(f)
        
        best_run = None
        best_value = float('-inf') if metric != "total_processing_time" else float('inf')
        
        for run in registry["runs"]:
            if "summary" in run and metric in run["summary"]:
                value = run["summary"][metric]
                
                if metric == "total_processing_time":  # Lower is better
                    if value < best_value:
                        best_value = value
                        best_run = run
                else:  # Higher is better
                    if value > best_value:
                        best_value = value
                        best_run = run
        
        return best_run
    
    def generate_reproducibility_report(self):
        """Generate a comprehensive reproducibility report."""
        print("DVC PIPELINE REPRODUCIBILITY REPORT")
        print("=" * 50)
        
        if not self.runs_registry.exists():
            print("No runs registry found. Run the pipeline first.")
            return
        
        with open(self.runs_registry, 'r') as f:
            registry = json.load(f)
        
        runs = registry["runs"]
        completed_runs = [r for r in runs if r["status"] == "completed"]
        
        print(f"Total Runs: {len(runs)}")
        print(f"Completed Runs: {len(completed_runs)}")
        print(f"Success Rate: {len(completed_runs)/len(runs):.2%}")
        
        if len(completed_runs) < 2:
            print("Need at least 2 completed runs for reproducibility analysis.")
            return
        
        # Analyze consistency across runs
        metrics_consistency = {}
        
        for run in completed_runs[-5:]:  # Analyze last 5 runs
            if "summary" in run:
                summary = run["summary"]
                for key, value in summary.items():
                    if isinstance(value, (int, float)):
                        if key not in metrics_consistency:
                            metrics_consistency[key] = []
                        metrics_consistency[key].append(value)
        
        print(f"\nMETRICS CONSISTENCY ANALYSIS:")
        print("-" * 30)
        
        for metric, values in metrics_consistency.items():
            if len(values) > 1:
                mean_val = sum(values) / len(values)
                std_val = (sum([(x - mean_val)**2 for x in values]) / len(values))**0.5
                cv = (std_val / mean_val * 100) if mean_val != 0 else 0
                
                print(f"{metric}: Mean={mean_val:.3f}, Std={std_val:.3f}, CV={cv:.1f}%")
        
        # Generate recommendations
        print(f"\nRECOMMENDATIONS:")
        print("-" * 20)
        
        if len(completed_runs) >= 3:
            recent_runs = completed_runs[-3:]
            processing_times = [r["summary"]["total_processing_time"] for r in recent_runs if "summary" in r]
            
            if processing_times:
                if processing_times[-1] > processing_times[0] * 1.2:
                    print("WARNING: Performance degradation detected - consider optimization")
                elif processing_times[-1] < processing_times[0] * 0.8:
                    print("Performance improvement detected")
                else:
                    print("Performance is stable")
    
    def show_trends(self, last_n_runs=10):
        """Show performance trends over time."""
        if not self.runs_registry.exists():
            print("No runs registry found.")
            return
        
        with open(self.runs_registry, 'r') as f:
            registry = json.load(f)
        
        runs = registry["runs"][-last_n_runs:]
        completed_runs = [r for r in runs if r["status"] == "completed" and "summary" in r]
        
        if len(completed_runs) < 2:
            print("Need at least 2 completed runs to show trends.")
            return
        
        # Prepare data for plotting
        timestamps = [datetime.fromisoformat(r["timestamp"]) for r in completed_runs]
        processing_times = [r["summary"]["total_processing_time"] for r in completed_runs]
        success_rates = [r["summary"]["overall_success_rate"] for r in completed_runs]
        
        # Create visualizations
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8))
        
        # Processing time trend
        ax1.plot(timestamps, processing_times, 'b-o', label='Processing Time')
        ax1.set_title('Processing Time Trend')
        ax1.set_ylabel('Time (seconds)')
        ax1.grid(True, alpha=0.3)
        
        # Success rate trend
        ax2.plot(timestamps, success_rates, 'g-o', label='Success Rate')
        ax2.set_title('Success Rate Trend')
        ax2.set_ylabel('Success Rate')
        ax2.set_xlabel('Run Timestamp')
        ax2.grid(True, alpha=0.3)
        
        plt.tight_layout()
        
        # Save the plot
        trends_plot = self.metrics_dir / "performance_trends.png"
        plt.savefig(trends_plot, dpi=300, bbox_inches='tight')
        print(f"Performance trends plot saved to: {trends_plot}")
        
        # Show recent statistics
        print(f"\nTRENDS ANALYSIS (Last {len(completed_runs)} runs):")
        print("-" * 40)
        print(f"Average Processing Time: {sum(processing_times)/len(processing_times):.2f}s")
        print(f"Average Success Rate: {sum(success_rates)/len(success_rates):.2%}")
        
        if len(processing_times) >= 3:
            recent_trend = (processing_times[-1] - processing_times[-3]) / 2
            if recent_trend > 0:
                print(f"WARNING: Processing time trending upward (+{recent_trend:.2f}s per run)")
            else:
                print(f"Processing time trending downward ({recent_trend:.2f}s per run)")


def main():
    parser = argparse.ArgumentParser(description="DVC Metrics Comparison and Analysis")
    parser.add_argument("--run1", help="First run ID to compare")
    parser.add_argument("--run2", help="Second run ID to compare")
    parser.add_argument("--compare-with-best", action="store_true", help="Compare current run with best previous run")
    parser.add_argument("--reproducibility-report", action="store_true", help="Generate reproducibility report")
    parser.add_argument("--show-trends", action="store_true", help="Show performance trends")
    parser.add_argument("--last-n-runs", type=int, default=10, help="Number of recent runs to analyze")
    
    args = parser.parse_args()
    
    comparator = DVCMetricsComparator()
    
    if args.run1 and args.run2:
        comparator.compare_two_runs(args.run1, args.run2)
    
    elif args.compare_with_best:
        best_run = comparator.find_best_run()
        if best_run:
            comparator.compare_two_runs(best_run["run_id"], "current")
        else:
            print("No previous runs found to compare with")
    
    elif args.reproducibility_report:
        comparator.generate_reproducibility_report()
    
    elif args.show_trends:
        comparator.show_trends(args.last_n_runs)
    
    else:
        print("Please specify an action. Use --help for options.")


if __name__ == "__main__":
    main()