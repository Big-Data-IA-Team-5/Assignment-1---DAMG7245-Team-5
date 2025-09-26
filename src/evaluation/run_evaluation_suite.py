#!/usr/bin/env python3
"""
Main Evaluation & Benchmarking Script

This script orchestrates the complete evaluation and benchmarking process for Parts 9 & 10:
- Parser quality evaluation using comparative analysis
- Regression testing with automated failure detection
- Distribution drift visualization and monitoring
- Performance benchmarking and cost analysis
- Report generation with actionable recommendations

Usage:
    python run_evaluation_suite.py --data-dir data/intermediate [options]
"""

import argparse
import json
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

# Import evaluation modules
from parser_quality_evaluator import ParserQualityEvaluator
from parser_regression_tester import ParserRegressionTester
from distribution_drift_visualizer import DistributionDriftVisualizer
from performance_benchmarker import PerformanceBenchmarker


def setup_logging(verbose: bool = False) -> logging.Logger:
    """Set up logging configuration"""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('evaluation_suite.log')
        ]
    )
    return logging.getLogger(__name__)


class EvaluationSuite:
    """
    Comprehensive evaluation and benchmarking suite for document parsing pipeline.
    Combines quality evaluation, regression testing, visualization, and performance analysis.
    """
    
    def __init__(self, data_dir: Path, pdf_path: Optional[Path] = None, output_dir: Optional[Path] = None):
        """
        Initialize evaluation suite
        
        Args:
            data_dir: Path to parsed data directory
            pdf_path: Optional PDF file for fresh benchmarking
            output_dir: Optional custom output directory
        """
        self.data_dir = Path(data_dir)
        self.pdf_path = Path(pdf_path) if pdf_path else None
        self.output_dir = output_dir or (self.data_dir / "evaluation_metrics")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize components
        # Initialize evaluation components with XBRL support
        xbrl_dir = self.data_dir.parent / "raw" / "xbrl_files"
        self.quality_evaluator = ParserQualityEvaluator(self.data_dir, xbrl_dir=xbrl_dir)
        self.regression_tester = ParserRegressionTester(self.data_dir)
        self.drift_visualizer = DistributionDriftVisualizer(self.data_dir, self.output_dir / "visualizations")
        self.performance_benchmarker = PerformanceBenchmarker(self.data_dir, self.output_dir / "benchmarks")
        
        # Results storage
        self.evaluation_results = {}
        
    def run_quality_evaluation(self) -> Dict:
        """Run comprehensive parser quality evaluation"""
        self.logger.info("Starting parser quality evaluation...")
        
        try:
            # Calculate text and table consistency metrics
            text_metrics = self.quality_evaluator.calculate_text_consistency_metrics()
            table_metrics = self.quality_evaluator.calculate_table_consistency_metrics()
            
            # Detect distribution drift
            drift_analysis = self.quality_evaluator.detect_distribution_drift()
            
            # Validate against XBRL ground truth
            self.logger.info("Validating parsed data against XBRL ground truth...")
            xbrl_validation = self.quality_evaluator.validate_against_xbrl_ground_truth()
            
            # Generate quality report
            quality_report = self.quality_evaluator.generate_evaluation_report()
            
            results = {
                "status": "success",
                "text_metrics": text_metrics,
                "table_metrics": table_metrics,
                "drift_analysis": drift_analysis,
                "xbrl_validation": xbrl_validation,
                "report_content": quality_report
            }
            
            self.logger.info("✅ Quality evaluation completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Quality evaluation failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_regression_testing(self) -> Dict:
        """Run regression testing with failure simulation"""
        self.logger.info("Starting regression testing...")
        
        try:
            # Run current regression tests
            test_results = self.regression_tester.run_regression_tests()
            
            # Test failure detection capabilities
            failure_simulations = {}
            for failure_type in ["accuracy_drop", "extraction_failure", "consistency_loss"]:
                simulation = self.regression_tester.simulate_parser_failure(failure_type)
                failure_simulations[failure_type] = simulation
            
            # Generate regression report
            regression_report = self.regression_tester.generate_regression_test_report()
            
            results = {
                "status": "success",
                "test_results": test_results,
                "failure_simulations": failure_simulations,
                "report_content": regression_report
            }
            
            # Log critical issues
            if test_results["overall_status"] == "FAIL":
                self.logger.error("🚨 CRITICAL: Regression tests are failing!")
            elif test_results["overall_status"] == "WARNING":
                self.logger.warning("⚠️ WARNING: Some regression tests failing")
            else:
                self.logger.info("✅ All regression tests passing")
            
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Regression testing failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_visualization_analysis(self) -> Dict:
        """Run distribution drift visualization analysis"""
        self.logger.info("Starting visualization analysis...")
        
        try:
            # Generate comprehensive visualizations
            viz_report = self.drift_visualizer.generate_comprehensive_visualization_report()
            
            # Create individual visualizations
            visualizations = {
                "text_analysis": self.drift_visualizer.create_text_distribution_analysis(),
                "table_analysis": self.drift_visualizer.create_table_structure_analysis(),
                "method_comparison": self.drift_visualizer.create_method_performance_comparison(),
                "drift_dashboard": self.drift_visualizer.create_drift_detection_dashboard()
            }
            
            results = {
                "status": "success",
                "visualizations": visualizations,
                "report_content": viz_report
            }
            
            self.logger.info("✅ Visualization analysis completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Visualization analysis failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_performance_benchmarking(self) -> Dict:
        """Run performance benchmarking and cost analysis"""
        self.logger.info("Starting performance benchmarking...")
        
        try:
            # Run benchmarking if PDF provided
            if self.pdf_path and self.pdf_path.exists():
                self.logger.info(f"Benchmarking with PDF: {self.pdf_path}")
                benchmark_results = self.performance_benchmarker.benchmark_full_pipeline(self.pdf_path)
            else:
                self.logger.info("No PDF provided, using existing data for analysis")
                benchmark_results = []
            
            # Analyze bottlenecks
            bottleneck_analysis = self.performance_benchmarker.analyze_bottlenecks()
            
            # Estimate costs
            cost_analysis = self.performance_benchmarker.estimate_cloud_costs()
            
            # Generate visualizations
            viz_files = self.performance_benchmarker.create_performance_visualizations()
            
            # Generate comprehensive report
            benchmarks_report = self.performance_benchmarker.generate_benchmarks_report()
            
            results = {
                "status": "success",
                "benchmark_results": [r.to_dict() for r in benchmark_results],
                "bottleneck_analysis": bottleneck_analysis,
                "cost_analysis": cost_analysis,
                "visualization_files": viz_files,
                "report_content": benchmarks_report
            }
            
            self.logger.info("✅ Performance benchmarking completed successfully")
            return results
            
        except Exception as e:
            self.logger.error(f"❌ Performance benchmarking failed: {e}")
            return {"status": "error", "error": str(e)}
    
    def run_complete_evaluation(self) -> Dict:
        """Run the complete evaluation suite"""
        self.logger.info("🚀 Starting complete evaluation suite...")
        
        start_time = datetime.now()
        
        # Run all evaluation components
        self.evaluation_results = {
            "timestamp": start_time.isoformat(),
            "quality_evaluation": self.run_quality_evaluation(),
            "regression_testing": self.run_regression_testing(),
            "visualization_analysis": self.run_visualization_analysis(),
            "performance_benchmarking": self.run_performance_benchmarking()
        }
        
        # Calculate overall status
        failed_components = [name for name, result in self.evaluation_results.items() 
                           if isinstance(result, dict) and result.get("status") == "error"]
        
        if failed_components:
            overall_status = "partial_failure"
            self.logger.warning(f"⚠️ Evaluation completed with failures in: {', '.join(failed_components)}")
        else:
            overall_status = "success"
            self.logger.info("✅ Complete evaluation suite finished successfully")
        
        # Add summary information
        end_time = datetime.now()
        self.evaluation_results["summary"] = {
            "overall_status": overall_status,
            "failed_components": failed_components,
            "total_duration": str(end_time - start_time),
            "completion_time": end_time.isoformat()
        }
        
        # Save results
        self._save_results()
        
        # Generate executive summary
        self._generate_executive_summary()
        
        return self.evaluation_results
    
    def _save_results(self):
        """Save evaluation results to JSON file"""
        results_file = self.output_dir / f"evaluation_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        # Create serializable copy (remove non-JSON-serializable content)
        serializable_results = {}
        for key, value in self.evaluation_results.items():
            if isinstance(value, dict):
                serializable_results[key] = {k: v for k, v in value.items() 
                                           if k != "report_content"}  # Exclude large text content
            else:
                serializable_results[key] = value
        
        with open(results_file, 'w') as f:
            json.dump(serializable_results, f, indent=2)
        
        self.logger.info(f"📁 Evaluation results saved to: {results_file}")
    
    def _generate_executive_summary(self):
        """Generate executive summary report"""
        summary_lines = [
            "# Parser Evaluation & Benchmarking Executive Summary",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Data Source:** `{self.data_dir}`",
            "",
            "## Overview",
            "",
            "This executive summary provides key findings from comprehensive evaluation of the",
            "document parsing pipeline, including quality assessment, regression testing,",
            "distribution analysis, and performance benchmarking.",
            "",
        ]
        
        # Overall status
        summary = self.evaluation_results.get("summary", {})
        status_icon = "✅" if summary.get("overall_status") == "success" else "⚠️"
        
        summary_lines.extend([
            "## Executive Status",
            "",
            f"{status_icon} **Overall Status:** {summary.get('overall_status', 'unknown').replace('_', ' ').title()}",
            f"⏱️ **Total Duration:** {summary.get('total_duration', 'unknown')}",
            "",
        ])
        
        if summary.get("failed_components"):
            summary_lines.extend([
                f"❌ **Failed Components:** {', '.join(summary['failed_components'])}",
                "",
            ])
        
        # Quality evaluation summary
        quality_results = self.evaluation_results.get("quality_evaluation", {})
        if quality_results.get("status") == "success":
            text_metrics = quality_results.get("text_metrics", {})
            table_metrics = quality_results.get("table_metrics", {})
            
            summary_lines.extend([
                "## Quality Assessment Summary",
                "",
                f"- **Text Extraction Success Rate:** {text_metrics.get('successful_extraction_rate', 0):.1%}",
                f"- **Average Characters per Page:** {text_metrics.get('avg_chars_per_page', 0):.0f}",
                f"- **OCR Usage Rate:** {text_metrics.get('ocr_rate', 0):.1%}",
            ])
            
            if "method_comparison" in table_metrics:
                method_count = len(table_metrics["method_comparison"])
                total_tables = sum(stats.get("table_count", 0) for stats in table_metrics["method_comparison"].values())
                summary_lines.extend([
                    f"- **Table Extraction Methods:** {method_count}",
                    f"- **Total Tables Extracted:** {total_tables}",
                ])
            
            summary_lines.append("")
        
        # Regression testing summary
        regression_results = self.evaluation_results.get("regression_testing", {})
        if regression_results.get("status") == "success":
            test_results = regression_results.get("test_results", {})
            
            summary_lines.extend([
                "## Regression Testing Summary",
                "",
                f"- **Tests Run:** {test_results.get('tests_run', 0)}",
                f"- **Tests Passed:** {test_results.get('tests_passed', 0)}",
                f"- **Tests Failed:** {test_results.get('tests_failed', 0)}",
                f"- **Overall Status:** {test_results.get('overall_status', 'unknown')}",
                "",
            ])
            
            # Highlight critical failures
            if test_results.get("tests_failed", 0) > 0:
                summary_lines.extend([
                    "### ⚠️ Critical Issues Detected",
                    "Regression tests have identified performance degradation.",
                    "Immediate investigation recommended.",
                    "",
                ])
        
        # Performance summary
        perf_results = self.evaluation_results.get("performance_benchmarking", {})
        if perf_results.get("status") == "success":
            bottleneck_analysis = perf_results.get("bottleneck_analysis", {})
            cost_analysis = perf_results.get("cost_analysis", {})
            
            if "performance_summary" in bottleneck_analysis:
                perf_summary = bottleneck_analysis["performance_summary"]
                
                summary_lines.extend([
                    "## Performance Summary",
                    "",
                    f"- **Average Processing Time:** {perf_summary.get('avg_runtime_per_page', 0):.2f} seconds/page",
                    f"- **Throughput:** {perf_summary.get('avg_throughput_pages_per_hour', 0):.0f} pages/hour",
                    f"- **Memory Usage:** {perf_summary.get('avg_memory_usage_mb', 0):.1f} MB average",
                    f"- **Success Rate:** {perf_summary.get('overall_success_rate', 0):.1f}%",
                    "",
                ])
            
            if "comparison" in cost_analysis:
                comparison = cost_analysis["comparison"]
                
                summary_lines.extend([
                    "## Cost Analysis Summary",
                    "",
                    f"- **Monthly Volume:** {cost_analysis.get('pages_per_month', 0):,} pages",
                    f"- **Cheapest Cloud Option:** {comparison.get('cheapest_cloud_service', 'unknown')}",
                    f"- **Cloud Cost:** ${comparison.get('cheapest_cloud_monthly_cost', 0):.2f}/month",
                    f"- **In-house Cost:** ${comparison.get('inhouse_monthly_cost', 0):.2f}/month",
                    f"- **Recommendation:** {comparison.get('recommendation', 'unknown').title()} processing",
                    "",
                ])
        
        # Key recommendations
        summary_lines.extend([
            "## Key Recommendations",
            "",
        ])
        
        # Collect recommendations from all components
        recommendations = []
        
        # Add regression test recommendations
        if regression_results.get("test_results", {}).get("overall_status") == "FAIL":
            recommendations.append("🚨 **URGENT:** Address failing regression tests immediately")
        
        # Add performance recommendations
        if perf_results.get("bottleneck_analysis", {}).get("recommendations"):
            perf_recs = perf_results["bottleneck_analysis"]["recommendations"]
            high_priority_recs = [r for r in perf_recs if r.get("priority") == "High"]
            for rec in high_priority_recs[:3]:  # Top 3 high priority
                recommendations.append(f"⚡ **Performance:** {rec.get('recommendation', 'Unknown')}")
        
        # Add cost recommendations
        if cost_analysis.get("comparison", {}).get("recommendation"):
            cost_rec = cost_analysis["comparison"]["recommendation"]
            recommendations.append(f"💰 **Cost Optimization:** Use {cost_rec} processing for optimal costs")
        
        if not recommendations:
            recommendations.append("✅ **System Status:** All metrics within acceptable ranges")
        
        for rec in recommendations[:5]:  # Top 5 recommendations
            summary_lines.append(f"- {rec}")
        
        summary_lines.extend([
            "",
            "## Next Steps",
            "",
            "1. **Review Detailed Reports:** Check individual component reports for detailed analysis",
            "2. **Monitor Metrics:** Set up regular monitoring based on established baselines", 
            "3. **Address Issues:** Prioritize and address any identified performance or quality issues",
            "4. **Regular Evaluation:** Schedule periodic re-evaluation to track improvements",
            "",
            "---",
            "",
            "### 📋 Detailed Reports Available:",
        ])
        
        # List available detailed reports
        report_files = []
        for component_dir in ["evaluation_metrics", "benchmarks", "visualizations"]:
            component_path = self.output_dir / component_dir
            if component_path.exists():
                report_files.extend([
                    str(f.relative_to(self.output_dir)) for f in component_path.rglob("*.md")
                ])
        
        for report_file in sorted(report_files):
            summary_lines.append(f"- `{report_file}`")
        
        summary_lines.extend([
            "",
            f"*Executive summary generated by Evaluation Suite at {datetime.now()}*"
        ])
        
        # Save executive summary
        summary_content = "\n".join(summary_lines)
        summary_file = self.output_dir / "EXECUTIVE_SUMMARY.md"
        
        with open(summary_file, 'w') as f:
            f.write(summary_content)
        
        self.logger.info(f"📊 Executive summary saved to: {summary_file}")
        
        # Also print key findings to console
        print("\n" + "="*60)
        print("🏆 EVALUATION SUITE COMPLETE")
        print("="*60)
        print(f"✅ Status: {summary.get('overall_status', 'unknown').replace('_', ' ').title()}")
        print(f"⏱️  Duration: {summary.get('total_duration', 'unknown')}")
        print(f"📊 Executive Summary: {summary_file}")
        print(f"📁 Results Directory: {self.output_dir}")
        
        if summary.get("failed_components"):
            print(f"❌ Failed Components: {', '.join(summary['failed_components'])}")
        
        print("="*60)


def main():
    """Main entry point for evaluation suite"""
    parser = argparse.ArgumentParser(
        description="Comprehensive Parser Evaluation & Benchmarking Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run complete evaluation suite
  python run_evaluation_suite.py --data-dir data/intermediate

  # Run with fresh PDF benchmarking
  python run_evaluation_suite.py --data-dir data/intermediate --pdf-path data/raw/tesla.pdf

  # Run specific components only
  python run_evaluation_suite.py --data-dir data/intermediate --component quality --component regression

  # Run with custom output directory
  python run_evaluation_suite.py --data-dir data/intermediate --output-dir results/evaluation
        """
    )
    
    parser.add_argument("--data-dir", required=True, type=Path,
                       help="Path to parsed data directory (data/intermediate)")
    parser.add_argument("--pdf-path", type=Path,
                       help="Optional PDF file for fresh benchmarking")
    parser.add_argument("--output-dir", type=Path,
                       help="Custom output directory for results")
    parser.add_argument("--component", action="append", 
                       choices=["quality", "regression", "visualization", "performance", "all"],
                       help="Specific components to run (default: all)")
    parser.add_argument("--verbose", "-v", action="store_true",
                       help="Enable verbose logging")
    
    args = parser.parse_args()
    
    # Set up logging
    logger = setup_logging(args.verbose)
    
    # Validate input directory
    if not args.data_dir.exists():
        logger.error(f"Data directory does not exist: {args.data_dir}")
        return 1
    
    # Validate PDF file if provided
    if args.pdf_path and not args.pdf_path.exists():
        logger.error(f"PDF file does not exist: {args.pdf_path}")
        return 1
    
    # Initialize evaluation suite
    try:
        suite = EvaluationSuite(args.data_dir, args.pdf_path, args.output_dir)
        
        # Determine which components to run
        components = args.component or ["all"]
        if "all" in components:
            components = ["quality", "regression", "visualization", "performance"]
        
        # Run requested components
        if len(components) == 4:  # All components
            results = suite.run_complete_evaluation()
        else:
            # Run individual components
            results = {"timestamp": datetime.now().isoformat()}
            
            if "quality" in components:
                results["quality_evaluation"] = suite.run_quality_evaluation()
            if "regression" in components:
                results["regression_testing"] = suite.run_regression_testing()
            if "visualization" in components:
                results["visualization_analysis"] = suite.run_visualization_analysis()
            if "performance" in components:
                results["performance_benchmarking"] = suite.run_performance_benchmarking()
            
            suite.evaluation_results = results
            suite._save_results()
            suite._generate_executive_summary()
        
        # Check for critical issues
        regression_results = results.get("regression_testing", {})
        if regression_results.get("test_results", {}).get("overall_status") == "FAIL":
            logger.error("🚨 CRITICAL: Regression tests failing - immediate attention required!")
            return 2  # Critical failure exit code
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ Evaluation suite failed: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())