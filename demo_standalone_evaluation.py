#!/usr/bin/env python3
"""
Demo script to test the standalone evaluation system with XBRL ground truth

This script demonstrates the complete standalone evaluation system including:
- XBRL ground truth loading and parsing
- Financial data extraction from parsed outputs
- Accuracy validation against ground truth
- Standalone metrics tracking without DVC dependencies

Usage:
    python demo_standalone_evaluation.py
"""

import json
import logging
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Run standalone evaluation demo"""
    
    # Set up paths
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data" / "intermediate"
    xbrl_dir = project_root / "data" / "raw" / "xbrl_files" 
    output_dir = project_root / "demo_presentation_output"
    
    logger.info("🚀 Starting standalone evaluation system demo...")
    logger.info(f"Data directory: {data_dir}")
    logger.info(f"XBRL directory: {xbrl_dir}")
    logger.info(f"Output directory: {output_dir}")
    
    # Check if required directories exist
    missing_dirs = []
    if not data_dir.exists():
        missing_dirs.append(str(data_dir))
    if not xbrl_dir.exists():
        missing_dirs.append(str(xbrl_dir))
    
    if missing_dirs:
        logger.error(f"❌ Missing required directories: {missing_dirs}")
        logger.info("Please ensure the data has been processed and XBRL files are available")
        return False
    
    try:
        # Import evaluation modules
        from src.evaluation.parser_quality_evaluator import ParserQualityEvaluator
        from src.evaluation.standalone_metrics_tracker import StandaloneMetricsTracker
        
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # 1. Initialize quality evaluator with XBRL support
        logger.info("📊 Initializing parser quality evaluator with XBRL ground truth...")
        evaluator = ParserQualityEvaluator(data_dir, output_dir=output_dir, xbrl_dir=xbrl_dir)
        
        # Check if XBRL data was loaded
        if evaluator.xbrl_ground_truth:
            logger.info(f"✅ Loaded XBRL ground truth from {len(evaluator.xbrl_ground_truth)} sources:")
            for source in evaluator.xbrl_ground_truth.keys():
                logger.info(f"   - {source}")
        else:
            logger.warning("⚠️  No XBRL ground truth data found")
        
        # 2. Run XBRL validation
        logger.info("🔍 Validating parsed data against XBRL ground truth...")
        xbrl_validation = evaluator.validate_against_xbrl_ground_truth()
        
        # Print validation summary
        if xbrl_validation.get("status") != "no_ground_truth":
            summary = xbrl_validation.get("summary", {})
            accuracy_metrics = xbrl_validation.get("accuracy_metrics", {})
            
            logger.info("📈 XBRL Validation Results:")
            logger.info(f"   Overall Status: {summary.get('overall_status', 'unknown')}")
            
            if accuracy_metrics:
                logger.info(f"   Average Accuracy: {accuracy_metrics.get('average_accuracy', 0):.1%}")
                logger.info(f"   Detection Rate: {accuracy_metrics.get('detection_rate', 0):.1%}")
                logger.info(f"   Exact Match Rate: {accuracy_metrics.get('exact_match_rate', 0):.1%}")
            
            if summary.get("key_findings"):
                logger.info("   Key Findings:")
                for finding in summary["key_findings"][:3]:
                    logger.info(f"   - {finding}")
        else:
            logger.warning(f"⚠️  XBRL validation status: {xbrl_validation.get('message', 'Unknown')}")
        
        # 3. Initialize standalone metrics tracker
        logger.info("📋 Setting up standalone metrics tracking...")
        metrics_dir = data_dir / "evaluation_metrics"
        tracker = StandaloneMetricsTracker(metrics_dir)
        
        # 4. Calculate quality metrics
        logger.info("🔬 Calculating text and table consistency metrics...")
        text_metrics = evaluator.calculate_text_consistency_metrics()
        table_metrics = evaluator.calculate_table_consistency_metrics()
        
        # 5. Package metrics for tracking
        evaluation_metrics = {
            "text_extraction": {
                "successful_extraction_rate": text_metrics.get("successful_extraction_rate", 0),
                "avg_chars_per_page": text_metrics.get("avg_chars_per_page", 0),
                "ocr_rate": text_metrics.get("ocr_rate", 0),
                "content_distribution_entropy": text_metrics.get("content_distribution_entropy", 0)
            },
            "table_extraction": {
                "total_tables_extracted": table_metrics.get("total_tables", 0), 
                "avg_content_quality": table_metrics.get("avg_quality", 0),
                "extraction_methods_used": table_metrics.get("methods_compared", 0)
            },
            "xbrl_validation": {
                "ground_truth_available": len(evaluator.xbrl_ground_truth) > 0,
                "validation_accuracy": xbrl_validation.get("accuracy_metrics", {}).get("average_accuracy", 0),
                "detection_rate": xbrl_validation.get("accuracy_metrics", {}).get("detection_rate", 0),
                "exact_match_rate": xbrl_validation.get("accuracy_metrics", {}).get("exact_match_rate", 0)
            },
            "overall": {
                "evaluation_timestamp": datetime.now().isoformat(),
                "data_sources_processed": len(evaluator.xbrl_ground_truth) + 1,  # +1 for parsed data
                "validation_status": xbrl_validation.get("summary", {}).get("overall_status", "unknown")
            }
        }
        
        # 6. Record metrics in standalone tracker
        logger.info("💾 Recording metrics in standalone tracker...")
        metrics_id = tracker.record_metrics(evaluation_metrics, "demo_evaluation")
        logger.info(f"   Metrics recorded with ID: {metrics_id}")
        
        # 7. Create baseline if none exists
        if not tracker.baselines:
            success = tracker.update_baseline("demo_baseline", metrics_id)
            if success:
                logger.info("🎯 Created demo baseline from current metrics")
        
        # 8. Generate comprehensive evaluation report
        logger.info("📝 Generating comprehensive evaluation report...")
        evaluation_report = evaluator.generate_evaluation_report()
        
        # 9. Generate metrics tracking report
        logger.info("📊 Generating standalone metrics tracking report...")
        tracking_report = tracker.generate_metrics_report(output_dir / f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md")
        
        # 10. Save comprehensive results
        demo_results = {
            "demo_timestamp": datetime.now().isoformat(),
            "system_status": "standalone_operational",
            "xbrl_validation": xbrl_validation,
            "quality_metrics": {
                "text_metrics": text_metrics,
                "table_metrics": table_metrics
            },
            "tracked_metrics": evaluation_metrics,
            "metrics_tracking_id": metrics_id,
            "output_files": {
                "evaluation_report": str(output_dir / "evaluation_report.md"),
                "metrics_report": str(output_dir / f"metrics_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"),
                "xbrl_validation": str(output_dir / "xbrl_validation_results.json")
            }
        }
        
        # Save main demo results
        results_file = output_dir / f"demo_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(results_file, 'w') as f:
            json.dump(demo_results, f, indent=2)
        
        # Save XBRL validation separately for detailed analysis
        xbrl_results_file = output_dir / "xbrl_validation_results.json"
        with open(xbrl_results_file, 'w') as f:
            json.dump(xbrl_validation, f, indent=2)
        
        logger.info("✅ Standalone evaluation demo completed successfully!")
        logger.info(f"📁 Results saved to: {results_file}")
        logger.info(f"📋 XBRL validation details: {xbrl_results_file}")
        
        # Print summary
        print("\n" + "="*60)
        print("🎯 STANDALONE EVALUATION SYSTEM DEMO SUMMARY")
        print("="*60)
        print(f"✅ System Status: {demo_results['system_status']}")
        print(f"🔍 XBRL Ground Truth: {len(evaluator.xbrl_ground_truth)} sources loaded")
        print(f"📊 Validation Accuracy: {xbrl_validation.get('accuracy_metrics', {}).get('average_accuracy', 0):.1%}")
        print(f"🎯 Metrics Tracking: ID {metrics_id}")
        print(f"📁 Output Directory: {output_dir}")
        print("="*60)
        
        return True
        
    except ImportError as e:
        logger.error(f"❌ Failed to import evaluation modules: {e}")
        logger.info("Please ensure the evaluation modules are properly installed")
        return False
    except Exception as e:
        logger.error(f"❌ Demo failed with error: {e}")
        logger.exception("Full error details:")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)