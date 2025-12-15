# KoTaP: Korean Tax Avoidance Panel Dataset (2011–2024)

## Version

Current release: v1.0 (September 2025)

## Overview

The **KoTaP dataset** provides a long-term firm-level panel of corporate tax avoidance and financial characteristics for all non-financial firms listed on the KOSPI and KOSDAQ markets in Korea from **2011 to 2024**.  
It is designed to treat corporate tax avoidance as a **predictor variable** and link it to multiple domains: profitability, stability, growth, and governance.  

- **Number of observations**: 12,653 firm-year observations  
- **Number of firms**: 1,754 non-financial firms  
- **Format**: CSV (UTF-8 encoded)  
- **Citation**: Please cite as *KoTaP: A Panel Dataset for Corporate Tax Avoidance, Performance, and Governance in Korea (2025, DOI)*  

---

## File Contents

- `KoTaP_Dataset.csv` : Main dataset (firm-year observations, standardized variables)  
- `README.md` (this file): Documentation and variable definitions  
- `Supplementary/` : Supplementary materials (organized by type)  

### Supplementary Structure

```
Supplementary/
│
├── Figures/
│   ├── Figure1_KoTaP_Distributions.png           ← Distribution of key variables
│   ├── Figure2_KoTaP_Correlations.png            ← Correlation heatmap of representative variables
│   ├── Figure3_Comparative_performance.png       ← Comparative performance across prediction tasks
│
├── Tables/
│   ├── Table_S-1_KoTaP_outliers_all.csv          ← Outlier diagnostics for all numeric variables
│   ├── Table_S-2_KoTaP_corr_all.csv              ← Full correlation matrix
│
└── Fundamental_Prediction/
    ├── Source_Code/                              ← Full set of source code used for fundamental prediction experiments
    ├── Table_S-4_integrated_results.docx         ← Integrated results of prediction experiments
    ├── Figure_S-8_results_table.png              ← Tabular summary of prediction results
    ├── Figure_S-7_model_ranking.png              ← Model ranking by performance
    ├── Figure_S-6_feature_importance.png         ← Feature importance analysis
    ├── Figure_S-5_temporal_analysis.png          ← Temporal performance analysis
    ├── Figure_S-4_residual_analysis.png          ← Residual error diagnostics
    ├── Figure_S-3_prediction_quality.png         ← Prediction quality plots
    ├── Figure_S-2_performance_heatmap.png        ← Performance heatmap across targets
    └── Figure_S-1_comprehensive_comparison.png   ← Comprehensive model comparison
```

---

## Variable Categories

The dataset contains 65 variables, organized into five categories:

### 1. Tax Avoidance Indicators
- `CETR`: Cash Effective Tax Rate = Cash Taxes Paid / Pre-tax Income  
- `GETR`: GAAP Effective Tax Rate = Total Tax Expense / Pre-tax Income  
- `TSTA`: Total Book–Tax Difference / Lagged Assets  
- `TSDA`: Discretionary Book–Tax Difference / Lagged Assets  

### 2. Profitability
- `ROA`: Net Income / Lagged Total Assets  
- `ROE`: Net Income / Lagged Equity  
- `CFO`: Operating Cash Flow / Lagged Total Assets  
- `LOSS`: Loss dummy (1 if Net Income < 0)  

### 3. Stability
- `LEV`: Total Liabilities / Total Assets  
- `CUR`: Current Assets / Current Liabilities  
- `SIZE`: ln(Total Assets)  
- `PPE`: Property, Plant & Equipment / Total Assets  
- `AGE`: ln(Firm age in years since establishment)  
- `INVREC`: (Inventory + Receivables) / Total Assets  

### 4. Growth
- `GRW`: Sales Growth Rate  
- `MB`: Market-to-Book Ratio  
- `TQ`: Tobin’s Q  

### 5. Governance
- `KOSPI`: Dummy (1 = KOSPI, 0 = KOSDAQ)  
- `BIG4`: Dummy (1 = audited by Big4)  
- `FORN`: Foreign Ownership (share, 0–1)  
- `OWN`: Largest Shareholder Ownership (share, 0–1)  

---

## Notes
- Variables are standardized to align with international accounting & finance research conventions.  
- All values are firm-year level observations.  
- Outliers and extreme values are retained; users may winsorize or trim as needed.  
- No missing observations are present in the released version (after preprocessing).  
- Supplementary files provide full descriptive statistics, outlier diagnostics, correlation matrices, and figures.  
- The `Source_Code` directory contains all scripts used to preprocess data, train baseline models (Random Forest, XGBoost, CatBoost, FT-Transformer, TabTransformer), and generate evaluation results reported in the manuscript.  
- Users can directly run these scripts to replicate Tables S-4 and Figures S-1–S-8.  
---

## Example Usage (Python)
```python
import pandas as pd

# Load dataset
df = pd.read_csv("KoTaP_Dataset.csv")

# Preview
print(df.head())

# Summary statistics for tax avoidance indicators
print(df[['CETR', 'GETR', 'TSTA', 'TSDA']].describe())

# Correlation between profitability and tax avoidance
corr = df[['CETR', 'GETR', 'ROA', 'ROE']].corr()
print(corr)
```

---

## License
- Dataset: Released under the **Creative Commons Attribution–NonCommercial 4.0 International (CC BY-NC 4.0) License**.  
  You are free to share and adapt for non-commercial purposes with proper attribution.  

- Source Code: Released under the **MIT License** (see `Fundamental_Prediction/Source_Code/LICENSE`).  
  This includes the full set of Python scripts used for baseline evaluation and prediction experiments to ensure reproducibility.

---

## Citation
When using this dataset, please cite:  

> Kim, H.J. (2025). *KoTaP: A Panel Dataset for Corporate Tax Avoidance, Performance, and Governance in Korea*. Zenodo. https://doi.org/10.5281/zenodo.16980886  
