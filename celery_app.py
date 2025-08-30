from celery import Celery
from celery.schedules import crontab
from config import Config
from database.models import create_tables, get_db
from strategies.pump_detector import PumpDetector
from strategies.top_movers import TopMoversStrategy
from trading.binance_client import BinanceClient
from notifications.telegram_bot import TelegramNotifier
from loguru import logger
import pandas as pd
from typing import Dict, List
import os

# Configurar logging
logger.add("logs/celery.log", rotation="1 day", retention="7 days")

# Crear aplicación Celery
celery_app = Celery(
    'cryptopump',
    broker=Config.REDIS_URL,
    backend=Config.REDIS_URL,
    include=['celery_app']
)

# Configuración de Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutos
    task_soft_time_limit=25 * 60,  # 25 minutos
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
)

# Inicializar componentes
config = Config()

# Inicializar BinanceClient de forma más robusta
try:
    if config.BINANCE_API_KEY and config.BINANCE_SECRET_KEY:
        binance_client = BinanceClient(config)
        logger.info("BinanceClient initialized successfully")
    else:
        logger.warning("Binance API credentials not configured. Some features may not work.")
        binance_client = None
except Exception as e:
    logger.error(f"Failed to initialize BinanceClient: {e}")
    binance_client = None

# Inicializar TelegramNotifier de forma más robusta
try:
    if config.TELEGRAM_BOT_TOKEN and config.TELEGRAM_CHAT_ID:
        telegram_notifier = TelegramNotifier(config)
        logger.info("TelegramNotifier initialized successfully")
    else:
        logger.warning("Telegram credentials not configured. Notifications will be disabled.")
        telegram_notifier = None
except Exception as e:
    logger.error(f"Failed to initialize TelegramNotifier: {e}")
    telegram_notifier = None

# Crear tablas de base de datos
create_tables()

@celery_app.task(bind=True)
def scan_pumps(self):
    """Tarea para escanear pumps"""
    try:
        logger.info("🚀 Iniciando escaneo de Pumps...")
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        # Inicializar detector de pumps
        pump_detector = PumpDetector(config, db)
        
        # Verificar que binance_client esté disponible
        if not binance_client:
            logger.error("BinanceClient not available. Cannot perform pump scan.")
            return {'pumps_detected': 0, 'error': 'BinanceClient not available'}
        
        # Obtener símbolos con mayor volumen
        symbols = get_high_volume_symbols()
        logger.info(f"📊 Obtenidos {len(symbols)} símbolos para análisis de pumps")
        
        pumps_detected = 0
        symbols_analyzed = 0
        
        for symbol in symbols[:50]:  # Limitar a top 50 por rendimiento
            try:
                symbols_analyzed += 1
                logger.info(f"🔍 Analizando pump {symbols_analyzed}/50: {symbol}")
                
                # Obtener datos de mercado
                market_data = binance_client.get_market_data(symbol, '1m', 100)
                
                if len(market_data) < 30:
                    logger.debug(f"📉 {symbol}: Datos insuficientes para análisis de pump ({len(market_data)} < 30)")
                    continue
                
                # Detectar pump
                pump_info = pump_detector.detect_pump(symbol, market_data)
                
                if pump_info:
                    pumps_detected += 1
                    logger.info(f"🚀 PUMP CONFIRMADO: {symbol} - {pump_info['price_change_percent']:.2f}% en {pump_info['time_window']//60}min")
                    
                    # Notificar por Telegram
                    if telegram_notifier:
                        telegram_notifier.notify_pump_detected(pump_info)
                    
                    # Verificar si debemos operar
                    if pump_detector.should_trade_pump(pump_info):
                        logger.info(f"💰 Evaluando operación en {symbol}...")
                        # Obtener balance de cuenta
                        balance = binance_client.get_account_balance()
                        position_size = pump_detector.calculate_position_size(pump_info, balance['USDT'])
                        
                        if position_size > 0:
                            logger.info(f"💸 Ejecutando operación en {symbol} - Tamaño: ${position_size:.2f}")
                            # Ejecutar trade
                            execute_pump_trade.delay(symbol, pump_info, position_size)
                        else:
                            logger.info(f"⚠️ {symbol}: Posición calculada es 0, no operando")
                    else:
                        logger.info(f"❌ {symbol}: No cumple criterios para operar")
                
            except Exception as e:
                logger.error(f"Error processing symbol {symbol}: {e}")
                continue
        
        logger.info(f"✅ Escaneo de pumps completado: {pumps_detected} pumps detectados de {symbols_analyzed} símbolos analizados")
        
        # Actualizar progreso
        self.update_state(
            state='SUCCESS',
            meta={'pumps_detected': pumps_detected, 'symbols_analyzed': symbols_analyzed}
        )
        
        return {'pumps_detected': pumps_detected, 'symbols_analyzed': symbols_analyzed}
        
    except Exception as e:
        logger.error(f"Error in pump scan: {e}")
        if telegram_notifier:
            telegram_notifier.notify_error(str(e), "Pump Scan")
        raise

@celery_app.task(bind=True)
def scan_top_movers(self):
    """Tarea para escanear top movers"""
    try:
        logger.info("🚀 Iniciando escaneo de Top Movers...")
        
        # Obtener sesión de base de datos
        db = next(get_db())
        
        # Inicializar estrategia de top movers
        top_movers_strategy = TopMoversStrategy(config, db)
        
        # Verificar que binance_client esté disponible
        if not binance_client:
            logger.error("BinanceClient not available. Cannot perform top movers scan.")
            return {'trades_executed': 0, 'error': 'BinanceClient not available'}
        
        # Obtener datos de todos los símbolos
        logger.info("📊 Obteniendo datos de mercado para todos los símbolos...")
        all_market_data = get_all_market_data()
        logger.info(f"📈 Datos obtenidos para {len(all_market_data)} símbolos")
        
        # Escanear top movers
        top_movers = top_movers_strategy.scan_top_movers(all_market_data)
        
        trades_executed = 0
        
        for analysis in top_movers:
            try:
                symbol = analysis['symbol']
                logger.info(f"🎯 Top Mover confirmado: {symbol} - {analysis['price_change_percent']:.2f}% - Score: {analysis.get('final_score', 0):.2f}")
                
                # Notificar por Telegram
                if telegram_notifier:
                    telegram_notifier.notify_top_mover_detected(analysis)
                
                # Verificar si debemos operar
                if top_movers_strategy.should_trade_top_mover(analysis):
                    logger.info(f"💰 Evaluando operación en Top Mover {symbol}...")
                    # Obtener balance de cuenta
                    balance = binance_client.get_account_balance()
                    position_size = top_movers_strategy.calculate_position_size(analysis, balance['USDT'])
                    
                    if position_size > 0:
                        logger.info(f"💸 Ejecutando operación en Top Mover {symbol} - Tamaño: ${position_size:.2f}")
                        # Ejecutar trade
                        execute_top_mover_trade.delay(symbol, analysis, position_size)
                        trades_executed += 1
                    else:
                        logger.info(f"⚠️ {symbol}: Posición calculada es 0, no operando")
                else:
                    logger.info(f"❌ {symbol}: No cumple criterios para operar")
                
            except Exception as e:
                logger.error(f"Error processing top mover {analysis.get('symbol', 'unknown')}: {e}")
                continue
        
        logger.info(f"✅ Escaneo de Top Movers completado: {len(top_movers)} top movers encontrados, {trades_executed} operaciones ejecutadas")
        
        # Actualizar progreso
        self.update_state(
            state='SUCCESS',
            meta={'top_movers_found': len(top_movers), 'trades_executed': trades_executed}
        )
        
        return {'top_movers_found': len(top_movers), 'trades_executed': trades_executed}
        
    except Exception as e:
        logger.error(f"Error in top movers scan: {e}")
        if telegram_notifier:
            telegram_notifier.notify_error(str(e), "Top Movers Scan")
        raise

@celery_app.task
def execute_pump_trade(symbol: str, pump_info: Dict, position_size: float):
    """Ejecuta trade de pump"""
    try:
        logger.info(f"Executing pump trade for {symbol}")
        
        # Calcular cantidad de tokens
        quantity = binance_client.calculate_position_size(symbol, position_size)
        
        if quantity <= 0:
            logger.warning(f"Invalid quantity for {symbol}")
            return
        
        # Calcular precios de SL/TP
        current_price = pump_info['current_price']
        stop_loss = current_price * (1 - config.STOP_LOSS_PERCENT / 100)
        take_profit = current_price * (1 + config.TAKE_PROFIT_PERCENT / 100)
        
        # Preparar información del trade
        trade_info = {
            'symbol': symbol,
            'side': 'buy',
            'quantity': quantity,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'usdt_amount': position_size,
            'strategy': 'pump'
        }
        
        # Ejecutar trade
        result = binance_client.execute_trade(trade_info)
        
        if result:
            # Notificar ejecución
            if telegram_notifier:
                telegram_notifier.notify_trade_executed(trade_info)
            
            # Guardar en base de datos
            save_trade_to_db.delay(symbol, 'pump', trade_info, result)
            
            logger.info(f"Pump trade executed successfully for {symbol}")
        else:
            logger.error(f"Failed to execute pump trade for {symbol}")
        
    except Exception as e:
        logger.error(f"Error executing pump trade for {symbol}: {e}")
        if telegram_notifier:
            telegram_notifier.notify_error(str(e), f"Pump Trade - {symbol}")

@celery_app.task
def execute_top_mover_trade(symbol: str, analysis: Dict, position_size: float):
    """Ejecuta trade de top mover"""
    try:
        logger.info(f"Executing top mover trade for {symbol}")
        
        # Calcular cantidad de tokens
        quantity = binance_client.calculate_position_size(symbol, position_size)
        
        if quantity <= 0:
            logger.warning(f"Invalid quantity for {symbol}")
            return
        
        # Determinar lado del trade
        side = 'buy' if analysis['final_signal'] == 'long' else 'sell'
        
        # Calcular precios de SL/TP
        current_price = analysis['current_price']
        if side == 'buy':
            stop_loss = current_price * (1 - config.STOP_LOSS_PERCENT / 100)
            take_profit = current_price * (1 + config.TAKE_PROFIT_PERCENT / 100)
        else:
            stop_loss = current_price * (1 + config.STOP_LOSS_PERCENT / 100)
            take_profit = current_price * (1 - config.TAKE_PROFIT_PERCENT / 100)
        
        # Preparar información del trade
        trade_info = {
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'entry_price': current_price,
            'stop_loss': stop_loss,
            'take_profit': take_profit,
            'usdt_amount': position_size,
            'strategy': 'top_movers'
        }
        
        # Ejecutar trade
        result = binance_client.execute_trade(trade_info)
        
        if result:
            # Notificar ejecución
            if telegram_notifier:
                telegram_notifier.notify_trade_executed(trade_info)
            
            # Guardar en base de datos
            save_trade_to_db.delay(symbol, 'top_movers', trade_info, result)
            
            logger.info(f"Top mover trade executed successfully for {symbol}")
        else:
            logger.error(f"Failed to execute top mover trade for {symbol}")
        
    except Exception as e:
        logger.error(f"Error executing top mover trade for {symbol}: {e}")
        if telegram_notifier:
            telegram_notifier.notify_error(str(e), f"Top Mover Trade - {symbol}")

@celery_app.task
def save_trade_to_db(symbol: str, strategy: str, trade_info: Dict, order_result: Dict):
    """Guarda trade en base de datos"""
    try:
        from database.models import Trade
        
        db = next(get_db())
        
        trade = Trade(
            symbol=symbol,
            side=trade_info['side'],
            strategy=strategy,
            entry_price=trade_info['entry_price'],
            quantity=trade_info['quantity'],
            stop_loss=trade_info['stop_loss'],
            take_profit=trade_info['take_profit'],
            binance_order_id=order_result['main_order']['id']
        )
        
        db.add(trade)
        db.commit()
        
        logger.info(f"Trade saved to database: {symbol}")
        
    except Exception as e:
        logger.error(f"Error saving trade to database: {e}")

@celery_app.task
def monitor_open_trades():
    """Monitorea trades abiertos y actualiza SL/TP"""
    try:
        from database.models import Trade
        from datetime import datetime
        
        db = next(get_db())
        
        # Verificar que binance_client esté disponible
        if not binance_client:
            logger.error("BinanceClient not available. Cannot monitor open trades.")
            return
        
        # Obtener trades abiertos
        open_trades = db.query(Trade).filter(Trade.status == 'open').all()
        
        for trade in open_trades:
            try:
                # Obtener precio actual
                market_data = binance_client.get_market_data(trade.symbol, '1m', 1)
                if len(market_data) == 0:
                    continue
                
                current_price = market_data.iloc[-1]['close']
                
                # Verificar stop loss
                if trade.side == 'buy' and current_price <= trade.stop_loss:
                    close_trade.delay(trade.id, current_price, 'stop_loss')
                elif trade.side == 'sell' and current_price >= trade.stop_loss:
                    close_trade.delay(trade.id, current_price, 'stop_loss')
                
                # Verificar take profit
                elif trade.side == 'buy' and current_price >= trade.take_profit:
                    close_trade.delay(trade.id, current_price, 'take_profit')
                elif trade.side == 'sell' and current_price <= trade.take_profit:
                    close_trade.delay(trade.id, current_price, 'take_profit')
                
            except Exception as e:
                logger.error(f"Error monitoring trade {trade.id}: {e}")
                continue
        
    except Exception as e:
        logger.error(f"Error in monitor open trades: {e}")

@celery_app.task
def close_trade(trade_id: int, exit_price: float, reason: str):
    """Cierra un trade"""
    try:
        from database.models import Trade
        from datetime import datetime
        
        db = next(get_db())
        
        trade = db.query(Trade).filter(Trade.id == trade_id).first()
        if not trade:
            return
        
        # Calcular P&L
        if trade.side == 'buy':
            pnl = (exit_price - trade.entry_price) * trade.quantity
        else:
            pnl = (trade.entry_price - exit_price) * trade.quantity
        
        pnl_percent = (pnl / (trade.entry_price * trade.quantity)) * 100
        
        # Actualizar trade
        trade.exit_price = exit_price
        trade.pnl = pnl
        trade.pnl_percent = pnl_percent
        trade.status = 'closed'
        trade.closed_at = datetime.now()
        
        db.commit()
        
        # Notificar cierre
        trade_info = {
            'symbol': trade.symbol,
            'side': trade.side,
            'entry_price': trade.entry_price,
            'exit_price': exit_price,
            'pnl': pnl,
            'pnl_percent': pnl_percent,
            'strategy': trade.strategy,
            'duration': str(trade.closed_at - trade.created_at)
        }
        
        if telegram_notifier:
            telegram_notifier.notify_trade_closed(trade_info)
        
        logger.info(f"Trade closed: {trade.symbol} - P&L: ${pnl:.2f}")
        
    except Exception as e:
        logger.error(f"Error closing trade {trade_id}: {e}")

@celery_app.task
def send_daily_summary():
    """Envía resumen diario"""
    try:
        from database.models import Trade
        from datetime import datetime, timedelta
        
        db = next(get_db())
        
        # Obtener trades del día
        today = datetime.now().date()
        daily_trades = db.query(Trade).filter(
            Trade.created_at >= today
        ).all()
        
        # Calcular estadísticas
        total_pnl = sum(trade.pnl or 0 for trade in daily_trades)
        winning_trades = len([t for t in daily_trades if t.pnl and t.pnl > 0])
        losing_trades = len([t for t in daily_trades if t.pnl and t.pnl < 0])
        
        win_rate = (winning_trades / len(daily_trades) * 100) if daily_trades else 0
        
        # Obtener balance
        if not binance_client:
            logger.error("BinanceClient not available. Cannot get account balance.")
            balance = {'total_usdt': 0}
        else:
            balance = binance_client.get_account_balance()
        
        summary = {
            'total_pnl': total_pnl,
            'total_pnl_percent': (total_pnl / balance['total_usdt'] * 100) if balance['total_usdt'] > 0 else 0,
            'winning_trades': winning_trades,
            'losing_trades': losing_trades,
            'win_rate': win_rate,
            'initial_balance': balance['total_usdt'] - total_pnl,
            'final_balance': balance['total_usdt'],
            'pumps_detected': len([t for t in daily_trades if t.strategy == 'pump']),
            'top_movers_analyzed': len([t for t in daily_trades if t.strategy == 'top_movers']),
            'date': today.strftime('%Y-%m-%d')
        }
        
        if telegram_notifier:
            telegram_notifier.notify_daily_summary(summary)
        
    except Exception as e:
        logger.error(f"Error sending daily summary: {e}")

def get_high_volume_symbols() -> List[str]:
    """Obtiene símbolos con mayor volumen"""
    try:
        if not binance_client:
            logger.error("BinanceClient not available. Cannot get high volume symbols.")
            return []
        
        symbols = binance_client.get_all_symbols()
        high_volume_symbols = []
        
        for symbol in symbols[:100]:  # Limitar para rendimiento
            try:
                ticker = binance_client.exchange.fetch_ticker(symbol)
                if ticker['quoteVolume'] > 1000000:  # Más de 1M USDT en 24h
                    high_volume_symbols.append(symbol)
            except:
                continue
        
        return high_volume_symbols
        
    except Exception as e:
        logger.error(f"Error getting high volume symbols: {e}")
        return []

def get_all_market_data() -> Dict[str, pd.DataFrame]:
    """Obtiene datos de mercado para todos los símbolos"""
    try:
        if not binance_client:
            logger.error("BinanceClient not available. Cannot get market data.")
            return {}
        
        symbols = get_high_volume_symbols()
        market_data = {}
        
        for symbol in symbols[:50]:  # Limitar para rendimiento
            try:
                data = binance_client.get_market_data(symbol, '1m', 100)
                if len(data) >= 50:
                    market_data[symbol] = data
            except:
                continue
        
        return market_data
        
    except Exception as e:
        logger.error(f"Error getting all market data: {e}")
        return {}

# Configurar tareas periódicas
@celery_app.on_after_configure.connect
def setup_periodic_tasks(sender, **kwargs):
    # Escanear pumps cada 30 segundos
    sender.add_periodic_task(
        30.0,
        scan_pumps.s(),
        name='scan-pumps-every-30s'
    )
    
    # Escanear top movers cada 5 minutos
    sender.add_periodic_task(
        300.0,
        scan_top_movers.s(),
        name='scan-top-movers-every-5min'
    )
    
    # Monitorear trades abiertos cada minuto
    sender.add_periodic_task(
        60.0,
        monitor_open_trades.s(),
        name='monitor-trades-every-1min'
    )
    
    # Resumen diario a las 00:00 UTC
    sender.add_periodic_task(
        crontab(hour=0, minute=0),
        send_daily_summary.s(),
        name='daily-summary-at-midnight'
    )

if __name__ == '__main__':
    celery_app.start()
