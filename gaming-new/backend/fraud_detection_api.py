from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest, RandomForestClassifier
from sklearn.preprocessing import StandardScaler, LabelEncoder
from sklearn.cluster import DBSCAN
from sklearn.svm import OneClassSVM
from sklearn.decomposition import PCA
from sklearn.metrics import silhouette_score
from scipy import stats
import sqlite3
import json
from datetime import datetime, timedelta
import asyncio
import uvicorn
from collections import defaultdict
import warnings
import logging
from pathlib import Path
warnings.filterwarnings('ignore')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Gaming Fraud Detection API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class FraudDetectionEngine:
    def __init__(self):
        self.df = None
        self.isolation_forest = None
        self.one_class_svm = None
        self.dbscan = None
        self.scaler = StandardScaler()
        self.pca = PCA(n_components=0.95)
        self.risk_thresholds = {
            'high': 0.8,
            'medium': 0.5,
            'low': 0.2
        }
        self.behavioral_patterns = {}
        self.time_series_features = None
        self.seasonal_patterns = {}
        
    def load_data(self, csv_path: str):
        """Load and preprocess gaming data"""
        self.df = pd.read_csv(csv_path)
        self.df = self.df.fillna(0)
        
        # Convert relevant columns to numeric
        numeric_cols = ['no_of_bets', 'stake_real_money', 'stake_free_money', 
                       'payout_base_win', 'refund_total', 'adjustment_total', 
                       'GGR', 'total_transactions', 'movement_wager_amt', 
                       'movement_win_amt', 'revenue_amt', 'bets_won_cnt']
        
        for col in numeric_cols:
            if col in self.df.columns:
                self.df[col] = pd.to_numeric(self.df[col], errors='coerce').fillna(0)
        
        # Enhanced feature engineering for fraud detection
        self.df['stake_to_payout_ratio'] = np.where(
            self.df['payout_base_win'] > 0,
            self.df['stake_real_money'] / self.df['payout_base_win'],
            0
        )
        
        self.df['win_rate'] = np.where(
            self.df['no_of_bets'] > 0,
            self.df['bets_won_cnt'] / self.df['no_of_bets'],
            0
        )
        
        self.df['avg_bet_size'] = np.where(
            self.df['no_of_bets'] > 0,
            self.df['stake_real_money'] / self.df['no_of_bets'],
            0
        )
        
        self.df['revenue_per_transaction'] = np.where(
            self.df['total_transactions'] > 0,
            self.df['revenue_amt'] / self.df['total_transactions'],
            0
        )
        
        # Advanced risk indicators
        self.df['ggr_margin'] = np.where(
            self.df['stake_real_money'] > 0,
            self.df['GGR'] / self.df['stake_real_money'],
            0
        )
        
        self.df['refund_rate'] = np.where(
            self.df['stake_real_money'] > 0,
            self.df['refund_total'] / self.df['stake_real_money'],
            0
        )
        
        # Time-series features
        self.df['timestamp_dt'] = pd.to_datetime(self.df['timestamp_end'])
        self.df['hour'] = self.df['timestamp_dt'].dt.hour
        self.df['day_of_week'] = self.df['timestamp_dt'].dt.dayofweek
        self.df['month'] = self.df['timestamp_dt'].dt.month
        self.df['quarter'] = self.df['timestamp_dt'].dt.quarter
        self.df['is_weekend'] = self.df['day_of_week'].isin([5, 6]).astype(int)
        self.df['is_business_hours'] = self.df['hour'].between(9, 17).astype(int)
        
        # Generate time-series features for seasonal analysis
        self._generate_time_series_features()
        
        return len(self.df)
    
    def _generate_time_series_features(self):
        """Generate time series features for anomaly detection"""
        # Daily aggregations
        daily_agg = self.df.groupby(self.df['timestamp_dt'].dt.date).agg({
            'stake_real_money': ['sum', 'mean', 'count'],
            'payout_base_win': ['sum', 'mean'],
            'GGR': ['sum', 'mean'],
            'operator_id': 'nunique'
        })
        
        # Flatten column names
        daily_agg.columns = ['_'.join(col).strip() for col in daily_agg.columns.values]
        daily_agg = daily_agg.reset_index()
        
        # Calculate rolling statistics
        for col in ['stake_real_money_sum', 'payout_base_win_sum', 'GGR_sum']:
            daily_agg[f'{col}_ma_7'] = daily_agg[col].rolling(window=7, min_periods=1).mean()
            daily_agg[f'{col}_ma_30'] = daily_agg[col].rolling(window=30, min_periods=1).mean()
            daily_agg[f'{col}_volatility'] = daily_agg[col].rolling(window=7, min_periods=1).std()
        
        self.time_series_features = daily_agg
    
    def detect_statistical_anomalies(self) -> List[Dict]:
        """Enhanced statistical anomaly detection using multiple algorithms"""
        features = ['stake_real_money', 'payout_base_win', 'GGR', 'no_of_bets',
                   'stake_to_payout_ratio', 'win_rate', 'avg_bet_size', 'revenue_per_transaction',
                   'ggr_margin', 'refund_rate', 'hour', 'day_of_week', 'is_weekend']
        
        X = self.df[features].replace([np.inf, -np.inf], 0).fillna(0)
        X_scaled = self.scaler.fit_transform(X)
        
        # Apply PCA for dimensionality reduction
        X_pca = self.pca.fit_transform(X_scaled)
        
        # Multiple anomaly detection algorithms
        # 1. Isolation Forest
        self.isolation_forest = IsolationForest(contamination=0.1, random_state=42)
        isolation_scores = self.isolation_forest.fit_predict(X_scaled)
        isolation_proba = self.isolation_forest.score_samples(X_scaled)
        
        # 2. One-Class SVM
        self.one_class_svm = OneClassSVM(nu=0.1, kernel='rbf', gamma='scale')
        svm_scores = self.one_class_svm.fit_predict(X_pca)
        
        # 3. DBSCAN for clustering-based anomaly detection
        self.dbscan = DBSCAN(eps=0.5, min_samples=5)
        cluster_labels = self.dbscan.fit_predict(X_pca)
        
        # 4. Statistical Z-score method
        z_scores = np.abs(stats.zscore(X_scaled, axis=0))
        z_anomalies = (z_scores > 3).any(axis=1)
        
        anomalies = []
        for idx in range(len(self.df)):
            # Combine scores from different methods
            isolation_anomaly = isolation_scores[idx] == -1
            svm_anomaly = svm_scores[idx] == -1
            cluster_anomaly = cluster_labels[idx] == -1
            z_anomaly = z_anomalies[idx]
            
            # Calculate ensemble anomaly score
            ensemble_score = (
                (isolation_anomaly * 0.3) + 
                (svm_anomaly * 0.3) + 
                (cluster_anomaly * 0.2) + 
                (z_anomaly * 0.2)
            )
            
            if ensemble_score > 0.5:  # Threshold for anomaly detection
                risk_score = ensemble_score
                if isolation_anomaly:
                    risk_score = 1 - ((isolation_proba[idx] - isolation_proba.min()) / 
                                    (isolation_proba.max() - isolation_proba.min()))
                
                anomalies.append({
                    'transaction_id': self.df.iloc[idx]['report_id'],
                    'operator_id': self.df.iloc[idx]['operator_id'],
                    'risk_score': float(risk_score),
                    'anomaly_type': 'statistical_ensemble',
                    'detection_methods': {
                        'isolation_forest': bool(isolation_anomaly),
                        'one_class_svm': bool(svm_anomaly),
                        'dbscan': bool(cluster_anomaly),
                        'z_score': bool(z_anomaly)
                    },
                    'features': {feat: float(self.df.iloc[idx][feat]) for feat in features},
                    'timestamp': self.df.iloc[idx]['timestamp_end']
                })
        
        return anomalies
    
    def detect_behavioral_patterns(self) -> List[Dict]:
        """Detect suspicious behavioral patterns"""
        suspicious_patterns = []
        
        # Group by operator for pattern analysis
        operator_stats = self.df.groupby('operator_id').agg({
            'stake_real_money': ['sum', 'mean', 'std'],
            'payout_base_win': ['sum', 'mean'],
            'GGR': ['sum', 'mean'],
            'no_of_bets': ['sum', 'mean'],
            'win_rate': 'mean',
            'avg_bet_size': 'mean'
        }).reset_index()
        
        operator_stats.columns = ['_'.join(col).strip() if col[1] else col[0] for col in operator_stats.columns]
        
        # Detect unusual win rates
        win_rate_threshold = operator_stats['win_rate_mean'].quantile(0.95)
        high_win_rate_operators = operator_stats[operator_stats['win_rate_mean'] > win_rate_threshold]
        
        for _, row in high_win_rate_operators.iterrows():
            operator_id = row['operator_id_']
            suspicious_patterns.append({
                'operator_id': operator_id,
                'pattern_type': 'unusual_win_rate',
                'risk_score': min(row['win_rate_mean'] * 1.5, 1.0),
                'details': {
                    'win_rate': float(row['win_rate_mean']),
                    'threshold': float(win_rate_threshold)
                }
            })
        
        # Detect unusual betting amounts
        stake_threshold = operator_stats['stake_real_money_mean'].quantile(0.95)
        high_stake_operators = operator_stats[operator_stats['stake_real_money_mean'] > stake_threshold]
        
        for _, row in high_stake_operators.iterrows():
            operator_id = row['operator_id_']
            if operator_id not in [p['operator_id'] for p in suspicious_patterns]:
                suspicious_patterns.append({
                    'operator_id': operator_id,
                    'pattern_type': 'unusual_stake_amount',
                    'risk_score': 0.7,
                    'details': {
                        'avg_stake': float(row['stake_real_money_mean']),
                        'threshold': float(stake_threshold)
                    }
                })
        
        return suspicious_patterns
    
    def detect_temporal_anomalies(self) -> List[Dict]:
        """Enhanced time-series anomaly detection"""
        temporal_anomalies = []
        
        if self.time_series_features is None:
            self._generate_time_series_features()
        
        # 1. Unusual activity hours detection
        unusual_hour_transactions = self.df[
            (self.df['hour'].between(2, 5)) & (self.df['stake_real_money'] > 0)
        ]
        
        # 2. Weekend vs weekday anomalies
        weekend_stats = self.df[self.df['is_weekend'] == 1].groupby('operator_id')['stake_real_money'].agg(['mean', 'std'])
        weekday_stats = self.df[self.df['is_weekend'] == 0].groupby('operator_id')['stake_real_money'].agg(['mean', 'std'])
        
        # 3. Seasonal pattern anomalies using time series features
        if len(self.time_series_features) > 7:
            for col in ['stake_real_money_sum', 'payout_base_win_sum', 'GGR_sum']:
                ts_data = self.time_series_features[col].dropna()
                if len(ts_data) > 0:
                    # Detect anomalies using statistical methods
                    Q1 = ts_data.quantile(0.25)
                    Q3 = ts_data.quantile(0.75)
                    IQR = Q3 - Q1
                    lower_bound = Q1 - 2.5 * IQR
                    upper_bound = Q3 + 2.5 * IQR
                    
                    anomalous_dates = self.time_series_features[
                        (self.time_series_features[col] < lower_bound) | 
                        (self.time_series_features[col] > upper_bound)
                    ]['timestamp_dt'].tolist()
                    
                    for anomalous_date in anomalous_dates:
                        anomalous_rows = self.time_series_features[
                            self.time_series_features['timestamp_dt'] == anomalous_date
                        ]
                        value = float(anomalous_rows[col].iloc[0]) if len(anomalous_rows) > 0 else 0
                        
                        temporal_anomalies.append({
                            'transaction_id': f'daily_anomaly_{anomalous_date}_{col}',
                            'operator_id': 'system_wide',
                            'anomaly_type': f'seasonal_{col}',
                            'risk_score': 0.8,
                            'details': {
                                'date': str(anomalous_date),
                                'metric': col,
                                'value': value,
                                'upper_bound': float(upper_bound),
                                'lower_bound': float(lower_bound)
                            },
                            'timestamp': str(anomalous_date)
                        })
        
        # 4. Velocity-based anomalies (rapid changes in stakes/payouts)
        operator_velocity = self.df.groupby(['operator_id', self.df['timestamp_dt'].dt.date]).agg({
            'stake_real_money': 'sum',
            'payout_base_win': 'sum'
        }).reset_index()
        
        for operator in operator_velocity['operator_id'].unique():
            op_data = operator_velocity[operator_velocity['operator_id'] == operator].sort_values('timestamp_dt')
            if len(op_data) > 1:
                # Calculate daily changes
                op_data['stake_change'] = op_data['stake_real_money'].pct_change()
                op_data['payout_change'] = op_data['payout_base_win'].pct_change()
                
                # Flag rapid increases (> 500% in one day)
                rapid_changes = op_data[
                    (op_data['stake_change'] > 5.0) | (op_data['payout_change'] > 5.0)
                ]
                
                for _, change_row in rapid_changes.iterrows():
                    temporal_anomalies.append({
                        'transaction_id': f'velocity_{operator}_{change_row["timestamp_dt"]}',
                        'operator_id': operator,
                        'anomaly_type': 'velocity_anomaly',
                        'risk_score': 0.9,
                        'details': {
                            'date': str(change_row['timestamp_dt']),
                            'stake_change_pct': float(change_row['stake_change'] * 100) if not np.isnan(change_row['stake_change']) else 0,
                            'payout_change_pct': float(change_row['payout_change'] * 100) if not np.isnan(change_row['payout_change']) else 0
                        },
                        'timestamp': str(change_row['timestamp_dt'])
                    })
        
        # Add unusual hour transactions
        for _, row in unusual_hour_transactions.iterrows():
            temporal_anomalies.append({
                'transaction_id': row['report_id'],
                'operator_id': row['operator_id'],
                'anomaly_type': 'unusual_timing',
                'risk_score': 0.6,
                'details': {
                    'hour': int(row['hour']),
                    'stake_amount': float(row['stake_real_money'])
                },
                'timestamp': row['timestamp_end']
            })
        
        return temporal_anomalies
    
    def get_real_time_risk_metrics(self) -> Dict:
        """Calculate real-time risk metrics"""
        if self.df is None:
            return {}
        
        total_transactions = len(self.df)
        high_risk_count = len(self.df[self.df['stake_real_money'] > self.df['stake_real_money'].quantile(0.9)])
        
        metrics = {
            'total_transactions': total_transactions,
            'high_risk_transactions': high_risk_count,
            'risk_percentage': (high_risk_count / total_transactions) * 100 if total_transactions > 0 else 0,
            'total_stakes': float(self.df['stake_real_money'].sum()),
            'total_payouts': float(self.df['payout_base_win'].sum()),
            'total_ggr': float(self.df['GGR'].sum()),
            'operators_count': self.df['operator_id'].nunique(),
            'avg_win_rate': float(self.df['win_rate'].mean()),
            'suspicious_operators': self.df[self.df['win_rate'] > 0.8]['operator_id'].nunique()
        }
        
        return metrics

fraud_engine = FraudDetectionEngine()

class FraudAlert(BaseModel):
    transaction_id: str
    operator_id: str
    risk_score: float
    anomaly_type: str
    timestamp: str
    details: Dict[str, Any]

class RiskMetrics(BaseModel):
    total_transactions: int
    high_risk_transactions: int
    risk_percentage: float
    total_stakes: float
    total_payouts: float
    total_ggr: float
    operators_count: int
    avg_win_rate: float
    suspicious_operators: int

@app.on_event("startup")
async def startup_event():
    """Initialize fraud detection system on startup"""
    try:
        data_loaded = fraud_engine.load_data("lotterries_processed.csv")
        print(f"Loaded {data_loaded} transactions for fraud analysis")
    except Exception as e:
        print(f"Error loading data: {e}")

@app.get("/")
async def root():
    return {"message": "Gaming Fraud Detection API", "status": "active"}

@app.get("/fraud/detect", response_model=List[FraudAlert])
async def detect_fraud():
    """Run comprehensive fraud detection analysis"""
    try:
        if fraud_engine.df is None:
            raise HTTPException(status_code=503, detail="Fraud detection system not initialized")
            
        all_anomalies = []
        logger.info("Starting fraud detection analysis")
        
        # Statistical anomalies
        try:
            logger.info("Running statistical anomaly detection")
            statistical = fraud_engine.detect_statistical_anomalies()
            logger.info(f"Found {len(statistical)} statistical anomalies")
            
            for anomaly in statistical:
                all_anomalies.append(FraudAlert(
                    transaction_id=str(anomaly['transaction_id']),
                    operator_id=str(anomaly['operator_id']),
                    risk_score=float(anomaly['risk_score']),
                    anomaly_type=str(anomaly['anomaly_type']),
                    timestamp=str(anomaly['timestamp']),
                    details=anomaly.get('features', {})
                ))
        except Exception as e:
            logger.error(f"Error in statistical anomaly detection: {e}")
            # Continue with other detection methods
        
        # Behavioral patterns
        try:
            logger.info("Running behavioral pattern detection")
            behavioral = fraud_engine.detect_behavioral_patterns()
            logger.info(f"Found {len(behavioral)} behavioral patterns")
            
            for pattern in behavioral:
                all_anomalies.append(FraudAlert(
                    transaction_id=f"pattern_{pattern['operator_id']}",
                    operator_id=str(pattern['operator_id']),
                    risk_score=float(pattern['risk_score']),
                    anomaly_type=str(pattern['pattern_type']),
                    timestamp=datetime.now().isoformat(),
                    details=pattern['details']
                ))
        except Exception as e:
            logger.error(f"Error in behavioral pattern detection: {e}")
            # Continue with other detection methods
        
        # Temporal anomalies
        try:
            logger.info("Running temporal anomaly detection")
            temporal = fraud_engine.detect_temporal_anomalies()
            logger.info(f"Found {len(temporal)} temporal anomalies")
            
            for anomaly in temporal:
                all_anomalies.append(FraudAlert(
                    transaction_id=str(anomaly['transaction_id']),
                    operator_id=str(anomaly['operator_id']),
                    risk_score=float(anomaly['risk_score']),
                    anomaly_type=str(anomaly['anomaly_type']),
                    timestamp=str(anomaly['timestamp']),
                    details=anomaly['details']
                ))
        except Exception as e:
            logger.error(f"Error in temporal anomaly detection: {e}")
            # Continue with other detection methods
        
        logger.info(f"Total anomalies found: {len(all_anomalies)}")
        return sorted(all_anomalies, key=lambda x: x.risk_score, reverse=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in fraud detection: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error detecting fraud: {str(e)}")

@app.get("/fraud/metrics", response_model=RiskMetrics)
async def get_risk_metrics():
    """Get real-time risk metrics"""
    try:
        metrics = fraud_engine.get_real_time_risk_metrics()
        return RiskMetrics(**metrics)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting metrics: {str(e)}")

@app.get("/fraud/operators/{operator_id}")
async def get_operator_risk_profile(operator_id: str):
    """Get detailed risk profile for specific operator"""
    try:
        operator_data = fraud_engine.df[fraud_engine.df['operator_id'] == operator_id]
        
        if operator_data.empty:
            raise HTTPException(status_code=404, detail="Operator not found")
        
        profile = {
            'operator_id': operator_id,
            'total_transactions': len(operator_data),
            'total_stakes': float(operator_data['stake_real_money'].sum()),
            'total_payouts': float(operator_data['payout_base_win'].sum()),
            'win_rate': float(operator_data['win_rate'].mean()),
            'avg_bet_size': float(operator_data['avg_bet_size'].mean()),
            'ggr': float(operator_data['GGR'].sum()),
            'risk_indicators': {
                'high_win_rate': float(operator_data['win_rate'].mean()) > 0.8,
                'unusual_stake_patterns': float(operator_data['stake_real_money'].std()) > operator_data['stake_real_money'].mean(),
                'negative_ggr': any(operator_data['GGR'] < 0)
            }
        }
        
        return profile
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting operator profile: {str(e)}")

@app.get("/fraud/trends")
async def get_fraud_trends():
    """Get fraud trends over time"""
    try:
        df = fraud_engine.df.copy()
        df['timestamp_dt'] = pd.to_datetime(df['timestamp_end'])
        df['date'] = df['timestamp_dt'].dt.date
        
        daily_trends = df.groupby('date').agg({
            'stake_real_money': 'sum',
            'payout_base_win': 'sum',
            'GGR': 'sum',
            'no_of_bets': 'sum',
            'operator_id': 'nunique'
        }).reset_index()
        
        trends = []
        for _, row in daily_trends.iterrows():
            trends.append({
                'date': row['date'].isoformat(),
                'total_stakes': float(row['stake_real_money']),
                'total_payouts': float(row['payout_base_win']),
                'ggr': float(row['GGR']),
                'total_bets': int(row['no_of_bets']),
                'active_operators': int(row['operator_id'])
            })
        
        return {'trends': trends}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting trends: {str(e)}")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)