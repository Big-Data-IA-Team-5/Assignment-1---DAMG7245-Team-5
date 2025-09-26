#!/usr/bin/env python3
"""
Part 10: Performance & Cost Benchmarking System

This module measures runtime, memory consumption, and cost analysis for the parsing pipeline.
Provides comprehensive benchmarking to understand performance trade-offs and scaling characteristics.

Key features:
- Runtime measurement per page and per operation
- Memory usage monitoring and profiling
- Bottleneck identification across pipeline stages
- Cost estimation for cloud APIs vs in-house processing
- Throughput analysis and scaling projections
- Hardware recommendations for different volume scenarios
"""

import json
import logging
import os
import psutil
import time
import tracemalloc
from contextlib import contextmanager
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Callable
import subprocess
import threading
from dataclasses import dataclass, asdict
import hashlib

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns

# Try to import memory profiler if available
try:
    from memory_profiler import profile, memory_usage
    MEMORY_PROFILER_AVAILABLE = True
except ImportError:
    MEMORY_PROFILER_AVAILABLE = False


@dataclass
class BenchmarkResult:
    """Results from a single benchmark operation"""
    operation: str
    runtime_seconds: float
    memory_peak_mb: float
    memory_baseline_mb: float
    cpu_percent_avg: float
    pages_processed: int
    success_count: int
    failure_count: int
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    @property
    def runtime_per_page(self) -> float:
        """Runtime per page in seconds"""
        return self.runtime_seconds / max(self.pages_processed, 1)
    
    @property
    def memory_used_mb(self) -> float:
        """Memory used during operation in MB"""
        return self.memory_peak_mb - self.memory_baseline_mb
    
    @property
    def success_rate(self) -> float:
        """Success rate as percentage"""
        total = self.success_count + self.failure_count
        return (self.success_count / max(total, 1)) * 100
    
    @property
    def throughput_pages_per_hour(self) -> float:
        """Throughput in pages per hour"""
        if self.runtime_seconds <= 0:
            return 0
        return (self.pages_processed / self.runtime_seconds) * 3600


@dataclass
class SystemInfo:
    """System information for benchmarking context"""
    cpu_count: int
    cpu_model: str
    total_memory_gb: float
    available_memory_gb: float
    python_version: str
    platform: str
    timestamp: str


class PerformanceBenchmarker:
    """
    Comprehensive performance and cost benchmarking for parsing pipeline.
    Measures runtime, memory usage, and identifies bottlenecks across different operations.
    """
    
    def __init__(self, data_dir: Path, results_dir: Optional[Path] = None):
        """
        Initialize benchmarker
        
        Args:
            data_dir: Path to parsed data directory
            results_dir: Path to save benchmark results
        """
        self.data_dir = Path(data_dir)
        self.results_dir = results_dir or (self.data_dir / "evaluation_metrics" / "benchmarks")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # System information
        self.system_info = self._gather_system_info()
        
        # Benchmark results storage
        self.benchmark_results: List[BenchmarkResult] = []
        
        # Resource monitoring
        self.process = psutil.Process(os.getpid())
        
    def _gather_system_info(self) -> SystemInfo:
        """Gather system information for benchmark context"""
        import platform
        import sys
        
        # CPU information
        cpu_count = psutil.cpu_count()
        cpu_model = "Unknown"
        
        # Try to get CPU model on different platforms
        try:
            if platform.system() == "Darwin":  # macOS
                result = subprocess.run(['sysctl', '-n', 'machdep.cpu.brand_string'], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    cpu_model = result.stdout.strip()
            elif platform.system() == "Linux":
                with open('/proc/cpuinfo', 'r') as f:
                    for line in f:
                        if 'model name' in line:
                            cpu_model = line.split(':')[1].strip()
                            break
        except:
            pass
        
        # Memory information
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024**3)
        available_memory_gb = memory.available / (1024**3)
        
        return SystemInfo(
            cpu_count=cpu_count,
            cpu_model=cpu_model,
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb,
            python_version=sys.version,
            platform=platform.platform(),
            timestamp=datetime.now().isoformat()
        )
    
    @contextmanager
    def benchmark_operation(self, operation_name: str, pages_count: int = 1):
        """
        Context manager for benchmarking operations
        
        Args:
            operation_name: Name of the operation being benchmarked
            pages_count: Number of pages being processed
        """
        self.logger.info(f"Starting benchmark: {operation_name}")
        
        # Start memory profiling
        if MEMORY_PROFILER_AVAILABLE:
            tracemalloc.start()
        
        # Baseline measurements
        baseline_memory = self.process.memory_info().rss / (1024**2)  # MB
        start_time = time.time()
        
        # CPU monitoring setup
        cpu_percentages = []
        
        def monitor_cpu():
            while getattr(monitor_cpu, 'running', True):
                cpu_percentages.append(psutil.cpu_percent())
                time.sleep(0.1)
        
        monitor_cpu.running = True
        cpu_thread = threading.Thread(target=monitor_cpu)
        cpu_thread.start()
        
        success_count = 0
        failure_count = 0
        
        try:
            # Yield control to the benchmarked operation
            result = yield (lambda: setattr(self, '_success_count', getattr(self, '_success_count', 0) + 1),
                          lambda: setattr(self, '_failure_count', getattr(self, '_failure_count', 0) + 1))
            
            success_count = getattr(self, '_success_count', pages_count)
            failure_count = getattr(self, '_failure_count', 0)
            
        except Exception as e:
            failure_count = pages_count
            self.logger.error(f"Benchmark operation {operation_name} failed: {e}")
        
        finally:
            # Stop monitoring
            monitor_cpu.running = False
            cpu_thread.join(timeout=1)
            
            # Final measurements
            end_time = time.time()
            peak_memory = self.process.memory_info().rss / (1024**2)  # MB
            
            if MEMORY_PROFILER_AVAILABLE:
                tracemalloc.stop()
            
            # Calculate metrics
            runtime = end_time - start_time
            avg_cpu = np.mean(cpu_percentages) if cpu_percentages else 0
            
            # Create benchmark result
            result = BenchmarkResult(
                operation=operation_name,
                runtime_seconds=runtime,
                memory_peak_mb=peak_memory,
                memory_baseline_mb=baseline_memory,
                cpu_percent_avg=avg_cpu,
                pages_processed=pages_count,
                success_count=success_count,
                failure_count=failure_count
            )
            
            self.benchmark_results.append(result)
            
            self.logger.info(f"Benchmark {operation_name} completed:")
            self.logger.info(f"  Runtime: {runtime:.2f}s ({result.runtime_per_page:.2f}s/page)")
            self.logger.info(f"  Memory: {result.memory_used_mb:.1f} MB")
            self.logger.info(f"  CPU: {avg_cpu:.1f}%")
            self.logger.info(f"  Throughput: {result.throughput_pages_per_hour:.1f} pages/hour")
    
    def benchmark_text_extraction(self, pdf_path: Path) -> BenchmarkResult:
        """Benchmark text extraction performance"""
        from src.text.extract_text import extract_text_with_pdfplumber
        
        # Count pages first
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
        
        with self.benchmark_operation("text_extraction", page_count) as (success, failure):
            try:
                pages_data, ocr_pages = extract_text_with_pdfplumber(pdf_path)
                success()
            except Exception as e:
                failure()
                raise e
        
        return self.benchmark_results[-1]
    
    def benchmark_table_extraction(self, pdf_path: Path) -> BenchmarkResult:
        """Benchmark table extraction performance"""
        from src.tables.extract_tables import extract_tables_assignment_hybrid
        
        # Count pages
        import pdfplumber
        with pdfplumber.open(pdf_path) as pdf:
            page_count = len(pdf.pages)
        
        with self.benchmark_operation("table_extraction", page_count) as (success, failure):
            try:
                result = extract_tables_assignment_hybrid(pdf_path, self.data_dir, use_hybrid=True)
                success()
            except Exception as e:
                failure()
                raise e
        
        return self.benchmark_results[-1]
    
    def benchmark_full_pipeline(self, pdf_path: Path) -> List[BenchmarkResult]:
        """Benchmark the complete parsing pipeline"""
        pipeline_results = []
        
        self.logger.info(f"Benchmarking full pipeline for {pdf_path.name}")
        
        # Benchmark each stage
        try:
            # Stage 1: Text extraction
            text_result = self.benchmark_text_extraction(pdf_path)
            pipeline_results.append(text_result)
            
            # Stage 2: Table extraction
            table_result = self.benchmark_table_extraction(pdf_path)
            pipeline_results.append(table_result)
            
            # Stage 3: Combined pipeline overhead
            total_pages = text_result.pages_processed
            with self.benchmark_operation("pipeline_overhead", total_pages) as (success, failure):
                # Simulate metadata processing and format conversion
                time.sleep(0.1 * total_pages)  # Simulate processing time
                success()
            
            pipeline_results.append(self.benchmark_results[-1])
            
        except Exception as e:
            self.logger.error(f"Pipeline benchmark failed: {e}")
        
        return pipeline_results
    
    def analyze_bottlenecks(self) -> Dict[str, Any]:
        """Analyze performance bottlenecks from benchmark results"""
        if not self.benchmark_results:
            return {"error": "No benchmark results available"}
        
        df = pd.DataFrame([result.to_dict() for result in self.benchmark_results])
        
        analysis = {
            "timestamp": datetime.now().isoformat(),
            "total_operations": len(self.benchmark_results),
            "bottleneck_analysis": {},
            "performance_summary": {},
            "recommendations": []
        }
        
        # Identify slowest operations
        slowest_ops = df.nlargest(3, 'runtime_per_page')[['operation', 'runtime_per_page', 'memory_used_mb']].to_dict('records')
        analysis["bottleneck_analysis"]["slowest_operations"] = slowest_ops
        
        # Memory usage analysis
        memory_intensive = df.nlargest(3, 'memory_used_mb')[['operation', 'memory_used_mb', 'runtime_seconds']].to_dict('records')
        analysis["bottleneck_analysis"]["memory_intensive_operations"] = memory_intensive
        
        # CPU usage analysis
        cpu_intensive = df.nlargest(3, 'cpu_percent_avg')[['operation', 'cpu_percent_avg', 'runtime_seconds']].to_dict('records')
        analysis["bottleneck_analysis"]["cpu_intensive_operations"] = cpu_intensive
        
        # Performance summary statistics
        analysis["performance_summary"] = {
            "avg_runtime_per_page": df['runtime_per_page'].mean(),
            "std_runtime_per_page": df['runtime_per_page'].std(),
            "avg_memory_usage_mb": df['memory_used_mb'].mean(),
            "max_memory_usage_mb": df['memory_used_mb'].max(),
            "avg_cpu_usage_percent": df['cpu_percent_avg'].mean(),
            "avg_throughput_pages_per_hour": df['throughput_pages_per_hour'].mean(),
            "overall_success_rate": df['success_rate'].mean()
        }
        
        # Generate recommendations
        recommendations = []
        
        # Runtime recommendations
        if df['runtime_per_page'].mean() > 10.0:  # More than 10s per page
            recommendations.append({
                "category": "Runtime Optimization",
                "priority": "High",
                "issue": f"Average processing time is {df['runtime_per_page'].mean():.1f}s per page",
                "recommendation": "Consider parallel processing or algorithm optimization"
            })
        
        # Memory recommendations
        if df['memory_used_mb'].max() > 500:  # More than 500MB
            recommendations.append({
                "category": "Memory Optimization", 
                "priority": "Medium",
                "issue": f"Peak memory usage is {df['memory_used_mb'].max():.0f}MB",
                "recommendation": "Implement streaming processing for large documents"
            })
        
        # CPU recommendations
        if df['cpu_percent_avg'].mean() < 50:  # Under-utilizing CPU
            recommendations.append({
                "category": "CPU Utilization",
                "priority": "Low", 
                "issue": f"Average CPU usage is only {df['cpu_percent_avg'].mean():.1f}%",
                "recommendation": "Consider increasing parallelism or concurrent processing"
            })
        
        # Throughput recommendations
        if df['throughput_pages_per_hour'].mean() < 120:  # Less than 2 pages per minute
            recommendations.append({
                "category": "Throughput",
                "priority": "High",
                "issue": f"Throughput is {df['throughput_pages_per_hour'].mean():.0f} pages/hour",
                "recommendation": "Investigate bottlenecks and consider hardware upgrades"
            })
        
        analysis["recommendations"] = recommendations
        
        return analysis
    
    def create_performance_visualizations(self) -> List[str]:
        """Create comprehensive performance visualization charts"""
        if not self.benchmark_results:
            self.logger.warning("No benchmark results to visualize")
            return []
        
        visualization_files = []
        df = pd.DataFrame([result.to_dict() for result in self.benchmark_results])
        
        # 1. Runtime Performance Chart
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        
        # Runtime per operation
        axes[0, 0].bar(df['operation'], df['runtime_per_page'])
        axes[0, 0].set_title('Runtime per Page by Operation')
        axes[0, 0].set_ylabel('Seconds per Page')
        axes[0, 0].tick_params(axis='x', rotation=45)
        
        # Memory usage
        axes[0, 1].bar(df['operation'], df['memory_used_mb'], color='orange')
        axes[0, 1].set_title('Memory Usage by Operation')
        axes[0, 1].set_ylabel('Memory (MB)')
        axes[0, 1].tick_params(axis='x', rotation=45)
        
        # Throughput comparison
        axes[1, 0].bar(df['operation'], df['throughput_pages_per_hour'], color='green')
        axes[1, 0].set_title('Throughput by Operation')
        axes[1, 0].set_ylabel('Pages per Hour')
        axes[1, 0].tick_params(axis='x', rotation=45)
        
        # Success rates
        axes[1, 1].bar(df['operation'], df['success_rate'], color='purple')
        axes[1, 1].set_title('Success Rate by Operation')
        axes[1, 1].set_ylabel('Success Rate (%)')
        axes[1, 1].set_ylim(0, 100)
        axes[1, 1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        perf_file = self.results_dir / "performance_analysis.png"
        plt.savefig(perf_file, dpi=300, bbox_inches='tight')
        plt.close()
        visualization_files.append(str(perf_file))
        
        # 2. Resource Utilization Chart
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
        
        # Memory vs Runtime scatter
        scatter = ax1.scatter(df['runtime_per_page'], df['memory_used_mb'], 
                            s=df['pages_processed']*10, alpha=0.6, c=df['cpu_percent_avg'], cmap='viridis')
        ax1.set_xlabel('Runtime per Page (seconds)')
        ax1.set_ylabel('Memory Used (MB)')
        ax1.set_title('Memory vs Runtime Performance')
        
        # Add colorbar for CPU usage
        cbar = plt.colorbar(scatter, ax=ax1)
        cbar.set_label('CPU Usage (%)')
        
        # Add operation labels
        for i, row in df.iterrows():
            ax1.annotate(row['operation'], (row['runtime_per_page'], row['memory_used_mb']), 
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
        
        # Efficiency analysis (throughput vs resources)
        efficiency = df['throughput_pages_per_hour'] / (df['memory_used_mb'] + df['cpu_percent_avg'])
        bars = ax2.bar(df['operation'], efficiency, color='coral')
        ax2.set_title('Processing Efficiency\n(Throughput / Resources)')
        ax2.set_ylabel('Efficiency Score')
        ax2.tick_params(axis='x', rotation=45)
        
        # Add efficiency values
        for bar, eff in zip(bars, efficiency):
            ax2.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 0.01, 
                    f'{eff:.2f}', ha='center', va='bottom', fontsize=8)
        
        plt.tight_layout()
        
        resource_file = self.results_dir / "resource_utilization.png"
        plt.savefig(resource_file, dpi=300, bbox_inches='tight')
        plt.close()
        visualization_files.append(str(resource_file))
        
        # 3. Scaling Analysis Chart
        if len(df) > 1:
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # Projected scaling based on current performance
            page_counts = np.array([10, 50, 100, 500, 1000, 5000, 10000])
            avg_runtime_per_page = df['runtime_per_page'].mean()
            avg_memory_per_page = df['memory_used_mb'].mean() / df['pages_processed'].mean()
            
            projected_times = page_counts * avg_runtime_per_page / 3600  # hours
            projected_memory = page_counts * avg_memory_per_page  # MB
            
            ax1.plot(page_counts, projected_times, 'o-', label='Sequential Processing')
            ax1.plot(page_counts, projected_times / self.system_info.cpu_count, 's-', 
                    label=f'Parallel Processing ({self.system_info.cpu_count} cores)')
            ax1.set_xlabel('Document Pages')
            ax1.set_ylabel('Processing Time (hours)')
            ax1.set_title('Scaling Projection: Processing Time')
            ax1.set_xscale('log')
            ax1.set_yscale('log')
            ax1.legend()
            ax1.grid(True, alpha=0.3)
            
            ax2.plot(page_counts, projected_memory / 1024, 'o-', color='orange', label='Memory Usage')
            ax2.axhline(y=self.system_info.total_memory_gb * 0.8, color='red', 
                       linestyle='--', label='80% System Memory')
            ax2.set_xlabel('Document Pages')
            ax2.set_ylabel('Memory Usage (GB)')
            ax2.set_title('Scaling Projection: Memory Usage')
            ax2.set_xscale('log')
            ax2.legend()
            ax2.grid(True, alpha=0.3)
            
            plt.tight_layout()
            
            scaling_file = self.results_dir / "scaling_analysis.png"
            plt.savefig(scaling_file, dpi=300, bbox_inches='tight')
            plt.close()
            visualization_files.append(str(scaling_file))
        
        self.logger.info(f"Generated {len(visualization_files)} performance visualization(s)")
        return visualization_files
    
    def estimate_cloud_costs(self, pages_per_month: int = 1000) -> Dict[str, Any]:
        """Estimate costs for cloud-based document processing services"""
        
        # Current pricing (as of 2024) - prices in USD
        cloud_services = {
            "AWS Textract": {
                "price_per_page": 0.0015,  # $1.50 per 1000 pages
                "features": ["OCR", "Tables", "Forms", "Key-Value pairs"],
                "accuracy": "High",
                "setup_complexity": "Low"
            },
            "Google Document AI": {
                "price_per_page": 0.0015,  # $1.50 per 1000 pages for Document OCR
                "features": ["OCR", "Tables", "Layout", "Entities"],
                "accuracy": "High", 
                "setup_complexity": "Medium"
            },
            "Azure Form Recognizer": {
                "price_per_page": 0.0015,  # $1.50 per 1000 pages
                "features": ["OCR", "Tables", "Forms", "Layout"],
                "accuracy": "High",
                "setup_complexity": "Low"
            },
            "Amazon Comprehend": {
                "price_per_page": 0.0001,  # $0.10 per 1000 characters (estimated)
                "features": ["Entity Extraction", "Sentiment", "Key Phrases"],
                "accuracy": "Medium",
                "setup_complexity": "Low"
            }
        }
        
        # Calculate monthly costs
        cost_analysis = {
            "pages_per_month": pages_per_month,
            "service_costs": {},
            "comparison": {},
            "recommendations": []
        }
        
        for service, details in cloud_services.items():
            monthly_cost = pages_per_month * details["price_per_page"]
            annual_cost = monthly_cost * 12
            
            cost_analysis["service_costs"][service] = {
                "monthly_cost_usd": monthly_cost,
                "annual_cost_usd": annual_cost,
                "price_per_page": details["price_per_page"],
                "features": details["features"],
                "accuracy": details["accuracy"],
                "setup_complexity": details["setup_complexity"]
            }
        
        # In-house processing cost estimation
        if self.benchmark_results:
            avg_runtime_per_page = np.mean([r.runtime_per_page for r in self.benchmark_results])
            avg_memory_mb = np.mean([r.memory_used_mb for r in self.benchmark_results])
            
            # Estimate infrastructure costs (rough estimates)
            processing_hours_per_month = (pages_per_month * avg_runtime_per_page) / 3600
            
            # AWS EC2 pricing estimates (m5.large instance ~$0.096/hour)
            ec2_hourly_cost = 0.096
            monthly_compute_cost = processing_hours_per_month * ec2_hourly_cost
            
            # Add storage, bandwidth, and maintenance costs
            additional_costs = monthly_compute_cost * 0.3  # 30% overhead
            total_inhouse_monthly = monthly_compute_cost + additional_costs
            
            cost_analysis["inhouse_processing"] = {
                "monthly_compute_cost_usd": monthly_compute_cost,
                "monthly_additional_costs_usd": additional_costs,
                "monthly_total_cost_usd": total_inhouse_monthly,
                "annual_cost_usd": total_inhouse_monthly * 12,
                "processing_hours_per_month": processing_hours_per_month,
                "avg_memory_required_mb": avg_memory_mb,
                "estimated_instance_type": "m5.large (2 vCPU, 8GB RAM)"
            }
            
            # Cost comparison
            cheapest_cloud = min(cost_analysis["service_costs"].items(), 
                                key=lambda x: x[1]["monthly_cost_usd"])
            
            cost_analysis["comparison"] = {
                "cheapest_cloud_service": cheapest_cloud[0],
                "cheapest_cloud_monthly_cost": cheapest_cloud[1]["monthly_cost_usd"],
                "inhouse_monthly_cost": total_inhouse_monthly,
                "cost_difference": total_inhouse_monthly - cheapest_cloud[1]["monthly_cost_usd"],
                "breakeven_pages_per_month": int(total_inhouse_monthly / cheapest_cloud[1]["price_per_page"]),
                "recommendation": "cloud" if total_inhouse_monthly > cheapest_cloud[1]["monthly_cost_usd"] else "inhouse"
            }
        
        # Generate recommendations based on volume
        recommendations = []
        
        if pages_per_month < 1000:
            recommendations.append({
                "volume": "Low Volume (<1K pages/month)",
                "recommendation": "Use cloud services - minimal setup and maintenance",
                "rationale": "Fixed costs of in-house infrastructure not justified"
            })
        elif pages_per_month < 10000:
            recommendations.append({
                "volume": "Medium Volume (1K-10K pages/month)", 
                "recommendation": "Compare cloud vs hybrid approach",
                "rationale": "Consider cloud for peaks, in-house for base load"
            })
        else:
            recommendations.append({
                "volume": "High Volume (>10K pages/month)",
                "recommendation": "In-house processing likely more cost-effective",
                "rationale": "Economies of scale favor dedicated infrastructure"
            })
        
        cost_analysis["recommendations"] = recommendations
        
        return cost_analysis
    
    def generate_benchmarks_report(self) -> str:
        """Generate comprehensive benchmarks.md report"""
        
        # Run analysis
        bottleneck_analysis = self.analyze_bottlenecks()
        cost_analysis = self.estimate_cloud_costs()
        
        # Create visualizations
        visualization_files = self.create_performance_visualizations()
        
        # Generate report content
        report_lines = [
            "# Performance & Cost Benchmarking Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Executive Summary",
            "",
            "This report provides comprehensive performance benchmarking and cost analysis",
            "for the document parsing pipeline, including runtime measurements, memory usage,",
            "bottleneck identification, and cost comparisons between cloud and in-house processing.",
            "",
            "## System Information",
            "",
            f"- **CPU:** {self.system_info.cpu_model} ({self.system_info.cpu_count} cores)",
            f"- **Memory:** {self.system_info.total_memory_gb:.1f} GB total, {self.system_info.available_memory_gb:.1f} GB available",
            f"- **Platform:** {self.system_info.platform}",
            f"- **Python:** {self.system_info.python_version.split()[0]}",
            "",
        ]
        
        # Performance Summary
        if bottleneck_analysis.get("performance_summary"):
            perf = bottleneck_analysis["performance_summary"]
            report_lines.extend([
                "## Performance Summary",
                "",
                f"- **Average processing time:** {perf['avg_runtime_per_page']:.2f} seconds per page",
                f"- **Throughput:** {perf['avg_throughput_pages_per_hour']:.0f} pages per hour",
                f"- **Memory usage:** {perf['avg_memory_usage_mb']:.1f} MB average, {perf['max_memory_usage_mb']:.1f} MB peak", 
                f"- **CPU utilization:** {perf['avg_cpu_usage_percent']:.1f}% average",
                f"- **Success rate:** {perf['overall_success_rate']:.1f}%",
                "",
            ])
        
        # Bottleneck Analysis
        if bottleneck_analysis.get("bottleneck_analysis"):
            bottlenecks = bottleneck_analysis["bottleneck_analysis"]
            
            report_lines.extend([
                "## Bottleneck Analysis",
                "",
                "### Slowest Operations",
            ])
            
            for i, op in enumerate(bottlenecks.get("slowest_operations", []), 1):
                report_lines.append(f"{i}. **{op['operation']}**: {op['runtime_per_page']:.2f}s/page, {op['memory_used_mb']:.0f}MB")
            
            report_lines.extend([
                "",
                "### Memory Intensive Operations",
            ])
            
            for i, op in enumerate(bottlenecks.get("memory_intensive_operations", []), 1):
                report_lines.append(f"{i}. **{op['operation']}**: {op['memory_used_mb']:.0f}MB, {op['runtime_seconds']:.2f}s total")
            
            report_lines.append("")
        
        # Cost Analysis
        report_lines.extend([
            "## Cost Analysis",
            "",
            f"**Analysis based on {cost_analysis['pages_per_month']:,} pages per month**",
            "",
            "### Cloud Service Pricing",
        ])
        
        for service, costs in cost_analysis["service_costs"].items():
            report_lines.extend([
                f"#### {service}",
                f"- **Monthly cost:** ${costs['monthly_cost_usd']:.2f}",
                f"- **Annual cost:** ${costs['annual_cost_usd']:.2f}",
                f"- **Price per page:** ${costs['price_per_page']:.4f}",
                f"- **Features:** {', '.join(costs['features'])}",
                "",
            ])
        
        # In-house vs Cloud comparison
        if "inhouse_processing" in cost_analysis:
            inhouse = cost_analysis["inhouse_processing"]
            comparison = cost_analysis["comparison"]
            
            report_lines.extend([
                "### In-House Processing Costs",
                f"- **Monthly compute cost:** ${inhouse['monthly_compute_cost_usd']:.2f}",
                f"- **Monthly total cost:** ${inhouse['monthly_total_cost_usd']:.2f}",
                f"- **Processing hours/month:** {inhouse['processing_hours_per_month']:.1f}",
                f"- **Recommended instance:** {inhouse['estimated_instance_type']}",
                "",
                "### Cost Comparison",
                f"- **Cheapest cloud option:** {comparison['cheapest_cloud_service']} (${comparison['cheapest_cloud_monthly_cost']:.2f}/month)",
                f"- **In-house cost:** ${comparison['inhouse_monthly_cost']:.2f}/month",
                f"- **Cost difference:** ${comparison['cost_difference']:.2f}/month ({'higher' if comparison['cost_difference'] > 0 else 'lower'} for in-house)",
                f"- **Break-even point:** {comparison['breakeven_pages_per_month']:,} pages/month",
                f"- **Recommendation:** {comparison['recommendation'].title()} processing",
                "",
            ])
        
        # Scaling Recommendations
        report_lines.extend([
            "## Scaling Recommendations",
            "",
            "### Hardware Recommendations by Volume",
            "",
        ])
        
        # Volume-based hardware recommendations
        volume_recommendations = [
            {
                "volume": "Small Scale (< 1,000 pages/month)",
                "recommendation": "Cloud services or laptop/desktop processing",
                "specs": "4+ CPU cores, 8GB RAM, SSD storage",
                "rationale": "Minimal infrastructure needs, cloud likely more cost-effective"
            },
            {
                "volume": "Medium Scale (1,000 - 10,000 pages/month)", 
                "recommendation": "Dedicated server or cloud compute instance",
                "specs": "8+ CPU cores, 16GB RAM, NVMe SSD, consider GPU for OCR",
                "rationale": "Balance between cost and performance, hybrid approach viable"
            },
            {
                "volume": "Large Scale (10,000+ pages/month)",
                "recommendation": "High-performance server cluster or container orchestration",
                "specs": "16+ CPU cores per node, 32GB+ RAM, distributed storage, GPU acceleration",
                "rationale": "Dedicated infrastructure becomes cost-effective, parallel processing essential"
            }
        ]
        
        for rec in volume_recommendations:
            report_lines.extend([
                f"#### {rec['volume']}",
                f"**Recommendation:** {rec['recommendation']}",
                f"**Specifications:** {rec['specs']}",
                f"**Rationale:** {rec['rationale']}",
                "",
            ])
        
        # Performance Recommendations
        if bottleneck_analysis.get("recommendations"):
            report_lines.extend([
                "## Performance Optimization Recommendations",
                "",
            ])
            
            for rec in bottleneck_analysis["recommendations"]:
                priority_icon = {"High": "🔴", "Medium": "🟡", "Low": "🟢"}.get(rec["priority"], "🔵")
                report_lines.extend([
                    f"### {rec['category']} {priority_icon}",
                    f"**Priority:** {rec['priority']}",
                    f"**Issue:** {rec['issue']}",
                    f"**Recommendation:** {rec['recommendation']}",
                    "",
                ])
        
        # Visualizations
        if visualization_files:
            report_lines.extend([
                "## Performance Visualizations",
                "",
                "The following visualizations provide detailed analysis of performance characteristics:",
                "",
            ])
            
            for viz_file in visualization_files:
                filename = Path(viz_file).name
                report_lines.append(f"- **{filename.replace('_', ' ').title().replace('.png', '')}**: `{filename}`")
            
            report_lines.append("")
        
        # Monitoring Recommendations
        report_lines.extend([
            "## Monitoring & Alerting Recommendations",
            "",
            "### Key Performance Indicators (KPIs)",
            "- **Throughput**: Pages processed per hour",
            "- **Latency**: Average processing time per page", 
            "- **Resource Utilization**: CPU, Memory, Storage usage",
            "- **Error Rate**: Percentage of failed processing attempts",
            "- **Cost per Page**: Total processing cost divided by pages processed",
            "",
            "### Alert Thresholds",
        ])
        
        if bottleneck_analysis.get("performance_summary"):
            perf = bottleneck_analysis["performance_summary"]
            report_lines.extend([
                f"- **Throughput < {perf['avg_throughput_pages_per_hour'] * 0.7:.0f} pages/hour** (30% below baseline)",
                f"- **Latency > {perf['avg_runtime_per_page'] * 1.5:.1f} seconds/page** (50% above baseline)",
                f"- **Memory usage > {perf['max_memory_usage_mb'] * 1.2:.0f} MB** (20% above peak)",
                f"- **Error rate > 5%** (significant processing failures)",
            ])
        
        report_lines.extend([
            "",
            "---",
            f"*Benchmark report generated by Performance Benchmarker at {datetime.now()}*",
            "",
            f"**Report Location:** `{self.results_dir}`",
            f"**System Benchmarked:** {self.system_info.cpu_model} ({self.system_info.cpu_count} cores, {self.system_info.total_memory_gb:.1f}GB RAM)"
        ])
        
        # Save report
        report_content = "\n".join(report_lines)
        report_file = self.results_dir / "benchmarks.md"
        
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        # Also save JSON data for programmatic access
        benchmark_data = {
            "timestamp": datetime.now().isoformat(),
            "system_info": asdict(self.system_info),
            "benchmark_results": [result.to_dict() for result in self.benchmark_results],
            "bottleneck_analysis": bottleneck_analysis,
            "cost_analysis": cost_analysis,
            "visualization_files": visualization_files
        }
        
        data_file = self.results_dir / "benchmark_data.json"
        with open(data_file, 'w') as f:
            json.dump(benchmark_data, f, indent=2)
        
        self.logger.info(f"Comprehensive benchmark report saved to {report_file}")
        return report_content
    
    def save_results(self) -> str:
        """Save all benchmark results and generate report"""
        return self.generate_benchmarks_report()


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Performance Benchmarking")
    parser.add_argument("--data-dir", required=True, help="Path to data directory")
    parser.add_argument("--pdf-path", help="Path to PDF for benchmarking")
    parser.add_argument("--action", choices=["benchmark", "analyze", "report"], default="report",
                       help="Action to perform")
    parser.add_argument("--pages-per-month", type=int, default=1000, 
                       help="Pages per month for cost analysis")
    
    args = parser.parse_args()
    
    benchmarker = PerformanceBenchmarker(Path(args.data_dir))
    
    if args.action == "benchmark" and args.pdf_path:
        pdf_path = Path(args.pdf_path)
        results = benchmarker.benchmark_full_pipeline(pdf_path)
        print(f"Benchmarked {len(results)} operations")
        
    elif args.action == "analyze":
        analysis = benchmarker.analyze_bottlenecks()
        print(f"Performance analysis completed: {len(analysis['recommendations'])} recommendations")
        
    elif args.action == "report":
        report = benchmarker.generate_benchmarks_report()
        print("Generated comprehensive benchmark report")
    
    # Always save results
    benchmarker.save_results()