"""
Main entry point for running Luigi warehouse pipeline
"""
import sys
import luigi
sys.path.insert(0, 'warehouse')
from tasks.analyze_ordinal_performance import AnalyzeOrdinalPerformance


if __name__ == '__main__':
    luigi.build([AnalyzeOrdinalPerformance()], local_scheduler=True)
