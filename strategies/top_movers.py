import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from loguru import logger
from database.models import TopMoverSignal
from sqlalchemy.orm import Session
from strategies.technical_analysis import TechnicalAnalyzer
from strategies.ai_models import AIModelManager

class TopMoversStrategy:
    def __init__(self, config, db_session: Session):
        self.config = config
        self.db = db_session
        self.technical_analyzer = TechnicalAnalyzer(config)
        self.ai_manager = AIModelManager(config)
        self.analyzed_symbols = set()  # Para evitar re-análisis frecuente
        
    def scan_top_movers(self, all_market_data: Dict[str, pd.DataFrame]) -> List[Dict]:
        """Escanea todos los símbolos para encontrar top movers"""
        try:
            top_movers = []
            
            for symbol, market_data in all_market_data.items():
                if len(market_data) < 50:  # Necesitamos suficientes datos
                    continue
                
                # Verificar si ya analizamos recientemente
                if symbol in self.analyzed_symbols:
                    continue
                
                # Calcular movimiento en ventana de tiempo
                movement_info = self._calculate_movement(symbol, market_data)
                
                if movement_info and movement_info['price_change_percent'] >= self.config.TOP_MOVERS_THRESHOLD:
                    # Análisis completo
                    analysis = self._analyze_symbol(symbol, market_data, movement_info)
                    
                    if analysis:
                        top_movers.append(analysis)
                        self.analyzed_symbols.add(symbol)
            
            # Limpiar símbolos analizados antiguos
            self._clean_analyzed_symbols()
            
            # Ordenar por score final
            top_movers.sort(key=lambda x: x['final_score'], reverse=True)
            
            return top_movers[:10]  # Top 10 movers
            
        except Exception as e:
            logger.error(f"Error scanning top movers: {e}")
            return []
    
    def _calculate_movement(self, symbol: str, market_data: pd.DataFrame) -> Optional[Dict]:
        """Calcula movimiento de precio en ventana de tiempo"""
        try:
            if len(market_data) < self.config.TOP_MOVERS_TIME_WINDOW // 60:
                return None
            
            # Obtener datos de la ventana de tiempo
            window_data = market_data.tail(self.config.TOP_MOVERS_TIME_WINDOW // 60)
            
            start_price = window_data.iloc[0]['close']
            end_price = window_data.iloc[-1]['close']
            price_change_percent = ((end_price - start_price) / start_price) * 100
            
            # Calcular volatilidad
            returns = window_data['close'].pct_change().dropna()
            volatility = returns.std() * np.sqrt(24 * 60)  # Anualizada
            
            # Calcular volumen promedio
            avg_volume = window_data['volume'].mean()
            current_volume = window_data.iloc[-1]['volume']
            volume_ratio = current_volume / avg_volume if avg_volume > 0 else 0
            
            return {
                'symbol': symbol,
                'price_change_percent': price_change_percent,
                'volatility': volatility,
                'volume_ratio': volume_ratio,
                'current_price': end_price,
                'timestamp': datetime.now()
            }
            
        except Exception as e:
            logger.error(f"Error calculating movement for {symbol}: {e}")
            return None
    
    def _analyze_symbol(self, symbol: str, market_data: pd.DataFrame, movement_info: Dict) -> Optional[Dict]:
        """Análisis completo de símbolo"""
        try:
            # Filtrar scams y tokens de baja calidad
            if not self._is_valid_symbol(symbol, market_data):
                return None
            
            # Análisis técnico
            technical_score = self.technical_analyzer.get_technical_score(market_data)
            technical_signal = self.technical_analyzer.get_signal_direction(market_data)
            
            # Análisis de IA
            ai_score = self.ai_manager.get_ai_score(market_data)
            ai_signal = self.ai_manager.get_signal(market_data)
            
            # Score combinado
            final_score = (technical_score * 0.6 + ai_score * 0.4)
            
            # Determinar señal final
            if technical_signal == ai_signal and technical_signal != 'neutral':
                final_signal = technical_signal
            elif final_score > 70:
                final_signal = 'long'
            elif final_score < 30:
                final_signal = 'short'
            else:
                final_signal = 'neutral'
            
            analysis = {
                'symbol': symbol,
                'price_change_percent': movement_info['price_change_percent'],
                'technical_score': technical_score,
                'ai_score': ai_score,
                'final_score': final_score,
                'technical_signal': technical_signal,
                'ai_signal': ai_signal,
                'final_signal': final_signal,
                'volatility': movement_info['volatility'],
                'volume_ratio': movement_info['volume_ratio'],
                'current_price': movement_info['current_price'],
                'timestamp': movement_info['timestamp']
            }
            
            # Guardar señal en base de datos
            self._save_top_mover_signal(analysis)
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error analyzing symbol {symbol}: {e}")
            return None
    
    def _is_valid_symbol(self, symbol: str, market_data: pd.DataFrame) -> bool:
        """Verifica si el símbolo es válido (no es scam)"""
        try:
            # Filtrar por volumen mínimo
            avg_volume = market_data['volume'].mean()
            if avg_volume < 10000:  # Volumen mínimo
                return False
            
            # Filtrar por volatilidad extrema (posible manipulación)
            returns = market_data['close'].pct_change().dropna()
            volatility = returns.std()
            if volatility > 0.5:  # Más de 50% de volatilidad diaria
                return False
            
            # Filtrar por gaps extremos
            price_changes = market_data['close'].pct_change().abs()
            if price_changes.max() > 0.3:  # Más de 30% en una vela
                return False
            
            # Filtrar símbolos con patrones sospechosos
            if self._has_suspicious_patterns(market_data):
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating symbol {symbol}: {e}")
            return False
    
    def _has_suspicious_patterns(self, market_data: pd.DataFrame) -> bool:
        """Detecta patrones sospechosos de manipulación"""
        try:
            # Verificar si hay muchas velas con el mismo precio
            unique_prices = market_data['close'].nunique()
            if unique_prices < len(market_data) * 0.3:  # Menos del 30% de precios únicos
                return True
            
            # Verificar si hay gaps extremos frecuentes
            price_changes = market_data['close'].pct_change().abs()
            extreme_changes = (price_changes > 0.1).sum()  # Más de 10% de cambio
            if extreme_changes > len(market_data) * 0.2:  # Más del 20% de velas extremas
                return True
            
            # Verificar si el volumen es muy irregular
            volume_changes = market_data['volume'].pct_change().abs()
            if volume_changes.std() > 2:  # Desviación estándar muy alta
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking suspicious patterns: {e}")
            return True
    
    def _clean_analyzed_symbols(self):
        """Limpia símbolos analizados hace más de 1 hora"""
        # En una implementación real, usaríamos timestamps
        # Por simplicidad, limitamos el tamaño del set
        if len(self.analyzed_symbols) > 100:
            self.analyzed_symbols.clear()
    
    def _save_top_mover_signal(self, analysis: Dict):
        """Guarda señal de top mover en base de datos"""
        try:
            signal = TopMoverSignal(
                symbol=analysis['symbol'],
                price_change_percent=analysis['price_change_percent'],
                technical_score=analysis['technical_score'],
                ai_score=analysis['ai_score'],
                final_score=analysis['final_score'],
                signal=analysis['final_signal']
            )
            
            self.db.add(signal)
            self.db.commit()
            
        except Exception as e:
            logger.error(f"Error saving top mover signal: {e}")
            self.db.rollback()
    
    def should_trade_top_mover(self, analysis: Dict) -> bool:
        """Determina si se debe operar el top mover"""
        try:
            # Verificar score mínimo
            if analysis['final_score'] < 75:
                return False
            
            # Verificar que las señales coincidan
            if analysis['technical_signal'] != analysis['ai_signal']:
                return False
            
            # Verificar volatilidad razonable
            if analysis['volatility'] > 0.3:  # Más de 30% anualizada
                return False
            
            # Verificar volumen suficiente
            if analysis['volume_ratio'] < 1.5:
                return False
            
            # Verificar límites de operaciones activas
            active_trades = self._get_active_trades_count()
            if active_trades >= self.config.MAX_CONCURRENT_TRADES:
                return False
            
            # Verificar cooldown
            if self._is_in_cooldown():
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error determining if should trade top mover: {e}")
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
            
            # Si hay más de 2 pérdidas consecutivas, activar cooldown
            consecutive_losses = 0
            for trade in recent_trades:
                if trade.pnl < 0:
                    consecutive_losses += 1
                else:
                    consecutive_losses = 0
                
                if consecutive_losses >= 2:
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error checking cooldown: {e}")
            return False
    
    def calculate_position_size(self, analysis: Dict, account_balance: float) -> float:
        """Calcula tamaño de posición para top mover"""
        try:
            # Porcentaje base del capital
            base_percentage = self.config.CAPITAL_PERCENTAGE
            
            # Ajustar según score final
            score_multiplier = analysis['final_score'] / 100
            
            # Ajustar según volatilidad (menos volatilidad = posición más grande)
            volatility_multiplier = max(0.5, 1 - analysis['volatility'])
            
            # Ajustar según dirección (long vs short)
            direction_multiplier = 1.0 if analysis['final_signal'] == 'long' else 0.8
            
            final_percentage = base_percentage * score_multiplier * volatility_multiplier * direction_multiplier
            
            position_size = account_balance * final_percentage
            
            return position_size
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return account_balance * self.config.CAPITAL_PERCENTAGE
