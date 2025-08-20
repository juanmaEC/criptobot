from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime, Boolean, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from config import Config

Base = declarative_base()

class Trade(Base):
    __tablename__ = 'trades'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    side = Column(String(10), nullable=False)  # 'long' or 'short'
    strategy = Column(String(20), nullable=False)  # 'pump' or 'top_movers'
    entry_price = Column(Float, nullable=False)
    exit_price = Column(Float)
    quantity = Column(Float, nullable=False)
    stop_loss = Column(Float)
    take_profit = Column(Float)
    trailing_stop = Column(Float)
    status = Column(String(20), default='open')  # 'open', 'closed', 'cancelled'
    pnl = Column(Float)
    pnl_percent = Column(Float)
    created_at = Column(DateTime, default=datetime.utcnow)
    closed_at = Column(DateTime)
    binance_order_id = Column(String(50))
    
class MarketData(Base):
    __tablename__ = 'market_data'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    open_price = Column(Float, nullable=False)
    high_price = Column(Float, nullable=False)
    low_price = Column(Float, nullable=False)
    close_price = Column(Float, nullable=False)
    volume = Column(Float, nullable=False)
    ema_fast = Column(Float)
    ema_slow = Column(Float)
    rsi = Column(Float)
    macd = Column(Float)
    macd_signal = Column(Float)
    macd_histogram = Column(Float)
    bb_upper = Column(Float)
    bb_middle = Column(Float)
    bb_lower = Column(Float)
    atr = Column(Float)
    
class PumpSignal(Base):
    __tablename__ = 'pump_signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    price_change_percent = Column(Float, nullable=False)
    volume_multiplier = Column(Float, nullable=False)
    time_window = Column(Integer, nullable=False)
    executed = Column(Boolean, default=False)
    
class TopMoverSignal(Base):
    __tablename__ = 'top_mover_signals'
    
    id = Column(Integer, primary_key=True)
    symbol = Column(String(20), nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
    price_change_percent = Column(Float, nullable=False)
    technical_score = Column(Float)
    ai_score = Column(Float)
    final_score = Column(Float)
    signal = Column(String(10))  # 'long', 'short', 'neutral'
    executed = Column(Boolean, default=False)
    
class BotStatus(Base):
    __tablename__ = 'bot_status'
    
    id = Column(Integer, primary_key=True)
    strategy = Column(String(20), nullable=False)
    status = Column(String(20), default='running')  # 'running', 'paused', 'stopped'
    active_trades = Column(Integer, default=0)
    daily_pnl = Column(Float, default=0.0)
    daily_pnl_percent = Column(Float, default=0.0)
    last_update = Column(DateTime, default=datetime.utcnow)
    
# Database connection
engine = create_engine(Config.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def create_tables():
    Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
