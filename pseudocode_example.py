"""
PSEUDOCÓDIGO DEL BOT CRYPTOPUMP
Muestra ambos caminos: Pump Detection y Top Movers
"""

# ============================================================================
# CAMINO 1: PUMP DETECTION
# ============================================================================

def pump_detection_strategy():
    """
    Estrategia de detección de pumps en tiempo real
    """
    
    # Configuración
    PUMP_THRESHOLD = 5.0  # 5% en 5 minutos
    VOLUME_MULTIPLIER = 2.0  # 2x volumen promedio
    TIME_WINDOW = 300  # 5 minutos en segundos
    
    while True:  # Ejecución 24/7
        # 1. Obtener símbolos con alto volumen
        high_volume_symbols = get_high_volume_symbols()
        
        for symbol in high_volume_symbols:
            # 2. Obtener datos de mercado recientes
            market_data = get_market_data(symbol, timeframe='1m', limit=100)
            
            # 3. Calcular métricas de pump
            recent_data = market_data.tail(TIME_WINDOW // 60)
            
            # Cambio de precio
            start_price = recent_data.iloc[0]['close']
            end_price = recent_data.iloc[-1]['close']
            price_change_percent = ((end_price - start_price) / start_price) * 100
            
            # Volumen
            avg_volume = recent_data['volume'].mean()
            current_volume = recent_data.iloc[-1]['volume']
            volume_multiplier = current_volume / avg_volume
            
            # 4. Verificar condiciones de pump
            if (price_change_percent >= PUMP_THRESHOLD and 
                volume_multiplier >= VOLUME_MULTIPLIER and
                price_change_percent > 0):  # Solo subidas
                
                # 5. Calcular score de calidad
                quality_score = calculate_pump_quality(
                    price_change_percent, 
                    volume_multiplier, 
                    TIME_WINDOW
                )
                
                # 6. Verificar si debemos operar
                if should_trade_pump(quality_score):
                    # 7. Calcular tamaño de posición
                    account_balance = get_account_balance()
                    position_size = calculate_position_size(
                        account_balance, 
                        quality_score
                    )
                    
                    # 8. Ejecutar trade
                    execute_pump_trade(symbol, position_size)
                    
                    # 9. Notificar por Telegram
                    notify_pump_detected(symbol, price_change_percent, volume_multiplier)
        
        sleep(30)  # Esperar 30 segundos antes del siguiente escaneo

def calculate_pump_quality(price_change, volume_mult, time_window):
    """
    Calcula score de calidad del pump (0-100)
    """
    # Score basado en cambio de precio (0-50 puntos)
    price_score = min(50, price_change * 5)
    
    # Score basado en volumen (0-30 puntos)
    volume_score = min(30, volume_mult * 10)
    
    # Score basado en velocidad (0-20 puntos)
    speed_score = max(0, 20 - (time_window / 60 * 2))
    
    total_score = price_score + volume_score + speed_score
    return min(100, total_score)

def execute_pump_trade(symbol, position_size):
    """
    Ejecuta trade de pump con SL/TP agresivos
    """
    # Obtener precio actual
    current_price = get_current_price(symbol)
    
    # Calcular SL/TP agresivos
    stop_loss = current_price * 0.97  # -3%
    take_profit = current_price * 1.06  # +6%
    
    # Colocar orden de compra
    buy_order = place_market_order(symbol, 'buy', position_size)
    
    # Colocar SL y TP
    place_stop_loss_order(symbol, 'sell', position_size, stop_loss)
    place_take_profit_order(symbol, 'sell', position_size, take_profit)
    
    # Guardar trade en base de datos
    save_trade_to_db(symbol, 'pump', 'buy', current_price, position_size)

# ============================================================================
# CAMINO 2: TOP MOVERS
# ============================================================================

def top_movers_strategy():
    """
    Estrategia de análisis de top movers con IA
    """
    
    # Configuración
    MOVEMENT_THRESHOLD = 2.5  # 2.5% en 30 minutos
    TIME_WINDOW = 1800  # 30 minutos
    
    while True:  # Ejecución cada 5 minutos
        # 1. Obtener todos los símbolos
        all_symbols = get_all_symbols()
        
        # 2. Filtrar por movimiento significativo
        significant_movers = []
        
        for symbol in all_symbols:
            market_data = get_market_data(symbol, timeframe='1m', limit=100)
            
            if len(market_data) < 50:
                continue
            
            # Calcular movimiento en ventana de tiempo
            window_data = market_data.tail(TIME_WINDOW // 60)
            start_price = window_data.iloc[0]['close']
            end_price = window_data.iloc[-1]['close']
            movement_percent = ((end_price - start_price) / start_price) * 100
            
            if abs(movement_percent) >= MOVEMENT_THRESHOLD:
                significant_movers.append({
                    'symbol': symbol,
                    'movement': movement_percent,
                    'market_data': market_data
                })
        
        # 3. Análisis completo de cada top mover
        for mover in significant_movers:
            symbol = mover['symbol']
            market_data = mover['market_data']
            
            # Filtrar scams
            if not is_valid_symbol(symbol, market_data):
                continue
            
            # 4. Análisis técnico
            technical_analysis = perform_technical_analysis(market_data)
            technical_score = technical_analysis['score']
            technical_signal = technical_analysis['signal']  # 'long', 'short', 'neutral'
            
            # 5. Análisis de IA
            ai_analysis = perform_ai_analysis(market_data)
            ai_score = ai_analysis['score']
            ai_signal = ai_analysis['signal']
            
            # 6. Score combinado
            final_score = (technical_score * 0.6) + (ai_score * 0.4)
            
            # 7. Determinar señal final
            if technical_signal == ai_signal and technical_signal != 'neutral':
                final_signal = technical_signal
            elif final_score > 70:
                final_signal = 'long'
            elif final_score < 30:
                final_signal = 'short'
            else:
                final_signal = 'neutral'
            
            # 8. Verificar si debemos operar
            if should_trade_top_mover(final_score, final_signal):
                # 9. Calcular posición
                account_balance = get_account_balance()
                position_size = calculate_top_mover_position(
                    account_balance, 
                    final_score, 
                    final_signal
                )
                
                # 10. Ejecutar trade
                execute_top_mover_trade(symbol, final_signal, position_size)
                
                # 11. Notificar
                notify_top_mover_detected(symbol, final_signal, final_score)
        
        sleep(300)  # Esperar 5 minutos

def perform_technical_analysis(market_data):
    """
    Análisis técnico completo
    """
    # EMA (9,21)
    ema_fast = calculate_ema(market_data['close'], 9)
    ema_slow = calculate_ema(market_data['close'], 21)
    ema_signal = ema_fast.iloc[-1] > ema_slow.iloc[-1]
    
    # RSI (14)
    rsi = calculate_rsi(market_data['close'], 14)
    current_rsi = rsi.iloc[-1]
    rsi_signal = 'oversold' if current_rsi < 30 else 'overbought' if current_rsi > 70 else 'neutral'
    
    # MACD (12,26,9)
    macd_data = calculate_macd(market_data['close'])
    macd_signal = macd_data['macd'].iloc[-1] > macd_data['signal'].iloc[-1]
    
    # Bollinger Bands
    bb_data = calculate_bollinger_bands(market_data['close'])
    bb_position = bb_data['position'].iloc[-1]
    bb_signal = 'lower' if bb_position < 0.2 else 'upper' if bb_position > 0.8 else 'middle'
    
    # Calcular score técnico (0-100)
    technical_score = 50  # Base
    
    # Ajustar según señales
    if ema_signal: technical_score += 20
    else: technical_score -= 20
    
    if rsi_signal == 'oversold': technical_score += 20
    elif rsi_signal == 'overbought': technical_score -= 20
    
    if macd_signal: technical_score += 20
    else: technical_score -= 20
    
    if bb_signal == 'lower': technical_score += 20
    elif bb_signal == 'upper': technical_score -= 20
    
    # Determinar señal técnica
    if technical_score > 70:
        technical_signal = 'long'
    elif technical_score < 30:
        technical_signal = 'short'
    else:
        technical_signal = 'neutral'
    
    return {
        'score': max(0, min(100, technical_score)),
        'signal': technical_signal,
        'indicators': {
            'ema': ema_signal,
            'rsi': rsi_signal,
            'macd': macd_signal,
            'bollinger': bb_signal
        }
    }

def perform_ai_analysis(market_data):
    """
    Análisis con IA (LSTM + PPO)
    """
    # LSTM: Predicción de precio
    lstm_prediction = lstm_model.predict(market_data)
    price_change_prediction = lstm_prediction['predicted_change']
    
    # PPO: Optimización de entrada
    state = create_state_vector(market_data)
    ppo_action = ppo_model.predict(state)
    
    # Convertir acciones a score
    if ppo_action == 0:  # Sell
        ppo_score = 25
    elif ppo_action == 2:  # Buy
        ppo_score = 75
    else:  # Hold
        ppo_score = 50
    
    # Combinar predicciones
    ai_score = (price_change_prediction * 0.7) + (ppo_score * 0.3)
    
    # Determinar señal IA
    if ai_score > 70:
        ai_signal = 'long'
    elif ai_score < 30:
        ai_signal = 'short'
    else:
        ai_signal = 'neutral'
    
    return {
        'score': max(0, min(100, ai_score)),
        'signal': ai_signal,
        'lstm_prediction': price_change_prediction,
        'ppo_action': ppo_action
    }

def execute_top_mover_trade(symbol, signal, position_size):
    """
    Ejecuta trade de top mover
    """
    current_price = get_current_price(symbol)
    
    # Determinar lado del trade
    if signal == 'long':
        side = 'buy'
        stop_loss = current_price * 0.975  # -2.5%
        take_profit = current_price * 1.05  # +5%
    else:  # short
        side = 'sell'
        stop_loss = current_price * 1.025  # +2.5%
        take_profit = current_price * 0.95  # -5%
    
    # Ejecutar trade
    main_order = place_market_order(symbol, side, position_size)
    
    # Colocar SL y TP
    place_stop_loss_order(symbol, 'sell' if side == 'buy' else 'buy', position_size, stop_loss)
    place_take_profit_order(symbol, 'sell' if side == 'buy' else 'buy', position_size, take_profit)
    
    # Guardar en BD
    save_trade_to_db(symbol, 'top_movers', side, current_price, position_size)

# ============================================================================
# GESTIÓN DE RIESGO COMÚN
# ============================================================================

def should_trade_pump(quality_score):
    """
    Verifica si se debe operar un pump
    """
    # Verificar score mínimo
    if quality_score < 70:
        return False
    
    # Verificar operaciones activas
    active_trades = get_active_trades_count()
    if active_trades >= MAX_CONCURRENT_TRADES:
        return False
    
    # Verificar cooldown por pérdidas
    if is_in_cooldown():
        return False
    
    return True

def should_trade_top_mover(final_score, final_signal):
    """
    Verifica si se debe operar un top mover
    """
    # Verificar score mínimo
    if final_score < 75:
        return False
    
    # Verificar que las señales coincidan
    if final_signal == 'neutral':
        return False
    
    # Verificar operaciones activas
    active_trades = get_active_trades_count()
    if active_trades >= MAX_CONCURRENT_TRADES:
        return False
    
    # Verificar cooldown
    if is_in_cooldown():
        return False
    
    return True

def is_in_cooldown():
    """
    Verifica si estamos en cooldown por pérdidas recientes
    """
    recent_trades = get_recent_trades(hours=24)
    consecutive_losses = 0
    
    for trade in recent_trades:
        if trade['pnl'] < 0:
            consecutive_losses += 1
        else:
            consecutive_losses = 0
        
        if consecutive_losses >= 3:  # 3 pérdidas consecutivas
            return True
    
    return False

# ============================================================================
# MONITOREO DE TRADES
# ============================================================================

def monitor_open_trades():
    """
    Monitorea trades abiertos y actualiza SL/TP
    """
    while True:
        open_trades = get_open_trades()
        
        for trade in open_trades:
            current_price = get_current_price(trade['symbol'])
            
            # Verificar stop loss
            if trade['side'] == 'buy' and current_price <= trade['stop_loss']:
                close_trade(trade['id'], current_price, 'stop_loss')
            elif trade['side'] == 'sell' and current_price >= trade['stop_loss']:
                close_trade(trade['id'], current_price, 'stop_loss')
            
            # Verificar take profit
            elif trade['side'] == 'buy' and current_price >= trade['take_profit']:
                close_trade(trade['id'], current_price, 'take_profit')
            elif trade['side'] == 'sell' and current_price <= trade['take_profit']:
                close_trade(trade['id'], current_price, 'take_profit')
            
            # Trailing stop (opcional)
            update_trailing_stop(trade, current_price)
        
        sleep(60)  # Verificar cada minuto

def close_trade(trade_id, exit_price, reason):
    """
    Cierra un trade y calcula P&L
    """
    trade = get_trade_by_id(trade_id)
    
    # Calcular P&L
    if trade['side'] == 'buy':
        pnl = (exit_price - trade['entry_price']) * trade['quantity']
    else:
        pnl = (trade['entry_price'] - exit_price) * trade['quantity']
    
    pnl_percent = (pnl / (trade['entry_price'] * trade['quantity'])) * 100
    
    # Actualizar trade
    update_trade(trade_id, {
        'exit_price': exit_price,
        'pnl': pnl,
        'pnl_percent': pnl_percent,
        'status': 'closed',
        'closed_at': datetime.now()
    })
    
    # Notificar cierre
    notify_trade_closed(trade['symbol'], pnl, pnl_percent, reason)

# ============================================================================
# EJECUCIÓN PRINCIPAL CON CELERY
# ============================================================================

def main_execution():
    """
    Ejecución principal del bot con Celery
    """
    
    # Configurar tareas periódicas
    schedule_tasks()
    
    # Iniciar workers
    start_celery_workers()
    
    # Iniciar scheduler
    start_celery_beat()
    
    # Monitoreo continuo
    while True:
        # Verificar estado de workers
        check_worker_health()
        
        # Verificar conexiones
        check_binance_connection()
        check_database_connection()
        check_redis_connection()
        
        # Logs de estado
        log_system_status()
        
        sleep(300)  # Verificar cada 5 minutos

def schedule_tasks():
    """
    Programa tareas con Celery Beat
    """
    # Pump detection cada 30 segundos
    add_periodic_task(30.0, pump_detection_strategy)
    
    # Top movers cada 5 minutos
    add_periodic_task(300.0, top_movers_strategy)
    
    # Monitoreo de trades cada minuto
    add_periodic_task(60.0, monitor_open_trades)
    
    # Resumen diario a las 00:00 UTC
    add_periodic_task(crontab(hour=0, minute=0), send_daily_summary)

# ============================================================================
# NOTIFICACIONES
# ============================================================================

def notify_pump_detected(symbol, price_change, volume_mult):
    """
    Notifica detección de pump por Telegram
    """
    message = f"""
🚨 PUMP DETECTADO 🚨

📊 Símbolo: {symbol}
📈 Cambio: {price_change:.2f}%
📊 Volumen: {volume_mult:.2f}x
🕐 Hora: {datetime.now().strftime('%H:%M:%S')}
    """
    
    send_telegram_message(message)

def notify_top_mover_detected(symbol, signal, score):
    """
    Notifica detección de top mover
    """
    emoji = "🟢" if signal == 'long' else "🔴"
    
    message = f"""
📊 TOP MOVER DETECTADO 📊

{emoji} Símbolo: {symbol}
🎯 Señal: {signal.upper()}
⭐ Score: {score:.1f}/100
🕐 Hora: {datetime.now().strftime('%H:%M:%S')}
    """
    
    send_telegram_message(message)

def notify_trade_closed(symbol, pnl, pnl_percent, reason):
    """
    Notifica cierre de trade
    """
    emoji = "🟢" if pnl > 0 else "🔴"
    
    message = f"""
🏁 TRADE CERRADO 🏁

{emoji} Símbolo: {symbol}
💰 P&L: ${pnl:.2f} ({pnl_percent:.2f}%)
📋 Razón: {reason}
🕐 Hora: {datetime.now().strftime('%H:%M:%S')}
    """
    
    send_telegram_message(message)

# ============================================================================
# RESUMEN
# ============================================================================

"""
RESUMEN DE AMBOS CAMINOS:

1. PUMP DETECTION:
   - Escaneo cada 30 segundos
   - Detecta movimientos >5% en ≤5 min
   - Requiere volumen 2x promedio
   - SL/TP agresivos (-3%/+6%)
   - Score de calidad basado en velocidad, volumen y cambio

2. TOP MOVERS:
   - Escaneo cada 5 minutos
   - Analiza movimientos ≥2.5% en 30 min
   - Análisis técnico completo (EMA, RSI, MACD, BB)
   - IA con LSTM + PPO
   - Score combinado técnico + IA
   - SL/TP moderados (-2.5%/+5%)

GESTIÓN DE RIESGO COMÚN:
- Máximo 5 operaciones simultáneas
- Cooldown tras 3 pérdidas consecutivas
- Stop loss y take profit automáticos
- Trailing stop opcional
- Notificaciones por Telegram

ARQUITECTURA:
- Celery para ejecución asíncrona
- PostgreSQL para persistencia
- Redis como broker de mensajes
- Telegram para notificaciones
- Logs detallados para monitoreo
"""
