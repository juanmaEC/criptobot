#!/usr/bin/env python3
"""
Script de diagnóstico para CryptoPump
Verifica el estado del sistema y ayuda a identificar problemas
"""

import os
import sys
import subprocess
import requests
from pathlib import Path
from dotenv import load_dotenv

def print_header(title):
    """Imprime un encabezado"""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print(f"{'='*60}")

def print_section(title):
    """Imprime una sección"""
    print(f"\n📋 {title}")
    print("-" * 40)

def check_env_file():
    """Verifica el archivo .env"""
    print_section("Verificación de archivo .env")
    
    env_file = Path('.env')
    if env_file.exists():
        print("✅ Archivo .env encontrado")
        
        # Cargar variables
        load_dotenv()
        
        # Verificar variables críticas
        critical_vars = {
            'BINANCE_API_KEY': 'API Key de Binance',
            'BINANCE_SECRET_KEY': 'Secret Key de Binance',
            'DATABASE_URL': 'URL de base de datos',
            'REDIS_URL': 'URL de Redis'
        }
        
        for var, description in critical_vars.items():
            value = os.getenv(var)
            if value:
                if 'KEY' in var or 'SECRET' in var:
                    print(f"✅ {description}: {'*' * 10} (configurada)")
                else:
                    print(f"✅ {description}: {value}")
            else:
                print(f"❌ {description}: NO CONFIGURADA")
        
        # Verificar variables opcionales
        optional_vars = {
            'TELEGRAM_BOT_TOKEN': 'Token de bot de Telegram',
            'TELEGRAM_CHAT_ID': 'Chat ID de Telegram'
        }
        
        for var, description in optional_vars.items():
            value = os.getenv(var)
            if value:
                print(f"✅ {description}: configurada")
            else:
                print(f"⚠️  {description}: no configurada (opcional)")
        
        return True
    else:
        print("❌ Archivo .env NO ENCONTRADO")
        print("💡 Crea el archivo .env basado en env_template.txt")
        return False

def check_docker_services():
    """Verifica el estado de los servicios de Docker"""
    print_section("Estado de servicios Docker")
    
    try:
        # Verificar si Docker está ejecutándose
        result = subprocess.run(['docker', 'info'], capture_output=True, text=True)
        if result.returncode != 0:
            print("❌ Docker no está ejecutándose")
            return False
        
        print("✅ Docker está ejecutándose")
        
        # Verificar servicios de docker-compose
        result = subprocess.run(['docker-compose', 'ps'], capture_output=True, text=True)
        if result.returncode == 0:
            print("\n📊 Servicios activos:")
            lines = result.stdout.strip().split('\n')
            for line in lines[2:]:  # Saltar encabezados
                if line.strip():
                    print(f"   {line}")
        else:
            print("❌ Error al verificar servicios de docker-compose")
            return False
        
        return True
        
    except FileNotFoundError:
        print("❌ Docker o docker-compose no encontrado")
        return False

def check_network_connectivity():
    """Verifica conectividad de red"""
    print_section("Verificación de conectividad")
    
    # Verificar conectividad a Binance
    try:
        response = requests.get('https://api.binance.com/api/v3/ping', timeout=10)
        if response.status_code == 200:
            print("✅ Conexión a Binance API: OK")
        else:
            print(f"⚠️  Conexión a Binance API: Status {response.status_code}")
    except Exception as e:
        print(f"❌ Conexión a Binance API: Error - {e}")
    
    # Verificar puertos locales
    ports_to_check = {
        5432: 'PostgreSQL',
        6379: 'Redis',
        8000: 'Aplicación principal',
        5555: 'Flower (monitoreo)'
    }
    
    for port, service in ports_to_check.items():
        try:
            response = requests.get(f'http://localhost:{port}', timeout=5)
            print(f"✅ {service} (puerto {port}): Accesible")
        except:
            print(f"❌ {service} (puerto {port}): No accesible")

def check_logs():
    """Verifica logs recientes"""
    print_section("Logs recientes")
    
    try:
        # Logs de Celery Worker
        print("📋 Últimas líneas de Celery Worker:")
        result = subprocess.run(['docker-compose', 'logs', '--tail=10', 'celery_worker'], 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        else:
            print("   No hay logs recientes")
        
        # Logs de la aplicación principal
        print("\n📋 Últimas líneas de la aplicación principal:")
        result = subprocess.run(['docker-compose', 'logs', '--tail=10', 'app'], 
                              capture_output=True, text=True)
        if result.stdout:
            print(result.stdout)
        else:
            print("   No hay logs recientes")
            
    except Exception as e:
        print(f"❌ Error al obtener logs: {e}")

def suggest_solutions():
    """Sugiere soluciones basadas en los problemas encontrados"""
    print_section("Sugerencias de solución")
    
    print("🔧 Pasos recomendados:")
    print("1. Si el archivo .env no existe:")
    print("   cp env_template.txt .env")
    print("   # Editar .env con tus credenciales")
    
    print("\n2. Si los servicios no están ejecutándose:")
    print("   docker-compose up -d")
    
    print("\n3. Si hay problemas de conectividad:")
    print("   docker-compose restart")
    
    print("\n4. Para ver logs en tiempo real:")
    print("   docker-compose logs -f celery_worker")
    
    print("\n5. Para reiniciar todo el sistema:")
    print("   docker-compose down")
    print("   docker-compose up -d")

def main():
    """Función principal"""
    print_header("DIAGNÓSTICO DE CRYPTOPUMP")
    
    # Verificar archivo .env
    env_ok = check_env_file()
    
    # Verificar servicios Docker
    docker_ok = check_docker_services()
    
    # Verificar conectividad
    check_network_connectivity()
    
    # Verificar logs
    check_logs()
    
    # Sugerir soluciones
    suggest_solutions()
    
    print_header("FIN DEL DIAGNÓSTICO")
    
    if not env_ok:
        print("❌ Problemas encontrados con la configuración")
        sys.exit(1)
    elif not docker_ok:
        print("❌ Problemas encontrados con Docker")
        sys.exit(1)
    else:
        print("✅ Sistema parece estar funcionando correctamente")

if __name__ == '__main__':
    main()
