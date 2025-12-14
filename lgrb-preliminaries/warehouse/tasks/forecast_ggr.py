"""
Time-series forecasting for GGR to study broad patterns over time.

This task:
1. Determines optimal lag using autocorrelation analysis
2. Builds autoregressive model with num_operators as exogenous variable
3. Compares expected vs actual GGR for each day
4. Interpolates missing days (if needed)
5. Analyzes trends and patterns in GGR over time
"""
import luigi
import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Try to import time-series libraries
try:
    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import acf, pacf
    from statsmodels.tsa.ar_model import AutoReg
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    print("Warning: statsmodels not available. Install with: pip install statsmodels")

try:
    from sklearn.linear_model import LinearRegression
    from sklearn.preprocessing import StandardScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error
    from sklearn.ensemble import IsolationForest
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except ImportError:
    XGBOOST_AVAILABLE = False
    print("Warning: xgboost not available. Install with: pip install xgboost")


class ForecastGGR(luigi.Task):
    """
    Time-series forecasting for GGR to understand broad patterns over time.
    Uses autoregression with num_operators as exogenous variable.
    """
    
    model_type = luigi.Parameter(default='autoregression')  # Options: autoregression, exponential_smoothing, arima, linear_trend
    max_lag = luigi.IntParameter(default=30)  # Maximum lag to test
    use_xgboost = luigi.BoolParameter(default=True)  # Use XGBoost instead of linear regression
    
    def requires(self):
        from warehouse.tasks.prepare_ggr_timeseries import PrepareGGRTimeSeries
        return PrepareGGRTimeSeries()
    
    def output(self):
        return {
            'forecast_results': luigi.LocalTarget('warehouse/data/ggr_forecast_results.csv'),
            'forecast_parquet': luigi.LocalTarget('warehouse/data/ggr_forecast.parquet'),
            'model_performance': luigi.LocalTarget('warehouse/data/ggr_model_performance.txt'),
            'expected_vs_actual': luigi.LocalTarget('warehouse/data/ggr_expected_vs_actual.csv'),
            'lag_analysis': luigi.LocalTarget('warehouse/data/ggr_lag_analysis.txt')
        }
    
    def run(self):
        # Load time-series data
        df = pd.read_csv(self.requires().output()['ggr_timeseries'].path)
        df['date'] = pd.to_datetime(df['date'])
        
        print(f"\n{'='*80}")
        print("GGR TIME-SERIES FORECASTING")
        print(f"{'='*80}")
        print(f"Model type: {self.model_type}")
        print(f"Total days: {len(df)}")
        print(f"Days with data: {(~df['GGR'].isna()).sum()}")
        print(f"Missing days: {df['GGR'].isna().sum()}")
        
        # First, interpolate missing values for continuous time-series
        df_interpolated = self._interpolate_missing_days(df)
        
        # Perform lag analysis to determine optimal lag
        optimal_lag, lag_report = self._analyze_lag(df_interpolated)
        
        # Save lag analysis
        with open(self.output()['lag_analysis'].path, 'w') as f:
            f.write(lag_report)
        
        # Build time-series model and generate expected GGR
        df_with_forecast = self._build_forecast_model(df_interpolated, optimal_lag)
        
        # Calculate expected vs actual comparison
        comparison_df = self._calculate_expected_vs_actual(df_with_forecast, df)
        
        # Detect anomalies using Isolation Forest
        comparison_df = self._detect_anomalies(comparison_df)
        
        # Evaluate model performance
        performance_report = self._evaluate_performance(comparison_df)
        
        # Save results
        df_with_forecast.to_csv(self.output()['forecast_results'].path, index=False)
        comparison_df.to_csv(self.output()['expected_vs_actual'].path, index=False)
        
        with open(self.output()['model_performance'].path, 'w') as f:
            f.write(performance_report)
        # Create parquet file with required columns
        parquet_df = df[['date', 'GGR', 'total_stake', 'total_payout', 'total_bets', 'operators_list']].copy()
        parquet_df['expected_GGR'] = df_with_forecast['expected_GGR']
        parquet_df['is_anomaly'] = comparison_df['is_anomaly']
        parquet_df['anomaly_score'] = comparison_df['anomaly_score']
        
        # Reorder columns for clarity
        parquet_df = parquet_df[['date', 'GGR', 'expected_GGR', 'is_anomaly', 'anomaly_score', 'total_stake', 'total_payout', 'total_bets', 'operators_list']]
        
        # Save as parquet
        parquet_df.to_parquet(self.output()['forecast_parquet'].path, index=False, engine='pyarrow')
        
        print(f"\n{'='*80}")
        print("FORECASTING COMPLETE")
        print(f"{'='*80}")
        print(f"✓ Forecast results CSV: {self.output()['forecast_results'].path}")
        print(f"✓ Forecast parquet: {self.output()['forecast_parquet'].path}")
        print(f"✓ Expected vs Actual: {self.output()['expected_vs_actual'].path}")
        print(f"✓ Model performance: {self.output()['model_performance'].path}")
    
    def _interpolate_missing_days(self, df):
        """Interpolate missing GGR values"""
        
        print("\nInterpolating missing days...")
        
        df_interp = df.copy()
        
        # Linear interpolation for missing values
        df_interp['GGR_interpolated'] = df_interp['GGR'].interpolate(method='linear', limit_direction='both')
        
        # If still have NaN (e.g., at edges), fill with mean
        mean_ggr = df_interp['GGR'].mean()
        df_interp['GGR_interpolated'] = df_interp['GGR_interpolated'].fillna(mean_ggr)
        
        # Track which values were interpolated
        df_interp['was_interpolated'] = df_interp['GGR'].isna().astype(int)
        
        interpolated_count = df_interp['was_interpolated'].sum()
        print(f"  Interpolated {interpolated_count} missing days")
        
        return df_interp
    
    def _analyze_lag(self, df):
        """Determine optimal lag using ACF/PACF analysis"""
        
        print(f"\nAnalyzing optimal lag (max_lag={self.max_lag})...")
        
        ggr_series = df['GGR_interpolated'].values
        
        if not STATSMODELS_AVAILABLE:
            print("  statsmodels not available, using default lag=7")
            return 7, "Lag analysis requires statsmodels"
        
        # Calculate ACF and PACF
        acf_values = acf(ggr_series, nlags=self.max_lag, fft=False)
        pacf_values = pacf(ggr_series, nlags=self.max_lag)
        
        # Find optimal lag where ACF drops below significance (0.2 threshold)
        significant_lags = np.where(np.abs(acf_values[1:]) > 0.2)[0] + 1
        
        if len(significant_lags) > 0:
            optimal_lag = int(significant_lags[-1])  # Last significant lag
        else:
            optimal_lag = 7  # Default to weekly pattern
        
        # Limit to reasonable range
        optimal_lag = min(optimal_lag, 14)  # Cap at 2 weeks
        optimal_lag = max(optimal_lag, 1)   # At least 1 day
        
        print(f"  Optimal lag determined: {optimal_lag} days")
        
        # Generate report
        report = f"""
{'='*80}
LAG ANALYSIS FOR GGR TIME-SERIES
{'='*80}

AUTOCORRELATION FUNCTION (ACF):
  Maximum lag tested: {self.max_lag}
  Optimal lag selected: {optimal_lag} days
  
ACF VALUES (first 14 lags):
"""
        for i in range(1, min(15, len(acf_values))):
            significance = "***" if abs(acf_values[i]) > 0.2 else "   "
            report += f"  Lag {i:2d}: {acf_values[i]:7.4f} {significance}\n"
        
        report += f"""
PARTIAL AUTOCORRELATION FUNCTION (PACF):
  PACF indicates direct correlation after removing indirect effects
  
PACF VALUES (first 14 lags):
"""
        for i in range(1, min(15, len(pacf_values))):
            significance = "***" if abs(pacf_values[i]) > 0.2 else "   "
            report += f"  Lag {i:2d}: {pacf_values[i]:7.4f} {significance}\n"
        
        report += f"""
INTERPRETATION:
  - Optimal lag of {optimal_lag} days suggests GGR has memory of approximately {optimal_lag} days
  - Significant ACF values (>0.2) indicate correlation with past values
  - This lag will be used in the autoregressive model
  
{'='*80}
"""
        
        print(report)
        return optimal_lag, report
    
    def _build_forecast_model(self, df, optimal_lag):
        """Build time-series forecasting model with optimal lag"""
        
        print(f"\nBuilding {self.model_type} model with lag={optimal_lag}...")
        
        # Use interpolated GGR for model training
        ggr_series = df['GGR_interpolated'].values
        num_operators = df['num_operators'].values
        total_bets = df['total_bets'].values
        total_stake = df['total_stake'].values if 'total_stake' in df.columns else None
        total_payout = df['total_payout'].values if 'total_payout' in df.columns else None
        
        # Encode game_type as numeric (one-hot encode all actual types)
        game_type_dummies = pd.get_dummies(df['modal_game_type'], prefix='game', drop_first=True)
        game_type_encoded = game_type_dummies.values
        
        print(f"  Game types encoded: {list(game_type_dummies.columns)}")
        
        if self.model_type == 'autoregression' and STATSMODELS_AVAILABLE and SKLEARN_AVAILABLE:
            expected_ggr = self._autoregression_with_exog(ggr_series, num_operators, total_bets, game_type_encoded, optimal_lag, total_stake, total_payout, use_xgboost=self.use_xgboost)
        elif self.model_type == 'exponential_smoothing' and STATSMODELS_AVAILABLE:
            expected_ggr = self._exponential_smoothing_forecast(ggr_series)
        elif self.model_type == 'arima' and STATSMODELS_AVAILABLE:
            expected_ggr = self._arima_forecast(ggr_series)
        else:
            # Fallback to simple linear trend
            print("  Using linear trend (fallback)")
            expected_ggr = self._linear_trend_forecast(ggr_series)
        
        df['expected_GGR'] = expected_ggr
        
        return df
    
    def _autoregression_with_exog(self, ggr_series, num_operators, total_bets, game_type_encoded, lag, total_stake=None, total_payout=None, use_xgboost=False):
        """Autoregressive model with multiple exogenous variables including lagged stake/payout"""
        
        model_name = "XGBoost" if use_xgboost else "Linear Regression"
        print(f"  Training AR({lag}) model with {model_name}: num_operators, total_bets, lagged stake/payout, game_type, day-of-week...")
        
        # Create lagged features
        n = len(ggr_series)
        X = []
        y = []
        exog = []
        
        for i in range(lag, n):
            # Lagged GGR values
            lag_features = [ggr_series[i-j] for j in range(1, lag+1)]
            X.append(lag_features)
            
            # Target
            y.append(ggr_series[i])
            
            # Exogenous variables: num_operators, total_bets, day of week, game_type dummies
            day_of_week = i % 7  # Simple day index
            is_weekend = 1 if day_of_week in [5, 6] else 0  # Saturday=5, Sunday=6
            exog_row = [num_operators[i], total_bets[i], is_weekend, day_of_week]
            exog_row.extend(game_type_encoded[i].tolist())  # Add all game type indicators
            
            # Note: Lagged stake/payout are redundant with lagged GGR since GGR = stake - payout
            # Keeping them commented out to avoid collinearity
            # if total_stake is not None and i > 0:
            #     exog_row.append(total_stake[i-1])  # Lagged stake
            # if total_payout is not None and i > 0:
            #     exog_row.append(total_payout[i-1])  # Lagged payout
            
            exog.append(exog_row)
        
        X = np.array(X)
        y = np.array(y)
        exog = np.array(exog)
        
        # Combine lag features with exogenous variables
        X_full = np.hstack([X, exog])
        
        # Train model (XGBoost or Linear Regression)
        if use_xgboost and XGBOOST_AVAILABLE:
            model = XGBRegressor(
                n_estimators=100,
                max_depth=6,
                learning_rate=0.1,
                random_state=42,
                verbosity=0
            )
            model.fit(X_full, y)
        else:
            model = LinearRegression()
            model.fit(X_full, y)
        
        # Generate predictions
        predictions = model.predict(X_full)
        
        # Pad beginning with initial values (where we don't have enough lags)
        expected = np.concatenate([ggr_series[:lag], predictions])
        
        # Calculate R2
        ss_res = np.sum((y - predictions) ** 2)
        ss_tot = np.sum((y - np.mean(y)) ** 2)
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        num_exog = X_full.shape[1] - lag
        num_game_types = num_exog - 4  # Subtract num_operators, total_bets, is_weekend, day_of_week
        print(f"  AR({lag}) {model_name} R2: {r2:.4f}")
        print(f"  Features: {lag} lag terms + {num_exog} exogenous (num_operators, total_bets, is_weekend, day_of_week, {num_game_types} game_type indicators)")
        
        return expected
    
    def _exponential_smoothing_forecast(self, series):
        """Exponential Smoothing forecast (Holt-Winters)"""
        
        try:
            # Fit exponential smoothing model
            model = ExponentialSmoothing(
                series,
                trend='add',
                seasonal=None,  # No seasonality with 1 year of data
                damped_trend=True
            )
            fitted_model = model.fit()
            
            # Get fitted values as "expected" GGR
            expected = fitted_model.fittedvalues
            
            # Handle edge cases where fitted values are shorter
            if len(expected) < len(series):
                # Pad with first/last values
                expected = np.concatenate([
                    np.full(len(series) - len(expected), expected[0]),
                    expected
                ])
            
            print(f"  Exponential smoothing model fitted")
            
            return expected
            
        except Exception as e:
            print(f"  Warning: Exponential smoothing failed ({e}), using linear trend")
            return self._linear_trend_forecast(series)
    
    def _arima_forecast(self, series):
        """ARIMA forecast"""
        
        try:
            # Fit ARIMA model - using simple (1,1,1) as starting point
            model = ARIMA(series, order=(1, 1, 1))
            fitted_model = model.fit()
            
            # Get fitted values
            expected = fitted_model.fittedvalues
            
            # ARIMA fitted values start from order+1, so pad beginning
            if len(expected) < len(series):
                expected = np.concatenate([
                    np.full(len(series) - len(expected), series[0]),
                    expected
                ])
            
            print(f"  ARIMA(1,1,1) model fitted")
            
            return expected
            
        except Exception as e:
            print(f"  Warning: ARIMA failed ({e}), using linear trend")
            return self._linear_trend_forecast(series)
    
    def _linear_trend_forecast(self, series):
        """Simple linear trend forecast"""
        
        # Create time index
        X = np.arange(len(series)).reshape(-1, 1)
        y = series
        
        # Fit linear regression
        if SKLEARN_AVAILABLE:
            model = LinearRegression()
            model.fit(X, y)
            expected = model.predict(X)
        else:
            # Simple numpy-based linear fit
            coeffs = np.polyfit(X.flatten(), y, 1)
            expected = np.polyval(coeffs, X.flatten())
        
        print(f"  Linear trend model fitted")
        
        return expected
    
    def _calculate_expected_vs_actual(self, df_forecast, df_original):
        """Calculate expected vs actual comparison"""
        
        print("\nCalculating expected vs actual comparison...")
        
        comparison = df_forecast[['date', 'expected_GGR', 'was_interpolated']].copy()
        
        # Use original GGR (not interpolated) for actual values
        comparison['actual_GGR'] = df_original['GGR']
        comparison['is_missing'] = df_original['is_missing']
        
        # Calculate deviation and percentage difference
        comparison['deviation'] = comparison['actual_GGR'] - comparison['expected_GGR']
        comparison['deviation_pct'] = (comparison['deviation'] / comparison['expected_GGR']) * 100
        
        # Add day of week for pattern analysis
        comparison['day_of_week'] = comparison['date'].dt.day_name()
        comparison['is_weekend'] = comparison['date'].dt.dayofweek.isin([5, 6]).astype(int)
        
        return comparison
    
    def _detect_anomalies(self, comparison_df):
        """Detect anomalous GGR days using Isolation Forest"""
        
        print("\nDetecting anomalies with Isolation Forest...")
        
        if not SKLEARN_AVAILABLE:
            print("  Sklearn not available, skipping anomaly detection")
            comparison_df['is_anomaly'] = 0
            comparison_df['anomaly_score'] = 0.0
            return comparison_df
        
        # Only use days with actual data for anomaly detection
        actual_days = comparison_df[comparison_df['is_missing'] == 0].copy()
        
        if len(actual_days) < 10:
            print("  Not enough data for anomaly detection")
            comparison_df['is_anomaly'] = 0
            comparison_df['anomaly_score'] = 0.0
            return comparison_df
        
        # Features for anomaly detection
        features = []
        feature_names = []
        
        # Deviation from expected (normalized)
        features.append((actual_days['deviation'] / actual_days['expected_GGR']).values.reshape(-1, 1))
        feature_names.append('deviation_pct')
        
        # Absolute deviation
        features.append(actual_days['deviation'].values.reshape(-1, 1))
        feature_names.append('deviation_abs')
        
        # GGR itself (normalized)
        mean_ggr = actual_days['actual_GGR'].mean()
        features.append((actual_days['actual_GGR'] / mean_ggr).values.reshape(-1, 1))
        feature_names.append('ggr_normalized')
        
        # Is weekend
        features.append(actual_days['is_weekend'].values.reshape(-1, 1))
        feature_names.append('is_weekend')
        
        # Combine features
        X = np.hstack(features)
        
        # Train Isolation Forest
        iso_forest = IsolationForest(
            contamination=0.05,  # Expect 5% anomalies
            random_state=42,
            n_estimators=100
        )
        
        predictions = iso_forest.fit_predict(X)
        scores = iso_forest.score_samples(X)
        
        # Add results to actual_days
        actual_days['is_anomaly'] = (predictions == -1).astype(int)
        actual_days['anomaly_score'] = -scores  # Negative scores, higher = more anomalous
        
        # Merge back to full comparison_df
        comparison_df = comparison_df.merge(
            actual_days[['date', 'is_anomaly', 'anomaly_score']],
            on='date',
            how='left'
        )
        
        # Fill missing days with 0
        comparison_df['is_anomaly'] = comparison_df['is_anomaly'].fillna(0).astype(int)
        comparison_df['anomaly_score'] = comparison_df['anomaly_score'].fillna(0.0)
        
        anomaly_count = comparison_df['is_anomaly'].sum()
        print(f"  Detected {anomaly_count} anomalous days ({anomaly_count/len(actual_days)*100:.1f}%)")
        
        # Show top anomalies
        if anomaly_count > 0:
            top_anomalies = comparison_df[comparison_df['is_anomaly'] == 1].nlargest(5, 'anomaly_score')
            print(f"\n  Top 5 anomalies:")
            for _, row in top_anomalies.iterrows():
                print(f"    {row['date'].date()}: GGR={row['actual_GGR']:,.0f}, Expected={row['expected_GGR']:,.0f}, Score={row['anomaly_score']:.3f}")
        
        return comparison_df
    
    def _evaluate_performance(self, comparison_df):
        """Evaluate forecast model performance"""
        
        # Only evaluate on days with actual data
        actual_days = comparison_df[comparison_df['is_missing'] == 0].copy()
        
        if len(actual_days) == 0:
            return "No actual data available for evaluation"
        
        # Calculate metrics
        mae = np.abs(actual_days['deviation']).mean()
        rmse = np.sqrt((actual_days['deviation'] ** 2).mean())
        mape = np.abs(actual_days['deviation_pct']).mean()
        
        # R-squared
        ss_res = (actual_days['deviation'] ** 2).sum()
        ss_tot = ((actual_days['actual_GGR'] - actual_days['actual_GGR'].mean()) ** 2).sum()
        r2 = 1 - (ss_res / ss_tot) if ss_tot > 0 else 0
        
        # Trend analysis
        ggr_trend = np.polyfit(range(len(actual_days)), actual_days['actual_GGR'].values, 1)[0]
        trend_direction = "increasing" if ggr_trend > 0 else "decreasing"
        
        # Weekend vs weekday comparison
        if 'is_weekend' in actual_days.columns:
            weekend_avg = actual_days[actual_days['is_weekend'] == 1]['actual_GGR'].mean()
            weekday_avg = actual_days[actual_days['is_weekend'] == 0]['actual_GGR'].mean()
            weekend_diff_pct = ((weekend_avg - weekday_avg) / weekday_avg * 100) if weekday_avg > 0 else 0
        else:
            weekend_avg = weekday_avg = weekend_diff_pct = 0
        
        mae_fmt = f"{mae:,.2f}"
        rmse_fmt = f"{rmse:,.2f}"
        mape_fmt = f"{mape:.2f}"
        r2_fmt = f"{r2:.4f}"
        mean_dev_fmt = f"{actual_days['deviation'].mean():,.2f}"
        std_dev_fmt = f"{actual_days['deviation'].std():,.2f}"
        min_dev_fmt = f"{actual_days['deviation'].min():,.2f}"
        max_dev_fmt = f"{actual_days['deviation'].max():,.2f}"
        trend_fmt = f"{ggr_trend:,.2f}"
        avg_ggr_fmt = f"{actual_days['actual_GGR'].mean():,.2f}"
        weekend_avg_fmt = f"{weekend_avg:,.2f}"
        weekday_avg_fmt = f"{weekday_avg:,.2f}"
        weekend_diff_fmt = f"{weekend_diff_pct:+.1f}"
        
        report = f"""
{'='*80}
GGR TIME-SERIES ANALYSIS
{'='*80}

MODEL: {self.model_type}

EVALUATION METRICS (on actual data only):
  Days evaluated: {len(actual_days)}
  Mean Absolute Error (MAE): {mae_fmt}
  Root Mean Squared Error (RMSE): {rmse_fmt}
  Mean Absolute Percentage Error (MAPE): {mape_fmt}%
  R-squared: {r2_fmt}

DEVIATION STATISTICS:
  Mean Deviation: {mean_dev_fmt}
  Std Dev of Deviation: {std_dev_fmt}
  Min Deviation: {min_dev_fmt}
  Max Deviation: {max_dev_fmt}

TREND ANALYSIS:
  Overall Trend: {trend_direction.capitalize()} ({trend_fmt} per day)
  Average GGR: {avg_ggr_fmt}
  
PATTERN ANALYSIS:
  Weekend Average GGR: {weekend_avg_fmt}
  Weekday Average GGR: {weekday_avg_fmt}
  Weekend vs Weekday: {weekend_diff_fmt}%

INTERPRETATION:
  - MAPE shows average forecast error as percentage
  - R-squared indicates how well the model explains GGR variance
  - Trend shows long-term GGR direction over time period
  - Pattern analysis reveals day-of-week effects

{'='*80}
"""
        
        print(report)
        return report


if __name__ == '__main__':
    luigi.build([ForecastGGR()], local_scheduler=True, log_level='INFO')
