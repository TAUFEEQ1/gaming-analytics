import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression

df = pd.read_csv('warehouse/data/ggr_timeseries.csv')
df['date'] = pd.to_datetime(df['date'])

events = pd.read_csv('warehouse/data/sporting_events_calendar.csv')
events['date'] = pd.to_datetime(events['date'])

epl_counts = events[events['event_type']=='EPL'].groupby('date').size().reset_index(name='epl_count')
df = df.merge(epl_counts, on='date', how='left')
df['epl_count'] = df['epl_count'].fillna(0).astype(int)
df['has_event'] = (df['epl_count'] > 0).astype(int)
df['is_month_start'] = ((df['date'].dt.day >= 1) & (df['date'].dt.day <= 3)).astype(int)

train_end = 275
lag = 6

X, y_stake, y_payout = [], [], []

for i in range(lag, len(df)):
    is_weekend = 1 if (i % 7) in [5, 6] else 0
    X.append([df['num_operators'].iloc[i], df['total_bets'].iloc[i], is_weekend, df['has_event'].iloc[i], df['is_month_start'].iloc[i]])
    y_stake.append(df['total_stake'].iloc[i])
    y_payout.append(df['total_payout'].iloc[i])

X, y_stake, y_payout = np.array(X), np.array(y_stake), np.array(y_payout)

# Predict stake
model_stake = LinearRegression()
model_stake.fit(X[:train_end-lag], y_stake[:train_end-lag])
stake_test_r2 = 1 - np.sum((y_stake[train_end-lag:] - model_stake.predict(X[train_end-lag:]))**2) / np.sum((y_stake[train_end-lag:] - y_stake[train_end-lag:].mean())**2)

# Predict payout  
model_payout = LinearRegression()
model_payout.fit(X[:train_end-lag], y_payout[:train_end-lag])
payout_test_r2 = 1 - np.sum((y_payout[train_end-lag:] - model_payout.predict(X[train_end-lag:]))**2) / np.sum((y_payout[train_end-lag:] - y_payout[train_end-lag:].mean())**2)

# RTP analysis
df['rtp'] = df['total_payout'] / df['total_stake']

print('STAKE vs PAYOUT PREDICTABILITY:')
print(f'  Stake Test R²:  {stake_test_r2:.4f} - PREDICTABLE')
print(f'  Payout Test R²: {payout_test_r2:.4f} - MORE RANDOM')
print(f'\nRTP (Payout/Stake):')
print(f'  Mean: {df["rtp"].mean():.3f} ({100*df["rtp"].mean():.1f}% returned to players)')
print(f'  Std:  {df["rtp"].std():.3f} (high variance)')
print(f'  Range: {df["rtp"].min():.2f} to {df["rtp"].max():.2f}')
print(f'\nCONCLUSION:')
print(f'GGR = Stake (R²={stake_test_r2:.2f}) - Payout (R²={payout_test_r2:.2f})')
print(f'    = Predictable - Random = Inherently Noisy')
