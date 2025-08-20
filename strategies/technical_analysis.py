import pandas as pd
import numpy as np
import ta
from typing import Dict, Tuple
from loguru import logger

class TechnicalAnalyzer:
    def __init__(self, config):
        self.config = config
        
    def calculate_ema(self, prices: pd.Series, fast_period: int = None, slow_period: int = None) -> Dict[str, pd.Series]:
        """Calcula EMA rápida y lenta"""
        fast_period = fast_period or self.config.EMA_FAST
        slow_period = slow_period or self.config.EMA_SLOW
        
        ema_fast = ta.trend.ema_indicator(prices, window=fast_period)
        ema_slow = ta.trend.ema_indicator(prices, window=slow_period)
        
        return {
            'ema_fast': ema_fast,
            'ema_slow': ema_slow,
            'ema_cross': ema_fast > ema_slow
        }
    
    def calculate_rsi(self, prices: pd.Series, period: int = None) -> pd.Series:
        """Calcula RSI"""
        period = period or self.config.RSI_PERIOD
        return ta.momentum.rsi(prices, window=period)
    
    def calculate_macd(self, prices: pd.Series, fast: int = None, slow: int = None, signal: int = None) -> Dict[str, pd.Series]:
        """Calcula MACD"""
        fast = fast or self.config.MACD_FAST
        slow = slow or self.config.MACD_SLOW
        signal = signal or self.config.MACD_SIGNAL
        
        macd = ta.trend.macd(prices, window_fast=fast, window_slow=slow)
        macd_signal = ta.trend.macd_signal(prices, window_fast=fast, window_slow=slow, window_sign=signal)
        macd_histogram = ta.trend.macd_diff(prices, window_fast=fast, window_slow=slow, window_sign=signal)
        
        return {
            'macd': macd,
            'macd_signal': macd_signal,
            'macd_histogram': macd_histogram,
            'macd_cross': macd > macd_signal
        }
    
    def calculate_bollinger_bands(self, prices: pd.Series, period: int = None, std: float = None) -> Dict[str, pd.Series]:
        """Calcula Bollinger Bands"""
        period = period or self.config.BOLLINGER_PERIOD
        std = std or self.config.BOLLINGER_STD
        
        bb_upper = ta.volatility.bollinger_hband(prices, window=period, window_dev=std)
        bb_middle = ta.volatility.bollinger_mavg(prices, window=period)
        bb_lower = ta.volatility.bollinger_lband(prices, window=period, window_dev=std)
        
        return {
            'bb_upper': bb_upper,
            'bb_middle': bb_middle,
            'bb_lower': bb_lower,
            'bb_position': (prices - bb_lower) / (bb_upper - bb_lower)
        }
    
    def calculate_atr(self, high: pd.Series, low: pd.Series, close: pd.Series, period: int = None) -> pd.Series:
        """Calcula ATR (Average True Range)"""
        period = period or self.config.ATR_PERIOD
        return ta.volatility.average_true_range(high, low, close, window=period)
    
    def calculate_volume_indicators(self, volume: pd.Series, prices: pd.Series) -> Dict[str, pd.Series]:
        """Calcula indicadores de volumen"""
        volume_sma = ta.volume.volume_sma(volume, window=20)
        volume_ratio = volume / volume_sma
        
        # On Balance Volume
        obv = ta.volume.on_balance_volume(prices, volume)
        
        return {
            'volume_sma': volume_sma,
            'volume_ratio': volume_ratio,
            'obv': obv
        }
    
    def get_technical_score(self, df: pd.DataFrame) -> float:
        """Calcula score técnico combinado (0-100)"""
        if len(df) < 50:
            return 50.0
        
        try:
            # EMA signals
            ema_data = self.calculate_ema(df['close'])
            ema_score = 20 if ema_data['ema_cross'].iloc[-1] else -20
            
            # RSI signals
            rsi = self.calculate_rsi(df['close'])
            current_rsi = rsi.iloc[-1]
            if current_rsi < 30:
                rsi_score = 20  # Oversold
            elif current_rsi > 70:
                rsi_score = -20  # Overbought
            else:
                rsi_score = 0
            
            # MACD signals
            macd_data = self.calculate_macd(df['close'])
            macd_score = 20 if macd_data['macd_cross'].iloc[-1] else -20
            
            # Bollinger Bands
            bb_data = self.calculate_bollinger_bands(df['close'])
            bb_position = bb_data['bb_position'].iloc[-1]
            if bb_position < 0.2:
                bb_score = 20  # Near lower band
            elif bb_position > 0.8:
                bb_score = -20  # Near upper band
            else:
                bb_score = 0
            
            # Volume
            volume_data = self.calculate_volume_indicators(df['volume'], df['close'])
            volume_score = 10 if volume_data['volume_ratio'].iloc[-1] > 1.5 else 0
            
            # Price momentum
            price_change = (df['close'].iloc[-1] - df['close'].iloc[-5]) / df['close'].iloc[-5] * 100
            momentum_score = min(20, max(-20, price_change * 2))
            
            # Combine scores
            total_score = 50 + ema_score + rsi_score + macd_score + bb_score + volume_score + momentum_score
            
            return max(0, min(100, total_score))
            
        except Exception as e:
            logger.error(f"Error calculating technical score: {e}")
            return 50.0
    
    def get_signal_direction(self, df: pd.DataFrame) -> str:
        """Determina dirección de señal basada en análisis técnico"""
        score = self.get_technical_score(df)
        
        if score > 70:
            return 'long'
        elif score < 30:
            return 'short'
        else:
            return 'neutral'
    
    def calculate_support_resistance(self, df: pd.DataFrame, window: int = 20) -> Dict[str, float]:
        """Calcula niveles de soporte y resistencia"""
        highs = df['high'].rolling(window=window, center=True).max()
        lows = df['low'].rolling(window=window, center=True).min()
        
        current_price = df['close'].iloc[-1]
        
        # Encontrar resistencia más cercana
        resistance_levels = highs[highs > current_price].dropna()
        nearest_resistance = resistance_levels.iloc[0] if len(resistance_levels) > 0 else current_price * 1.05
        
        # Encontrar soporte más cercano
        support_levels = lows[lows < current_price].dropna()
        nearest_support = support_levels.iloc[0] if len(support_levels) > 0 else current_price * 0.95
        
        return {
            'support': nearest_support,
            'resistance': nearest_resistance
        }
