# CryptoPump Bot - Bot de Trading Algorítmico para Binance

Un bot de trading algorítmico modular y avanzado para Binance que opera 24/7, implementando estrategias de detección de pumps y análisis de top movers con inteligencia artificial.

## 🚀 Características

### Estrategias de Trading
- **Pump Detection**: Detecta subidas rápidas (>5% en ≤5 minutos) con alto volumen
- **Top Movers**: Analiza movimientos ≥2-3% en 30 minutos con filtros anti-scam
- **Análisis Técnico**: EMA, RSI, MACD, Bollinger Bands, ATR
- **Inteligencia Artificial**: LSTM para predicción de precios y PPO para optimización de entradas

### Gestión de Riesgo
- Stop Loss y Take Profit automáticos
- Trailing Stop dinámico
- Tamaño de posición basado en volatilidad
- Máximo número de operaciones simultáneas
- Cooldown tras pérdidas
- Límites diarios de pérdida

### Infraestructura
- **24/7 Operación**: Celery + Celery Beat para tareas asíncronas
- **Base de Datos**: PostgreSQL para persistencia de datos
- **Cache**: Redis para Celery y datos temporales
- **Notificaciones**: Telegram en tiempo real
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

### Parámetros de Trading

```env
# Capital y Riesgo
CAPITAL_PERCENTAGE=5.0
MAX_CONCURRENT_TRADES=3
DAILY_LOSS_LIMIT=10.0

# Pump Detection
PUMP_THRESHOLD_PERCENT=5.0
PUMP_TIME_WINDOW=300
PUMP_VOLUME_MULTIPLIER=3.0

# Top Movers
TOP_MOVERS_THRESHOLD=2.5
TOP_MOVERS_TIME_WINDOW=1800
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

### Pump Detection
1. **Detección**: Monitorea cambios de precio >5% en ≤5 minutos
2. **Validación**: Verifica volumen alto (3x promedio)
3. **Entrada**: Ejecuta entrada rápida con SL/TP agresivos
4. **Gestión**: Trailing stop y monitoreo continuo

### Top Movers
1. **Escaneo**: Identifica movimientos ≥2-3% en 30 minutos
2. **Filtrado**: Descarta scams (volumen bajo, patrones sospechosos)
3. **Análisis**: Aplica TA (EMA, RSI, MACD, Bollinger, ATR)
4. **IA**: LSTM predice precio, PPO optimiza entrada
5. **Decisión**: Score combinado determina long/short

## 🛡️ Gestión de Riesgo

- **Position Sizing**: Basado en ATR y volatilidad
- **Stop Loss**: 2-5% según estrategia
- **Take Profit**: 3-8% según momentum
- **Trailing Stop**: Ajuste dinámico
- **Cooldown**: 30-60 minutos tras pérdidas
- **Límites**: Máximo 3 trades simultáneos
- **Daily Limit**: 10% pérdida máxima diaria

## 📱 Notificaciones

### Telegram
- Detección de pumps y top movers
- Ejecución y cierre de trades
- Errores y alertas críticas
- Resúmenes diarios
- Estado del bot

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
│   └── binance_client.py    # Cliente Binance
├── notifications/
│   └── telegram_bot.py      # Bot de Telegram
├── logs/                    # Archivos de log
├── data/                    # Datos temporales
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
🤖 CryptoPump Bot iniciado
📊 Escaneando mercado...
🚀 Pump detectado: BTCUSDT +7.2% en 3min
💰 Trade ejecutado: BTCUSDT LONG @ $45,000
📈 Take Profit alcanzado: +4.5%
📊 Resumen diario: +12.3% (5 trades)
```

## ⚠️ Disclaimer

**ADVERTENCIA**: Este bot es para fines educativos y de investigación. El trading de criptomonedas conlleva riesgos significativos. No inviertas más de lo que puedas permitirte perder. Los resultados pasados no garantizan resultados futuros.

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
