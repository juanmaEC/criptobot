#!/usr/bin/env python3
"""
Script de inicio para CryptoPump Bot
Ejecuta todos los componentes necesarios
"""

import os
import sys
import subprocess
import time
import signal
import threading
from pathlib import Path

class CryptoPumpStarter:
    def __init__(self):
        self.processes = []
        self.running = False
        
    def check_dependencies(self):
        """Verifica que las dependencias estén instaladas"""
        print("🔍 Verificando dependencias...")
        
        # Verificar Python
        if sys.version_info < (3, 8):
            print("❌ Se requiere Python 3.8 o superior")
            return False
        
        # Verificar archivos necesarios
        required_files = [
            'config.py',
            'celery_app.py',
            'main.py',
            'requirements.txt'
        ]
        
        for file in required_files:
            if not Path(file).exists():
                print(f"❌ Archivo faltante: {file}")
                return False
        
        print("✅ Dependencias verificadas")
        return True
    
    def check_environment(self):
        """Verifica variables de entorno"""
        print("🔍 Verificando variables de entorno...")
        
        required_vars = [
            'BINANCE_API_KEY',
            'BINANCE_SECRET_KEY',
            'TELEGRAM_BOT_TOKEN',
            'TELEGRAM_CHAT_ID'
        ]
        
        missing_vars = []
        for var in required_vars:
            if not os.getenv(var):
                missing_vars.append(var)
        
        if missing_vars:
            print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
            print("📋 Copia env_example.txt a .env y configura las variables")
            return False
        
        print("✅ Variables de entorno verificadas")
        return True
    
    def start_redis(self):
        """Inicia Redis si no está ejecutándose"""
        print("🔍 Verificando Redis...")
        
        try:
            import redis
            r = redis.Redis(host='localhost', port=6379, db=0)
            r.ping()
            print("✅ Redis ya está ejecutándose")
            return True
        except:
            print("⚠️ Redis no está ejecutándose")
            print("💡 Inicia Redis manualmente: redis-server")
            print("💡 O instala con: sudo apt-get install redis-server")
            return False
    
    def start_celery_worker(self):
        """Inicia Celery worker"""
        print("🚀 Iniciando Celery worker...")
        
        cmd = [
            sys.executable, '-m', 'celery', 
            '-A', 'celery_app', 
            'worker', 
            '--loglevel=info',
            '--concurrency=2'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(('Celery Worker', process))
        print("✅ Celery worker iniciado")
        return True
    
    def start_celery_beat(self):
        """Inicia Celery beat (scheduler)"""
        print("🚀 Iniciando Celery beat...")
        
        cmd = [
            sys.executable, '-m', 'celery', 
            '-A', 'celery_app', 
            'beat', 
            '--loglevel=info'
        ]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(('Celery Beat', process))
        print("✅ Celery beat iniciado")
        return True
    
    def start_main_bot(self):
        """Inicia el bot principal"""
        print("🚀 Iniciando bot principal...")
        
        cmd = [sys.executable, 'main.py']
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        self.processes.append(('Main Bot', process))
        print("✅ Bot principal iniciado")
        return True
    
    def monitor_processes(self):
        """Monitorea los procesos en segundo plano"""
        while self.running:
            for name, process in self.processes:
                if process.poll() is not None:
                    print(f"⚠️ {name} se ha detenido (código: {process.returncode})")
                    # Reiniciar proceso si es necesario
                    if name == 'Celery Worker':
                        self.start_celery_worker()
                    elif name == 'Celery Beat':
                        self.start_celery_beat()
                    elif name == 'Main Bot':
                        self.start_main_bot()
            
            time.sleep(10)
    
    def start(self):
        """Inicia todos los componentes del bot"""
        print("""
╔══════════════════════════════════════════════════════════════╗
║                    CRYPTOPUMP BOT                            ║
║                                                              ║
║  🤖 Iniciando Bot de Trading Algorítmico                    ║
║  📊 Pump Detection + Top Movers                             ║
║  ⚡ Celery + Celery Beat                                     ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
        """)
        
        # Verificaciones previas
        if not self.check_dependencies():
            return False
        
        if not self.check_environment():
            return False
        
        if not self.start_redis():
            print("⚠️ Continuando sin Redis (algunas funciones pueden no funcionar)")
        
        # Iniciar componentes
        try:
            self.start_celery_worker()
            time.sleep(2)
            
            self.start_celery_beat()
            time.sleep(2)
            
            self.start_main_bot()
            
            print("""
🎉 ¡BOT INICIADO EXITOSAMENTE! 🎉

📊 Componentes activos:
✅ Celery Worker
✅ Celery Beat (Scheduler)
✅ Bot Principal

📋 Tareas programadas:
• Pump Detection (cada 30s)
• Top Movers (cada 5min)
• Monitoreo de Trades (cada 1min)
• Resumen Diario (00:00 UTC)

📱 Notificaciones por Telegram activas
📈 Monitoreo en logs/bot.log

💡 Para detener: Ctrl+C
            """)
            
            # Iniciar monitoreo en segundo plano
            self.running = True
            monitor_thread = threading.Thread(target=self.monitor_processes)
            monitor_thread.daemon = True
            monitor_thread.start()
            
            # Mantener el script ejecutándose
            try:
                while self.running:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\n🛑 Recibida señal de parada...")
                self.stop()
            
        except Exception as e:
            print(f"❌ Error iniciando bot: {e}")
            self.stop()
            return False
        
        return True
    
    def stop(self):
        """Detiene todos los procesos"""
        print("🛑 Deteniendo bot...")
        self.running = False
        
        for name, process in self.processes:
            try:
                print(f"🛑 Deteniendo {name}...")
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} detenido")
            except subprocess.TimeoutExpired:
                print(f"⚠️ Forzando parada de {name}...")
                process.kill()
            except Exception as e:
                print(f"⚠️ Error deteniendo {name}: {e}")
        
        self.processes.clear()
        print("✅ Bot detenido completamente")

def main():
    """Función principal"""
    starter = CryptoPumpStarter()
    
    # Configurar manejo de señales
    def signal_handler(signum, frame):
        print(f"\n📡 Recibida señal {signum}")
        starter.stop()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Iniciar bot
    success = starter.start()
    
    if not success:
        print("❌ No se pudo iniciar el bot")
        sys.exit(1)

if __name__ == "__main__":
    main()
