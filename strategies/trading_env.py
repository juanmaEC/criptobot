import numpy as np
import pandas as pd
from gym import Env
from gym.spaces import Box, Discrete
from typing import Dict, Any

class TradingEnvironment(Env):
    def __init__(self, df: pd.DataFrame, config):
        super(TradingEnvironment, self).__init__()
        
        self.df = df
        self.config = config
        self.current_step = 0
        self.initial_balance = 10000
        self.balance = self.initial_balance
        self.shares_held = 0
        self.total_shares_sold = 0
        self.total_sales_value = 0
        
        # Action space: 0 = sell, 1 = hold, 2 = buy
        self.action_space = Discrete(3)
        
        # Observation space: price, volume, technical indicators
        self.observation_space = Box(
            low=-np.inf, 
            high=np.inf, 
            shape=(10,), 
            dtype=np.float32
        )
        
    def _get_observation(self):
        """Obtiene observación actual del mercado"""
        if self.current_step >= len(self.df):
            return np.zeros(10)
        
        current_data = self.df.iloc[self.current_step]
        
        # Precios normalizados
        price = current_data['close'] / self.df['close'].max()
        volume = current_data['volume'] / self.df['volume'].max()
        
        # Indicadores técnicos
        if self.current_step >= 20:
            recent_data = self.df.iloc[self.current_step-20:self.current_step+1]
            
            # RSI
            rsi = self._calculate_rsi(recent_data['close'])
            
            # MACD
            macd, macd_signal = self._calculate_macd(recent_data['close'])
            
            # Bollinger Bands
            bb_position = self._calculate_bb_position(recent_data['close'])
            
            # Momentum
            momentum = (current_data['close'] - recent_data['close'].iloc[-5]) / recent_data['close'].iloc[-5]
            
        else:
            rsi = 50
            macd = 0
            macd_signal = 0
            bb_position = 0.5
            momentum = 0
        
        # Portfolio state
        portfolio_value = self.balance + (self.shares_held * current_data['close'])
        portfolio_return = (portfolio_value - self.initial_balance) / self.initial_balance
        
        return np.array([
            price,
            volume,
            rsi / 100,
            macd,
            macd_signal,
            bb_position,
            momentum,
            portfolio_return,
            self.shares_held / 1000,  # Normalized shares
            self.balance / self.initial_balance
        ], dtype=np.float32)
    
    def _calculate_rsi(self, prices, period=14):
        """Calcula RSI"""
        delta = prices.diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()
        rs = gain / loss
        rsi = 100 - (100 / (1 + rs))
        return rsi.iloc[-1] if not rsi.empty else 50
    
    def _calculate_macd(self, prices, fast=12, slow=26, signal=9):
        """Calcula MACD"""
        ema_fast = prices.ewm(span=fast).mean()
        ema_slow = prices.ewm(span=slow).mean()
        macd = ema_fast - ema_slow
        macd_signal = macd.ewm(span=signal).mean()
        return macd.iloc[-1] if not macd.empty else 0, macd_signal.iloc[-1] if not macd_signal.empty else 0
    
    def _calculate_bb_position(self, prices, period=20, std=2):
        """Calcula posición en Bollinger Bands"""
        sma = prices.rolling(window=period).mean()
        std_dev = prices.rolling(window=period).std()
        upper_band = sma + (std_dev * std)
        lower_band = sma - (std_dev * std)
        
        current_price = prices.iloc[-1]
        if upper_band.iloc[-1] != lower_band.iloc[-1]:
            position = (current_price - lower_band.iloc[-1]) / (upper_band.iloc[-1] - lower_band.iloc[-1])
            return max(0, min(1, position))
        return 0.5
    
    def step(self, action):
        """Ejecuta acción y retorna nuevo estado"""
        self.current_step += 1
        
        if self.current_step >= len(self.df):
            return self._get_observation(), 0, True, {}
        
        current_price = self.df.iloc[self.current_step]['close']
        
        # Ejecutar acción
        reward = 0
        if action == 0:  # Sell
            if self.shares_held > 0:
                self.total_sales_value += self.shares_held * current_price
                self.total_shares_sold += self.shares_held
                self.balance += self.shares_held * current_price
                self.shares_held = 0
        elif action == 2:  # Buy
            if self.balance > 0:
                shares_to_buy = self.balance / current_price
                self.shares_held += shares_to_buy
                self.balance = 0
        
        # Calcular reward
        portfolio_value = self.balance + (self.shares_held * current_price)
        reward = (portfolio_value - self.initial_balance) / self.initial_balance
        
        # Penalizar por trading frecuente
        if action != 1:  # Si no es hold
            reward -= 0.001
        
        done = self.current_step >= len(self.df) - 1
        
        return self._get_observation(), reward, done, {}
    
    def reset(self):
        """Resetea el entorno"""
        self.current_step = 0
        self.balance = self.initial_balance
        self.shares_held = 0
        self.total_shares_sold = 0
        self.total_sales_value = 0
        return self._get_observation()
    
    def render(self):
        """Renderiza el estado actual"""
        pass
