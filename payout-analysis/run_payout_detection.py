"""
Run the payout anomaly detection pipeline.

This script orchestrates the payout analysis pipeline using basic scripts:

PIPELINE:
1. Filter and extract payout data  
2. Train hybrid models (regression + isolation forest) for payout prediction
3. Detect payout anomalies using statistical outlier detection
4. Generate payout anomaly report
5. Cluster operators for analysis

Usage:
    python run_payout_detection.py
"""
import luigi
import argparse
from warehouse.tasks.detect_anomalies import DetectAnomalies
from warehouse.tasks.generate_anomaly_report import GenerateAnomalyReport
from warehouse.tasks.cluster_operators import ClusterOperatorsDBSCAN
from warehouse.tasks.filter_and_extract import ExtractColumns
from warehouse.tasks.train_hybrid_models import TrainHybridModels
from warehouse.tasks.filter_by_sample_size import FilterBySampleSize



def run_pipeline():
    """Run the payout anomaly detection pipeline"""
    print("🔄 Running payout anomaly detection pipeline...")
    luigi.build(
        [DetectAnomalies(), GenerateAnomalyReport(), ClusterOperatorsDBSCAN()],
        local_scheduler=True,
        log_level='INFO'
    )


def run_specific_task(task):
    """Run a specific task"""
    tasks = {
        'filter_extract': ExtractColumns,
        'filter_sample': FilterBySampleSize,
        'train_models': TrainHybridModels,
        'detect_anomalies': DetectAnomalies,
        'generate_report': GenerateAnomalyReport,
        'cluster_operators': ClusterOperatorsDBSCAN
    }
    
    if task not in tasks:
        print(f"❌ Unknown task: {task}")
        print(f"Available tasks: {', '.join(tasks.keys())}")
        return
    
    task_class = tasks[task]
    print(f"🔄 Running {task}...")
    luigi.build([task_class()], local_scheduler=True, log_level='INFO')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Gaming Anomaly Detection Pipeline')
    parser.add_argument('--task', type=str,
                       help='Run specific task only')
    
    args = parser.parse_args()
    
    print("🎯 Gaming Operator Payout Anomaly Detection")
    print("=" * 60)
    
    if args.task:
        run_specific_task(args.task)
    else:
        run_pipeline()
    
    print("\n✅ Pipeline execution completed!")
    print("\n📊 Check outputs in warehouse/data/:")
    print("   📄 REPORTS:")
    print("     - anomaly_report.md")
    print("   📊 DATA:")
    print("     - anomalies_with_context.csv")
    print("     - anomaly_summary.csv")
    print("     - operator_clusters.csv")
    print("   🤖 MODELS:")
    print("     - models/hybrid_model.pkl")
