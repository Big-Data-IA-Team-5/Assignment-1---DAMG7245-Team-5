#!/usr/bin/env python3
"""
Enhanced PDF-XBRL Mapper with Natural Language Processing and Taxonomy Lookup

This module provides intelligent mapping between PDF table labels and XBRL concepts
using various techniques including semantic similarity, fuzzy matching, and 
financial taxonomy knowledge.
"""

import re
import logging
from typing import Dict, List, Tuple, Optional, Any
from difflib import SequenceMatcher
import pandas as pd

# Optional imports for enhanced NLP capabilities
try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.metrics.pairwise import cosine_similarity
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    logging.warning("sklearn not available - falling back to basic similarity")

try:
    import numpy as np
    NUMPY_AVAILABLE = True
except ImportError:
    NUMPY_AVAILABLE = False
    logging.warning("numpy not available - using basic math operations")

logger = logging.getLogger(__name__)

class EnhancedPDFXBRLMapper:
    """Enhanced mapper with multiple matching strategies."""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.similarity_threshold = config.get('similarity_threshold', 0.6)
        self.fuzzy_threshold = config.get('fuzzy_threshold', 0.7)
        
        # Financial taxonomy mapping
        self.financial_taxonomy = self._build_financial_taxonomy()
        
        # Initialize TF-IDF vectorizer if available
        self.vectorizer = None
        if SKLEARN_AVAILABLE:
            self.vectorizer = TfidfVectorizer(
                stop_words='english',
                lowercase=True,
                token_pattern=r'\b[a-zA-Z][a-zA-Z\s]+\b'
            )
    
    def _build_financial_taxonomy(self) -> Dict[str, List[str]]:
        """
        Build a comprehensive financial taxonomy mapping.
        
        Returns:
            Dictionary mapping XBRL concepts to related terms and synonyms
        """
        return {
            'assets': [
                'total assets', 'assets', 'asset', 'total asset',
                'current assets', 'non-current assets', 'fixed assets',
                'tangible assets', 'intangible assets', 'property plant equipment'
            ],
            'cash': [
                'cash', 'cash equivalents', 'cash and cash equivalents',
                'liquid assets', 'cash flows', 'cash balance',
                'restricted cash', 'unrestricted cash'
            ],
            'equity': [
                'shareholders equity', 'stockholders equity', 'equity',
                'total equity', 'owners equity', 'retained earnings',
                'common stock', 'preferred stock', 'additional paid capital'
            ],
            'expenses': [
                'expenses', 'total expenses', 'operating expenses',
                'cost of goods sold', 'cogs', 'general expenses',
                'administrative expenses', 'selling expenses',
                'depreciation', 'amortization', 'impairment'
            ],
            'liabilities': [
                'liabilities', 'total liabilities', 'current liabilities',
                'non-current liabilities', 'long-term debt', 'short-term debt',
                'accounts payable', 'accrued expenses', 'deferred revenue'
            ],
            'net_income': [
                'net income', 'net earnings', 'profit', 'net profit',
                'income before taxes', 'earnings', 'bottom line',
                'profit after tax', 'net loss'
            ],
            'revenue': [
                'revenue', 'total revenue', 'sales', 'total sales',
                'gross revenue', 'net revenue', 'operating revenue',
                'service revenue', 'product revenue', 'top line'
            ]
        }
    
    def preprocess_text(self, text: str) -> str:
        """
        Clean and normalize text for better matching.
        
        Args:
            text: Raw text to preprocess
            
        Returns:
            Cleaned and normalized text
        """
        if not text or pd.isna(text):
            return ""
        
        # Convert to lowercase
        text = str(text).lower()
        
        # Remove special characters and numbers at start/end
        text = re.sub(r'^[^\w\s]+|[^\w\s]+$', '', text)
        
        # Replace multiple spaces with single space
        text = re.sub(r'\s+', ' ', text)
        
        # Remove common financial prefixes/suffixes
        prefixes_to_remove = ['total', 'net', 'gross', 'consolidated']
        for prefix in prefixes_to_remove:
            text = re.sub(rf'^{prefix}\s+', '', text)
        
        return text.strip()
    
    def calculate_fuzzy_similarity(self, text1: str, text2: str) -> float:
        """
        Calculate fuzzy string similarity using sequence matching.
        
        Args:
            text1: First text string
            text2: Second text string
            
        Returns:
            Similarity score between 0 and 1
        """
        text1_clean = self.preprocess_text(text1)
        text2_clean = self.preprocess_text(text2)
        
        return SequenceMatcher(None, text1_clean, text2_clean).ratio()
    
    def calculate_tfidf_similarity(self, pdf_labels: List[str], xbrl_concepts: List[str]) -> np.ndarray:
        """
        Calculate TF-IDF based similarity matrix.
        
        Args:
            pdf_labels: List of PDF table labels
            xbrl_concepts: List of XBRL concept names
            
        Returns:
            Similarity matrix (pdf_labels x xbrl_concepts)
        """
        if not SKLEARN_AVAILABLE or not NUMPY_AVAILABLE:
            return None
        
        # Combine all terms for taxonomy expansion
        expanded_concepts = []
        for concept in xbrl_concepts:
            concept_terms = [concept]
            if concept in self.financial_taxonomy:
                concept_terms.extend(self.financial_taxonomy[concept])
            expanded_concepts.append(' '.join(concept_terms))
        
        # Preprocess texts
        processed_labels = [self.preprocess_text(label) for label in pdf_labels]
        processed_concepts = [self.preprocess_text(concept) for concept in expanded_concepts]
        
        try:
            # Create TF-IDF matrix
            all_texts = processed_labels + processed_concepts
            tfidf_matrix = self.vectorizer.fit_transform(all_texts)
            
            # Split into labels and concepts matrices
            label_matrix = tfidf_matrix[:len(pdf_labels)]
            concept_matrix = tfidf_matrix[len(pdf_labels):]
            
            # Calculate cosine similarity
            similarity_matrix = cosine_similarity(label_matrix, concept_matrix)
            return similarity_matrix
        
        except Exception as e:
            logger.warning(f"TF-IDF similarity calculation failed: {e}")
            return None
    
    def find_best_matches(self, pdf_labels: List[str], xbrl_concepts: List[str]) -> Dict[str, Tuple[str, float, str]]:
        """
        Find best matches using multiple strategies.
        
        Args:
            pdf_labels: List of PDF table column labels
            xbrl_concepts: List of available XBRL concepts
            
        Returns:
            Dictionary mapping pdf_label -> (xbrl_concept, confidence, method)
        """
        matches = {}
        
        # Strategy 1: Exact and fuzzy matching
        for pdf_label in pdf_labels:
            best_concept = None
            best_score = 0.0
            best_method = "fuzzy"
            
            for xbrl_concept in xbrl_concepts:
                # Check exact match first
                if self.preprocess_text(pdf_label) == self.preprocess_text(xbrl_concept):
                    matches[pdf_label] = (xbrl_concept, 1.0, "exact")
                    continue
                
                # Check taxonomy matches
                if xbrl_concept in self.financial_taxonomy:
                    for synonym in self.financial_taxonomy[xbrl_concept]:
                        similarity = self.calculate_fuzzy_similarity(pdf_label, synonym)
                        if similarity > best_score and similarity >= self.fuzzy_threshold:
                            best_concept = xbrl_concept
                            best_score = similarity
                            best_method = "taxonomy"
                
                # Direct fuzzy matching
                similarity = self.calculate_fuzzy_similarity(pdf_label, xbrl_concept)
                if similarity > best_score and similarity >= self.fuzzy_threshold:
                    best_concept = xbrl_concept
                    best_score = similarity
                    best_method = "fuzzy"
            
            if best_concept and pdf_label not in matches:
                matches[pdf_label] = (best_concept, best_score, best_method)
        
        # Strategy 2: TF-IDF similarity (if available)
        if SKLEARN_AVAILABLE and NUMPY_AVAILABLE:
            tfidf_similarities = self.calculate_tfidf_similarity(pdf_labels, xbrl_concepts)
            
            if tfidf_similarities is not None:
                for i, pdf_label in enumerate(pdf_labels):
                    if pdf_label not in matches:  # Only for unmatched labels
                        best_idx = np.argmax(tfidf_similarities[i])
                        best_score = tfidf_similarities[i][best_idx]
                        
                        if best_score >= self.similarity_threshold:
                            matches[pdf_label] = (xbrl_concepts[best_idx], best_score, "tfidf")
        
        return matches
    
    def map_pdf_labels_to_xbrl(self, pdf_labels: List[str], 
                              xbrl_concepts: Optional[List[str]] = None,
                              include_confidence: bool = True) -> Dict[str, Any]:
        """
        Enhanced mapping with multiple strategies and detailed results.
        
        Args:
            pdf_labels: List of PDF table column labels
            xbrl_concepts: List of available XBRL concepts
            include_confidence: Whether to include confidence scores
            
        Returns:
            Enhanced mapping dictionary with confidence scores and methods
        """
        if not xbrl_concepts:
            xbrl_concepts = list(self.financial_taxonomy.keys())
        
        # Clean labels
        cleaned_labels = [label for label in pdf_labels if label and not pd.isna(label)]
        
        if not cleaned_labels:
            logger.warning("No valid PDF labels to map")
            return {}
        
        # Find matches using multiple strategies
        matches = self.find_best_matches(cleaned_labels, xbrl_concepts)
        
        # Prepare results
        results = {}
        for label in pdf_labels:
            if label in matches:
                concept, confidence, method = matches[label]
                if include_confidence:
                    results[label] = {
                        'xbrl_concept': concept,
                        'confidence': confidence,
                        'method': method,
                        'mapped': True
                    }
                else:
                    results[label] = concept
            else:
                if include_confidence:
                    results[label] = {
                        'xbrl_concept': None,
                        'confidence': 0.0,
                        'method': 'none',
                        'mapped': False
                    }
                else:
                    results[label] = None
        
        return results
    
    def generate_mapping_analysis(self, pdf_labels: List[str], 
                                xbrl_concepts: List[str]) -> Dict[str, Any]:
        """
        Generate comprehensive mapping analysis.
        
        Args:
            pdf_labels: List of PDF table labels
            xbrl_concepts: List of XBRL concepts
            
        Returns:
            Detailed analysis of mapping results
        """
        mappings = self.map_pdf_labels_to_xbrl(pdf_labels, xbrl_concepts, include_confidence=True)
        
        # Analyze results
        total_labels = len(pdf_labels)
        mapped_labels = sum(1 for m in mappings.values() if m.get('mapped', False))
        unmapped_labels = total_labels - mapped_labels
        
        # Group by confidence ranges
        high_confidence = sum(1 for m in mappings.values() if m.get('confidence', 0) >= 0.8)
        medium_confidence = sum(1 for m in mappings.values() if 0.6 <= m.get('confidence', 0) < 0.8)
        low_confidence = sum(1 for m in mappings.values() if 0.3 <= m.get('confidence', 0) < 0.6)
        
        # Group by method
        method_counts = {}
        for mapping in mappings.values():
            method = mapping.get('method', 'none')
            method_counts[method] = method_counts.get(method, 0) + 1
        
        return {
            'total_labels': total_labels,
            'mapped_labels': mapped_labels,
            'unmapped_labels': unmapped_labels,
            'mapping_rate': mapped_labels / total_labels if total_labels > 0 else 0,
            'confidence_distribution': {
                'high_confidence': high_confidence,
                'medium_confidence': medium_confidence, 
                'low_confidence': low_confidence
            },
            'method_distribution': method_counts,
            'detailed_mappings': mappings,
            'recommendations': self._generate_recommendations(mappings, xbrl_concepts)
        }
    
    def _generate_recommendations(self, mappings: Dict[str, Any], 
                                xbrl_concepts: List[str]) -> List[str]:
        """Generate recommendations for improving mappings."""
        recommendations = []
        
        unmapped_count = sum(1 for m in mappings.values() if not m.get('mapped', False))
        low_confidence_count = sum(1 for m in mappings.values() if m.get('confidence', 0) < 0.6)
        
        if unmapped_count > 0:
            recommendations.append(f"Consider manual review of {unmapped_count} unmapped labels")
            
        if low_confidence_count > 0:
            recommendations.append(f"Review {low_confidence_count} low-confidence mappings")
            
        recommendations.append("Consider expanding financial taxonomy with domain-specific terms")
        recommendations.append("Implement temporal matching for period-specific data")
        
        return recommendations

# Export the enhanced mapper for use in Lab 11
__all__ = ['EnhancedPDFXBRLMapper']