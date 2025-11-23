from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional, Literal

class StatCard(BaseModel):
    title: str
    value: str
    subtitle: str
    trend: Literal['up', 'down', 'neutral']
    icon: str

class AnomalyNotification(BaseModel):
    id: int
    type: Literal['stakes', 'payouts']
    severity: Literal['critical', 'high', 'medium', 'low']
    timestamp: datetime
    value: float
    normalRange: str
    zScore: float
    message: str

class AnomalyTableRecord(BaseModel):
    id: int
    time: datetime
    stake: float
    gamers: int
    skins: int
    payout: float
    peopleWin: int
    peopleLost: int
    anomalyType: Literal['stake', 'payout']
    severity: Literal['critical', 'high', 'medium', 'low']

class ChartDataPoint(BaseModel):
    timestamp: datetime
    value: float
    isAnomaly: Optional[bool] = False

class ChartData(BaseModel):
    timestamps: List[datetime]
    values: List[float]
    anomalies: List[dict]
    bounds: dict

class StakesPayoutsChartResponse(BaseModel):
    chartType: Literal['stakes', 'payouts']
    data: ChartData
    mean: float
    std: float

class DashboardSummary(BaseModel):
    stats: List[StatCard]
    recentAnomalies: List[AnomalyNotification]
    totalAnomalies: int
    lastUpdated: datetime
