#!/usr/bin/env python3
"""
Script para probar el BinanceClient del bot
"""

import os
import sys
from dotenv import load_dotenv
from config import Config
from trading.binance_client import BinanceClient
from loguru import logger

# Configurar logging
logger.add("logs/test_binance_bot.log", rotation="1 day", retention="7 days")

def test_binance_client():
    """Prueba el BinanceClient del bot"""
    print("🔍 Probando BinanceClient del bot...")
    
    try:
        # Cargar configuración
        load_dotenv()
        config = Config()
        
        print(f"📋 Configuración del bot:")
        print(f"   - API Key: {'✅ Configurada' if config.BINANCE_API_KEY else '❌ No configurada'}")
        if config.BINANCE_API_KEY:
            masked_api_key = config.BINANCE_API_KEY[:8] + "..." + config.BINANCE_API_KEY[-8:] if len(config.BINANCE_API_KEY) > 16 else "***"
            print(f"   - API Key (masked): {masked_api_key}")
        print(f"   - Secret Key: {'✅ Configurada' if config.BINANCE_SECRET_KEY else '❌ No configurada'}")
        if config.BINANCE_SECRET_KEY:
            masked_secret_key = config.BINANCE_SECRET_KEY[:8] + "..." + config.BINANCE_SECRET_KEY[-8:] if len(config.BINANCE_SECRET_KEY) > 16 else "***"
            print(f"   - Secret Key (masked): {masked_secret_key}")
        print(f"   - Testnet: {'✅ Activado' if config.BINANCE_TESTNET else '❌ Desactivado'}")
        print(f"   - Testnet valor raw: '{config.BINANCE_TESTNET}' (tipo: {type(config.BINANCE_TESTNET)})")
        
        # Verificar valor directo del env
        testnet_env = os.getenv('BINANCE_TESTNET', 'true').lower() == 'true'
        print(f"   - Testnet desde env: '{testnet_env}' (tipo: {type(testnet_env)})")
        
        # Inicializar BinanceClient
        print("🔄 Inicializando BinanceClient...")
        binance_client = BinanceClient(config)
        print("✅ BinanceClient inicializado correctamente")
        
        # Probar obtención de balance
        print("💰 Probando obtención de balance...")
        balance = binance_client.get_account_balance()
        print(f"✅ Balance obtenido: {balance}")
        
        # Probar obtención de símbolos
        print("📊 Probando obtención de símbolos...")
        symbols = binance_client.get_all_symbols()
        print(f"✅ Símbolos obtenidos: {len(symbols)} símbolos")
        
        print("\n🎉 ¡BinanceClient del bot funciona correctamente!")
        return True
        
    except Exception as e:
        print(f"❌ Error en BinanceClient del bot: {e}")
        logger.error(f"Error testing BinanceClient: {e}")
        return False

if __name__ == "__main__":
    test_binance_client()
