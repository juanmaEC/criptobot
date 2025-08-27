#!/usr/bin/env python3
"""
Script de inicio seguro para CryptoPump Docker
Verifica las variables de entorno necesarias antes de iniciar los contenedores
"""

import os
import sys
import subprocess
from pathlib import Path

def check_env_file():
    """Verifica si existe el archivo .env"""
    env_file = Path('.env')
    if not env_file.exists():
        print("❌ Archivo .env no encontrado")
        print("📝 Crea un archivo .env basado en env_template.txt")
        print("💡 Ejemplo:")
        print("   cp env_template.txt .env")
        print("   # Luego edita .env con tus credenciales")
        return False
    return True

def check_required_env_vars():
    """Verifica las variables de entorno requeridas"""
    required_vars = [
        'BINANCE_API_KEY',
        'BINANCE_SECRET_KEY'
    ]
    
    missing_vars = []
    for var in required_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"❌ Variables de entorno faltantes: {', '.join(missing_vars)}")
        print("📝 Asegúrate de configurar estas variables en tu archivo .env")
        return False
    
    print("✅ Variables de entorno requeridas configuradas")
    return True

def check_optional_env_vars():
    """Verifica las variables de entorno opcionales"""
    optional_vars = [
        'TELEGRAM_BOT_TOKEN',
        'TELEGRAM_CHAT_ID'
    ]
    
    missing_vars = []
    for var in optional_vars:
        if not os.getenv(var):
            missing_vars.append(var)
    
    if missing_vars:
        print(f"⚠️  Variables opcionales no configuradas: {', '.join(missing_vars)}")
        print("📱 Las notificaciones de Telegram estarán deshabilitadas")
    else:
        print("✅ Variables de Telegram configuradas")
    
    return True

def start_docker_services():
    """Inicia los servicios de Docker"""
    try:
        print("🚀 Iniciando servicios de Docker...")
        
        # Construir las imágenes
        print("🔨 Construyendo imágenes...")
        subprocess.run(['docker-compose', 'build'], check=True)
        
        # Iniciar los servicios
        print("▶️  Iniciando servicios...")
        subprocess.run(['docker-compose', 'up', '-d'], check=True)
        
        print("✅ Servicios iniciados correctamente")
        print("\n📊 Servicios disponibles:")
        print("   - Aplicación principal: http://localhost:8000")
        print("   - Flower (monitoreo): http://localhost:5555")
        print("   - PostgreSQL: localhost:5432")
        print("   - Redis: localhost:6379")
        
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"❌ Error al iniciar servicios: {e}")
        return False
    except FileNotFoundError:
        print("❌ Docker Compose no encontrado")
        print("💡 Asegúrate de tener Docker y Docker Compose instalados")
        return False

def show_logs():
    """Muestra los logs de los servicios"""
    try:
        print("\n📋 Mostrando logs de Celery Worker...")
        subprocess.run(['docker-compose', 'logs', '-f', 'celery_worker'])
    except KeyboardInterrupt:
        print("\n👋 Logs detenidos")

def main():
    """Función principal"""
    print("🤖 CryptoPump Docker - Inicio Seguro")
    print("=" * 50)
    
    # Verificar archivo .env
    if not check_env_file():
        sys.exit(1)
    
    # Cargar variables de entorno
    from dotenv import load_dotenv
    load_dotenv()
    
    # Verificar variables requeridas
    if not check_required_env_vars():
        sys.exit(1)
    
    # Verificar variables opcionales
    check_optional_env_vars()
    
    print("\n" + "=" * 50)
    
    # Iniciar servicios
    if not start_docker_services():
        sys.exit(1)
    
    # Preguntar si mostrar logs
    try:
        show_logs_choice = input("\n¿Mostrar logs de Celery Worker? (y/n): ").lower()
        if show_logs_choice in ['y', 'yes', 'sí', 'si']:
            show_logs()
    except KeyboardInterrupt:
        print("\n👋 Hasta luego!")

if __name__ == '__main__':
    main()
