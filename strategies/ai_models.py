import numpy as np
import pandas as pd
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
from stable_baselines3 import PPO
from stable_baselines3.common.vec_env import DummyVecEnv
from typing import Dict, List, Tuple
from loguru import logger
import joblib
import os

class LSTMPredictor:
    def __init__(self, config, model_path: str = 'models/lstm_model.h5'):
        self.config = config
        self.model_path = model_path
        self.model = None
        self.scaler = None
        self.sequence_length = config.LSTM_SEQUENCE_LENGTH
        self.prediction_horizon = config.LSTM_PREDICTION_HORIZON
        
    def prepare_data(self, df: pd.DataFrame) -> Tuple[np.ndarray, np.ndarray]:
        """Prepara datos para LSTM"""
        # Normalizar datos
        data = df[['close', 'volume', 'high', 'low']].values
        
        # Crear secuencias
        X, y = [], []
        for i in range(self.sequence_length, len(data) - self.prediction_horizon):
            X.append(data[i-self.sequence_length:i])
            y.append(data[i:i+self.prediction_horizon, 0])  # Solo precio de cierre
            
        return np.array(X), np.array(y)
    
    def build_model(self, input_shape: Tuple[int, int]) -> Sequential:
        """Construye modelo LSTM"""
        model = Sequential([
            LSTM(50, return_sequences=True, input_shape=input_shape),
            Dropout(0.2),
            LSTM(50, return_sequences=False),
            Dropout(0.2),
            Dense(25),
            Dense(self.prediction_horizon)
        ])
        
        model.compile(optimizer=Adam(learning_rate=0.001), loss='mse')
        return model
    
    def train(self, df: pd.DataFrame, epochs: int = 100, batch_size: int = 32):
        """Entrena modelo LSTM"""
        try:
            X, y = self.prepare_data(df)
            
            if len(X) < 100:
                logger.warning("Insufficient data for LSTM training")
                return False
            
            # Split train/validation
            split = int(0.8 * len(X))
            X_train, X_val = X[:split], X[split:]
            y_train, y_val = y[:split], y[split:]
            
            # Build and train model
            self.model = self.build_model((X.shape[1], X.shape[2]))
            
            history = self.model.fit(
                X_train, y_train,
                validation_data=(X_val, y_val),
                epochs=epochs,
                batch_size=batch_size,
                verbose=0
            )
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            
            logger.info(f"LSTM model trained successfully. Final loss: {history.history['loss'][-1]:.6f}")
            return True
            
        except Exception as e:
            logger.error(f"Error training LSTM model: {e}")
            return False
    
    def load_model(self) -> bool:
        """Carga modelo LSTM pre-entrenado"""
        try:
            if os.path.exists(self.model_path):
                self.model = tf.keras.models.load_model(self.model_path)
                logger.info("LSTM model loaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading LSTM model: {e}")
            return False
    
    def predict(self, df: pd.DataFrame) -> float:
        """Predice precio futuro"""
        try:
            if self.model is None:
                if not self.load_model():
                    return 0.0
            
            # Preparar datos para predicción
            data = df[['close', 'volume', 'high', 'low']].values
            if len(data) < self.sequence_length:
                return 0.0
            
            # Última secuencia
            sequence = data[-self.sequence_length:].reshape(1, self.sequence_length, 4)
            
            # Predicción
            prediction = self.model.predict(sequence, verbose=0)
            
            # Retornar cambio porcentual promedio
            current_price = data[-1, 0]
            predicted_prices = prediction[0]
            avg_change = np.mean([(p - current_price) / current_price * 100 for p in predicted_prices])
            
            return avg_change
            
        except Exception as e:
            logger.error(f"Error in LSTM prediction: {e}")
            return 0.0

class PPOTrader:
    def __init__(self, config, model_path: str = 'models/ppo_model.zip'):
        self.config = config
        self.model_path = model_path
        self.model = None
        self.env = None
        
    def create_env(self, df: pd.DataFrame):
        """Crea entorno de trading para PPO"""
        from strategies.trading_env import TradingEnvironment
        
        self.env = DummyVecEnv([lambda: TradingEnvironment(df, self.config)])
        return self.env
    
    def train(self, df: pd.DataFrame, total_timesteps: int = 10000):
        """Entrena modelo PPO"""
        try:
            if self.env is None:
                self.create_env(df)
            
            self.model = PPO(
                "MlpPolicy",
                self.env,
                learning_rate=0.0003,
                n_steps=2048,
                batch_size=64,
                n_epochs=10,
                gamma=0.99,
                verbose=0
            )
            
            self.model.learn(total_timesteps=total_timesteps)
            
            # Save model
            os.makedirs(os.path.dirname(self.model_path), exist_ok=True)
            self.model.save(self.model_path)
            
            logger.info(f"PPO model trained successfully for {total_timesteps} timesteps")
            return True
            
        except Exception as e:
            logger.error(f"Error training PPO model: {e}")
            return False
    
    def load_model(self) -> bool:
        """Carga modelo PPO pre-entrenado"""
        try:
            if os.path.exists(self.model_path):
                self.model = PPO.load(self.model_path)
                logger.info("PPO model loaded successfully")
                return True
            return False
        except Exception as e:
            logger.error(f"Error loading PPO model: {e}")
            return False
    
    def get_action(self, state: np.ndarray) -> int:
        """Obtiene acción del modelo PPO"""
        try:
            if self.model is None:
                if not self.load_model():
                    return 1  # Hold
            
            action, _ = self.model.predict(state, deterministic=True)
            return action
            
        except Exception as e:
            logger.error(f"Error getting PPO action: {e}")
            return 1  # Hold

class AIModelManager:
    def __init__(self, config):
        self.config = config
        self.lstm = LSTMPredictor(config)
        self.ppo = PPOTrader(config)
        
    def get_ai_score(self, df: pd.DataFrame) -> float:
        """Combina predicciones de LSTM y PPO para score final"""
        try:
            # LSTM prediction
            lstm_prediction = self.lstm.predict(df)
            
            # PPO action (si hay modelo disponible)
            if len(df) >= 50:
                # Crear estado para PPO (simplificado)
                recent_data = df.tail(50)
                state = np.array([
                    recent_data['close'].pct_change().mean(),
                    recent_data['volume'].pct_change().mean(),
                    recent_data['close'].std(),
                    recent_data['volume'].std()
                ])
                
                ppo_action = self.ppo.get_action(state)
                ppo_score = (ppo_action - 1) * 25  # Convertir acción a score
            else:
                ppo_score = 0
            
            # Combinar scores
            ai_score = (lstm_prediction * 0.7 + ppo_score * 0.3)
            
            # Normalizar a 0-100
            ai_score = max(0, min(100, 50 + ai_score * 10))
            
            return ai_score
            
        except Exception as e:
            logger.error(f"Error calculating AI score: {e}")
            return 50.0
    
    def get_signal(self, df: pd.DataFrame) -> str:
        """Determina señal basada en IA"""
        score = self.get_ai_score(df)
        
        if score > 70:
            return 'long'
        elif score < 30:
            return 'short'
        else:
            return 'neutral'
