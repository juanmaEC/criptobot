#!/usr/bin/env python3
"""
Bot de Trading Algorítmico para Detección de Pumps y Top Movers
Ejecuta 24/7 usando Celery + Celery Beat para scheduler y ejecución asíncrona
Configurado para saldo inicial de 200 USDT y objetivo del 75% diario
"""

import os
import sys
import signal
import time
from loguru import logger
from config import Config
from database.models import create_tables
from notifications.telegram_bot import TelegramNotifier
from trading.binance_client import BinanceClient
from trading.balance_manager import BalanceManager

# Configurar logging
logger.add("logs/bot.log", rotation="1 day", retention="7 days", level="INFO")

class CryptoPumpBot:
    def __init__(self):
        self.config = Config()
        self.telegram_notifier = TelegramNotifier(self.config)
        self.binance_client = BinanceClient(self.config)
        self.balance_manager = BalanceManager(self.config)
        self.running = False
        
    def initialize(self):
        """Inicializa el bot"""
        try:
            logger.info("🚀 Iniciando CryptoPump Bot...")
            
            # Crear directorios necesarios
            os.makedirs("logs", exist_ok=True)
            os.makedirs("models", exist_ok=True)
            os.makedirs("data", exist_ok=True)
            
            # Crear tablas de base de datos
            create_tables()
            logger.info("✅ Base de datos inicializada")
            
            # Verificar conexión con Binance
            balance = self.binance_client.get_account_balance()
            logger.info(f"✅ Conexión Binance establecida - Balance: ${balance['total_usdt']:.2f}")
            
            # Obtener información de balance actual
            balance_summary = self.balance_manager.get_balance_summary()
            daily_progress = self.balance_manager.get_daily_progress()
            
            # Enviar mensaje de inicio por Telegram con información detallada
            if self.config.ENABLE_BOT_STATUS_NOTIFICATIONS:
                self.telegram_notifier.notify_bot_started(balance)
            
            logger.info(f"""
✅ Bot inicializado correctamente
💰 Saldo inicial: ${self.config.INITIAL_BALANCE:.2f} USDT
🎯 Objetivo diario: ${self.config.DAILY_TARGET_AMOUNT:.2f} USDT ({self.config.DAILY_TARGET_PERCENTAGE}%)
📊 Saldo actual: ${balance['total_usdt']:.2f} USDT
📈 Progreso diario: {daily_progress['progress_percent']:.1f}%
            """)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando bot: {e}")
            if self.config.ENABLE_BOT_STATUS_NOTIFICATIONS:
                self.telegram_notifier.notify_bot_error(str(e), "Inicialización")
            return False
    
    def start(self):
        """Inicia el bot"""
        if not self.initialize():
            logger.error("❌ No se pudo inicializar el bot")
            return
        
        self.running = True
        logger.info("🚀 Bot iniciado - Ejecutando 24/7...")
        
        # Configurar manejo de señales para cierre graceful
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
        
        try:
            # El bot se ejecuta principalmente a través de Celery
            # Este proceso principal solo monitorea el estado
            while self.running:
                time.sleep(60)  # Verificar estado cada minuto
                
                # Verificar progreso hacia objetivo diario
                daily_progress = self.balance_manager.get_daily_progress()
                
                # Si se alcanzó el objetivo diario, enviar notificación
                if self.balance_manager.is_daily_target_reached():
                    logger.info("🎯 ¡Objetivo diario alcanzado!")
                    if self.config.ENABLE_BOT_STATUS_NOTIFICATIONS:
                        self.telegram_notifier.send_message_sync(f"""
🎯 <b>¡OBJETIVO DIARIO ALCANZADO!</b> 🎯

💰 <b>Saldo Actual:</b> ${daily_progress['current_balance']:.2f} USDT
📈 <b>P&L Diario:</b> ${daily_progress['daily_pnl']:.2f} ({daily_progress['daily_pnl_percent']:.2f}%)
🎯 <b>Objetivo:</b> ${self.config.DAILY_TARGET_AMOUNT:.2f} USDT
📊 <b>Progreso:</b> {daily_progress['progress_percent']:.1f}%

🕐 <i>Alcanzado: {time.strftime('%H:%M:%S')}</i>
                        """)
                
                # Aquí podrías agregar lógica de monitoreo adicional
                # como verificar que las tareas de Celery estén ejecutándose
                
        except KeyboardInterrupt:
            logger.info("⚠️ Recibida señal de interrupción")
        except Exception as e:
            logger.error(f"❌ Error en el bucle principal: {e}")
            if self.config.ENABLE_BOT_STATUS_NOTIFICATIONS:
                self.telegram_notifier.notify_bot_error(str(e), "Bucle principal")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el bot"""
        logger.info("🛑 Deteniendo bot...")
        self.running = False
        
        # Obtener balance final
        balance_summary = self.balance_manager.get_balance_summary()
        daily_progress = self.balance_manager.get_daily_progress()
        
        # Enviar mensaje de parada con información de balance
        if self.config.ENABLE_BOT_STATUS_NOTIFICATIONS:
            self.telegram_notifier.notify_bot_stopped("Parada manual del usuario")
        
        logger.info(f"""
✅ Bot detenido correctamente
💰 Saldo final: ${balance_summary['current_balance']:.2f} USDT
📈 P&L diario: ${daily_progress['daily_pnl']:.2f} ({daily_progress['daily_pnl_percent']:.2f}%)
📊 Trades hoy: {balance_summary['trades_today']}
🎯 Progreso objetivo: {daily_progress['progress_percent']:.1f}%
        """)
    
    def signal_handler(self, signum, frame):
        """Maneja señales de sistema"""
        logger.info(f"📡 Recibida señal {signum}")
        self.stop()

def main():
    """Función principal"""
    print("""
╔══════════════════════════════════════════════════════════════╗
║                    CRYPTOPUMP BOT                            ║
║                                                              ║
║  🤖 Bot de Trading Algorítmico para Detección de Pumps      ║
║  📊 Top Movers con Análisis Técnico + IA                    ║
║  ⚡ Ejecución 24/7 con Celery + Celery Beat                 ║
║  💰 Saldo Inicial: $200 USDT                                ║
║  🎯 Objetivo: 75% diario ($150 USDT)                        ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Verificar variables de entorno críticas
    required_env_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY',
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    missing_vars = []
    for var in required_env_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        logger.error(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        print(f"""
❌ ERROR: Variables de entorno faltantes:
{', '.join(missing_vars)}

📋 Por favor, configura las variables en tu archivo .env:
BINANCE_API_KEY=tu_api_key
BINANCE_SECRET_KEY=tu_secret_key
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id

💡 Copia env_example.txt a .env y edita las variables
        """)
        sys.exit(1)
    
    # Crear y ejecutar bot
    bot = CryptoPumpBot()
    bot.start()

if __name__ == "__main__":
    main()
