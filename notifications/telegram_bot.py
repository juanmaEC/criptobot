import asyncio
import telegram
from telegram.ext import Application, CommandHandler, ContextTypes
from typing import Dict, List, Optional
from loguru import logger
from config import Config
from datetime import datetime

class TelegramNotifier:
    def __init__(self, config: Config):
        self.config = config
        self.bot = None
        self.chat_id = config.TELEGRAM_CHAT_ID
        self.initialize_bot()
        
    def initialize_bot(self):
        """Inicializa el bot de Telegram"""
        try:
            if not self.config.TELEGRAM_BOT_TOKEN:
                logger.warning("Telegram bot token not configured")
                return
                
            self.bot = telegram.Bot(token=self.config.TELEGRAM_BOT_TOKEN)
            logger.info("Telegram bot initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Telegram bot: {e}")
    
    async def send_message(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Envía mensaje por Telegram"""
        try:
            if not self.bot or not self.chat_id:
                logger.warning("Telegram bot not properly configured")
                return False
                
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode=parse_mode
            )
            return True
            
        except Exception as e:
            logger.error(f"Error sending Telegram message: {e}")
            return False
    
    def send_message_sync(self, message: str, parse_mode: str = 'HTML') -> bool:
        """Envía mensaje de forma síncrona"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.send_message(message, parse_mode))
            loop.close()
            return result
        except Exception as e:
            logger.error(f"Error sending sync Telegram message: {e}")
            return False
    
    def notify_bot_started(self, balance_info: Dict = None) -> bool:
        """Notifica que el bot ha iniciado"""
        try:
            message = f"""
🤖 <b>BOT INICIADO</b> 🤖

✅ <b>Estado:</b> FUNCIONANDO
💰 <b>Saldo Inicial:</b> ${self.config.INITIAL_BALANCE:.2f} USDT
🎯 <b>Objetivo Diario:</b> ${self.config.DAILY_TARGET_AMOUNT:.2f} USDT ({self.config.DAILY_TARGET_PERCENTAGE}%)
📊 <b>Saldo Actual:</b> ${balance_info.get('total_usdt', self.config.INITIAL_BALANCE):.2f} USDT

⚡ <b>Configuración Agresiva:</b>
• Capital por operación: {self.config.CAPITAL_PERCENTAGE*100:.0f}%
• Máximo trades simultáneos: {self.config.MAX_CONCURRENT_TRADES}
• Stop Loss: {self.config.STOP_LOSS_PERCENT}%
• Take Profit: {self.config.TAKE_PROFIT_PERCENT}%

🕐 <i>Iniciado: {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying bot start: {e}")
            return False
    
    def notify_bot_stopped(self, reason: str = "Parada manual") -> bool:
        """Notifica que el bot se ha detenido"""
        try:
            message = f"""
🛑 <b>BOT DETENIDO</b> 🛑

❌ <b>Estado:</b> PARADO
🔍 <b>Razón:</b> {reason}
🕐 <b>Duración de sesión:</b> {datetime.now().strftime('%H:%M:%S')}

⚠️ <i>El bot ha dejado de operar</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying bot stop: {e}")
            return False
    
    def notify_bot_error(self, error_message: str, context: str = "") -> bool:
        """Notifica errores críticos del bot"""
        try:
            message = f"""
🚨 <b>ERROR CRÍTICO DEL BOT</b> 🚨

❌ <b>Estado:</b> ERROR
🔍 <b>Contexto:</b> {context}
💥 <b>Error:</b> {error_message}

⚠️ <b>El bot puede haberse detenido</b>
🕐 <i>Ocurrido: {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying bot error: {e}")
            return False
    
    def notify_pump_detected(self, pump_info: Dict) -> bool:
        """Notifica detección de pump"""
        try:
            message = f"""
🚨 <b>PUMP DETECTADO</b> 🚨

📊 <b>Símbolo:</b> {pump_info['symbol']}
📈 <b>Cambio de Precio:</b> {pump_info['price_change_percent']:.2f}%
⏱️ <b>Ventana de Tiempo:</b> {pump_info['time_window']//60} minutos
📊 <b>Volumen:</b> {pump_info['volume_multiplier']:.2f}x promedio
💰 <b>Precio Actual:</b> ${pump_info['current_price']:.6f}

🕐 <i>Detectado: {pump_info['timestamp'].strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying pump detection: {e}")
            return False
    
    def notify_top_mover_detected(self, analysis: Dict) -> bool:
        """Notifica detección de top mover"""
        try:
            signal_emoji = "🟢" if analysis['final_signal'] == 'long' else "🔴" if analysis['final_signal'] == 'short' else "⚪"
            
            message = f"""
📊 <b>TOP MOVER DETECTADO</b> 📊

{signal_emoji} <b>Símbolo:</b> {analysis['symbol']}
📈 <b>Cambio de Precio:</b> {analysis['price_change_percent']:.2f}%
🎯 <b>Señal:</b> {analysis['final_signal'].upper()}
📊 <b>Score Técnico:</b> {analysis['technical_score']:.1f}/100
🤖 <b>Score IA:</b> {analysis['ai_score']:.1f}/100
⭐ <b>Score Final:</b> {analysis['final_score']:.1f}/100

💰 <b>Precio Actual:</b> ${analysis['current_price']:.6f}
📊 <b>Volatilidad:</b> {analysis['volatility']:.2%}
📈 <b>Volumen:</b> {analysis['volume_ratio']:.2f}x promedio

🕐 <i>Analizado: {analysis['timestamp'].strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying top mover detection: {e}")
            return False
    
    def notify_trade_executed(self, trade_info: Dict, balance_info: Dict) -> bool:
        """Notifica ejecución de trade con información de saldo"""
        try:
            side_emoji = "🟢" if trade_info['side'] == 'buy' else "🔴"
            
            # Calcular porcentaje del capital usado
            capital_percentage = (trade_info['usdt_amount'] / balance_info['total_usdt']) * 100
            
            message = f"""
💼 <b>TRADE EJECUTADO</b> 💼

{side_emoji} <b>Símbolo:</b> {trade_info['symbol']}
📊 <b>Lado:</b> {trade_info['side'].upper()}
💰 <b>Cantidad:</b> {trade_info['quantity']:.6f}
💵 <b>Precio:</b> ${trade_info['entry_price']:.6f}
💸 <b>Valor:</b> ${trade_info['usdt_amount']:.2f} ({capital_percentage:.1f}% del capital)

🛑 <b>Stop Loss:</b> ${trade_info.get('stop_loss', 'N/A'):.6f}
🎯 <b>Take Profit:</b> ${trade_info.get('take_profit', 'N/A'):.6f}

📋 <b>Estrategia:</b> {trade_info['strategy']}

💰 <b>SALDO ACTUAL:</b> ${balance_info['total_usdt']:.2f} USDT
📊 <b>USDT Disponible:</b> ${balance_info['USDT']:.2f}
🎯 <b>Objetivo Diario:</b> ${self.config.DAILY_TARGET_AMOUNT:.2f} USDT

🕐 <i>Ejecutado: {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying trade execution: {e}")
            return False
    
    def notify_trade_closed(self, trade_info: Dict, balance_info: Dict) -> bool:
        """Notifica cierre de trade con información de saldo"""
        try:
            pnl_emoji = "🟢" if trade_info['pnl'] > 0 else "🔴"
            
            # Calcular progreso hacia objetivo diario
            daily_progress = (balance_info['total_usdt'] - self.config.INITIAL_BALANCE) / self.config.DAILY_TARGET_AMOUNT * 100
            
            message = f"""
🏁 <b>TRADE CERRADO</b> 🏁

{pnl_emoji} <b>Símbolo:</b> {trade_info['symbol']}
📊 <b>Lado:</b> {trade_info['side'].upper()}
💰 <b>Precio Entrada:</b> ${trade_info['entry_price']:.6f}
💵 <b>Precio Salida:</b> ${trade_info['exit_price']:.6f}

{pnl_emoji} <b>P&L:</b> ${trade_info['pnl']:.2f} ({trade_info['pnl_percent']:.2f}%)
⏱️ <b>Duración:</b> {trade_info['duration']}

📋 <b>Estrategia:</b> {trade_info['strategy']}

💰 <b>SALDO ACTUAL:</b> ${balance_info['total_usdt']:.2f} USDT
📊 <b>USDT Disponible:</b> ${balance_info['USDT']:.2f}
🎯 <b>Progreso Diario:</b> {daily_progress:.1f}% (${balance_info['total_usdt'] - self.config.INITIAL_BALANCE:.2f} / ${self.config.DAILY_TARGET_AMOUNT:.2f})

🕐 <i>Cerrado: {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying trade closure: {e}")
            return False
    
    def notify_error(self, error_message: str, context: str = "") -> bool:
        """Notifica errores del bot"""
        try:
            message = f"""
⚠️ <b>ERROR DEL BOT</b> ⚠️

🔍 <b>Contexto:</b> {context}
❌ <b>Error:</b> {error_message}

🕐 <i>Ocurrido: {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying error: {e}")
            return False
    
    def notify_daily_summary(self, summary: Dict) -> bool:
        """Notifica resumen diario"""
        try:
            total_pnl_emoji = "🟢" if summary['total_pnl'] > 0 else "🔴"
            
            # Calcular progreso hacia objetivo
            daily_progress = (summary['final_balance'] - self.config.INITIAL_BALANCE) / self.config.DAILY_TARGET_AMOUNT * 100
            
            message = f"""
📊 <b>RESUMEN DIARIO</b> 📊

{total_pnl_emoji} <b>P&L Total:</b> ${summary['total_pnl']:.2f} ({summary['total_pnl_percent']:.2f}%)
📈 <b>Trades Ganadores:</b> {summary['winning_trades']}
📉 <b>Trades Perdedores:</b> {summary['losing_trades']}
📊 <b>Win Rate:</b> {summary['win_rate']:.1f}%

💰 <b>Balance Inicial:</b> ${summary['initial_balance']:.2f}
💵 <b>Balance Final:</b> ${summary['final_balance']:.2f}
🎯 <b>Objetivo Diario:</b> ${self.config.DAILY_TARGET_AMOUNT:.2f} USDT
📈 <b>Progreso Objetivo:</b> {daily_progress:.1f}%

🚨 <b>Pumps Detectados:</b> {summary['pumps_detected']}
📊 <b>Top Movers Analizados:</b> {summary['top_movers_analyzed']}

🕐 <i>Fecha: {summary['date']}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying daily summary: {e}")
            return False
    
    def notify_bot_status(self, status: Dict) -> bool:
        """Notifica estado del bot"""
        try:
            status_emoji = "🟢" if status['status'] == 'running' else "🔴" if status['status'] == 'stopped' else "🟡"
            
            # Calcular progreso hacia objetivo diario
            daily_progress = (status['current_balance'] - self.config.INITIAL_BALANCE) / self.config.DAILY_TARGET_AMOUNT * 100
            
            message = f"""
🤖 <b>ESTADO DEL BOT</b> 🤖

{status_emoji} <b>Estado:</b> {status['status'].upper()}
📊 <b>Trades Activos:</b> {status['active_trades']}
💰 <b>P&L Diario:</b> ${status['daily_pnl']:.2f} ({status['daily_pnl_percent']:.2f}%)

💰 <b>Saldo Actual:</b> ${status['current_balance']:.2f} USDT
🎯 <b>Progreso Objetivo:</b> {daily_progress:.1f}% (${status['current_balance'] - self.config.INITIAL_BALANCE:.2f} / ${self.config.DAILY_TARGET_AMOUNT:.2f})

🕐 <b>Última Actualización:</b> {status['last_update'].strftime('%H:%M:%S')}
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error notifying bot status: {e}")
            return False
    
    def send_test_message(self) -> bool:
        """Envía mensaje de prueba"""
        try:
            message = f"""
🧪 <b>MENSAJE DE PRUEBA</b> 🧪

✅ El bot de notificaciones está funcionando correctamente.
💰 Saldo inicial configurado: ${self.config.INITIAL_BALANCE:.2f} USDT
🎯 Objetivo diario: ${self.config.DAILY_TARGET_AMOUNT:.2f} USDT ({self.config.DAILY_TARGET_PERCENTAGE}%)

🕐 <i>Enviado: {datetime.now().strftime('%H:%M:%S')}</i>
            """
            
            return self.send_message_sync(message)
            
        except Exception as e:
            logger.error(f"Error sending test message: {e}")
            return False
