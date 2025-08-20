import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
from database.models import PumpSignal
from sqlalchemy.orm import Session

class PumpDetector:
    def __init__(self, config, db_session: Session):
        self.config = config
        self.db = db_session
        self.detected_pumps = set()  # Para evitar duplicados
        
    def detect_pump(self, symbol: str, market_data: pd.DataFrame) -> Optional[Dict]:
        """Detecta si hay un pump en el símbolo dado"""
        try:
            if len(market_data) < 30:
                return None
            
            # Obtener datos recientes
            recent_data = market_data.tail(self.config.PUMP_TIME_WINDOW // 60 + 10)  # +10 para margen
            
            if len(recent_data) < 5:
                return None
            
            # Calcular cambio de precio en ventana de tiempo
            start_price = recent_data.iloc[0]['close']
            end_price = recent_data.iloc[-1]['close']
            price_change_percent = ((end_price - start_price) / start_price) * 100
            
            # Calcular volumen promedio
            avg_volume = recent_data['volume'].mean()
            current_volume = recent_data.iloc[-1]['volume']
            volume_multiplier = current_volume / avg_volume if avg_volume > 0 else 0
            
            # Verificar condiciones de pump
            is_pump = (
                price_change_percent >= self.config.PUMP_THRESHOLD_PERCENT and
                volume_multiplier >= self.config.PUMP_VOLUME_MULTIPLIER and
                price_change_percent > 0  # Solo subidas
            )
            
            if is_pump:
                # Verificar si ya fue detectado recientemente
                pump_key = f"{symbol}_{datetime.now().strftime('%Y%m%d_%H%M')}"
                if pump_key in self.detected_pumps:
                    return None
                
                self.detected_pumps.add(pump_key)
                
                # Limpiar pumps antiguos (más de 1 hora)
                self._clean_old_pumps()
                
                pump_info = {
                    'symbol': symbol,
                    'price_change_percent': price_change_percent,
                    'volume_multiplier': volume_multiplier,
                    'time_window': self.config.PUMP_TIME_WINDOW,
                    'current_price': end_price,
                    'volume': current_volume,
                    'timestamp': datetime.now()
                }
                
                # Guardar señal en base de datos
                self._save_pump_signal(pump_info)
                
                logger.info(f"PUMP DETECTED: {symbol} - {price_change_percent:.2f}% in {self.config.PUMP_TIME_WINDOW//60}min, Volume: {volume_multiplier:.2f}x")
                
                return pump_info
            
            return None
            
        except Exception as e:
            logger.error(f"Error detecting pump for {symbol}: {e}")
            return None
    
    def _clean_old_pumps(self):
        """Limpia pumps detectados hace más de 1 hora"""
        current_time = datetime.now()
        old_pumps = set()
        
        for pump_key in self.detected_pumps:
            try:
                # Extraer timestamp del pump_key
                parts = pump_key.split('_')
                if len(parts) >= 3:
                    pump_time = datetime.strptime(f"{parts[1]}_{parts[2]}", '%Y%m%d_%H%M')
                    if (current_time - pump_time).total_seconds() > 3600:  # 1 hora
                        old_pumps.add(pump_key)
            except:
                old_pumps.add(pump_key)
        
        self.detected_pumps -= old_pumps
    
    def _save_pump_signal(self, pump_info: Dict):
        """Guarda señal de pump en base de datos"""
        try:
            signal = PumpSignal(
                symbol=pump_info['symbol'],
                price_change_percent=pump_info['price_change_percent'],
                volume_multiplier=pump_info['volume_multiplier'],
                time_window=pump_info['time_window']
            )
            
            self.db.add(signal)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving pump signal: {e}")
            self.db.rollback()
    
    def get_pump_quality_score(self, pump_info: Dict) -> float:
        """Calcula score de calidad del pump (0-100)"""
        try:
            price_change = pump_info['price_change_percent']
            volume_mult = pump_info['volume_multiplier']
            
            # Score basado en cambio de precio (0-50 puntos)
            price_score = min(50, price_change * 5)
            
            # Score basado en volumen (0-30 puntos)
            volume_score = min(30, volume_mult * 10)
            
            # Score basado en velocidad (0-20 puntos)
            time_window_minutes = pump_info['time_window'] / 60
            speed_score = max(0, 20 - (time_window_minutes * 2))
            
            total_score = price_score + volume_score + speed_score
            
            return min(100, total_score)
            
        except Exception as e:
            logger.error(f"Error calculating pump quality score: {e}")
            return 50.0
    
    def should_trade_pump(self, pump_info: Dict) -> bool:
        """Determina si se debe operar el pump"""
        try:
            # Verificar score de calidad
            quality_score = self.get_pump_quality_score(pump_info)
            
            # Verificar si ya hay muchas operaciones activas
            active_trades = self._get_active_trades_count()
            
            # Verificar si estamos en cooldown por pérdidas recientes
            in_cooldown = self._is_in_cooldown()
            
            should_trade = (
                quality_score >= 70 and  # Score mínimo
                active_trades < self.config.MAX_CONCURRENT_TRADES and
                not in_cooldown and
                pump_info['price_change_percent'] <= 15  # No entrar en pumps muy extremos
            )
            
            return should_trade
            
        except Exception as e:
            logger.error(f"Error determining if should trade pump: {e}")
            return False
    
    def _get_active_trades_count(self) -> int:
        """Obtiene número de operaciones activas"""
        try:
            from database.models import Trade
            return self.db.query(Trade).filter(Trade.status == 'open').count()
        except Exception as e:
            logger.error(f"Error getting active trades count: {e}")
            return 0
    
    def _is_in_cooldown(self) -> bool:
        """Verifica si estamos en cooldown por pérdidas recientes"""
        try:
            from database.models import Trade
            from datetime import datetime, timedelta
            
            # Buscar pérdidas en las últimas 24 horas
            yesterday = datetime.now() - timedelta(days=1)
            recent_trades = self.db.query(Trade).filter(
                Trade.closed_at >= yesterday,
                Trade.pnl < 0
            ).all()
            
            # Si hay más de 3 pérdidas consecutivas, activar cooldown
            consecutive_losses = 0
            for trade in recent_trades:
                if trade.pnl < 0:
                    consecutive_losses += 1
                else:
                    consecutive_losses = 0
                
                if consecutive_losses >= 3:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False
    
    def calculate_position_size(self, pump_info: Dict, account_balance: float) -> float:
        """Calcula tamaño de posición para pump"""
        try:
            # Porcentaje base del capital
            base_percentage = self.config.CAPITAL_PERCENTAGE
            
            # Ajustar según calidad del pump
            quality_score = self.get_pump_quality_score(pump_info)
            quality_multiplier = quality_score / 100
            
            # Ajustar según volatilidad (pumps más rápidos = posición más pequeña)
            time_window_minutes = pump_info['time_window'] / 60
            volatility_multiplier = max(0.5, 1 - (time_window_minutes / 10))
            
            final_percentage = base_percentage * quality_multiplier * volatility_multiplier
            
            position_size = account_balance * final_percentage
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return account_balance * self.config.CAPITAL_PERCENTAGE
