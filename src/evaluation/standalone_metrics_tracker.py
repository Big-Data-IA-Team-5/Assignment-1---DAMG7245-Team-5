#!/usr/bin/env python3
"""
Standalone Metrics Tracking System

This module provides independent metrics tracking and regression detection without DVC dependency.
It creates a self-contained system for monitoring parser quality over time and detecting when
metrics degrade after code changes.

Key features:
- JSON-based metrics storage (no external dependencies)
- Automated baseline management
- Change detection and alerting
- Historical trend analysis
- Git integration for change correlation (optional)
"""

import json
import logging
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import hashlib
import shutil

import numpy as np


class StandaloneMetricsTracker:
    """
    Independent metrics tracking system for parser quality monitoring.
    Stores metrics in JSON format and provides regression detection capabilities.
    """
    
    def __init__(self, metrics_dir: Path, baseline_days: int = 7):
        """
        Initialize metrics tracker
        
        Args:
            metrics_dir: Directory to store metrics files
            baseline_days: Number of days to use for baseline calculation
        """
        self.metrics_dir = Path(metrics_dir)
        self.metrics_dir.mkdir(parents=True, exist_ok=True)
        
        self.baseline_days = baseline_days
        self.logger = logging.getLogger(__name__)
        
        # Metrics storage files
        self.current_metrics_file = self.metrics_dir / "current_metrics.json"
        self.historical_metrics_file = self.metrics_dir / "historical_metrics.jsonl"
        self.baselines_file = self.metrics_dir / "baselines.json"
        self.alerts_file = self.metrics_dir / "alerts.json"
        
        # Load existing data
        self.baselines = self._load_baselines()
        
    def _load_baselines(self) -> Dict[str, Any]:
        """Load baseline metrics from file"""
        if self.baselines_file.exists():
            with open(self.baselines_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _save_baselines(self):
        """Save baseline metrics to file"""
        with open(self.baselines_file, 'w') as f:
            json.dump(self.baselines, f, indent=2)
    
    def _get_git_info(self) -> Dict[str, str]:
        """Get current git information (optional)"""
        git_info = {"commit": "unknown", "branch": "unknown", "author": "unknown"}
        
        try:
            # Get current commit hash
            result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.metrics_dir.parent)
            if result.returncode == 0:
                git_info["commit"] = result.stdout.strip()[:8]
            
            # Get current branch
            result = subprocess.run(['git', 'rev-parse', '--abbrev-ref', 'HEAD'], 
                                  capture_output=True, text=True, cwd=self.metrics_dir.parent)
            if result.returncode == 0:
                git_info["branch"] = result.stdout.strip()
            
            # Get author of last commit
            result = subprocess.run(['git', 'log', '-1', '--pretty=format:%an'], 
                                  capture_output=True, text=True, cwd=self.metrics_dir.parent)
            if result.returncode == 0:
                git_info["author"] = result.stdout.strip()
                
        except Exception:
            pass  # Git info is optional
        
        return git_info
    
    def record_metrics(self, metrics: Dict[str, Any], source: str = "evaluation") -> str:
        """
        Record new metrics and check for regressions
        
        Args:
            metrics: Dictionary of metrics to record
            source: Source of the metrics (e.g., "evaluation", "pipeline")
        
        Returns:
            Metrics ID for tracking
        """
        timestamp = datetime.now()
        metrics_id = f"{source}_{timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        # Add metadata
        metrics_record = {
            "id": metrics_id,
            "timestamp": timestamp.isoformat(),
            "source": source,
            "git_info": self._get_git_info(),
            "metrics": metrics
        }
        
        # Save current metrics
        with open(self.current_metrics_file, 'w') as f:
            json.dump(metrics_record, f, indent=2)
        
        # Append to historical log
        with open(self.historical_metrics_file, 'a') as f:
            f.write(json.dumps(metrics_record) + '\n')
        
        # Check for regressions
        alerts = self._check_regressions(metrics_record)
        if alerts:
            self._save_alerts(alerts, metrics_id)
        
        self.logger.info(f"Recorded metrics: {metrics_id}")
        if alerts:
            self.logger.warning(f"Regression alerts generated: {len(alerts)}")
        
        return metrics_id
    
    def _check_regressions(self, current_record: Dict) -> List[Dict]:
        """Check current metrics against baselines for regressions"""
        alerts = []
        current_metrics = current_record["metrics"]
        
        # Check against established baselines
        for baseline_name, baseline_data in self.baselines.items():
            baseline_metrics = baseline_data.get("metrics", {})
            
            for metric_name, current_value in self._flatten_metrics(current_metrics).items():
                if metric_name in self._flatten_metrics(baseline_metrics):
                    baseline_value = self._get_nested_value(baseline_metrics, metric_name)
                    
                    # Calculate relative change
                    if isinstance(current_value, (int, float)) and isinstance(baseline_value, (int, float)):
                        if baseline_value != 0:
                            relative_change = (current_value - baseline_value) / baseline_value
                        else:
                            relative_change = 1.0 if current_value != 0 else 0.0
                        
                        # Define thresholds based on metric type
                        threshold = self._get_regression_threshold(metric_name)
                        
                        if abs(relative_change) > threshold:
                            severity = "critical" if abs(relative_change) > threshold * 2 else "warning"
                            
                            alert = {
                                "metric": metric_name,
                                "baseline": baseline_value,
                                "current": current_value,
                                "relative_change": relative_change,
                                "threshold": threshold,
                                "severity": severity,
                                "baseline_source": baseline_name,
                                "timestamp": current_record["timestamp"]
                            }
                            alerts.append(alert)
        
        return alerts
    
    def _flatten_metrics(self, metrics: Dict, prefix: str = "") -> Dict[str, Any]:
        """Flatten nested metrics dictionary"""
        flattened = {}
        
        for key, value in metrics.items():
            full_key = f"{prefix}.{key}" if prefix else key
            
            if isinstance(value, dict):
                flattened.update(self._flatten_metrics(value, full_key))
            else:
                flattened[full_key] = value
        
        return flattened
    
    def _get_nested_value(self, data: Dict, key_path: str) -> Any:
        """Get value from nested dictionary using dot notation"""
        keys = key_path.split('.')
        value = data
        
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return None
        
        return value
    
    def _get_regression_threshold(self, metric_name: str) -> float:
        """Get regression threshold based on metric type"""
        # Define different thresholds for different types of metrics
        if any(keyword in metric_name.lower() for keyword in ['success', 'rate', 'accuracy']):
            return 0.1  # 10% threshold for success/accuracy metrics
        elif any(keyword in metric_name.lower() for keyword in ['time', 'runtime', 'duration']):
            return 0.2  # 20% threshold for timing metrics
        elif any(keyword in metric_name.lower() for keyword in ['memory', 'usage']):
            return 0.3  # 30% threshold for memory metrics
        elif any(keyword in metric_name.lower() for keyword in ['quality', 'score']):
            return 0.15  # 15% threshold for quality metrics
        else:
            return 0.25  # 25% default threshold
    
    def _save_alerts(self, alerts: List[Dict], metrics_id: str):
        """Save regression alerts to file"""
        alert_record = {
            "timestamp": datetime.now().isoformat(),
            "metrics_id": metrics_id,
            "alerts": alerts
        }
        
        # Load existing alerts
        existing_alerts = []
        if self.alerts_file.exists():
            with open(self.alerts_file, 'r') as f:
                existing_alerts = json.load(f)
        
        # Add new alerts
        existing_alerts.append(alert_record)
        
        # Keep only last 100 alert records
        existing_alerts = existing_alerts[-100:]
        
        # Save alerts
        with open(self.alerts_file, 'w') as f:
            json.dump(existing_alerts, f, indent=2)
    
    def update_baseline(self, baseline_name: str, source_metrics_id: Optional[str] = None) -> bool:
        """
        Update baseline metrics from current or specified metrics
        
        Args:
            baseline_name: Name for the baseline (e.g., "production", "stable")
            source_metrics_id: Optional specific metrics ID to use as baseline
        
        Returns:
            True if baseline was updated successfully
        """
        try:
            if source_metrics_id:
                # Use specific metrics record
                source_metrics = self._get_metrics_by_id(source_metrics_id)
            else:
                # Use current metrics
                if not self.current_metrics_file.exists():
                    self.logger.error("No current metrics found for baseline creation")
                    return False
                
                with open(self.current_metrics_file, 'r') as f:
                    source_metrics = json.load(f)
            
            if not source_metrics:
                self.logger.error("Source metrics not found")
                return False
            
            # Create baseline record
            baseline_record = {
                "name": baseline_name,
                "created": datetime.now().isoformat(),
                "source_id": source_metrics.get("id", "unknown"),
                "source_timestamp": source_metrics.get("timestamp", "unknown"),
                "git_info": source_metrics.get("git_info", {}),
                "metrics": source_metrics.get("metrics", {})
            }
            
            # Save baseline
            self.baselines[baseline_name] = baseline_record
            self._save_baselines()
            
            self.logger.info(f"Baseline '{baseline_name}' updated successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to update baseline: {e}")
            return False
    
    def _get_metrics_by_id(self, metrics_id: str) -> Optional[Dict]:
        """Get metrics record by ID from historical data"""
        if not self.historical_metrics_file.exists():
            return None
        
        with open(self.historical_metrics_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    if record.get("id") == metrics_id:
                        return record
                except json.JSONDecodeError:
                    continue
        
        return None
    
    def get_historical_trends(self, days: int = 30, metrics: Optional[List[str]] = None) -> Dict[str, List]:
        """
        Get historical trends for specified metrics
        
        Args:
            days: Number of days of history to retrieve
            metrics: Optional list of specific metrics to track
        
        Returns:
            Dictionary with metric trends over time
        """
        if not self.historical_metrics_file.exists():
            return {}
        
        cutoff_date = datetime.now() - timedelta(days=days)
        trends = {}
        
        with open(self.historical_metrics_file, 'r') as f:
            for line in f:
                try:
                    record = json.loads(line.strip())
                    record_date = datetime.fromisoformat(record["timestamp"])
                    
                    if record_date >= cutoff_date:
                        flat_metrics = self._flatten_metrics(record["metrics"])
                        
                        for metric_name, value in flat_metrics.items():
                            # Filter metrics if specified
                            if metrics and metric_name not in metrics:
                                continue
                            
                            if isinstance(value, (int, float)):
                                if metric_name not in trends:
                                    trends[metric_name] = []
                                
                                trends[metric_name].append({
                                    "timestamp": record["timestamp"],
                                    "value": value,
                                    "source": record.get("source", "unknown")
                                })
                                
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        # Sort trends by timestamp
        for metric_name in trends:
            trends[metric_name].sort(key=lambda x: x["timestamp"])
        
        return trends
    
    def detect_metric_degradation(self, metric_name: str, lookback_days: int = 7) -> Dict[str, Any]:
        """
        Detect if a specific metric has been degrading over time
        
        Args:
            metric_name: Name of the metric to analyze
            lookback_days: Number of days to analyze
        
        Returns:
            Analysis of metric degradation
        """
        trends = self.get_historical_trends(lookback_days, [metric_name])
        
        if metric_name not in trends or len(trends[metric_name]) < 3:
            return {"status": "insufficient_data", "message": "Not enough data points for analysis"}
        
        values = [point["value"] for point in trends[metric_name]]
        timestamps = [point["timestamp"] for point in trends[metric_name]]
        
        # Calculate trend using linear regression
        x = np.arange(len(values))
        coefficients = np.polyfit(x, values, 1)
        slope = coefficients[0]
        
        # Calculate relative trend
        if len(values) > 0 and values[0] != 0:
            relative_trend = slope / abs(values[0])
        else:
            relative_trend = 0
        
        # Determine degradation status
        threshold = self._get_regression_threshold(metric_name) / 2  # Use half threshold for trends
        
        if relative_trend < -threshold:
            status = "degrading"
            severity = "high" if relative_trend < -threshold * 2 else "medium"
        elif relative_trend > threshold:
            status = "improving"
            severity = "good"
        else:
            status = "stable"
            severity = "normal"
        
        return {
            "status": status,
            "severity": severity,
            "slope": slope,
            "relative_trend": relative_trend,
            "data_points": len(values),
            "time_range": {
                "start": timestamps[0],
                "end": timestamps[-1]
            },
            "values": {
                "first": values[0],
                "last": values[-1],
                "min": min(values),
                "max": max(values),
                "mean": np.mean(values)
            }
        }
    
    def generate_metrics_report(self, output_file: Optional[Path] = None) -> str:
        """Generate comprehensive metrics tracking report"""
        report_lines = [
            "# Metrics Tracking Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Current Status",
        ]
        
        # Current metrics summary
        if self.current_metrics_file.exists():
            with open(self.current_metrics_file, 'r') as f:
                current = json.load(f)
            
            report_lines.extend([
                "",
                f"- **Latest Metrics ID:** {current.get('id', 'unknown')}",
                f"- **Recorded:** {current.get('timestamp', 'unknown')}",
                f"- **Source:** {current.get('source', 'unknown')}",
                f"- **Git Commit:** {current.get('git_info', {}).get('commit', 'unknown')}",
                "",
            ])
        
        # Baselines summary
        if self.baselines:
            report_lines.extend([
                "## Established Baselines",
                "",
            ])
            
            for baseline_name, baseline_data in self.baselines.items():
                report_lines.extend([
                    f"### {baseline_name}",
                    f"- **Created:** {baseline_data.get('created', 'unknown')}",
                    f"- **Source ID:** {baseline_data.get('source_id', 'unknown')}",
                    f"- **Git Commit:** {baseline_data.get('git_info', {}).get('commit', 'unknown')}",
                    "",
                ])
        
        # Recent alerts
        if self.alerts_file.exists():
            with open(self.alerts_file, 'r') as f:
                alerts_data = json.load(f)
            
            if alerts_data:
                recent_alerts = alerts_data[-5:]  # Last 5 alert records
                
                report_lines.extend([
                    "## Recent Regression Alerts",
                    "",
                ])
                
                for alert_record in recent_alerts:
                    timestamp = alert_record.get('timestamp', 'unknown')
                    alerts = alert_record.get('alerts', [])
                    
                    report_lines.extend([
                        f"### {timestamp}",
                        f"**Metrics ID:** {alert_record.get('metrics_id', 'unknown')}",
                        "",
                    ])
                    
                    for alert in alerts[:3]:  # Top 3 alerts per record
                        severity_icon = "🚨" if alert.get('severity') == 'critical' else "⚠️"
                        report_lines.extend([
                            f"{severity_icon} **{alert.get('metric', 'unknown')}**",
                            f"- Baseline: {alert.get('baseline', 'N/A')}",
                            f"- Current: {alert.get('current', 'N/A')}", 
                            f"- Change: {alert.get('relative_change', 0):.2%}",
                            "",
                        ])
        
        # Historical trends analysis
        key_metrics = [
            "successful_extraction_rate",
            "avg_runtime_per_page", 
            "avg_content_quality",
            "avg_throughput_pages_per_hour"
        ]
        
        trends = self.get_historical_trends(30, key_metrics)
        
        if trends:
            report_lines.extend([
                "## Key Metrics Trends (30 days)",
                "",
            ])
            
            for metric_name in key_metrics:
                if metric_name in trends and len(trends[metric_name]) > 0:
                    degradation = self.detect_metric_degradation(metric_name, 30)
                    
                    status_icon = {
                        "improving": "📈",
                        "degrading": "📉", 
                        "stable": "➡️"
                    }.get(degradation.get("status"), "❓")
                    
                    values = degradation.get("values", {})
                    
                    report_lines.extend([
                        f"### {metric_name.replace('_', ' ').title()} {status_icon}",
                        f"- **Status:** {degradation.get('status', 'unknown').title()}",
                        f"- **Trend:** {degradation.get('relative_trend', 0):.2%} per measurement",
                        f"- **Current:** {values.get('last', 'N/A')}",
                        f"- **Average:** {values.get('mean', 'N/A')}",
                        f"- **Data Points:** {degradation.get('data_points', 0)}",
                        "",
                    ])
        
        # Usage recommendations
        report_lines.extend([
            "## Usage & Recommendations",
            "",
            "### Creating Baselines",
            "```bash",
            "# Create baseline from current metrics",
            "tracker.update_baseline('production')",
            "",
            "# Create baseline from specific metrics ID", 
            "tracker.update_baseline('stable', 'evaluation_20241001_120000')",
            "```",
            "",
            "### Monitoring Commands",
            "```bash",
            "# Check for recent degradation",
            "python -c \"from metrics_tracker import StandaloneMetricsTracker; t=StandaloneMetricsTracker('data/intermediate/evaluation_metrics'); print(t.detect_metric_degradation('successful_extraction_rate'))\"",
            "",
            "# Get trends for key metrics",
            "python -c \"from metrics_tracker import StandaloneMetricsTracker; t=StandaloneMetricsTracker('data/intermediate/evaluation_metrics'); print(t.get_historical_trends(7))\"",
            "```",
            "",
            "---",
            f"*Metrics report generated by Standalone Metrics Tracker at {datetime.now()}*"
        ])
        
        report_content = "\n".join(report_lines)
        
        # Save report
        if not output_file:
            output_file = self.metrics_dir / f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        
        with open(output_file, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Metrics report saved to: {output_file}")
        return report_content
    
    return summary
    
    def compare_with_baseline(self, current_metrics: Dict, source_id: str = "default") -> Dict[str, Any]:
        """
        Compare current metrics with baseline
        
        Args:
            current_metrics: Current metrics to compare
            source_id: Source identifier
        
        Returns:
            Comparison results including drift analysis
        """
        baseline_file = self.baselines_dir / f"baseline_{source_id}.json"
        
        if not baseline_file.exists():
            return {
                "status": "no_baseline",
                "message": "No baseline available for comparison",
                "overall_drift": 0.0,
                "alerts": []
            }
        
        try:
            with open(baseline_file, 'r') as f:
                baseline = json.load(f)
        except Exception as e:
            return {
                "status": "error",
                "message": f"Could not load baseline: {e}",
                "overall_drift": 0.0,
                "alerts": []
            }
        
        baseline_metrics = baseline.get("metrics", {})
        
        comparison = {
            "status": "ok",
            "baseline_timestamp": baseline.get("timestamp", "unknown"),
            "drift_analysis": {},
            "overall_drift": 0.0,
            "alerts": []
        }
        
        # Compare metrics
        drift_values = []
        
        def compare_nested(current, baseline_data, prefix=""):
            nonlocal drift_values
            
            for key, current_value in current.items():
                full_key = f"{prefix}.{key}" if prefix else key
                
                if isinstance(current_value, dict) and key in baseline_data and isinstance(baseline_data[key], dict):
                    compare_nested(current_value, baseline_data[key], full_key)
                elif key in baseline_data and isinstance(current_value, (int, float)) and isinstance(baseline_data[key], (int, float)):
                    baseline_value = baseline_data[key]
                    
                    if baseline_value != 0:
                        relative_change = (current_value - baseline_value) / abs(baseline_value)
                    else:
                        relative_change = 1.0 if current_value != 0 else 0.0
                    
                    drift_magnitude = abs(relative_change)
                    drift_values.append(drift_magnitude)
                    
                    comparison["drift_analysis"][full_key] = {
                        "current_value": current_value,
                        "baseline_value": baseline_value,
                        "relative_change": relative_change,
                        "drift_magnitude": drift_magnitude
                    }
        
        compare_nested(current_metrics, baseline_metrics)
        
        # Calculate overall drift
        if drift_values:
            comparison["overall_drift"] = max(drift_values)
            
            # Determine status based on drift
            if comparison["overall_drift"] >= 0.30:  # 30% threshold
                comparison["status"] = "critical"
                comparison["alerts"].append("Critical drift detected - immediate investigation required")
            elif comparison["overall_drift"] >= 0.15:  # 15% threshold
                comparison["status"] = "warning"
                comparison["alerts"].append("Significant drift detected - monitor closely")
        
        return comparison
    
    def cleanup_old_data(self, keep_days: int = 90):
        """Clean up old metrics data to prevent unlimited growth"""
        if not self.historical_metrics_file.exists():
            return
        
        cutoff_date = datetime.now() - timedelta(days=keep_days)
        temp_file = self.historical_metrics_file.with_suffix('.tmp')
        
        kept_records = 0
        with open(self.historical_metrics_file, 'r') as infile, open(temp_file, 'w') as outfile:
            for line in infile:
                try:
                    record = json.loads(line.strip())
                    record_date = datetime.fromisoformat(record["timestamp"])
                    
                    if record_date >= cutoff_date:
                        outfile.write(line)
                        kept_records += 1
                        
                except (json.JSONDecodeError, KeyError, ValueError):
                    continue
        
        # Replace original file with cleaned version
        shutil.move(temp_file, self.historical_metrics_file)
        
        self.logger.info(f"Cleaned metrics data: kept {kept_records} records from last {keep_days} days")


def integrate_with_evaluation_suite(data_dir: Path) -> StandaloneMetricsTracker:
    """
    Create metrics tracker and integrate with evaluation suite results
    
    Args:
        data_dir: Path to data directory containing evaluation results
    
    Returns:
        Configured metrics tracker
    """
    metrics_tracker = StandaloneMetricsTracker(data_dir / "evaluation_metrics")
    
    # Look for recent evaluation results
    results_pattern = data_dir / "evaluation_metrics" / "evaluation_results_*.json"
    result_files = list(Path(data_dir).glob("evaluation_metrics/evaluation_results_*.json"))
    
    if result_files:
        # Use most recent evaluation results
        latest_results = max(result_files, key=lambda x: x.stat().st_mtime)
        
        try:
            with open(latest_results, 'r') as f:
                evaluation_data = json.load(f)
            
            # Extract key metrics for tracking
            tracked_metrics = {}
            
            # Text extraction metrics
            if "quality_evaluation" in evaluation_data:
                quality = evaluation_data["quality_evaluation"]
                if "text_metrics" in quality:
                    text_metrics = quality["text_metrics"]
                    tracked_metrics.update({
                        "text_extraction": {
                            "successful_extraction_rate": text_metrics.get("successful_extraction_rate", 0),
                            "avg_chars_per_page": text_metrics.get("avg_chars_per_page", 0),
                            "ocr_rate": text_metrics.get("ocr_rate", 0),
                            "content_distribution_entropy": text_metrics.get("content_distribution_entropy", 0)
                        }
                    })
                
                # Table extraction metrics
                if "table_metrics" in quality and "method_comparison" in quality["table_metrics"]:
                    method_comparison = quality["table_metrics"]["method_comparison"]
                    
                    # Calculate aggregate table metrics
                    total_tables = sum(stats.get("table_count", 0) for stats in method_comparison.values())
                    avg_quality = np.mean([stats.get("avg_content_quality", 0) for stats in method_comparison.values()])
                    
                    tracked_metrics.update({
                        "table_extraction": {
                            "total_tables_extracted": total_tables,
                            "avg_content_quality": avg_quality,
                            "methods_used": len(method_comparison)
                        }
                    })
            
            # Performance metrics
            if "performance_benchmarking" in evaluation_data:
                perf = evaluation_data["performance_benchmarking"]
                if "bottleneck_analysis" in perf and "performance_summary" in perf["bottleneck_analysis"]:
                    perf_summary = perf["bottleneck_analysis"]["performance_summary"]
                    tracked_metrics.update({
                        "performance": {
                            "avg_runtime_per_page": perf_summary.get("avg_runtime_per_page", 0),
                            "avg_throughput_pages_per_hour": perf_summary.get("avg_throughput_pages_per_hour", 0),
                            "avg_memory_usage_mb": perf_summary.get("avg_memory_usage_mb", 0),
                            "overall_success_rate": perf_summary.get("overall_success_rate", 0)
                        }
                    })
            
            # Regression testing status
            if "regression_testing" in evaluation_data:
                regression = evaluation_data["regression_testing"]
                if "test_results" in regression:
                    test_results = regression["test_results"]
                    tracked_metrics.update({
                        "regression_testing": {
                            "tests_passed": test_results.get("tests_passed", 0),
                            "tests_failed": test_results.get("tests_failed", 0),
                            "overall_status_numeric": 1 if test_results.get("overall_status") == "PASS" else 0
                        }
                    })
            
            # Record metrics in tracker
            if tracked_metrics:
                metrics_id = metrics_tracker.record_metrics(tracked_metrics, "evaluation_suite")
                
                # Create baseline if none exists
                if not metrics_tracker.baselines:
                    metrics_tracker.update_baseline("initial_baseline", metrics_id)
                    print(f"Created initial baseline from evaluation results: {metrics_id}")
                
                print(f"Recorded evaluation metrics: {metrics_id}")
            
        except Exception as e:
            print(f"Failed to integrate evaluation results: {e}")
    
    return metrics_tracker


if __name__ == "__main__":
    # Example usage and testing
    import argparse
    
    parser = argparse.ArgumentParser(description="Standalone Metrics Tracking")
    parser.add_argument("--data-dir", required=True, help="Path to data directory")
    parser.add_argument("--action", choices=["integrate", "report", "baseline", "trends"], 
                       default="integrate", help="Action to perform")
    parser.add_argument("--baseline-name", help="Name for new baseline")
    parser.add_argument("--metric", help="Specific metric to analyze")
    parser.add_argument("--days", type=int, default=30, help="Number of days for analysis")
    
    args = parser.parse_args()
    
    data_dir = Path(args.data_dir)
    
    if args.action == "integrate":
        tracker = integrate_with_evaluation_suite(data_dir)
        print("Integration with evaluation suite completed")
        
    elif args.action == "report":
        tracker = StandaloneMetricsTracker(data_dir / "evaluation_metrics")
        report = tracker.generate_metrics_report()
        print("Generated metrics tracking report")
        
    elif args.action == "baseline":
        tracker = StandaloneMetricsTracker(data_dir / "evaluation_metrics")
        baseline_name = args.baseline_name or "manual_baseline"
        success = tracker.update_baseline(baseline_name)
        print(f"Baseline update {'successful' if success else 'failed'}")
        
    elif args.action == "trends":
        tracker = StandaloneMetricsTracker(data_dir / "evaluation_metrics")
        if args.metric:
            degradation = tracker.detect_metric_degradation(args.metric, args.days)
            print(f"Degradation analysis for {args.metric}:")
            print(json.dumps(degradation, indent=2))
        else:
            trends = tracker.get_historical_trends(args.days)
            print(f"Historical trends for last {args.days} days:")
            for metric, data in trends.items():
                print(f"  {metric}: {len(data)} data points")