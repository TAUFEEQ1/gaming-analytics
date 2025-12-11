# Gaming Fraud Detection System

A comprehensive real-time fraud detection system for gaming/lottery transactions using state-of-the-art machine learning algorithms based on recent research papers (2023-2024).

## 🎯 Features

### Advanced Fraud Detection Algorithms
- **Isolation Forest**: Anomaly detection using ensemble of isolation trees (98.72% efficiency)
- **DBSCAN Clustering**: Density-based spatial clustering for fraud group identification
- **Local Outlier Factor (LOF)**: Local density-based anomaly detection
- **LSTM Autoencoder**: Neural network for temporal sequence anomaly detection
- **Ensemble Method**: Combines all algorithms with weighted scoring

### Real-Time Analytics
- Live fraud detection with risk scoring
- Behavioral pattern analysis
- Temporal anomaly detection
- Operator risk profiling
- Interactive dashboard with real-time updates

### Key Risk Indicators
- Unusual win rates (>80% threshold)
- Suspicious stake-to-payout ratios
- Temporal patterns (night/weekend activity)
- Perfect win rate detection
- Negative GGR patterns
- Transaction density anomalies

## 📊 Dataset

The system analyzes `lotterries_processed.csv` with 15,365+ gaming transactions containing:
- Operator information
- Stake amounts and payouts
- Win/loss ratios
- Transaction timestamps
- Game categories
- Revenue metrics (GGR)

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Required packages (see requirements.txt)

### Installation & Running
```bash
# Clone or download the fraud detection system
# Ensure lotterries_processed.csv is in the directory

# Run the complete system (recommended)
python run_fraud_detection.py full

# Or run specific components
python run_fraud_detection.py basic      # Basic API only
python run_fraud_detection.py enhanced   # Enhanced API only
python run_fraud_detection.py test       # Run tests only
```

### Manual Setup
```bash
# Install requirements
pip install -r requirements.txt

# Start basic API (Terminal 1)
python fraud_detection_api.py

# Start enhanced API (Terminal 2) 
python enhanced_fraud_detection.py

# Open dashboard
open fraud_dashboard.html

# Run tests
python test_fraud_detection.py
```

## 🌐 API Endpoints

### Basic Fraud Detection API (Port 8000)
- `GET /fraud/detect` - Run fraud detection analysis
- `GET /fraud/metrics` - Get real-time risk metrics  
- `GET /fraud/operators/{id}` - Get operator risk profile
- `GET /fraud/trends` - Get fraud trends over time
- `GET /docs` - Interactive API documentation

### Enhanced Fraud Detection API (Port 8001)
- `GET /fraud/detect/enhanced` - Run ensemble fraud detection
- `GET /fraud/metrics/enhanced` - Get enhanced risk metrics
- `GET /fraud/models/performance` - Get model performance metrics
- `GET /docs` - Interactive API documentation

## 📈 Dashboard Features

The real-time dashboard (`fraud_dashboard.html`) provides:

### Key Metrics Cards
- Total transactions count
- Risk percentage
- Total GGR (Gross Gaming Revenue)
- Suspicious operators count

### Visualizations
- **Risk Distribution**: Doughnut chart showing risk levels
- **Daily Trends**: Line chart of stakes vs payouts over time
- **Fraud Alerts**: Real-time alert feed with risk scoring

### Auto-Refresh
- Updates every 30 seconds
- Real-time fraud alerts
- Live risk metrics

## 🧠 Machine Learning Models

### 1. Isolation Forest
- **Purpose**: Statistical anomaly detection
- **Parameters**: 8% contamination rate, 200 estimators
- **Features**: Stakes, payouts, win rates, transaction patterns

### 2. DBSCAN Clustering  
- **Purpose**: Group identification and outlier detection
- **Parameters**: Adaptive eps/min_samples based on silhouette score
- **Output**: Suspicious clusters with high win rates

### 3. LSTM Autoencoder
- **Purpose**: Temporal sequence anomaly detection
- **Architecture**: 24-hour time series windows
- **Features**: Temporal patterns with cyclical encoding

### 4. Local Outlier Factor
- **Purpose**: Local density-based anomaly detection
- **Parameters**: 20 neighbors, 10% contamination
- **Strength**: Detects local anomalies in operator behavior

### 5. Ensemble Method
- **Weighted Scoring**: Combines all model outputs
- **Weights**: Isolation Forest (30%), LSTM (30%), DBSCAN (20%), LOF (20%)
- **Agreement Bonus**: Higher scores when multiple models agree

## 📊 Risk Assessment

### Risk Levels
- **Very High** (90%+): Critical fraud indicators
- **High** (75-89%): Strong fraud signals  
- **Medium** (50-74%): Moderate risk patterns
- **Low** (<50%): Minor anomalies

### Fraud Indicators
1. **Perfect Win Rates** (≥95%)
2. **Unusual Stakes** (>95th percentile)
3. **Zero Loss Patterns** (GGR ≤ 0)
4. **Night Activity** (2-5 AM transactions)
5. **Cluster Outliers** (Isolated operators)

## 🔬 Research Foundation

Based on recent academic research (2023-2024):
- "Using Artificial Intelligence Algorithms to Predict Problem Gambling" (83% AUC)
- "Illegal Online Gambling Site Detection using ML" (11,172 sites analyzed)  
- "Detection of Problem Gambling with Less Features" (arXiv 2024)
- "Comprehensive Investigation of Anomaly Detection Methods" (Wiley 2024)

## 🧪 Testing

The test suite (`test_fraud_detection.py`) validates:
- API connectivity and responses
- Fraud detection functionality
- Risk metrics calculation
- Operator profiling
- Dashboard data feeds
- Model performance tracking

### Running Tests
```bash
python test_fraud_detection.py
```

Expected output shows test results for all components with success rates.

## 📁 File Structure
```
fraud-detection-system/
├── fraud_detection_api.py          # Basic API with core algorithms
├── enhanced_fraud_detection.py     # Advanced API with ensemble methods
├── fraud_dashboard.html            # Real-time analytics dashboard  
├── test_fraud_detection.py         # Comprehensive test suite
├── run_fraud_detection.py          # System runner and manager
├── requirements.txt                # Python dependencies
├── lotterries_processed.csv        # Gaming transaction dataset
└── README.md                       # This documentation
```

## 🔧 Configuration

### Model Parameters
- **Isolation Forest**: 8% contamination, 200 estimators
- **DBSCAN**: Adaptive parameters via silhouette optimization
- **LSTM**: 24-hour windows, 50 epochs training
- **Risk Thresholds**: Configurable in risk_thresholds dict

### Performance Tuning
- Adjust contamination rates based on expected fraud percentage
- Modify time series windows for different temporal patterns
- Tune ensemble weights based on model performance

## 🚨 Alerts & Monitoring

### Alert Types
1. **Statistical**: Isolation Forest anomalies
2. **Behavioral**: Unusual operator patterns  
3. **Temporal**: Time-based suspicious activity
4. **Cluster**: Group-based fraud detection
5. **Ensemble**: Multi-algorithm consensus

### Real-Time Features
- Auto-refresh every 30 seconds
- Color-coded risk levels
- Operator-specific risk profiles
- Historical trend analysis

## 🔐 Security

- No sensitive data exposure in logs
- API-only access to fraud detection
- Read-only dashboard implementation
- No data modification capabilities

## 📞 Support

For issues or questions:
- Check the test suite output for diagnostics
- Review API documentation at `/docs` endpoints  
- Examine model performance metrics
- Validate data file format and completeness

## 🎉 Success Metrics

A successful deployment will show:
- ✅ All API tests passing (≥80% success rate)
- ✅ Real-time dashboard loading with data
- ✅ Fraud alerts being generated
- ✅ Model performance metrics updating
- ✅ Risk percentages within expected ranges

The system is now ready for real-time gaming fraud detection!