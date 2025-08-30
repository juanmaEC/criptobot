import os
from dotenv import load_dotenv
import ccxt

# 🔹 Cargar las variables de entorno del archivo .env
load_dotenv()

API_KEY = os.getenv("BINANCE_API_KEY")
API_SECRET = os.getenv("BINANCE_SECRET_KEY")

# 🔹 Conexión a Binance Testnet
exchange = ccxt.binance({
    "apiKey": API_KEY,
    "secret": API_SECRET,
    "enableRateLimit": True,
    "options": {"defaultType": "spot"},  # spot, future, margin...
})

# 🔹 Sobrescribimos las URLs para usar el entorno de test
exchange.set_sandbox_mode(True)

try:
    balance = exchange.fetch_balance()
    print("✅ Conexión exitosa a Binance Testnet")
    print(balance)
except Exception as e:
    print("❌ Error de conexión:", str(e))
