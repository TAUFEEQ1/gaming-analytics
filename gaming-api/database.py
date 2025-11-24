from sqlalchemy import create_engine, Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./gaming_metrics.db")

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Database Models
class RollingInterestingWithGlobalZ(Base):
    __tablename__ = "rolling_interesting_with_global_z"
    
    ID = Column(Integer, primary_key=True)
    stake = Column(Float)
    payout = Column(Float)
    house_net = Column(Float)
    outpay = Column(Float)
    time = Column(DateTime)
    stake_global_mean = Column(Float)
    stake_global_std = Column(Float)
    stake_global_z = Column(Float)
    payout_global_mean = Column(Float)
    payout_global_std = Column(Float)
    payout_global_z = Column(Float)
    house_net_global_mean = Column(Float)
    house_net_global_std = Column(Float)
    house_net_global_z = Column(Float)
    outpay_global_mean = Column(Float)
    outpay_global_std = Column(Float)
    outpay_global_z = Column(Float)

class OnlineCasino(Base):
    __tablename__ = "online_casino"
    
    ID = Column(Integer, primary_key=True)
    gamers = Column(Integer)
    skins = Column(Integer)
    money = Column(Float)
    ticks = Column(Float)
    peopleWin = Column(Float)
    peopleLost = Column(Float)
    outpay = Column(Float)
    time = Column(DateTime)
    moderator = Column(Integer)

class InterestingData(Base):
    __tablename__ = "interesting_data"
    
    ID = Column(Integer, primary_key=True)
    stake = Column(Float)
    payout = Column(Float)
    house_net = Column(Float)
    outpay = Column(Float)
    time = Column(DateTime)

class Rolling1Min(Base):
    __tablename__ = "rolling_1min"
    
    time = Column(DateTime, primary_key=True)
    stake = Column(Float)
    payout = Column(Float)
    stake_rolling_mean_3 = Column(Float)
    stake_rolling_std_3 = Column(Float)
    stake_zscore_3 = Column(Float)
    payout_rolling_mean_3 = Column(Float)
    payout_rolling_std_3 = Column(Float)
    payout_zscore_3 = Column(Float)

class Rolling3Min(Base):
    __tablename__ = "rolling_3min"
    
    time = Column(DateTime, primary_key=True)
    stake = Column(Float)
    payout = Column(Float)
    stake_rolling_mean_3 = Column(Float)
    stake_rolling_std_3 = Column(Float)
    stake_zscore_3 = Column(Float)
    payout_rolling_mean_3 = Column(Float)
    payout_rolling_std_3 = Column(Float)
    payout_zscore_3 = Column(Float)

class Rolling5Min(Base):
    __tablename__ = "rolling_5min"
    
    time = Column(DateTime, primary_key=True)
    stake = Column(Float)
    payout = Column(Float)
    stake_rolling_mean_3 = Column(Float)
    stake_rolling_std_3 = Column(Float)
    stake_zscore_3 = Column(Float)
    payout_rolling_mean_3 = Column(Float)
    payout_rolling_std_3 = Column(Float)
    payout_zscore_3 = Column(Float)

class RollingInterestingWithDBSCAN(Base):
    __tablename__ = "rolling_interesting_with_dbscan"
    
    ID = Column(Integer, primary_key=True)
    stake = Column(Float)
    payout = Column(Float)
    house_net = Column(Float)
    outpay = Column(Float)
    time = Column(DateTime)
    stake_global_mean = Column(Float)
    stake_global_std = Column(Float)
    stake_global_z = Column(Float)
    payout_global_mean = Column(Float)
    payout_global_std = Column(Float)
    payout_global_z = Column(Float)
    house_net_global_mean = Column(Float)
    house_net_global_std = Column(Float)
    house_net_global_z = Column(Float)
    outpay_global_mean = Column(Float)
    outpay_global_std = Column(Float)
    outpay_global_z = Column(Float)
    db_anomaly = Column(Integer)
    db_cluster = Column(Integer)

class Notification(Base):
    __tablename__ = "notifications"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    timestamp = Column(DateTime, nullable=False)
    anomaly_type = Column(String, nullable=False)  # 'stake' or 'payout'
    severity = Column(String, nullable=False)  # 'critical', 'high', 'medium'
    value = Column(Float, nullable=False)
    z_score = Column(Float, nullable=False)
    message = Column(String, nullable=False)
    is_read = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

# Create tables if they don't exist
Base.metadata.create_all(bind=engine)
