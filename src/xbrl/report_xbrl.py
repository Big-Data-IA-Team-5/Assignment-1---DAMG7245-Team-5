"""
XBRL Reporting Module for Project LANTERN

This module provides comprehensive reporting functionality for XBRL validation
results, generating both JSON and Markdown reports with visualizations.
"""

import pandas as pd
import numpy as np
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class XBRLReporter:
    """
    XBRL Reporter for generating comprehensive validation reports.
    
    This class creates detailed reports from XBRL validation results including
    summary statistics, detailed discrepancy analysis, and formatted outputs.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize XBRL Reporter.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.report_title = self.config.get('report_title', 'XBRL Cross-Verification Report')
        self.include_charts = self.config.get('include_charts', False)
    
    def generate_markdown_report(self, validation_summary: Dict[str, Any],
                               discrepancies: List[Dict[str, Any]],
                               categorized_discrepancies: Dict[str, List[Dict[str, Any]]],
                               metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Generate a comprehensive Markdown report.
        
        Args:
            validation_summary: Summary statistics from validation
            discrepancies: List of all discrepancies
            categorized_discrepancies: Discrepancies organized by category
            metadata: Optional metadata about the validation run
            
        Returns:
            Markdown formatted report string
        """
        report_lines = []
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        # Header
        report_lines.extend([
            f"# {self.report_title}",
            f"",
            f"**Generated:** {timestamp}  ",
            f"**Project:** LANTERN - Lab 11 XBRL Cross-Verification  ",
            ""
        ])
        
        # Add metadata if provided
        if metadata:
            report_lines.extend([
                "## Validation Metadata",
                ""
            ])
            for key, value in metadata.items():
                report_lines.append(f"- **{key}:** {value}")
            report_lines.append("")
        
        # Executive Summary
        report_lines.extend(self._generate_executive_summary(validation_summary))
        
        # Detailed Statistics
        report_lines.extend(self._generate_detailed_statistics(validation_summary, discrepancies))
        
        # Discrepancy Analysis by Category
        report_lines.extend(self._generate_category_analysis(categorized_discrepancies))
        
        # Critical Issues
        if categorized_discrepancies.get('critical'):
            report_lines.extend(self._generate_critical_issues_section(categorized_discrepancies['critical']))
        
        # Recommendations
        report_lines.extend(self._generate_recommendations(categorized_discrepancies, validation_summary))
        
        # Detailed Discrepancy Tables
        report_lines.extend(self._generate_detailed_tables(categorized_discrepancies))
        
        # Appendix
        report_lines.extend(self._generate_appendix(validation_summary))
        
        return "\\n".join(report_lines)
    
    def _generate_executive_summary(self, validation_summary: Dict[str, Any]) -> List[str]:
        """Generate executive summary section."""
        lines = [
            "## Executive Summary",
            ""
        ]
        
        total_discrepancies = validation_summary.get('total_discrepancies', 0)
        severity_dist = validation_summary.get('severity_distribution', {})
        
        if total_discrepancies == 0:
            lines.extend([
                "✅ **Validation Status:** PASS  ",
                "🎯 **Key Finding:** All PDF table data matches XBRL filings within acceptable tolerances.",
                ""
            ])
        else:
            status = "FAIL" if severity_dist.get('critical', 0) > 0 else "WARNING"
            icon = "❌" if status == "FAIL" else "⚠️"
            
            lines.extend([
                f"{icon} **Validation Status:** {status}  ",
                f"📊 **Total Discrepancies:** {total_discrepancies}  ",
                f"🔴 **Critical Issues:** {severity_dist.get('critical', 0)}  ",
                f"🟡 **Moderate Issues:** {severity_dist.get('moderate', 0)}  ",
                f"🟢 **Minor Issues:** {severity_dist.get('minor', 0)}  ",
                ""
            ])
        
        return lines
    
    def _generate_detailed_statistics(self, validation_summary: Dict[str, Any],
                                    discrepancies: List[Dict[str, Any]]) -> List[str]:
        """Generate detailed statistics section."""
        lines = [
            "## Detailed Statistics",
            ""
        ]
        
        # Overall stats
        lines.extend([
            "### Overall Validation Results",
            "",
            "| Metric | Value |",
            "|--------|-------|"
        ])
        
        total = validation_summary.get('total_discrepancies', 0)
        value_mismatches = validation_summary.get('value_mismatches', 0)
        category_counts = validation_summary.get('category_counts', {})
        
        lines.extend([
            f"| Total Discrepancies | {total} |",
            f"| Value Mismatches | {value_mismatches} |",
            f"| Missing Data Issues | {category_counts.get('missing_data', 0)} |",
            f"| Unmapped Labels | {category_counts.get('unmapped', 0)} |",
            f"| Processing Errors | {category_counts.get('errors', 0)} |",
            ""
        ])
        
        # Percentage differences
        perc_stats = validation_summary.get('percentage_difference_stats')
        if perc_stats:
            lines.extend([
                "### Percentage Difference Analysis",
                "",
                "| Statistic | Value |",
                "|-----------|--------|",
                f"| Mean Difference | {perc_stats.get('mean', 0):.2f}% |",
                f"| Median Difference | {perc_stats.get('median', 0):.2f}% |",
                f"| Maximum Difference | {perc_stats.get('max', 0):.2f}% |",
                f"| Minimum Difference | {perc_stats.get('min', 0):.2f}% |",
                ""
            ])
        
        return lines
    
    def _generate_category_analysis(self, categorized_discrepancies: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate category analysis section."""
        lines = [
            "## Discrepancy Analysis by Category",
            ""
        ]
        
        category_descriptions = {
            'critical': "🔴 **Critical Issues** - Large value mismatches requiring immediate attention",
            'moderate': "🟡 **Moderate Issues** - Scale mismatches or moderate value differences",
            'minor': "🟢 **Minor Issues** - Small differences within reasonable bounds",
            'missing_data': "📊 **Missing Data** - Values missing from PDF or XBRL",
            'unmapped': "🔗 **Unmapped Labels** - PDF labels without XBRL concept mapping",
            'errors': "⚠️ **Processing Errors** - Technical issues during validation"
        }
        
        for category, description in category_descriptions.items():
            count = len(categorized_discrepancies.get(category, []))
            lines.extend([
                f"### {description}",
                f"**Count:** {count}",
                ""
            ])
            
            if count > 0 and count <= 10:  # Show details for small counts
                lines.append("**Items:**")
                for item in categorized_discrepancies[category]:
                    pdf_label = item.get('pdf_label', 'Unknown')
                    xbrl_concept = item.get('xbrl_concept', 'None')
                    lines.append(f"- {pdf_label} → {xbrl_concept}")
                lines.append("")
        
        return lines
    
    def _generate_critical_issues_section(self, critical_issues: List[Dict[str, Any]]) -> List[str]:
        """Generate critical issues section."""
        lines = [
            "## Critical Issues Requiring Immediate Attention",
            ""
        ]
        
        if not critical_issues:
            lines.extend([
                "No critical issues found.",
                ""
            ])
            return lines
        
        lines.extend([
            "| PDF Label | XBRL Concept | PDF Value | XBRL Value | Difference (%) | Type |",
            "|-----------|--------------|-----------|------------|----------------|------|"
        ])
        
        for issue in critical_issues:
            pdf_label = issue.get('pdf_label', 'N/A')
            xbrl_concept = issue.get('xbrl_concept', 'N/A')
            pdf_value = issue.get('pdf_value', 'N/A')
            xbrl_value = issue.get('xbrl_value', 'N/A')
            perc_diff = issue.get('percentage_difference', 'N/A')
            issue_type = issue.get('discrepancy_type', 'N/A')
            
            # Format values
            pdf_val_str = f"{pdf_value:,.0f}" if isinstance(pdf_value, (int, float)) else str(pdf_value)
            xbrl_val_str = f"{xbrl_value:,.0f}" if isinstance(xbrl_value, (int, float)) else str(xbrl_value)
            perc_str = f"{perc_diff:.2f}%" if isinstance(perc_diff, (int, float)) else str(perc_diff)
            
            lines.append(f"| {pdf_label} | {xbrl_concept} | {pdf_val_str} | {xbrl_val_str} | {perc_str} | {issue_type} |")
        
        lines.append("")
        return lines
    
    def _generate_recommendations(self, categorized_discrepancies: Dict[str, List[Dict[str, Any]]],
                                validation_summary: Dict[str, Any]) -> List[str]:
        """Generate recommendations section."""
        lines = [
            "## Recommendations",
            ""
        ]
        
        critical_count = len(categorized_discrepancies.get('critical', []))
        moderate_count = len(categorized_discrepancies.get('moderate', []))
        unmapped_count = len(categorized_discrepancies.get('unmapped', []))
        missing_count = len(categorized_discrepancies.get('missing_data', []))
        
        if critical_count > 0:
            lines.extend([
                "### Immediate Actions Required",
                "",
                f"1. **Review {critical_count} critical discrepancies** - These represent significant value mismatches",
                "2. **Verify PDF extraction accuracy** - Check if table parsing captured correct values",
                "3. **Validate XBRL concept mapping** - Ensure correct financial concepts are being compared",
                "4. **Check data periods** - Verify that PDF and XBRL data represent the same time periods",
                ""
            ])
        
        if moderate_count > 0:
            lines.extend([
                "### Medium Priority Actions",
                "",
                f"1. **Investigate {moderate_count} moderate issues** - Often scale factor mismatches",
                "2. **Review unit specifications** - Check if values are in thousands vs. actual amounts",
                "3. **Verify calculation methods** - Ensure consistent aggregation approaches",
                ""
            ])
        
        if unmapped_count > 0:
            lines.extend([
                "### Mapping Improvements",
                "",
                f"1. **Add mappings for {unmapped_count} unmapped labels** - Improve concept coverage",
                "2. **Enhance fuzzy matching rules** - Reduce false negatives in label matching",
                "3. **Create custom mapping rules** - For company-specific terminology",
                ""
            ])
        
        if missing_count > 0:
            lines.extend([
                "### Data Quality Improvements",
                "",
                f"1. **Address {missing_count} missing data issues** - Improve data completeness",
                "2. **Enhance PDF table extraction** - Capture more comprehensive financial data",
                "3. **Verify XBRL concept availability** - Check if concepts exist in filing",
                ""
            ])
        
        lines.extend([
            "### General Recommendations",
            "",
            "1. **Implement tolerance tuning** - Adjust validation thresholds based on business requirements",
            "2. **Add temporal matching** - Ensure PDF and XBRL data are from same reporting periods",
            "3. **Enhance preprocessing** - Improve label cleaning and standardization",
            "4. **Create validation workflows** - Establish regular cross-verification processes",
            ""
        ])
        
        return lines
    
    def _generate_detailed_tables(self, categorized_discrepancies: Dict[str, List[Dict[str, Any]]]) -> List[str]:
        """Generate detailed discrepancy tables."""
        lines = [
            "## Detailed Discrepancy Tables",
            ""
        ]
        
        for category, discrepancies in categorized_discrepancies.items():
            if not discrepancies:
                continue
            
            lines.extend([
                f"### {category.replace('_', ' ').title()} ({len(discrepancies)} items)",
                ""
            ])
            
            # Create table
            if discrepancies:
                lines.extend([
                    "| PDF Label | XBRL Concept | PDF Value | XBRL Value | Difference | Type |",
                    "|-----------|--------------|-----------|------------|------------|------|"
                ])
                
                for disc in discrepancies:
                    pdf_label = disc.get('pdf_label', 'N/A')
                    xbrl_concept = disc.get('xbrl_concept', 'N/A')
                    pdf_value = disc.get('pdf_value', 'N/A')
                    xbrl_value = disc.get('xbrl_value', 'N/A')
                    difference = disc.get('difference', 'N/A')
                    disc_type = disc.get('discrepancy_type', 'N/A')
                    
                    # Format values for display
                    pdf_str = f"{pdf_value:,.0f}" if isinstance(pdf_value, (int, float)) else str(pdf_value)
                    xbrl_str = f"{xbrl_value:,.0f}" if isinstance(xbrl_value, (int, float)) else str(xbrl_value)
                    diff_str = f"{difference:,.2f}" if isinstance(difference, (int, float)) else str(difference)
                    
                    lines.append(f"| {pdf_label} | {xbrl_concept} | {pdf_str} | {xbrl_str} | {diff_str} | {disc_type} |")
                
                lines.append("")
        
        return lines
    
    def _generate_appendix(self, validation_summary: Dict[str, Any]) -> List[str]:
        """Generate appendix section."""
        lines = [
            "## Appendix",
            "",
            "### Validation Configuration",
            "",
            f"- **Validation Timestamp:** {validation_summary.get('validation_timestamp', 'N/A')}",
            "- **Tolerance Settings:**",
            "  - Numeric Tolerance: 0.01",
            "  - Percentage Tolerance: 0.1%",
            "  - Relative Tolerance: 1e-6",
            "",
            "### About This Report",
            "",
            "This report was generated by Project LANTERN's XBRL Cross-Verification system (Lab 11).",
            "The system compares PDF table extractions against authoritative XBRL filings to ensure",
            "data accuracy and identify potential issues in financial data processing.",
            "",
            "### Legend",
            "",
            "- 🔴 **Critical:** Large discrepancies requiring immediate attention",
            "- 🟡 **Moderate:** Scale mismatches or moderate differences",
            "- 🟢 **Minor:** Small differences within acceptable bounds",
            "- 📊 **Missing Data:** Values not found in one source",
            "- 🔗 **Unmapped:** PDF labels without XBRL mapping",
            "- ⚠️ **Errors:** Technical processing issues",
            ""
        ]
        
        return lines
    
    def save_markdown_report(self, report_content: str, output_path: str) -> str:
        """
        Save Markdown report to file.
        
        Args:
            report_content: Markdown content string
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        logger.info(f"Markdown report saved to {output_file}")
        return str(output_file)
    
    def generate_json_report(self, validation_summary: Dict[str, Any],
                           discrepancies: List[Dict[str, Any]],
                           categorized_discrepancies: Dict[str, List[Dict[str, Any]]],
                           metadata: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Generate structured JSON report.
        
        Args:
            validation_summary: Summary statistics
            discrepancies: All discrepancies
            categorized_discrepancies: Categorized discrepancies
            metadata: Optional metadata
            
        Returns:
            JSON report dictionary
        """
        report = {
            'report_metadata': {
                'title': self.report_title,
                'generated_timestamp': datetime.now().isoformat(),
                'report_version': '1.0.0',
                'generator': 'LANTERN XBRL Cross-Verification System'
            },
            'validation_metadata': metadata or {},
            'validation_summary': validation_summary,
            'discrepancy_analysis': {
                'total_discrepancies': len(discrepancies),
                'categorized_counts': {k: len(v) for k, v in categorized_discrepancies.items()},
                'categories': categorized_discrepancies
            },
            'detailed_discrepancies': discrepancies,
            'recommendations': self._generate_json_recommendations(categorized_discrepancies)
        }
        
        return report
    
    def _generate_json_recommendations(self, categorized_discrepancies: Dict[str, List[Dict[str, Any]]]) -> Dict[str, List[str]]:
        """Generate recommendations in JSON format."""
        recommendations = {}
        
        critical_count = len(categorized_discrepancies.get('critical', []))
        moderate_count = len(categorized_discrepancies.get('moderate', []))
        unmapped_count = len(categorized_discrepancies.get('unmapped', []))
        missing_count = len(categorized_discrepancies.get('missing_data', []))
        
        if critical_count > 0:
            recommendations['critical_actions'] = [
                f"Review {critical_count} critical discrepancies immediately",
                "Verify PDF extraction accuracy for significant mismatches",
                "Validate XBRL concept mapping correctness",
                "Check temporal alignment of PDF and XBRL data"
            ]
        
        if moderate_count > 0:
            recommendations['moderate_actions'] = [
                f"Investigate {moderate_count} moderate issues",
                "Review unit specifications and scale factors",
                "Verify calculation and aggregation methods"
            ]
        
        if unmapped_count > 0:
            recommendations['mapping_improvements'] = [
                f"Add mappings for {unmapped_count} unmapped labels",
                "Enhance fuzzy matching algorithms",
                "Create company-specific mapping rules"
            ]
        
        if missing_count > 0:
            recommendations['data_quality'] = [
                f"Address {missing_count} missing data issues",
                "Improve PDF table extraction coverage",
                "Verify XBRL concept availability in filings"
            ]
        
        recommendations['general'] = [
            "Implement dynamic tolerance tuning",
            "Add comprehensive temporal matching",
            "Enhance label preprocessing and standardization",
            "Establish regular validation workflows"
        ]
        
        return recommendations
    
    def save_json_report(self, report_data: Dict[str, Any], output_path: str) -> str:
        """
        Save JSON report to file.
        
        Args:
            report_data: JSON report dictionary
            output_path: Output file path
            
        Returns:
            Path to saved file
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, default=str, ensure_ascii=False)
        
        logger.info(f"JSON report saved to {output_file}")
        return str(output_file)


def main():
    """
    Example usage of XBRLReporter.
    """
    # Example data
    validation_summary = {
        'validation_timestamp': datetime.now().isoformat(),
        'total_discrepancies': 3,
        'value_mismatches': 2,
        'category_counts': {'critical': 1, 'moderate': 1, 'minor': 1},
        'severity_distribution': {'critical': 1, 'moderate': 1, 'minor': 1, 'data_issues': 0, 'errors': 0}
    }
    
    discrepancies = [
        {
            'pdf_label': 'Net Income',
            'xbrl_concept': 'NetIncomeLoss',
            'pdf_value': 25000,
            'xbrl_value': 25100,
            'difference': 100,
            'percentage_difference': 0.4,
            'discrepancy_type': 'value_mismatch'
        }
    ]
    
    categorized = {'critical': [], 'moderate': discrepancies, 'minor': []}
    
    reporter = XBRLReporter()
    report = reporter.generate_markdown_report(validation_summary, discrepancies, categorized)
    
    print("Generated Markdown Report:")
    print(report[:500] + "..." if len(report) > 500 else report)


if __name__ == "__main__":
    main()