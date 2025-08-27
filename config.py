import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Binance API
    BINANCE_API_KEY = os.getenv('BINANCE_API_KEY')
    BINANCE_SECRET_KEY = os.getenv('BINANCE_SECRET_KEY')
    BINANCE_TESTNET = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
    
    # Database
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/cryptopump')
    
    # Redis for Celery
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    
    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
    
    # Account Configuration
    INITIAL_BALANCE = float(os.getenv('INITIAL_BALANCE', '200.0'))  # Saldo inicial 200 USDT
    DAILY_TARGET_PERCENTAGE = float(os.getenv('DAILY_TARGET_PERCENTAGE', '75.0'))  # 75% rendimiento diario
    DAILY_TARGET_AMOUNT = INITIAL_BALANCE * (DAILY_TARGET_PERCENTAGE / 100)  # 150 USDT diario
    
    # Trading Parameters
    CAPITAL_PERCENTAGE = float(os.getenv('CAPITAL_PERCENTAGE', '0.15'))  # 15% por operación para mayor agresividad
    MAX_CONCURRENT_TRADES = int(os.getenv('MAX_CONCURRENT_TRADES', '3'))
    MAX_DAILY_LOSS = float(os.getenv('MAX_DAILY_LOSS', '0.10'))  # 10% máximo pérdida diaria
    
    # Pump Detection - Ajustado para mayor agresividad
    PUMP_THRESHOLD_PERCENT = float(os.getenv('PUMP_THRESHOLD_PERCENT', '3.0'))  # Reducido a 3%
    PUMP_TIME_WINDOW = int(os.getenv('PUMP_TIME_WINDOW', '180'))  # 3 minutos
    PUMP_VOLUME_MULTIPLIER = float(os.getenv('PUMP_VOLUME_MULTIPLIER', '1.5'))  # Reducido a 1.5x
    
    # Top Movers - Ajustado para mayor agresividad
    TOP_MOVERS_THRESHOLD = float(os.getenv('TOP_MOVERS_THRESHOLD', '1.5'))  # Reducido a 1.5%
    TOP_MOVERS_TIME_WINDOW = int(os.getenv('TOP_MOVERS_TIME_WINDOW', '900'))  # 15 minutos
    
    # Risk Management - Ajustado para mayor agresividad
    STOP_LOSS_PERCENT = float(os.getenv('STOP_LOSS_PERCENT', '2.0'))  # Reducido a 2%
    TAKE_PROFIT_PERCENT = float(os.getenv('TAKE_PROFIT_PERCENT', '4.0'))  # Reducido a 4%
    TRAILING_STOP_PERCENT = float(os.getenv('TRAILING_STOP_PERCENT', '1.5'))  # Reducido a 1.5%
    COOLDOWN_AFTER_LOSS = int(os.getenv('COOLDOWN_AFTER_LOSS', '1800'))  # 30 minutos
    
    # Technical Analysis
    EMA_FAST = int(os.getenv('EMA_FAST', '9'))
    EMA_SLOW = int(os.getenv('EMA_SLOW', '21'))
    RSI_PERIOD = int(os.getenv('RSI_PERIOD', '14'))
    MACD_FAST = int(os.getenv('MACD_FAST', '12'))
    MACD_SLOW = int(os.getenv('MACD_SLOW', '26'))
    MACD_SIGNAL = int(os.getenv('MACD_SIGNAL', '9'))
    BOLLINGER_PERIOD = int(os.getenv('BOLLINGER_PERIOD', '20'))
    BOLLINGER_STD = float(os.getenv('BOLLINGER_STD', '2.0'))
    ATR_PERIOD = int(os.getenv('ATR_PERIOD', '14'))
    
    # AI/ML
    LSTM_SEQUENCE_LENGTH = int(os.getenv('LSTM_SEQUENCE_LENGTH', '60'))
    LSTM_PREDICTION_HORIZON = int(os.getenv('LSTM_PREDICTION_HORIZON', '10'))
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FILE = os.getenv('LOG_FILE', 'logs/cryptopump.log')
    
    # Bot Status Notifications
    ENABLE_BOT_STATUS_NOTIFICATIONS = os.getenv('ENABLE_BOT_STATUS_NOTIFICATIONS', 'true').lower() == 'true'
    ENABLE_DETAILED_TRADE_NOTIFICATIONS = os.getenv('ENABLE_DETAILED_TRADE_NOTIFICATIONS', 'true').lower() == 'true'
