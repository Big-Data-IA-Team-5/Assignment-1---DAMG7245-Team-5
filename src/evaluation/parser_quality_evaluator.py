#!/usr/bin/env python3
"""
Part 9: Parser Quality Evaluation & Regression Detection

This module evaluates parsing quality by comparing different extraction methods
and detecting regressions using existing parsed data rather than manual ground truth.
Now includes XBRL ground truth validation for financial data accuracy.

Core functionality:
- Compare extraction methods (camelot_stream vs pdfplumber vs camelot_lattice)
- Calculate consistency metrics between different parsers on same content
- Detect distribution drift in extracted data characteristics
- Monitor extraction quality over time using historical data
- Generate regression tests based on current performance baselines
- Validate financial data against XBRL ground truth
"""
    
    def _load_xbrl_ground_truth(self) -> Dict[str, Any]:
        """Load and parse XBRL files for ground truth financial data comparison"""
        xbrl_data = {}
        
        if not self.xbrl_dir.exists():
            self.logger.warning(f"XBRL directory not found: {self.xbrl_dir}")
            return {}
        
        # Find XBRL files
        xbrl_files = list(self.xbrl_dir.glob("*.xbrl")) + list(self.xbrl_dir.glob("*.xml"))
        
        if not xbrl_files:
            self.logger.warning(f"No XBRL files found in: {self.xbrl_dir}")
            return {}
        
        for xbrl_file in xbrl_files:
            try:
                self.logger.info(f"Loading XBRL ground truth from: {xbrl_file}")
                
                # Parse XBRL/XML file
                tree = ET.parse(xbrl_file)
                root = tree.getroot()
                
                # Extract financial data with namespaces handling
                financial_facts = self._extract_xbrl_financial_facts(root)
                
                # Store with filename as key
                file_key = xbrl_file.stem.lower()
                xbrl_data[file_key] = {
                    "source_file": str(xbrl_file),
                    "financial_facts": financial_facts,
                    "parsed_timestamp": datetime.now().isoformat()
                }
                
                self.logger.info(f"Extracted {len(financial_facts)} financial facts from {file_key}")
                
            except ET.ParseError as e:
                self.logger.error(f"Failed to parse XBRL file {xbrl_file}: {e}")
            except Exception as e:
                self.logger.error(f"Error loading XBRL file {xbrl_file}: {e}")
        
        return xbrl_data
    
    def _extract_xbrl_financial_facts(self, root: ET.Element) -> Dict[str, Any]:
        """Extract financial facts from XBRL root element"""
        financial_facts = {}
        
        # Common financial fact patterns to look for
        financial_patterns = {
            'revenue': ['Revenue', 'SalesRevenueNet', 'Revenues', 'TotalRevenues'],
            'net_income': ['NetIncomeLoss', 'NetIncome', 'ProfitLoss', 'EarningsLossFromContinuingOperations'],
            'total_assets': ['Assets', 'TotalAssets', 'AssetsTotal'],
            'total_equity': ['StockholdersEquity', 'Equity', 'TotalEquity', 'ShareholdersEquity'],
            'cash': ['Cash', 'CashAndCashEquivalents', 'CashAndShortTermInvestments'],
            'debt': ['Debt', 'TotalDebt', 'LongTermDebt'],
            'shares_outstanding': ['SharesOutstanding', 'CommonStockSharesOutstanding']
        }
        
        # Get all namespaces
        namespaces = {}
        for prefix, uri in root.attrib.items():
            if prefix.startswith('xmlns'):
                ns_prefix = prefix.split(':')[1] if ':' in prefix else 'default'
                namespaces[ns_prefix] = uri
        
        # If no explicit namespaces found, try to infer from tag names
        if not namespaces:
            for elem in root.iter():
                if ':' in elem.tag:
                    prefix, _ = elem.tag.split(':', 1)
                    if prefix not in namespaces:
                        namespaces[prefix] = elem.tag.split('}')[0][1:] if elem.tag.startswith('{') else ''
        
        # Search for financial data
        for category, patterns in financial_patterns.items():
            category_data = []
            
            for pattern in patterns:
                # Search with and without namespaces
                elements = []
                
                # Direct tag name search
                elements.extend(root.findall(f".//{pattern}"))
                
                # Namespace-aware search
                for ns_prefix, ns_uri in namespaces.items():
                    if ns_uri:
                        elements.extend(root.findall(f".//{{{ns_uri}}}{pattern}"))
                    elements.extend(root.findall(f".//{ns_prefix}:{pattern}", namespaces))
                
                # Case-insensitive search
                for elem in root.iter():
                    if elem.tag.lower().endswith(pattern.lower()) or pattern.lower() in elem.tag.lower():
                        elements.append(elem)
                
                # Extract values from found elements
                for elem in elements:
                    try:
                        # Get the value
                        value = elem.text
                        if value and value.strip():
                            # Clean and convert value
                            cleaned_value = self._clean_financial_value(value.strip())
                            if cleaned_value is not None:
                                fact = {
                                    "concept": pattern,
                                    "value": cleaned_value,
                                    "tag_name": elem.tag,
                                    "context": elem.attrib.get("contextRef", ""),
                                    "unit": elem.attrib.get("unitRef", ""),
                                    "decimals": elem.attrib.get("decimals", ""),
                                    "scale": elem.attrib.get("scale", "")
                                }
                                category_data.append(fact)
                    except (ValueError, AttributeError):
                        continue
            
            if category_data:
                # Keep the most recent or contextually relevant data
                financial_facts[category] = self._select_best_financial_fact(category_data)
        
        # Also extract any other numerical data that might be financial
        self._extract_additional_numerical_facts(root, financial_facts)
        
        return financial_facts
    
    def _clean_financial_value(self, value_str: str) -> Optional[float]:
        """Clean and convert financial value string to float"""
        try:
            # Remove common formatting
            cleaned = re.sub(r'[,$\s()]', '', value_str)
            
            # Handle negative values in parentheses
            if value_str.strip().startswith('(') and value_str.strip().endswith(')'):
                cleaned = '-' + cleaned
            
            # Convert to float
            return float(cleaned)
        except (ValueError, TypeError):
            return None
    
    def _select_best_financial_fact(self, facts: List[Dict]) -> Dict[str, Any]:
        """Select the best financial fact from multiple candidates"""
        if not facts:
            return {}
        
        if len(facts) == 1:
            return facts[0]
        
        # Prefer facts with recent periods or specific contexts
        scored_facts = []
        for fact in facts:
            score = 0
            
            # Prefer facts with contextRef (usually more specific)
            if fact.get("context"):
                score += 10
            
            # Prefer facts with units
            if fact.get("unit"):
                score += 5
            
            # Prefer larger absolute values (often more complete data)
            if isinstance(fact.get("value"), (int, float)):
                score += min(abs(fact["value"]) / 1000000, 50)  # Scale factor
            
            scored_facts.append((score, fact))
        
        # Return highest scored fact
        return max(scored_facts, key=lambda x: x[0])[1]
    
    def _extract_additional_numerical_facts(self, root: ET.Element, financial_facts: Dict):
        """Extract additional numerical facts that might be relevant"""
        numerical_facts = []
        
        for elem in root.iter():
            if elem.text and elem.text.strip():
                try:
                    value = self._clean_financial_value(elem.text.strip())
                    if value is not None and abs(value) > 1000:  # Filter out small/irrelevant numbers
                        tag_name = elem.tag.split('}')[-1] if '}' in elem.tag else elem.tag
                        
                        # Skip if already categorized
                        already_found = False
                        for category_facts in financial_facts.values():
                            if isinstance(category_facts, dict) and category_facts.get("value") == value:
                                already_found = True
                                break
                        
                        if not already_found:
                            numerical_facts.append({
                                "tag_name": tag_name,
                                "value": value,
                                "context": elem.attrib.get("contextRef", ""),
                                "unit": elem.attrib.get("unitRef", "")
                            })
                except:
                    continue
        
        if numerical_facts:
            financial_facts["other_numerical"] = numerical_facts[:20]  # Limit to avoid overloadg quality by comparing different extraction methods
and detecting regressions using existing parsed data rather than manual ground truth.
Now includes XBRL ground truth validation for financial data accuracy.

Core functionality:
- Compare extraction methods (camelot_stream vs pdfplumber vs camelot_lattice)
- Calculate consistency metrics between different parsers on same content
- Detect distribution drift in extracted data characteristics
- Monitor extraction quality over time using historical data
- Generate regression tests based on current performance baselines
- Validate financial data against XBRL ground truth
"""

import json
import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import hashlib
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from dataclasses import dataclass, asdict
import Levenshtein  # For edit distance calculations


@dataclass
class ParsingMetrics:
    """Metrics for a single parsing run"""
    timestamp: str
    method: str
    total_pages: int
    successful_extractions: int
    avg_content_quality: float
    avg_accuracy: Optional[float]  # Camelot only
    total_tables: int
    total_text_chars: int
    financial_score_avg: float
    ocr_pages: int
    failed_extractions: int
    
    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass 
class ConsistencyMetrics:
    """Metrics comparing consistency between parsing methods"""
    page_overlap_ratio: float  # Pages where both methods found content
    table_count_similarity: float  # How similar are table counts per page
    content_similarity_avg: float  # Average content similarity score
    structure_consistency: float  # How consistent are table structures
    method_agreement_score: float  # Overall agreement between methods


class ParserQualityEvaluator:
    """
    Evaluates parser quality using comparative analysis between different methods
    and validates against XBRL ground truth where available
    """
    
    def __init__(self, data_dir: Path, output_dir: Path = None, xbrl_dir: Path = None):
        """
        Initialize evaluator
        
        Args:
            data_dir: Directory containing parsed data from different methods
            output_dir: Directory for evaluation outputs
            xbrl_dir: Directory containing XBRL files for ground truth comparison
        """
        self.data_dir = Path(data_dir)
        self.output_dir = Path(output_dir or data_dir.parent / "evaluation_outputs")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # XBRL ground truth directory
        self.xbrl_dir = Path(xbrl_dir) if xbrl_dir else self.data_dir.parent / "raw" / "xbrl_files"
        
        self.logger = logging.getLogger(__name__)
        
        # Set up directory structure  
        self.tables_dir = self.data_dir / "tables"
        self.text_dir = self.data_dir / "text_extraction"
        
        # Load parsed data for comparison
        self.table_analysis = self._load_table_analysis()
        self.text_analysis = self._load_text_analysis()
        
        # Load XBRL ground truth data
        self.xbrl_ground_truth = self._load_xbrl_ground_truth()
        
    def _load_table_analysis(self) -> Dict:
        """Load comprehensive table analysis data"""
        analysis_file = self.tables_dir / "_comprehensive_analysis.json"
        if analysis_file.exists():
            with open(analysis_file, 'r') as f:
                return json.load(f)
        return {}
    
    def _load_text_analysis(self) -> Dict:
        """Load text extraction analysis data"""
        ocr_file = self.text_dir / "_ocr_pages.json"
        if ocr_file.exists():
            with open(ocr_file, 'r') as f:
                return json.load(f)
        return {}
    
    def calculate_text_consistency_metrics(self) -> Dict[str, float]:
        """
        Calculate text extraction consistency by analyzing character/word distributions,
        extraction success rates, and content patterns across pages.
        """
        metrics = {}
        
        # Analyze per-page text files
        pages_dir = self.text_dir / "pages"
        if not pages_dir.exists():
            return {"error": "No per-page text data found"}
        
        page_files = list(pages_dir.glob("page_*.txt"))
        page_stats = []
        
        for page_file in sorted(page_files):
            with open(page_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Calculate page-level statistics
            char_count = len(content)
            word_count = len(content.split())
            line_count = len(content.split('\n'))
            
            # Analyze content characteristics
            numeric_ratio = len(re.findall(r'\d', content)) / max(char_count, 1)
            financial_keywords = len(re.findall(
                r'\b(revenue|income|assets|liabilities|earnings|profit|cash|million|billion)\b', 
                content.lower()
            ))
            special_chars = len(re.findall(r'[^\w\s]', content))
            
            page_stats.append({
                'page': int(re.search(r'page_(\d+)', page_file.name).group(1)),
                'char_count': char_count,
                'word_count': word_count,
                'line_count': line_count,
                'numeric_ratio': numeric_ratio,
                'financial_keywords': financial_keywords,
                'special_char_ratio': special_chars / max(char_count, 1),
                'avg_words_per_line': word_count / max(line_count, 1)
            })
        
        if not page_stats:
            return {"error": "No page statistics calculated"}
        
        # Calculate consistency metrics
        df = pd.DataFrame(page_stats)
        
        metrics.update({
            'total_pages_with_text': len(page_stats),
            'avg_chars_per_page': df['char_count'].mean(),
            'std_chars_per_page': df['char_count'].std(),
            'chars_cv': df['char_count'].std() / max(df['char_count'].mean(), 1),  # Coefficient of variation
            'avg_words_per_page': df['word_count'].mean(),
            'avg_numeric_ratio': df['numeric_ratio'].mean(),
            'avg_financial_keywords': df['financial_keywords'].mean(),
            'content_distribution_entropy': self._calculate_entropy(df['char_count'].values),
            'successful_extraction_rate': (df['char_count'] > 0).mean(),
        })
        
        # OCR analysis from existing data
        if self.text_analysis:
            metrics.update({
                'ocr_pages_count': len(self.text_analysis.get('ocr_pages_list', [])),
                'ocr_rate': len(self.text_analysis.get('ocr_pages_list', [])) / max(self.text_analysis.get('total_pages', 1), 1),
                'pdfplumber_success_rate': self.text_analysis.get('summary', {}).get('successful_pdfplumber', 0) / max(self.text_analysis.get('total_pages', 1), 1)
            })
        
        return metrics
    
    def calculate_table_consistency_metrics(self) -> Dict[str, Any]:
        """
        Calculate table extraction consistency by comparing different methods
        and analyzing structural patterns in extracted tables.
        """
        metrics = {}
        
        # Load table index for detailed analysis
        index_file = self.tables_dir / "_comprehensive_index.csv"
        if not index_file.exists():
            return {"error": "No table index found"}
        
        df_index = pd.read_csv(index_file)
        
        # Method comparison analysis
        method_stats = {}
        for method in df_index['method'].unique():
            method_data = df_index[df_index['method'] == method]
            method_stats[method] = {
                'table_count': len(method_data),
                'page_coverage': len(method_data['page'].unique()),
                'avg_rows': method_data['rows'].mean(),
                'avg_cols': method_data['cols'].mean(),
                'avg_content_quality': method_data.get('content_quality', pd.Series([0])).mean(),
                'avg_accuracy': method_data.get('accuracy', pd.Series([0])).mean(),
                'pages': sorted(method_data['page'].unique().tolist())
            }
        
        metrics['method_comparison'] = method_stats
        
        # Calculate cross-method consistency for overlapping pages
        consistency_metrics = self._calculate_cross_method_consistency(df_index)
        metrics.update(consistency_metrics)
        
        # Table structure analysis
        structure_metrics = self._analyze_table_structures(df_index)
        metrics.update(structure_metrics)
        
        # Use existing comprehensive analysis
        if self.table_analysis:
            metrics['existing_analysis'] = self.table_analysis
        
        return metrics
    
    def _calculate_cross_method_consistency(self, df_index: pd.DataFrame) -> Dict[str, float]:
        """Calculate consistency metrics between different parsing methods"""
        methods = df_index['method'].unique()
        if len(methods) < 2:
            return {'consistency_note': 'Only one method available for comparison'}
        
        # Find pages where multiple methods extracted tables
        page_method_counts = df_index.groupby('page')['method'].nunique()
        overlapping_pages = page_method_counts[page_method_counts > 1].index.tolist()
        
        if not overlapping_pages:
            return {'page_overlap_ratio': 0.0, 'note': 'No overlapping extractions found'}
        
        # Calculate agreement metrics for overlapping pages
        agreements = []
        structure_similarities = []
        
        for page in overlapping_pages:
            page_tables = df_index[df_index['page'] == page]
            if len(page_tables) >= 2:
                # Compare table counts and structures
                table_counts = page_tables.groupby('method').size()
                count_similarity = 1.0 - (table_counts.std() / max(table_counts.mean(), 1))
                agreements.append(count_similarity)
                
                # Compare table dimensions
                for method_combo in [(methods[0], methods[1])] if len(methods) >= 2 else []:
                    method1_tables = page_tables[page_tables['method'] == method_combo[0]]
                    method2_tables = page_tables[page_tables['method'] == method_combo[1]]
                    
                    if len(method1_tables) > 0 and len(method2_tables) > 0:
                        # Compare first table from each method
                        t1 = method1_tables.iloc[0]
                        t2 = method2_tables.iloc[0]
                        
                        row_similarity = 1.0 - abs(t1['rows'] - t2['rows']) / max(t1['rows'] + t2['rows'], 1)
                        col_similarity = 1.0 - abs(t1['cols'] - t2['cols']) / max(t1['cols'] + t2['cols'], 1)
                        structure_similarities.append((row_similarity + col_similarity) / 2)
        
        return {
            'page_overlap_ratio': len(overlapping_pages) / len(df_index['page'].unique()),
            'table_count_consistency': np.mean(agreements) if agreements else 0.0,
            'structure_consistency': np.mean(structure_similarities) if structure_similarities else 0.0,
            'overlapping_pages_count': len(overlapping_pages),
            'total_pages_with_tables': len(df_index['page'].unique())
        }
    
    def _analyze_table_structures(self, df_index: pd.DataFrame) -> Dict[str, Any]:
        """Analyze patterns in table structures"""
        return {
            'table_size_distribution': {
                'avg_rows': df_index['rows'].mean(),
                'std_rows': df_index['rows'].std(),
                'avg_cols': df_index['cols'].mean(),
                'std_cols': df_index['cols'].std(),
                'median_table_cells': df_index.apply(lambda x: x['rows'] * x['cols'], axis=1).median(),
                'size_entropy': self._calculate_entropy(df_index.apply(lambda x: x['rows'] * x['cols'], axis=1).values)
            },
            'quality_distribution': {
                'avg_quality': df_index.get('content_quality', pd.Series([0])).mean(),
                'quality_std': df_index.get('content_quality', pd.Series([0])).std(),
                'high_quality_ratio': (df_index.get('content_quality', pd.Series([0])) > 0.7).mean()
            }
        }
    
    def _calculate_entropy(self, values: np.ndarray) -> float:
        """Calculate entropy of a distribution"""
        if len(values) == 0:
            return 0.0
        
        # Bin the values and calculate probability distribution
        hist, _ = np.histogram(values, bins=min(10, len(values)))
        probs = hist / hist.sum()
        probs = probs[probs > 0]  # Remove zero probabilities
        
        if len(probs) <= 1:
            return 0.0
        
        return -np.sum(probs * np.log2(probs))
    
    def detect_distribution_drift(self, baseline_metrics: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Detect distribution drift by comparing current metrics to baseline.
        If no baseline provided, use current metrics as new baseline.
        """
        current_text_metrics = self.calculate_text_consistency_metrics()
        current_table_metrics = self.calculate_table_consistency_metrics()
        
        current_metrics = {
            'timestamp': datetime.now().isoformat(),
            'text_metrics': current_text_metrics,
            'table_metrics': current_table_metrics
        }
        
        # Save current metrics as potential baseline
        metrics_file = self.metrics_dir / f"metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(metrics_file, 'w') as f:
            json.dump(current_metrics, f, indent=2)
        
        if baseline_metrics is None:
            # Look for most recent baseline
            baseline_file = self._find_latest_baseline()
            if baseline_file:
                with open(baseline_file, 'r') as f:
                    baseline_metrics = json.load(f)
            else:
                return {
                    'status': 'baseline_created',
                    'message': 'No baseline found, current metrics saved as new baseline',
                    'baseline_file': str(metrics_file)
                }
        
        # Calculate drift metrics
        drift_analysis = {}
        
        # Text drift analysis
        if 'text_metrics' in baseline_metrics:
            text_drift = self._calculate_drift(
                current_text_metrics, 
                baseline_metrics['text_metrics']
            )
            drift_analysis['text_drift'] = text_drift
        
        # Table drift analysis  
        if 'table_metrics' in baseline_metrics:
            table_drift = self._calculate_drift(
                current_table_metrics.get('table_size_distribution', {}),
                baseline_metrics['table_metrics'].get('table_size_distribution', {})
            )
            drift_analysis['table_drift'] = table_drift
        
        # Overall drift assessment
        drift_analysis['overall_assessment'] = self._assess_overall_drift(drift_analysis)
        drift_analysis['current_metrics_file'] = str(metrics_file)
        
        return drift_analysis
    
    def _find_latest_baseline(self) -> Optional[Path]:
        """Find the most recent metrics file to use as baseline"""
        metrics_files = list(self.metrics_dir.glob("metrics_*.json"))
        if metrics_files:
            return max(metrics_files, key=lambda x: x.stat().st_mtime)
        return None
    
    def _calculate_drift(self, current: Dict, baseline: Dict) -> Dict[str, float]:
        """Calculate drift between current and baseline metrics"""
        drift_scores = {}
        
        for key in baseline.keys():
            if key in current and isinstance(current[key], (int, float)) and isinstance(baseline[key], (int, float)):
                if baseline[key] != 0:
                    # Calculate relative change
                    relative_change = abs(current[key] - baseline[key]) / abs(baseline[key])
                    drift_scores[f'{key}_drift'] = relative_change
                else:
                    # Handle zero baseline
                    drift_scores[f'{key}_drift'] = 1.0 if current[key] != 0 else 0.0
        
        return drift_scores
    
    def _assess_overall_drift(self, drift_analysis: Dict) -> Dict[str, Any]:
        """Provide overall assessment of drift severity"""
        all_drifts = []
        
        for category, drifts in drift_analysis.items():
            if isinstance(drifts, dict):
                all_drifts.extend([v for v in drifts.values() if isinstance(v, (int, float))])
        
        if not all_drifts:
            return {'status': 'no_drift_data', 'severity': 'unknown'}
        
        max_drift = max(all_drifts)
        avg_drift = np.mean(all_drifts)
        
        # Define severity thresholds
        if max_drift > 0.5 or avg_drift > 0.3:
            severity = 'high'
        elif max_drift > 0.2 or avg_drift > 0.1:
            severity = 'medium'
        else:
            severity = 'low'
        
        return {
            'severity': severity,
            'max_drift': max_drift,
            'avg_drift': avg_drift,
            'total_metrics_compared': len(all_drifts),
            'recommendation': self._get_drift_recommendation(severity, max_drift)
        }
    
    def _get_drift_recommendation(self, severity: str, max_drift: float) -> str:
        """Get recommendation based on drift severity"""
        recommendations = {
            'high': f'ALERT: Significant drift detected ({max_drift:.2%}). Investigate parsing changes immediately.',
            'medium': f'WARNING: Moderate drift detected ({max_drift:.2%}). Monitor closely and consider investigation.',
            'low': f'INFO: Minor drift detected ({max_drift:.2%}). Normal variation, continue monitoring.'
        }
        return recommendations.get(severity, 'Monitor parsing consistency.')
    
    def generate_evaluation_report(self) -> str:
        """Generate comprehensive evaluation report"""
        report_lines = [
            "# Parser Quality Evaluation Report",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "This report analyzes parsing quality using comparative analysis of different extraction methods",
            "rather than manual ground truth. Focus is on consistency, patterns, and regression detection.",
            "",
        ]
        
        # Text extraction analysis
        text_metrics = self.calculate_text_consistency_metrics()
        report_lines.extend([
            "## Text Extraction Analysis",
            "",
            f"- **Total pages processed:** {text_metrics.get('total_pages_with_text', 0)}",
            f"- **Average characters per page:** {text_metrics.get('avg_chars_per_page', 0):.0f}",
            f"- **Character count variability (CV):** {text_metrics.get('chars_cv', 0):.3f}",
            f"- **OCR usage rate:** {text_metrics.get('ocr_rate', 0):.2%}",
            f"- **Successful extraction rate:** {text_metrics.get('successful_extraction_rate', 0):.2%}",
            f"- **Average numeric content ratio:** {text_metrics.get('avg_numeric_ratio', 0):.3f}",
            f"- **Content distribution entropy:** {text_metrics.get('content_distribution_entropy', 0):.3f}",
            "",
        ])
        
        # Table extraction analysis
        table_metrics = self.calculate_table_consistency_metrics()
        report_lines.extend([
            "## Table Extraction Analysis",
            "",
        ])
        
        if 'method_comparison' in table_metrics:
            for method, stats in table_metrics['method_comparison'].items():
                report_lines.extend([
                    f"### {method.title()} Method",
                    f"- **Tables extracted:** {stats['table_count']}",
                    f"- **Pages covered:** {stats['page_coverage']}",
                    f"- **Average table size:** {stats['avg_rows']:.1f} × {stats['avg_cols']:.1f}",
                    f"- **Average quality score:** {stats['avg_content_quality']:.3f}",
                ])
                if stats['avg_accuracy'] > 0:
                    report_lines.append(f"- **Average accuracy:** {stats['avg_accuracy']:.1f}%")
                report_lines.append("")
        
        # Consistency analysis
        if 'page_overlap_ratio' in table_metrics:
            report_lines.extend([
                "## Cross-Method Consistency",
                "",
                f"- **Page overlap ratio:** {table_metrics['page_overlap_ratio']:.2%}",
                f"- **Table count consistency:** {table_metrics.get('table_count_consistency', 0):.3f}",
                f"- **Structure consistency:** {table_metrics.get('structure_consistency', 0):.3f}",
                "",
            ])
        
        # Distribution analysis
        if 'table_size_distribution' in table_metrics:
            size_dist = table_metrics['table_size_distribution']
            report_lines.extend([
                "## Table Structure Patterns",
                "",
                f"- **Average table size:** {size_dist['avg_rows']:.1f} × {size_dist['avg_cols']:.1f}",
                f"- **Size variability:** ±{size_dist['std_rows']:.1f} rows, ±{size_dist['std_cols']:.1f} cols",
                f"- **Median cell count:** {size_dist['median_table_cells']:.0f}",
                f"- **Size distribution entropy:** {size_dist['size_entropy']:.3f}",
                "",
            ])
        
        # Drift analysis
        drift_analysis = self.detect_distribution_drift()
        if 'overall_assessment' in drift_analysis:
            assessment = drift_analysis['overall_assessment']
            report_lines.extend([
                "## Distribution Drift Analysis",
                "",
                f"- **Drift severity:** {assessment['severity'].upper()}",
                f"- **Maximum drift:** {assessment.get('max_drift', 0):.2%}",
                f"- **Average drift:** {assessment.get('avg_drift', 0):.2%}",
                f"- **Recommendation:** {assessment.get('recommendation', 'N/A')}",
                "",
            ])
        
        # Recommendations
        report_lines.extend([
            "## Quality Recommendations",
            "",
            self._generate_quality_recommendations(text_metrics, table_metrics),
            "",
            "---",
            f"*Report generated by Parser Quality Evaluator at {datetime.now()}*"
        ])
        
        report_content = "\n".join(report_lines)
        
        # Save report
        report_file = self.metrics_dir / f"quality_evaluation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
        with open(report_file, 'w') as f:
            f.write(report_content)
        
        self.logger.info(f"Quality evaluation report saved to: {report_file}")
        return report
    
    def validate_against_xbrl_ground_truth(self) -> Dict[str, Any]:
        """
        Compare parsed financial data against XBRL ground truth
        
        Returns:
            Validation results comparing extracted vs ground truth financial data
        """
        if not self.xbrl_ground_truth:
            return {
                "status": "no_ground_truth",
                "message": "No XBRL ground truth data available for comparison"
            }
        
        validation_results = {
            "validation_timestamp": datetime.now().isoformat(),
            "ground_truth_sources": list(self.xbrl_ground_truth.keys()),
            "financial_fact_comparisons": {},
            "accuracy_metrics": {},
            "missing_extractions": [],
            "false_extractions": [],
            "overall_accuracy": 0.0
        }
        
        # Try to find parsed financial data in tables
        parsed_financial_data = self._extract_parsed_financial_data()
        
        if not parsed_financial_data:
            validation_results["message"] = "No financial data found in parsed outputs"
            return validation_results
        
        # Compare against each XBRL source
        for xbrl_source, xbrl_data in self.xbrl_ground_truth.items():
            ground_truth_facts = xbrl_data.get("financial_facts", {})
            
            comparison = self._compare_financial_facts(
                parsed_financial_data, 
                ground_truth_facts,
                xbrl_source
            )
            
            validation_results["financial_fact_comparisons"][xbrl_source] = comparison
        
        # Calculate overall accuracy metrics
        validation_results["accuracy_metrics"] = self._calculate_validation_accuracy(
            validation_results["financial_fact_comparisons"]
        )
        
        # Generate summary
        validation_results["summary"] = self._generate_validation_summary(validation_results)
        
        return validation_results
    
    def _extract_parsed_financial_data(self) -> Dict[str, List[Dict]]:
        """Extract financial data from parsed table and text outputs"""
        financial_data = {}
        
        # Search through table data
        if self.table_analysis and "method_comparison" in self.table_analysis:
            for method, method_data in self.table_analysis["method_comparison"].items():
                if "tables" in method_data:
                    financial_values = []
                    
                    for table in method_data["tables"]:
                        # Extract numerical values that could be financial
                        if "data" in table:
                            for row in table["data"]:
                                for cell in row:
                                    # Look for financial patterns
                                    financial_value = self._extract_financial_from_text(str(cell))
                                    if financial_value:
                                        financial_values.extend(financial_value)
                    
                    if financial_values:
                        financial_data[f"tables_{method}"] = financial_values
        
        # Search through text extraction data
        text_files = list(self.text_dir.glob("page_*.json"))
        text_financial_data = []
        
        for text_file in text_files:
            try:
                with open(text_file, 'r') as f:
                    text_data = json.load(f)
                
                if "extracted_text" in text_data:
                    text = text_data["extracted_text"]
                    financial_values = self._extract_financial_from_text(text)
                    if financial_values:
                        text_financial_data.extend(financial_values)
                        
            except Exception as e:
                self.logger.warning(f"Error reading text file {text_file}: {e}")
        
        if text_financial_data:
            financial_data["text_extraction"] = text_financial_data
        
        return financial_data
    
    def _extract_financial_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Extract financial values and patterns from text"""
        financial_patterns = []
        
        if not isinstance(text, str):
            return financial_patterns
        
        # Common financial value patterns
        patterns = {
            'currency_millions': r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:million|mil\b)',
            'currency_billions': r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:billion|bil\b)', 
            'currency_exact': r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
            'percentage': r'(\d{1,3}(?:\.\d{1,2})?)%',
            'large_numbers': r'\b(\d{1,3}(?:,\d{3})+)\b'
        }
        
        # Context patterns to identify what the numbers might represent
        context_patterns = {
            'revenue': r'(?:revenue|sales|income)[^\d]*(\$?\d+(?:,\d{3})*(?:\.\d+)?)',
            'net_income': r'(?:net income|profit|earnings)[^\d]*(\$?\d+(?:,\d{3})*(?:\.\d+)?)',
            'assets': r'(?:total assets|assets)[^\d]*(\$?\d+(?:,\d{3})*(?:\.\d+)?)',
            'cash': r'(?:cash|cash and equivalents)[^\d]*(\$?\d+(?:,\d{3})*(?:\.\d+)?)'
        }
        
        # Extract patterns with context
        for context_name, pattern in context_patterns.items():
            matches = re.finditer(pattern, text.lower(), re.IGNORECASE)
            for match in matches:
                value_str = match.group(1)
                cleaned_value = self._clean_financial_value(value_str)
                
                if cleaned_value is not None:
                    financial_patterns.append({
                        'context': context_name,
                        'value': cleaned_value,
                        'original_text': match.group(0),
                        'pattern_type': 'contextual'
                    })
        
        # Extract general financial patterns
        for pattern_name, pattern in patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                value_str = match.group(1)
                cleaned_value = self._clean_financial_value(value_str)
                
                if cleaned_value is not None:
                    # Apply scaling based on pattern
                    if pattern_name == 'currency_millions':
                        cleaned_value *= 1_000_000
                    elif pattern_name == 'currency_billions':
                        cleaned_value *= 1_000_000_000
                    
                    financial_patterns.append({
                        'context': 'unknown',
                        'value': cleaned_value,
                        'original_text': match.group(0),
                        'pattern_type': pattern_name
                    })
        
        return financial_patterns
    
    def _compare_financial_facts(self, parsed_data: Dict, ground_truth: Dict, source_name: str) -> Dict[str, Any]:
        """Compare parsed financial data against ground truth facts"""
        comparison = {
            "source": source_name,
            "matches": [],
            "near_matches": [],
            "missing": [],
            "false_positives": [],
            "accuracy_score": 0.0
        }
        
        # Flatten ground truth for easier comparison
        gt_values = {}
        for category, fact_data in ground_truth.items():
            if isinstance(fact_data, dict) and "value" in fact_data:
                gt_values[category] = fact_data["value"]
        
        # Flatten parsed data
        parsed_values = []
        for method, values in parsed_data.items():
            for value_data in values:
                parsed_values.append(value_data)
        
        # Compare each ground truth value
        for category, gt_value in gt_values.items():
            if not isinstance(gt_value, (int, float)):
                continue
            
            best_match = None
            best_accuracy = 0.0
            
            # Find best matching parsed value
            for parsed_value_data in parsed_values:
                parsed_value = parsed_value_data.get("value")
                if not isinstance(parsed_value, (int, float)):
                    continue
                
                # Calculate accuracy
                if gt_value != 0:
                    relative_error = abs(parsed_value - gt_value) / abs(gt_value)
                    accuracy = max(0, 1 - relative_error)
                else:
                    accuracy = 1.0 if parsed_value == 0 else 0.0
                
                if accuracy > best_accuracy:
                    best_accuracy = accuracy
                    best_match = {
                        "parsed_value": parsed_value,
                        "ground_truth": gt_value,
                        "accuracy": accuracy,
                        "relative_error": relative_error if gt_value != 0 else 0,
                        "context": parsed_value_data.get("context", "unknown"),
                        "source_method": method if method.startswith("tables_") else "text_extraction"
                    }
            
            if best_match:
                if best_accuracy >= 0.9:  # 90% accuracy threshold for matches
                    comparison["matches"].append({
                        "category": category,
                        **best_match
                    })
                elif best_accuracy >= 0.5:  # 50% accuracy threshold for near matches
                    comparison["near_matches"].append({
                        "category": category,
                        **best_match
                    })
                else:
                    comparison["missing"].append({
                        "category": category,
                        "ground_truth": gt_value,
                        "best_attempt": best_match
                    })
            else:
                comparison["missing"].append({
                    "category": category,
                    "ground_truth": gt_value,
                    "reason": "no_parsed_values_found"
                })
        
        # Calculate overall accuracy score
        total_facts = len(gt_values)
        if total_facts > 0:
            match_score = len(comparison["matches"]) * 1.0
            near_match_score = len(comparison["near_matches"]) * 0.5
            comparison["accuracy_score"] = (match_score + near_match_score) / total_facts
        
        return comparison
    
    def _calculate_validation_accuracy(self, comparisons: Dict) -> Dict[str, float]:
        """Calculate overall validation accuracy metrics"""
        if not comparisons:
            return {}
        
        total_matches = 0
        total_near_matches = 0
        total_missing = 0
        total_facts = 0
        accuracy_scores = []
        
        for source, comparison in comparisons.items():
            total_matches += len(comparison.get("matches", []))
            total_near_matches += len(comparison.get("near_matches", []))
            total_missing += len(comparison.get("missing", []))
            
            source_total = total_matches + total_near_matches + total_missing
            total_facts += source_total
            
            if comparison.get("accuracy_score") is not None:
                accuracy_scores.append(comparison["accuracy_score"])
        
        metrics = {}
        
        if total_facts > 0:
            metrics["exact_match_rate"] = total_matches / total_facts
            metrics["near_match_rate"] = total_near_matches / total_facts
            metrics["missing_rate"] = total_missing / total_facts
            metrics["detection_rate"] = (total_matches + total_near_matches) / total_facts
        
        if accuracy_scores:
            metrics["average_accuracy"] = np.mean(accuracy_scores)
            metrics["min_accuracy"] = min(accuracy_scores)
            metrics["max_accuracy"] = max(accuracy_scores)
        
        return metrics
    
    def _generate_validation_summary(self, validation_results: Dict) -> Dict[str, Any]:
        """Generate human-readable validation summary"""
        accuracy_metrics = validation_results.get("accuracy_metrics", {})
        
        summary = {
            "overall_status": "unknown",
            "key_findings": [],
            "recommendations": []
        }
        
        # Determine overall status
        avg_accuracy = accuracy_metrics.get("average_accuracy", 0)
        detection_rate = accuracy_metrics.get("detection_rate", 0)
        
        if avg_accuracy >= 0.8 and detection_rate >= 0.7:
            summary["overall_status"] = "excellent"
            summary["key_findings"].append("High accuracy financial data extraction achieved")
        elif avg_accuracy >= 0.6 and detection_rate >= 0.5:
            summary["overall_status"] = "good"
            summary["key_findings"].append("Good financial data extraction with room for improvement")
        elif avg_accuracy >= 0.4 or detection_rate >= 0.3:
            summary["overall_status"] = "needs_improvement"
            summary["key_findings"].append("Financial data extraction needs significant improvement")
        else:
            summary["overall_status"] = "poor"
            summary["key_findings"].append("Financial data extraction failing to capture ground truth")
        
        # Add specific findings
        if accuracy_metrics.get("exact_match_rate", 0) > 0.5:
            summary["key_findings"].append(f"Strong exact match rate: {accuracy_metrics['exact_match_rate']:.1%}")
        
        if accuracy_metrics.get("missing_rate", 1) > 0.5:
            summary["key_findings"].append(f"High missing data rate: {accuracy_metrics['missing_rate']:.1%}")
        
        # Add recommendations
        if detection_rate < 0.5:
            summary["recommendations"].append("Improve financial data pattern recognition")
            summary["recommendations"].append("Consider additional table extraction methods")
        
        if accuracy_metrics.get("exact_match_rate", 0) < 0.3:
            summary["recommendations"].append("Refine numerical value extraction and formatting")
        
        if len(validation_results.get("ground_truth_sources", [])) == 1:
            summary["recommendations"].append("Add more XBRL sources for comprehensive validation")
        
        return summary_content
    
    def _generate_quality_recommendations(self, text_metrics: Dict, table_metrics: Dict) -> str:
        """Generate recommendations based on analysis results"""
        recommendations = []
        
        # Text extraction recommendations
        if text_metrics.get('ocr_rate', 0) > 0.1:
            recommendations.append(
                "• **High OCR usage detected** - Consider improving PDF quality or extraction parameters"
            )
        
        if text_metrics.get('chars_cv', 0) > 1.0:
            recommendations.append(
                "• **High text length variability** - Pages may have inconsistent content or extraction issues"
            )
        
        # Table extraction recommendations
        if 'method_comparison' in table_metrics and len(table_metrics['method_comparison']) > 1:
            methods = table_metrics['method_comparison']
            best_method = max(methods.keys(), key=lambda k: methods[k]['avg_content_quality'])
            recommendations.append(
                f"• **Best performing method:** {best_method} (quality: {methods[best_method]['avg_content_quality']:.3f})"
            )
        
        if table_metrics.get('page_overlap_ratio', 0) < 0.3:
            recommendations.append(
                "• **Low method agreement** - Different extraction methods finding different content"
            )
        
        if not recommendations:
            recommendations.append("• **Parsing quality appears stable** - Continue monitoring for consistency")
        
        return "\n".join(recommendations)