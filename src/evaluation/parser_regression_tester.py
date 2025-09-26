#!/usr/bin/env python3
"""
Part 9: Parser Regression Testing Framework

This module provides automated regression testing for parsing quality by establishing
baseline performance thresholds and detecting when parsing quality degrades.

Key features:
- Automated threshold setting based on current parsing performance
- Unit tests that fail when quality drops below acceptable levels
- Simulation of parser failures to validate test sensitivity
- Integration with existing parsed data for realistic testing
"""

import json
import logging
import unittest
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from unittest.mock import patch
import tempfile
import shutil

import numpy as np
import pandas as pd

from parser_quality_evaluator import ParserQualityEvaluator, ParsingMetrics


class ParserRegressionTester:
    """
    Manages regression testing for parser quality using baseline performance metrics
    derived from existing parsed data.
    """
    
    def __init__(self, data_dir: Path, thresholds_file: Optional[Path] = None):
        """
        Initialize regression tester
        
        Args:
            data_dir: Path to parsed data directory
            thresholds_file: Optional path to custom thresholds file
        """
        self.data_dir = Path(data_dir)
        self.evaluator = ParserQualityEvaluator(data_dir)
        self.thresholds_file = thresholds_file or (self.data_dir / "evaluation_metrics" / "quality_thresholds.json")
        
        # Set up logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)
        
        # Load or create quality thresholds
        self.thresholds = self._load_or_create_thresholds()
        
    def _load_or_create_thresholds(self) -> Dict[str, Any]:
        """Load existing thresholds or create new ones based on current performance"""
        if self.thresholds_file.exists():
            with open(self.thresholds_file, 'r') as f:
                thresholds = json.load(f)
            self.logger.info(f"Loaded existing thresholds from {self.thresholds_file}")
            return thresholds
        else:
            return self._create_baseline_thresholds()
    
    def _create_baseline_thresholds(self) -> Dict[str, Any]:
        """
        Create baseline quality thresholds based on current parser performance.
        These thresholds represent acceptable minimum quality levels.
        """
        self.logger.info("Creating baseline quality thresholds from current performance...")
        
        # Get current performance metrics
        text_metrics = self.evaluator.calculate_text_consistency_metrics()
        table_metrics = self.evaluator.calculate_table_consistency_metrics()
        
        # Set conservative thresholds (allowing for some performance degradation)
        thresholds = {
            "metadata": {
                "created": datetime.now().isoformat(),
                "description": "Baseline quality thresholds derived from current parser performance",
                "version": "1.0"
            },
            "text_extraction": {
                # Allow 20% degradation from current performance
                "min_successful_extraction_rate": max(0.7, text_metrics.get('successful_extraction_rate', 0.8) * 0.8),
                "min_avg_chars_per_page": max(100, text_metrics.get('avg_chars_per_page', 1000) * 0.5),
                "max_ocr_rate": min(0.3, text_metrics.get('ocr_rate', 0.1) * 2.0),  # Allow some increase in OCR usage
                "max_chars_cv": min(2.0, text_metrics.get('chars_cv', 1.0) * 1.5),  # Coefficient of variation
                "min_content_entropy": max(1.0, text_metrics.get('content_distribution_entropy', 2.0) * 0.7)
            },
            "table_extraction": {},
            "consistency": {
                "min_method_agreement": 0.6,  # At least 60% agreement between methods
                "min_structure_consistency": 0.5,  # At least 50% structure similarity
                "max_drift_threshold": 0.3  # Maximum 30% drift from baseline
            },
            "performance": {
                "max_processing_time_per_page": 30.0,  # seconds
                "max_memory_usage_mb": 1000,  # MB
                "min_throughput_pages_per_hour": 120
            }
        }
        
        # Add table-specific thresholds if table data exists
        if 'method_comparison' in table_metrics:
            method_stats = table_metrics['method_comparison']
            best_quality = max((stats.get('avg_content_quality', 0) for stats in method_stats.values()), default=0.5)
            
            thresholds["table_extraction"] = {
                "min_table_count_per_document": max(5, len(method_stats) * 0.7),
                "min_content_quality": max(0.3, best_quality * 0.7),
                "min_page_coverage_ratio": 0.4,  # At least 40% of pages should have tables
                "max_extraction_failure_rate": 0.2  # Max 20% extraction failures
            }
            
            # Add method-specific thresholds
            for method, stats in method_stats.items():
                thresholds["table_extraction"][f"{method}_min_quality"] = max(0.3, stats.get('avg_content_quality', 0.5) * 0.8)
                if 'avg_accuracy' in stats and stats['avg_accuracy'] > 0:
                    thresholds["table_extraction"][f"{method}_min_accuracy"] = max(70.0, stats['avg_accuracy'] * 0.9)
        
        # Save thresholds
        self.thresholds_file.parent.mkdir(exist_ok=True)
        with open(self.thresholds_file, 'w') as f:
            json.dump(thresholds, f, indent=2)
        
        self.logger.info(f"Created baseline thresholds saved to {self.thresholds_file}")
        return thresholds
    
    def run_regression_tests(self) -> Dict[str, Any]:
        """
        Run comprehensive regression tests and return results
        
        Returns:
            Dictionary containing test results and any failures detected
        """
        test_results = {
            "timestamp": datetime.now().isoformat(),
            "tests_run": 0,
            "tests_passed": 0,
            "tests_failed": 0,
            "failures": [],
            "warnings": [],
            "overall_status": "UNKNOWN"
        }
        
        # Run text extraction regression tests
        text_results = self._test_text_extraction_quality()
        test_results["text_extraction_tests"] = text_results
        
        # Run table extraction regression tests  
        table_results = self._test_table_extraction_quality()
        test_results["table_extraction_tests"] = table_results
        
        # Run consistency regression tests
        consistency_results = self._test_parsing_consistency()
        test_results["consistency_tests"] = consistency_results
        
        # Aggregate results
        all_test_categories = [text_results, table_results, consistency_results]
        
        for category_results in all_test_categories:
            test_results["tests_run"] += category_results.get("tests_run", 0)
            test_results["tests_passed"] += category_results.get("tests_passed", 0)
            test_results["tests_failed"] += category_results.get("tests_failed", 0)
            test_results["failures"].extend(category_results.get("failures", []))
            test_results["warnings"].extend(category_results.get("warnings", []))
        
        # Determine overall status
        if test_results["tests_failed"] == 0:
            test_results["overall_status"] = "PASS"
        elif test_results["tests_failed"] / max(test_results["tests_run"], 1) > 0.2:
            test_results["overall_status"] = "FAIL"
        else:
            test_results["overall_status"] = "WARNING"
        
        # Save test results
        results_file = self.data_dir / "evaluation_metrics" / f"regression_test_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(test_results, f, indent=2)
        
        self.logger.info(f"Regression test results saved to {results_file}")
        return test_results
    
    def _test_text_extraction_quality(self) -> Dict[str, Any]:
        """Test text extraction quality against thresholds"""
        results = {"tests_run": 0, "tests_passed": 0, "tests_failed": 0, "failures": [], "warnings": []}
        
        current_metrics = self.evaluator.calculate_text_consistency_metrics()
        thresholds = self.thresholds.get("text_extraction", {})
        
        # Test successful extraction rate
        results["tests_run"] += 1
        success_rate = current_metrics.get('successful_extraction_rate', 0)
        min_success = thresholds.get('min_successful_extraction_rate', 0.7)
        
        if success_rate >= min_success:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["failures"].append({
                "test": "text_extraction_success_rate",
                "expected": f">= {min_success:.2%}",
                "actual": f"{success_rate:.2%}",
                "message": "Text extraction success rate below acceptable threshold"
            })
        
        # Test average characters per page
        results["tests_run"] += 1
        avg_chars = current_metrics.get('avg_chars_per_page', 0)
        min_chars = thresholds.get('min_avg_chars_per_page', 100)
        
        if avg_chars >= min_chars:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["failures"].append({
                "test": "avg_chars_per_page",
                "expected": f">= {min_chars:.0f}",
                "actual": f"{avg_chars:.0f}",
                "message": "Average characters per page below acceptable threshold"
            })
        
        # Test OCR usage rate
        results["tests_run"] += 1
        ocr_rate = current_metrics.get('ocr_rate', 0)
        max_ocr = thresholds.get('max_ocr_rate', 0.3)
        
        if ocr_rate <= max_ocr:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["failures"].append({
                "test": "ocr_usage_rate",
                "expected": f"<= {max_ocr:.2%}",
                "actual": f"{ocr_rate:.2%}",
                "message": "OCR usage rate higher than acceptable threshold"
            })
        
        # Test content variability
        results["tests_run"] += 1
        chars_cv = current_metrics.get('chars_cv', 0)
        max_cv = thresholds.get('max_chars_cv', 2.0)
        
        if chars_cv <= max_cv:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["failures"].append({
                "test": "content_variability",
                "expected": f"<= {max_cv:.3f}",
                "actual": f"{chars_cv:.3f}",
                "message": "Content length variability higher than acceptable threshold"
            })
        
        return results
    
    def _test_table_extraction_quality(self) -> Dict[str, Any]:
        """Test table extraction quality against thresholds"""
        results = {"tests_run": 0, "tests_passed": 0, "tests_failed": 0, "failures": [], "warnings": []}
        
        current_metrics = self.evaluator.calculate_table_consistency_metrics()
        thresholds = self.thresholds.get("table_extraction", {})
        
        if 'method_comparison' not in current_metrics:
            results["warnings"].append("No table extraction data available for testing")
            return results
        
        method_stats = current_metrics['method_comparison']
        
        # Test overall table count
        results["tests_run"] += 1
        total_tables = sum(stats['table_count'] for stats in method_stats.values())
        min_tables = thresholds.get('min_table_count_per_document', 5)
        
        if total_tables >= min_tables:
            results["tests_passed"] += 1
        else:
            results["tests_failed"] += 1
            results["failures"].append({
                "test": "total_table_count",
                "expected": f">= {min_tables}",
                "actual": f"{total_tables}",
                "message": "Total extracted tables below acceptable threshold"
            })
        
        # Test method-specific quality
        for method, stats in method_stats.items():
            method_quality_key = f"{method}_min_quality"
            if method_quality_key in thresholds:
                results["tests_run"] += 1
                actual_quality = stats.get('avg_content_quality', 0)
                min_quality = thresholds[method_quality_key]
                
                if actual_quality >= min_quality:
                    results["tests_passed"] += 1
                else:
                    results["tests_failed"] += 1
                    results["failures"].append({
                        "test": f"{method}_content_quality",
                        "expected": f">= {min_quality:.3f}",
                        "actual": f"{actual_quality:.3f}",
                        "message": f"{method} content quality below acceptable threshold"
                    })
            
            # Test accuracy for methods that provide it
            accuracy_key = f"{method}_min_accuracy"
            if accuracy_key in thresholds and 'avg_accuracy' in stats and stats['avg_accuracy'] > 0:
                results["tests_run"] += 1
                actual_accuracy = stats['avg_accuracy']
                min_accuracy = thresholds[accuracy_key]
                
                if actual_accuracy >= min_accuracy:
                    results["tests_passed"] += 1
                else:
                    results["tests_failed"] += 1
                    results["failures"].append({
                        "test": f"{method}_accuracy",
                        "expected": f">= {min_accuracy:.1f}%",
                        "actual": f"{actual_accuracy:.1f}%",
                        "message": f"{method} accuracy below acceptable threshold"
                    })
        
        return results
    
    def _test_parsing_consistency(self) -> Dict[str, Any]:
        """Test consistency between different parsing methods"""
        results = {"tests_run": 0, "tests_passed": 0, "tests_failed": 0, "failures": [], "warnings": []}
        
        current_metrics = self.evaluator.calculate_table_consistency_metrics()
        thresholds = self.thresholds.get("consistency", {})
        
        # Test page overlap ratio
        if 'page_overlap_ratio' in current_metrics:
            results["tests_run"] += 1
            overlap_ratio = current_metrics['page_overlap_ratio']
            min_overlap = thresholds.get('min_method_agreement', 0.6)
            
            if overlap_ratio >= min_overlap:
                results["tests_passed"] += 1
            else:
                results["tests_failed"] += 1
                results["failures"].append({
                    "test": "method_agreement",
                    "expected": f">= {min_overlap:.2%}",
                    "actual": f"{overlap_ratio:.2%}",
                    "message": "Method agreement lower than acceptable threshold"
                })
        
        # Test structure consistency
        if 'structure_consistency' in current_metrics:
            results["tests_run"] += 1
            structure_consistency = current_metrics['structure_consistency']
            min_structure = thresholds.get('min_structure_consistency', 0.5)
            
            if structure_consistency >= min_structure:
                results["tests_passed"] += 1
            else:
                results["tests_failed"] += 1
                results["failures"].append({
                    "test": "structure_consistency",
                    "expected": f">= {min_structure:.3f}",
                    "actual": f"{structure_consistency:.3f}",
                    "message": "Structure consistency lower than acceptable threshold"
                })
        
        # Test distribution drift
        drift_analysis = self.evaluator.detect_distribution_drift()
        if 'overall_assessment' in drift_analysis:
            results["tests_run"] += 1
            max_drift = drift_analysis['overall_assessment'].get('max_drift', 0)
            drift_threshold = thresholds.get('max_drift_threshold', 0.3)
            
            if max_drift <= drift_threshold:
                results["tests_passed"] += 1
            else:
                results["tests_failed"] += 1
                results["failures"].append({
                    "test": "distribution_drift",
                    "expected": f"<= {drift_threshold:.2%}",
                    "actual": f"{max_drift:.2%}",
                    "message": "Distribution drift exceeds acceptable threshold"
                })
        
        return results
    
    def simulate_parser_failure(self, failure_type: str = "accuracy_drop") -> Dict[str, Any]:
        """
        Simulate parser failures to validate that regression tests properly detect issues.
        
        Args:
            failure_type: Type of failure to simulate
                - "accuracy_drop": Simulate accuracy degradation
                - "extraction_failure": Simulate extraction failures
                - "consistency_loss": Simulate consistency issues
        
        Returns:
            Results showing whether tests properly detected the simulated failure
        """
        self.logger.info(f"Simulating parser failure: {failure_type}")
        
        # Create temporary modified thresholds to simulate failure
        original_thresholds = self.thresholds.copy()
        
        try:
            if failure_type == "accuracy_drop":
                # Simulate accuracy drop by raising thresholds artificially
                if "table_extraction" in self.thresholds:
                    for key, value in self.thresholds["table_extraction"].items():
                        if "min_quality" in key:
                            self.thresholds["table_extraction"][key] = value * 2.0  # Double the requirement
                        elif "min_accuracy" in key:
                            self.thresholds["table_extraction"][key] = min(99.0, value * 1.5)
                
            elif failure_type == "extraction_failure":
                # Simulate extraction failure by setting very high success requirements
                self.thresholds["text_extraction"]["min_successful_extraction_rate"] = 0.99
                self.thresholds["text_extraction"]["min_avg_chars_per_page"] *= 10
                
            elif failure_type == "consistency_loss":
                # Simulate consistency issues by setting very high consistency requirements
                self.thresholds["consistency"]["min_method_agreement"] = 0.95
                self.thresholds["consistency"]["min_structure_consistency"] = 0.9
                self.thresholds["consistency"]["max_drift_threshold"] = 0.01
            
            # Run tests with simulated failure conditions
            test_results = self.run_regression_tests()
            
            # Validate that tests detected the failure
            simulation_results = {
                "failure_type": failure_type,
                "tests_detected_failure": test_results["tests_failed"] > 0,
                "failure_count": test_results["tests_failed"],
                "overall_status": test_results["overall_status"],
                "detected_issues": test_results["failures"],
                "validation": "PASS" if test_results["tests_failed"] > 0 else "FAIL"
            }
            
            if simulation_results["validation"] == "PASS":
                self.logger.info(f"✓ Regression tests successfully detected simulated {failure_type}")
            else:
                self.logger.warning(f"✗ Regression tests failed to detect simulated {failure_type}")
            
            return simulation_results
            
        finally:
            # Restore original thresholds
            self.thresholds = original_thresholds
    
    def generate_regression_test_report(self) -> str:
        """Generate comprehensive regression testing report"""
        # Run current regression tests
        test_results = self.run_regression_tests()
        
        # Test failure detection capabilities
        failure_simulations = {}
        for failure_type in ["accuracy_drop", "extraction_failure", "consistency_loss"]:
            failure_simulations[failure_type] = self.simulate_parser_failure(failure_type)
        
        # Generate report
        report_lines = [
            "# Parser Regression Testing Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Current Status",
            "",
            f"- **Overall Status:** {test_results['overall_status']}",
            f"- **Tests Run:** {test_results['tests_run']}",
            f"- **Tests Passed:** {test_results['tests_passed']}",
            f"- **Tests Failed:** {test_results['tests_failed']}",
            f"- **Success Rate:** {test_results['tests_passed'] / max(test_results['tests_run'], 1):.1%}",
            "",
        ]
        
        # Add detailed test results
        if test_results["failures"]:
            report_lines.extend([
                "## Failed Tests",
                "",
            ])
            for failure in test_results["failures"]:
                report_lines.extend([
                    f"### {failure['test'].replace('_', ' ').title()}",
                    f"- **Expected:** {failure['expected']}",
                    f"- **Actual:** {failure['actual']}",
                    f"- **Issue:** {failure['message']}",
                    "",
                ])
        
        # Add warnings
        if test_results["warnings"]:
            report_lines.extend([
                "## Warnings",
                "",
            ])
            for warning in test_results["warnings"]:
                report_lines.append(f"- {warning}")
            report_lines.append("")
        
        # Add failure detection validation results
        report_lines.extend([
            "## Failure Detection Validation",
            "Testing whether regression tests can properly detect different types of parser degradation:",
            "",
        ])
        
        for failure_type, sim_results in failure_simulations.items():
            status_icon = "✓" if sim_results["validation"] == "PASS" else "✗"
            report_lines.extend([
                f"### {failure_type.replace('_', ' ').title()} Detection",
                f"{status_icon} **Status:** {sim_results['validation']}",
                f"- **Failures Detected:** {sim_results['failure_count']}",
                f"- **Test Sensitivity:** {'Good' if sim_results['tests_detected_failure'] else 'Poor'}",
                "",
            ])
        
        # Add threshold information
        report_lines.extend([
            "## Current Quality Thresholds",
            "",
            "### Text Extraction Thresholds",
        ])
        
        text_thresholds = self.thresholds.get("text_extraction", {})
        for key, value in text_thresholds.items():
            if isinstance(value, float):
                if "rate" in key or "ratio" in key:
                    report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value:.2%}")
                else:
                    report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value:.3f}")
            else:
                report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        report_lines.extend([
            "",
            "### Table Extraction Thresholds",
        ])
        
        table_thresholds = self.thresholds.get("table_extraction", {})
        for key, value in table_thresholds.items():
            if isinstance(value, float):
                if "accuracy" in key:
                    report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value:.1f}%")
                else:
                    report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value:.3f}")
            else:
                report_lines.append(f"- **{key.replace('_', ' ').title()}:** {value}")
        
        report_lines.extend([
            "",
            "## Recommendations",
            "",
        ])
        
        # Generate recommendations based on results
        if test_results["overall_status"] == "FAIL":
            report_lines.append("🚨 **IMMEDIATE ACTION REQUIRED:** Multiple regression tests failing")
        elif test_results["overall_status"] == "WARNING":
            report_lines.append("⚠️ **MONITOR CLOSELY:** Some tests failing, investigate trends")
        else:
            report_lines.append("✅ **QUALITY STABLE:** All regression tests passing")
        
        if test_results["failures"]:
            report_lines.append("- Investigate root causes of failed tests")
            report_lines.append("- Consider updating parsing parameters or thresholds")
            
        # Check failure detection capability
        detection_failures = sum(1 for sim in failure_simulations.values() if sim["validation"] == "FAIL")
        if detection_failures > 0:
            report_lines.append(f"- **CRITICAL:** {detection_failures} failure detection tests failed - regression tests may not detect real issues")
        
        report_lines.extend([
            "",
            "---",
            f"*Report generated by Parser Regression Tester at {datetime.now()}*"
        ])
        
        report_content = "\n".join(report_lines)
        
        # Save report
        report_file = self.data_dir / "evaluation_metrics" / f"regression_test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Regression test report saved to: {report_file}")
        return report_content


# Unit test class for integration with standard testing frameworks
class TestParserRegression(unittest.TestCase):
    """
    Unit tests for parser regression detection.
    These tests will fail when parser quality drops below acceptable thresholds.
    """
    
    @classmethod
    def setUpClass(cls):
        """Set up test environment"""
        # This should point to your actual data directory
        data_dir = Path("data/intermediate")
        if not data_dir.exists():
            raise unittest.SkipTest("Data directory not found - ensure pipeline has been run")
        
        cls.tester = ParserRegressionTester(data_dir)
        cls.test_results = cls.tester.run_regression_tests()
    
    def test_text_extraction_success_rate(self):
        """Test that text extraction success rate meets threshold"""
        text_tests = self.test_results.get("text_extraction_tests", {})
        failures = [f for f in text_tests.get("failures", []) if f["test"] == "text_extraction_success_rate"]
        
        self.assertEqual(len(failures), 0, 
            f"Text extraction success rate below threshold: {failures[0]['message'] if failures else ''}")
    
    def test_table_extraction_quality(self):
        """Test that table extraction quality meets thresholds"""
        table_tests = self.test_results.get("table_extraction_tests", {})
        quality_failures = [f for f in table_tests.get("failures", []) if "quality" in f["test"]]
        
        self.assertEqual(len(quality_failures), 0,
            f"Table extraction quality issues detected: {quality_failures}")
    
    def test_method_consistency(self):
        """Test that parsing methods maintain consistency"""
        consistency_tests = self.test_results.get("consistency_tests", {})
        consistency_failures = consistency_tests.get("failures", [])
        
        self.assertEqual(len(consistency_failures), 0,
            f"Parser consistency issues detected: {consistency_failures}")
    
    def test_no_distribution_drift(self):
        """Test that data distributions haven't drifted significantly"""
        consistency_tests = self.test_results.get("consistency_tests", {})
        drift_failures = [f for f in consistency_tests.get("failures", []) if f["test"] == "distribution_drift"]
        
        self.assertEqual(len(drift_failures), 0,
            f"Significant distribution drift detected: {drift_failures[0]['message'] if drift_failures else ''}")
    
    def test_overall_regression_status(self):
        """Test overall regression status"""
        overall_status = self.test_results.get("overall_status", "UNKNOWN")
        
        self.assertNotEqual(overall_status, "FAIL",
            f"Overall regression tests failed. Failed tests: {self.test_results.get('tests_failed', 0)}")


if __name__ == "__main__":
    # Example usage
    import argparse
    
    parser = argparse.ArgumentParser(description="Parser Regression Testing")
    parser.add_argument("--data-dir", required=True, help="Path to parsed data directory")
    parser.add_argument("--action", choices=["test", "report", "simulate"], default="test", 
                       help="Action to perform")
    parser.add_argument("--failure-type", choices=["accuracy_drop", "extraction_failure", "consistency_loss"],
                       help="Type of failure to simulate")
    
    args = parser.parse_args()
    
    tester = ParserRegressionTester(Path(args.data_dir))
    
    if args.action == "test":
        results = tester.run_regression_tests()
        print(f"Tests: {results['tests_run']}, Passed: {results['tests_passed']}, Failed: {results['tests_failed']}")
        print(f"Status: {results['overall_status']}")
        
    elif args.action == "report":
        report = tester.generate_regression_test_report()
        print("Generated comprehensive regression test report")
        
    elif args.action == "simulate":
        failure_type = args.failure_type or "accuracy_drop"
        sim_results = tester.simulate_parser_failure(failure_type)
        print(f"Simulation: {sim_results['validation']} - {'Tests detected failure' if sim_results['tests_detected_failure'] else 'Tests missed failure'}")