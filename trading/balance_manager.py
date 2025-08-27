"""
Balance Manager para CryptoPump Bot
Maneja el balance inicial de 200 USDT y objetivo del 75% diario
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Optional
from loguru import logger
from config import Config

class BalanceManager:
    def __init__(self, config: Config):
        self.config = config
        self.balance_file = "data/balance.json"
        self.ensure_data_directory()
        self.load_balance_data()
        
    def ensure_data_directory(self):
        """Asegura que existe el directorio de datos"""
        os.makedirs("data", exist_ok=True)
    
    def load_balance_data(self):
        """Carga datos de balance desde archivo"""
        try:
            if os.path.exists(self.balance_file):
                with open(self.balance_file, 'r') as f:
                    self.balance_data = json.load(f)
            else:
                # Inicializar con saldo inicial
                self.balance_data = {
                    'initial_balance': self.config.INITIAL_BALANCE,
                    'current_balance': self.config.INITIAL_BALANCE,
                    'daily_target': self.config.DAILY_TARGET_AMOUNT,
                    'daily_start_balance': self.config.INITIAL_BALANCE,
                    'daily_pnl': 0.0,
                    'daily_pnl_percent': 0.0,
                    'total_pnl': 0.0,
                    'total_pnl_percent': 0.0,
                    'trades_today': 0,
                    'winning_trades_today': 0,
                    'losing_trades_today': 0,
                    'last_reset_date': datetime.now().strftime('%Y-%m-%d'),
                    'created_at': datetime.now().isoformat(),
                    'updated_at': datetime.now().isoformat()
                }
                self.save_balance_data()
                
        except Exception as e:
            logger.error(f"Error loading balance data: {e}")
            self.reset_balance_data()
    
    def save_balance_data(self):
        """Guarda datos de balance en archivo"""
        try:
            self.balance_data['updated_at'] = datetime.now().isoformat()
            with open(self.balance_file, 'w') as f:
                json.dump(self.balance_data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving balance data: {e}")
    
    def reset_balance_data(self):
        """Resetea datos de balance"""
        self.balance_data = {
            'initial_balance': self.config.INITIAL_BALANCE,
            'current_balance': self.config.INITIAL_BALANCE,
            'daily_target': self.config.DAILY_TARGET_AMOUNT,
            'daily_start_balance': self.config.INITIAL_BALANCE,
            'daily_pnl': 0.0,
            'daily_pnl_percent': 0.0,
            'total_pnl': 0.0,
            'total_pnl_percent': 0.0,
            'trades_today': 0,
            'winning_trades_today': 0,
            'losing_trades_today': 0,
            'last_reset_date': datetime.now().strftime('%Y-%m-%d'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.save_balance_data()
    
    def check_daily_reset(self):
        """Verifica si es necesario resetear datos diarios"""
        today = datetime.now().strftime('%Y-%m-%d')
        if self.balance_data['last_reset_date'] != today:
            logger.info("Nuevo día detectado, reseteando datos diarios")
            self.balance_data['daily_start_balance'] = self.balance_data['current_balance']
            self.balance_data['daily_pnl'] = 0.0
            self.balance_data['daily_pnl_percent'] = 0.0
            self.balance_data['trades_today'] = 0
            self.balance_data['winning_trades_today'] = 0
            self.balance_data['losing_trades_today'] = 0
            self.balance_data['last_reset_date'] = today
            self.save_balance_data()
    
    def get_current_balance(self) -> float:
        """Obtiene balance actual"""
        self.check_daily_reset()
        return self.balance_data['current_balance']
    
    def get_daily_progress(self) -> Dict:
        """Obtiene progreso hacia objetivo diario"""
        self.check_daily_reset()
        
        current_balance = self.balance_data['current_balance']
        daily_start = self.balance_data['daily_start_balance']
        daily_target = self.config.DAILY_TARGET_AMOUNT
        
        daily_pnl = current_balance - daily_start
        daily_pnl_percent = (daily_pnl / daily_start) * 100 if daily_start > 0 else 0
        progress_percent = (daily_pnl / daily_target) * 100 if daily_target > 0 else 0
        
        return {
            'current_balance': current_balance,
            'daily_start_balance': daily_start,
            'daily_pnl': daily_pnl,
            'daily_pnl_percent': daily_pnl_percent,
            'daily_target': daily_target,
            'progress_percent': progress_percent,
            'remaining_target': daily_target - daily_pnl
        }
    
    def calculate_position_size(self, available_balance: float) -> float:
        """Calcula tamaño de posición basado en configuración"""
        position_size = available_balance * self.config.CAPITAL_PERCENTAGE
        
        # Asegurar que no exceda el balance disponible
        if position_size > available_balance:
            position_size = available_balance * 0.95  # 95% del balance disponible
        
        return position_size
    
    def can_trade(self, required_amount: float) -> bool:
        """Verifica si se puede realizar una operación"""
        self.check_daily_reset()
        
        current_balance = self.balance_data['current_balance']
        
        # Verificar si hay suficiente balance
        if required_amount > current_balance:
            return False
        
        # Verificar límite de pérdida diaria
        daily_pnl = current_balance - self.balance_data['daily_start_balance']
        max_daily_loss = self.balance_data['daily_start_balance'] * self.config.MAX_DAILY_LOSS
        
        if daily_pnl < -max_daily_loss:
            logger.warning("Límite de pérdida diaria alcanzado")
            return False
        
        # Verificar número máximo de trades simultáneos
        if self.balance_data['trades_today'] >= self.config.MAX_CONCURRENT_TRADES:
            logger.warning("Máximo número de trades simultáneos alcanzado")
            return False
        
        return True
    
    def record_trade(self, trade_info: Dict):
        """Registra una operación completada"""
        self.check_daily_reset()
        
        pnl = trade_info.get('pnl', 0)
        pnl_percent = trade_info.get('pnl_percent', 0)
        
        # Actualizar balance
        self.balance_data['current_balance'] += pnl
        self.balance_data['total_pnl'] += pnl
        
        # Actualizar estadísticas diarias
        self.balance_data['daily_pnl'] += pnl
        self.balance_data['trades_today'] += 1
        
        if pnl > 0:
            self.balance_data['winning_trades_today'] += 1
        else:
            self.balance_data['losing_trades_today'] += 1
        
        # Calcular porcentajes
        if self.balance_data['daily_start_balance'] > 0:
            self.balance_data['daily_pnl_percent'] = (
                self.balance_data['daily_pnl'] / self.balance_data['daily_start_balance']
            ) * 100
        
        if self.config.INITIAL_BALANCE > 0:
            self.balance_data['total_pnl_percent'] = (
                self.balance_data['total_pnl'] / self.config.INITIAL_BALANCE
            ) * 100
        
        self.save_balance_data()
        
        logger.info(f"Trade registrado: P&L ${pnl:.2f} ({pnl_percent:.2f}%)")
    
    def get_balance_summary(self) -> Dict:
        """Obtiene resumen completo del balance"""
        self.check_daily_reset()
        
        progress = self.get_daily_progress()
        
        return {
            'initial_balance': self.config.INITIAL_BALANCE,
            'current_balance': self.balance_data['current_balance'],
            'daily_target': self.config.DAILY_TARGET_AMOUNT,
            'daily_progress': progress,
            'total_pnl': self.balance_data['total_pnl'],
            'total_pnl_percent': self.balance_data['total_pnl_percent'],
            'trades_today': self.balance_data['trades_today'],
            'winning_trades_today': self.balance_data['winning_trades_today'],
            'losing_trades_today': self.balance_data['losing_trades_today'],
            'win_rate_today': (
                self.balance_data['winning_trades_today'] / self.balance_data['trades_today'] * 100
                if self.balance_data['trades_today'] > 0 else 0
            ),
            'last_reset_date': self.balance_data['last_reset_date'],
            'updated_at': self.balance_data['updated_at']
        }
    
    def is_daily_target_reached(self) -> bool:
        """Verifica si se ha alcanzado el objetivo diario"""
        progress = self.get_daily_progress()
        return progress['daily_pnl'] >= self.config.DAILY_TARGET_AMOUNT
    
    def get_available_trading_balance(self) -> float:
        """Obtiene balance disponible para trading"""
        current_balance = self.get_current_balance()
        return current_balance * 0.95  # 95% del balance actual para seguridad


