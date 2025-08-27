# CryptoPump Bot - Bot de Trading Algorítmico para Binance

Un bot de trading algorítmico modular y avanzado para Binance que opera 24/7, implementando estrategias de detección de pumps y análisis de top movers con inteligencia artificial.

**🎯 Configurado para saldo inicial de 200 USDT y objetivo del 75% diario ($150 USDT)**

## 🚀 Características

### Estrategias de Trading
- **Pump Detection**: Detecta subidas rápidas (>3% en ≤3 minutos) con alto volumen
- **Top Movers**: Analiza movimientos ≥1.5% en 15 minutos con filtros anti-scam
- **Análisis Técnico**: EMA, RSI, MACD, Bollinger Bands, ATR
- **Inteligencia Artificial**: LSTM para predicción de precios y PPO para optimización de entradas

### Gestión de Riesgo (Configuración Agresiva)
- **Saldo Inicial**: 200 USDT
- **Objetivo Diario**: 75% ($150 USDT)
- **Capital por Operación**: 15% del balance disponible
- **Stop Loss**: 2% por operación
- **Take Profit**: 4% por operación
- **Máximo Trades Simultáneos**: 3
- **Límite de Pérdida Diaria**: 10%
- **Cooldown tras Pérdidas**: 30 minutos

### Infraestructura
- **24/7 Operación**: Celery + Celery Beat para tareas asíncronas
- **Base de Datos**: PostgreSQL para persistencia de datos
- **Cache**: Redis para Celery y datos temporales
- **Notificaciones**: Telegram en tiempo real con información detallada
- **Logging**: Sistema completo de logs
- **Monitoreo**: Flower para supervisión de Celery

## 📋 Requisitos

### Para ejecución local:
- Python 3.11+
- PostgreSQL 15+
- Redis 7+
- API Keys de Binance
- Bot de Telegram

### Para ejecución con Docker:
- Docker Desktop
- Docker Compose

## 🛠️ Instalación

### Opción 1: Instalación Local

1. **Clonar el repositorio**:
```bash
git clone <repository-url>
cd cryptoPump
```

2. **Crear entorno virtual**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
# o
venv\Scripts\activate     # Windows
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**:
```bash
# Instalar PostgreSQL y Redis
# Crear base de datos 'cryptopump'
```

5. **Configurar variables de entorno**:
```bash
cp env_example.txt .env
# Editar .env con tus configuraciones
```

### Opción 2: Instalación con Docker (Recomendado)

1. **Clonar el repositorio**:
```bash
git clone <repository-url>
cd cryptoPump
```

2. **Configurar variables de entorno**:
```bash
cp env_example.txt .env
# Editar .env con tus configuraciones
```

3. **Ejecutar con Docker**:
```bash
# En Windows:
docker-start.bat start

# En Linux/Mac:
./docker-start.sh start
```

## ⚙️ Configuración

### Variables de Entorno Críticas

```env
# Binance API
BINANCE_API_KEY=tu_api_key
BINANCE_SECRET_KEY=tu_secret_key

# Base de Datos
DATABASE_URL=postgresql://usuario:password@localhost:5432/cryptopump

# Redis
REDIS_URL=redis://localhost:6379/0

# Telegram
TELEGRAM_BOT_TOKEN=tu_bot_token
TELEGRAM_CHAT_ID=tu_chat_id
```

### Parámetros de Trading (Configuración Agresiva)

```env
# Cuenta y Objetivos
INITIAL_BALANCE=200.0
DAILY_TARGET_PERCENTAGE=75.0

# Capital y Riesgo
CAPITAL_PERCENTAGE=0.15
MAX_CONCURRENT_TRADES=3
MAX_DAILY_LOSS=0.10

# Pump Detection (Ajustado para mayor agresividad)
PUMP_THRESHOLD_PERCENT=3.0
PUMP_TIME_WINDOW=180
PUMP_VOLUME_MULTIPLIER=1.5

# Top Movers (Ajustado para mayor agresividad)
TOP_MOVERS_THRESHOLD=1.5
TOP_MOVERS_TIME_WINDOW=900

# Gestión de Riesgo (Ajustado para mayor agresividad)
STOP_LOSS_PERCENT=2.0
TAKE_PROFIT_PERCENT=4.0
TRAILING_STOP_PERCENT=1.5
COOLDOWN_AFTER_LOSS=1800
```

## 🚀 Ejecución

### Con Docker (Recomendado)

```bash
# Iniciar el bot
docker-start.bat start    # Windows
./docker-start.sh start   # Linux/Mac

# Ver logs en tiempo real
docker-start.bat logs
./docker-start.sh logs

# Ver estado de servicios
docker-start.bat status
./docker-start.sh status

# Detener el bot
docker-start.bat stop
./docker-start.sh stop

# Reiniciar
docker-start.bat restart
./docker-start.sh restart

# Limpiar todo (contenedores, volúmenes, datos)
docker-start.bat clean
./docker-start.sh clean
```

### Sin Docker

```bash
# 1. Iniciar servicios de base de datos
# PostgreSQL y Redis deben estar ejecutándose

# 2. Ejecutar el bot
python start_bot.py

# O ejecutar componentes individualmente:
python main.py                    # Bot principal
celery -A celery_app worker       # Celery worker
celery -A celery_app beat         # Celery beat (scheduler)
```

## 📊 Tareas Programadas

El bot ejecuta automáticamente las siguientes tareas:

| Tarea | Frecuencia | Descripción |
|-------|------------|-------------|
| `scan_pumps` | Cada 30 segundos | Escanea pumps en tiempo real |
| `scan_top_movers` | Cada 5 minutos | Analiza top movers |
| `monitor_open_trades` | Cada 1 minuto | Monitorea trades abiertos |
| `send_daily_summary` | Diario a 00:00 UTC | Resumen diario por Telegram |

## 🧠 Estrategias

### Pump Detection (Configuración Agresiva)
1. **Detección**: Monitorea cambios de precio >3% en ≤3 minutos
2. **Validación**: Verifica volumen alto (1.5x promedio)
3. **Entrada**: Ejecuta entrada rápida con SL/TP agresivos
4. **Gestión**: Trailing stop y monitoreo continuo

### Top Movers (Configuración Agresiva)
1. **Escaneo**: Identifica movimientos ≥1.5% en 15 minutos
2. **Filtrado**: Descarta scams (volumen bajo, patrones sospechosos)
3. **Análisis**: Aplica TA (EMA, RSI, MACD, Bollinger, ATR)
4. **IA**: LSTM predice precio, PPO optimiza entrada
5. **Decisión**: Score combinado determina long/short

## 🛡️ Gestión de Riesgo

- **Position Sizing**: 15% del balance disponible por operación
- **Stop Loss**: 2% según estrategia
- **Take Profit**: 4% según momentum
- **Trailing Stop**: Ajuste dinámico 1.5%
- **Cooldown**: 30 minutos tras pérdidas
- **Límites**: Máximo 3 trades simultáneos
- **Daily Limit**: 10% pérdida máxima diaria
- **Objetivo Diario**: 75% ($150 USDT)

## 📱 Notificaciones

### Telegram (Mejoradas)
- **Inicio/Parada del Bot**: Con información de balance y configuración
- **Detección de Pumps**: Con detalles técnicos
- **Top Movers**: Con análisis completo y scores
- **Ejecución de Trades**: Con saldo actual y porcentaje usado
- **Cierre de Trades**: Con P&L y progreso hacia objetivo diario
- **Errores Críticos**: Con contexto y estado del bot
- **Resúmenes Diarios**: Con progreso hacia objetivo
- **Objetivo Diario Alcanzado**: Notificación especial

### Ejemplo de Notificación de Trade:
```
💼 TRADE EJECUTADO 💼

🟢 Símbolo: BTCUSDT
📊 Lado: BUY
💰 Cantidad: 0.001234
💵 Precio: $45,000.00
💸 Valor: $30.00 (15.0% del capital)

🛑 Stop Loss: $44,100.00
🎯 Take Profit: $46,800.00

📋 Estrategia: Pump Detection

💰 SALDO ACTUAL: $200.00 USDT
📊 USDT Disponible: $170.00
🎯 Objetivo Diario: $150.00 USDT

🕐 Ejecutado: 14:30:25
```

## 📈 Monitoreo

### Flower (Web UI)
- Acceso: http://localhost:5555
- Monitoreo de tareas Celery
- Estadísticas de ejecución
- Logs en tiempo real

### Logs
- Archivos en `logs/`
- Rotación automática
- Niveles: DEBUG, INFO, WARNING, ERROR

### Balance Manager
- Archivo: `data/balance.json`
- Seguimiento de saldo inicial ($200 USDT)
- Progreso hacia objetivo diario (75%)
- Estadísticas de trades y win rate

## 🏗️ Arquitectura

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Binance API   │    │   PostgreSQL    │    │     Redis       │
│   (ccxt)        │    │   (Datos)       │    │   (Celery)      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              CryptoPump Bot                     │
         │  ┌─────────────┐  ┌─────────────┐              │
         │  │   Main      │  │  Celery     │              │
         │  │   Bot       │  │  Worker     │              │
         │  └─────────────┘  └─────────────┘              │
         │  ┌─────────────┐  ┌─────────────┐              │
         │  │  Celery     │  │  Telegram   │              │
         │  │   Beat      │  │  Bot        │              │
         │  └─────────────┘  └─────────────┘              │
         └─────────────────────────────────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              Estrategias                        │
         │  ┌─────────────┐  ┌─────────────┐              │
         │  │   Pump      │  │   Top       │              │
         │  │ Detection   │  │  Movers     │              │
         │  └─────────────┘  └─────────────┘              │
         │  ┌─────────────┐  ┌─────────────┐              │
         │  │ Technical   │  │     AI      │              │
         │  │ Analysis    │  │  Models     │              │
         │  └─────────────┘  └─────────────┘              │
         └─────────────────────────────────────────────────┘
                                 │
         ┌─────────────────────────────────────────────────┐
         │              Balance Manager                    │
         │  ┌─────────────┐  ┌─────────────┐              │
         │  │   Saldo     │  │  Objetivo   │              │
         │  │  Inicial    │  │  Diario     │              │
         │  │  $200 USDT  │  │  75% $150   │              │
         │  └─────────────┘  └─────────────┘              │
         └─────────────────────────────────────────────────┘
```

## 🔧 Estructura del Proyecto

```
cryptoPump/
├── config.py                 # Configuración centralizada
├── main.py                   # Punto de entrada principal
├── celery_app.py            # Configuración de Celery
├── requirements.txt          # Dependencias Python
├── .env                      # Variables de entorno
├── env_example.txt          # Ejemplo de variables
├── docker-start.bat         # Script de inicio Windows
├── docker-start.sh          # Script de inicio Linux/Mac
├── Dockerfile               # Imagen Docker
├── docker-compose.yml       # Orquestación Docker
├── .dockerignore            # Archivos ignorados por Docker
├── database/
│   ├── models.py            # Modelos SQLAlchemy
│   └── init.sql             # Inicialización DB
├── strategies/
│   ├── pump_detector.py     # Detección de pumps
│   ├── top_movers.py        # Estrategia top movers
│   ├── technical_analysis.py # Indicadores técnicos
│   ├── ai_models.py         # Modelos LSTM/PPO
│   └── trading_env.py       # Entorno de trading
├── trading/
│   ├── binance_client.py    # Cliente Binance
│   └── balance_manager.py   # Gestión de balance
├── notifications/
│   └── telegram_bot.py      # Bot de Telegram
├── logs/                    # Archivos de log
├── data/                    # Datos temporales
│   └── balance.json         # Datos de balance
└── models/                  # Modelos AI guardados
```

## 🐳 Docker

### Servicios Incluidos
- **app**: Aplicación principal
- **celery_worker**: Worker de Celery
- **celery_beat**: Scheduler de Celery
- **postgres**: Base de datos PostgreSQL
- **redis**: Cache y broker de mensajes
- **flower**: Monitoreo web (opcional)

### Comandos Docker

```bash
# Construir imágenes
docker-compose build

# Iniciar todos los servicios
docker-compose up -d

# Ver logs
docker-compose logs -f

# Ver estado
docker-compose ps

# Detener servicios
docker-compose down

# Limpiar volúmenes
docker-compose down -v
```

## 🔍 Troubleshooting

### Problemas Comunes

1. **Error de conexión a Binance**:
   - Verificar API keys en `.env`
   - Comprobar límites de API

2. **Error de base de datos**:
   - Verificar que PostgreSQL esté ejecutándose
   - Comprobar `DATABASE_URL` en `.env`

3. **Celery no ejecuta tareas**:
   - Verificar que Redis esté ejecutándose
   - Comprobar `REDIS_URL` en `.env`

4. **No llegan notificaciones**:
   - Verificar `TELEGRAM_BOT_TOKEN` y `TELEGRAM_CHAT_ID`
   - Comprobar que el bot esté iniciado

### Logs de Debug

```bash
# Ver logs detallados
docker-compose logs -f app
docker-compose logs -f celery_worker
docker-compose logs -f celery_beat
```

## 📊 Ejemplo de Uso

### Configuración Inicial

1. **Crear archivo `.env`**:
```env
BINANCE_API_KEY=tu_api_key_aqui
BINANCE_SECRET_KEY=tu_secret_key_aqui
TELEGRAM_BOT_TOKEN=tu_bot_token_aqui
TELEGRAM_CHAT_ID=tu_chat_id_aqui
INITIAL_BALANCE=200.0
DAILY_TARGET_PERCENTAGE=75.0
```

2. **Iniciar con Docker**:
```bash
docker-start.bat start
```

3. **Verificar estado**:
```bash
docker-start.bat status
```

4. **Monitorear logs**:
```bash
docker-start.bat logs
```

### Notificaciones Esperadas

```
🤖 BOT INICIADO
💰 Saldo Inicial: $200.00 USDT
🎯 Objetivo Diario: $150.00 USDT (75%)
📊 Saldo Actual: $200.00 USDT

🚀 Pump detectado: BTCUSDT +3.2% en 2min
💰 Trade ejecutado: BTCUSDT LONG @ $45,000 (15% del capital)
📈 Take Profit alcanzado: +4.0%
📊 Resumen diario: +12.3% (5 trades) - Progreso: 8.2%
🎯 ¡OBJETIVO DIARIO ALCANZADO! +75.0%
```

## ⚠️ Disclaimer

**ADVERTENCIA**: Este bot está configurado para trading agresivo con objetivo del 75% diario. El trading de criptomonedas conlleva riesgos significativos. No inviertas más de lo que puedas permitirte perder. Los resultados pasados no garantizan resultados futuros.

## 🤝 Contribuciones

Las contribuciones son bienvenidas. Por favor:

1. Fork el proyecto
2. Crea una rama para tu feature
3. Commit tus cambios
4. Push a la rama
5. Abre un Pull Request

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver `LICENSE` para más detalles.

## 🆘 Soporte

- **Issues**: Crear issue en GitHub
- **Documentación**: Revisar este README
- **Logs**: Verificar archivos en `logs/`
- **Monitoreo**: Acceder a Flower en http://localhost:5555

---

**¡Que tengas éxito en tu trading! 🚀**
