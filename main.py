#!/usr/bin/env python3
"""
Bot de Trading Algorítmico para Detección de Pumps y Top Movers
Ejecuta 24/7 usando Celery + Celery Beat para scheduler y ejecución asíncrona
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

# Configurar logging
logger.add("logs/bot.log", rotation="1 day", retention="7 days", level="INFO")

class CryptoPumpBot:
    def __init__(self):
        self.config = Config()
        self.telegram_notifier = TelegramNotifier(self.config)
        self.binance_client = BinanceClient(self.config)
        self.running = False
        
    def initialize(self):
        """Inicializa el bot"""
        try:
            logger.info("🚀 Iniciando CryptoPump Bot...")
            
            # Crear directorios necesarios
            os.makedirs("logs", exist_ok=True)
            os.makedirs("models", exist_ok=True)
            
            # Crear tablas de base de datos
            create_tables()
            logger.info("✅ Base de datos inicializada")
            
            # Verificar conexión con Binance
            balance = self.binance_client.get_account_balance()
            logger.info(f"✅ Conexión Binance establecida - Balance: ${balance['total_usdt']:.2f}")
            
            # Enviar mensaje de inicio por Telegram
            self.telegram_notifier.send_message_sync("""
🤖 <b>CRYPTOPUMP BOT INICIADO</b> 🤖

✅ Bot iniciado correctamente
💰 Balance: ${:.2f}
🕐 Hora: {}

📋 <b>Estrategias Activas:</b>
• Pump Detection (cada 30s)
• Top Movers (cada 5min)
• Monitoreo de Trades (cada 1min)
• Resumen Diario (00:00 UTC)
            """.format(balance['total_usdt'], time.strftime('%H:%M:%S')))
            
            logger.info("✅ Bot inicializado correctamente")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error inicializando bot: {e}")
            self.telegram_notifier.notify_error(str(e), "Inicialización")
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
                
                # Aquí podrías agregar lógica de monitoreo adicional
                # como verificar que las tareas de Celery estén ejecutándose
                
        except KeyboardInterrupt:
            logger.info("⚠️ Recibida señal de interrupción")
        except Exception as e:
            logger.error(f"❌ Error en el bucle principal: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Detiene el bot"""
        logger.info("🛑 Deteniendo bot...")
        self.running = False
        
        # Enviar mensaje de parada
        self.telegram_notifier.send_message_sync("""
🛑 <b>CRYPTOPUMP BOT DETENIDO</b> 🛑

⏰ Detenido: {}
📊 Estado: Finalizado correctamente
            """.format(time.strftime('%H:%M:%S')))
        
        logger.info("✅ Bot detenido correctamente")
    
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
        """)
        sys.exit(1)
    
    # Crear y ejecutar bot
    bot = CryptoPumpBot()
    bot.start()

if __name__ == "__main__":
    main()
