import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from loguru import logger
from config import Config

class BinanceClient:
    def __init__(self, config: Config):
        self.config = config
        self.exchange = None
        self.initialize_exchange()
        
    def initialize_exchange(self):
        """Inicializa conexión con Binance"""
        try:
            exchange_config = {
                'apiKey': self.config.BINANCE_API_KEY,
                'secret': self.config.BINANCE_SECRET_KEY,
                'enableRateLimit': True,
                'options': {
                    'defaultType': 'spot'
                }
            }
            
            self.exchange = ccxt.binance(exchange_config)
            
            # Configurar sandbox mode para testnet
            if self.config.BINANCE_TESTNET:
                self.exchange.set_sandbox_mode(True)
                logger.info("Configurando sandbox mode para testnet")
            else:
                logger.info("Configurando modo producción")
            
            # Mostrar la URL base que está usando el exchange
            logger.info(f"URL base del exchange: {self.exchange.urls['api']['public']}")
            
            # Cargar mercados
            self.exchange.load_markets()
            logger.info("Binance client initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing Binance client: {e}")
            raise
    
    def get_account_balance(self) -> Dict[str, float]:
        """Obtiene balance de la cuenta"""
        try:
            balance = self.exchange.fetch_balance()
            return {
                'USDT': float(balance.get('USDT', {}).get('free', 0)),
                'BTC': float(balance.get('BTC', {}).get('free', 0)),
                'total_usdt': float(balance.get('USDT', {}).get('total', 0))
            }
        except Exception as e:
            logger.error(f"Error fetching account balance: {e}")
            return {'USDT': 0, 'BTC': 0, 'total_usdt': 0}
    
    def get_market_data(self, symbol: str, timeframe: str = '1m', limit: int = 100) -> pd.DataFrame:
        """Obtiene datos de mercado"""
        try:
            ohlcv = self.exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            
            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df
            
        except Exception as e:
            logger.error(f"Error fetching market data for {symbol}: {e}")
            return pd.DataFrame()
    
    def get_all_symbols(self) -> List[str]:
        """Obtiene todos los símbolos disponibles"""
        try:
            symbols = []
            for symbol in self.exchange.symbols:
                if symbol.endswith('/USDT') and 'UPUSDT' not in symbol and 'DOWNUSDT' not in symbol:
                    symbols.append(symbol)
            return symbols
        except Exception as e:
            logger.error(f"Error fetching symbols: {e}")
            return []
    
    def place_market_order(self, symbol: str, side: str, quantity: float) -> Optional[Dict]:
        """Coloca orden de mercado"""
        try:
            order = self.exchange.create_market_order(
                symbol=symbol,
                side=side,
                amount=quantity
            )
            
            logger.info(f"Market order placed: {symbol} {side} {quantity}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing market order: {e}")
            return None
    
    def place_limit_order(self, symbol: str, side: str, quantity: float, price: float) -> Optional[Dict]:
        """Coloca orden límite"""
        try:
            order = self.exchange.create_limit_order(
                symbol=symbol,
                side=side,
                amount=quantity,
                price=price
            )
            
            logger.info(f"Limit order placed: {symbol} {side} {quantity} @ {price}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing limit order: {e}")
            return None
    
    def place_stop_loss_order(self, symbol: str, side: str, quantity: float, stop_price: float) -> Optional[Dict]:
        """Coloca orden de stop loss"""
        try:
            # Para stop loss, usamos stop market order
            order_type = 'stop_market' if side == 'sell' else 'stop_market'
            
            order = self.exchange.create_order(
                symbol=symbol,
                type=order_type,
                side=side,
                amount=quantity,
                price=stop_price,
                params={'stopPrice': stop_price}
            )
            
            logger.info(f"Stop loss order placed: {symbol} {side} {quantity} @ {stop_price}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing stop loss order: {e}")
            return None
    
    def place_take_profit_order(self, symbol: str, side: str, quantity: float, take_profit_price: float) -> Optional[Dict]:
        """Coloca orden de take profit"""
        try:
            order = self.exchange.create_limit_order(
                symbol=symbol,
                side=side,
                amount=quantity,
                price=take_profit_price
            )
            
            logger.info(f"Take profit order placed: {symbol} {side} {quantity} @ {take_profit_price}")
            return order
            
        except Exception as e:
            logger.error(f"Error placing take profit order: {e}")
            return None
    
    def cancel_order(self, symbol: str, order_id: str) -> bool:
        """Cancela una orden"""
        try:
            result = self.exchange.cancel_order(order_id, symbol)
            logger.info(f"Order cancelled: {symbol} {order_id}")
            return True
        except Exception as e:
            logger.error(f"Error cancelling order: {e}")
            return False
    
    def get_order_status(self, symbol: str, order_id: str) -> Optional[Dict]:
        """Obtiene estado de una orden"""
        try:
            order = self.exchange.fetch_order(order_id, symbol)
            return order
        except Exception as e:
            logger.error(f"Error fetching order status: {e}")
            return None
    
    def get_open_orders(self, symbol: str = None) -> List[Dict]:
        """Obtiene órdenes abiertas"""
        try:
            orders = self.exchange.fetch_open_orders(symbol)
            return orders
        except Exception as e:
            logger.error(f"Error fetching open orders: {e}")
            return []
    
    def get_trade_history(self, symbol: str = None, limit: int = 100) -> List[Dict]:
        """Obtiene historial de trades"""
        try:
            trades = self.exchange.fetch_my_trades(symbol, limit=limit)
            return trades
        except Exception as e:
            logger.error(f"Error fetching trade history: {e}")
            return []
    
    def calculate_position_size(self, symbol: str, usdt_amount: float) -> float:
        """Calcula cantidad de tokens basada en cantidad USDT"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Obtener precisión del símbolo
            market = self.exchange.market(symbol)
            amount_precision = market['precision']['amount']
            
            # Calcular cantidad
            quantity = usdt_amount / current_price
            
            # Redondear según precisión
            quantity = round(quantity, amount_precision)
            
            return quantity
            
        except Exception as e:
            logger.error(f"Error calculating position size: {e}")
            return 0.0
    
    def get_symbol_info(self, symbol: str) -> Optional[Dict]:
        """Obtiene información del símbolo"""
        try:
            market = self.exchange.market(symbol)
            ticker = self.exchange.fetch_ticker(symbol)
            
            return {
                'symbol': symbol,
                'base': market['base'],
                'quote': market['quote'],
                'min_amount': market['limits']['amount']['min'],
                'max_amount': market['limits']['amount']['max'],
                'min_cost': market['limits']['cost']['min'],
                'price_precision': market['precision']['price'],
                'amount_precision': market['precision']['amount'],
                'current_price': ticker['last'],
                'bid': ticker['bid'],
                'ask': ticker['ask'],
                'spread': (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100
            }
            
        except Exception as e:
            logger.error(f"Error fetching symbol info: {e}")
            return None
    
    def check_liquidity(self, symbol: str, amount_usdt: float) -> bool:
        """Verifica si hay suficiente liquidez para la operación"""
        try:
            ticker = self.exchange.fetch_ticker(symbol)
            current_price = ticker['last']
            
            # Verificar volumen 24h
            volume_24h = ticker['quoteVolume']
            if volume_24h < amount_usdt * 10:  # Al menos 10x el volumen de la operación
                return False
            
            # Verificar spread
            spread = (ticker['ask'] - ticker['bid']) / ticker['bid'] * 100
            if spread > 1:  # Spread máximo del 1%
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking liquidity: {e}")
            return False
    
    def execute_trade(self, trade_info: Dict) -> Optional[Dict]:
        """Ejecuta una operación completa con SL/TP"""
        try:
            symbol = trade_info['symbol']
            side = trade_info['side']
            quantity = trade_info['quantity']
            stop_loss = trade_info.get('stop_loss')
            take_profit = trade_info.get('take_profit')
            
            # Verificar liquidez
            if not self.check_liquidity(symbol, trade_info.get('usdt_amount', 0)):
                logger.warning(f"Insufficient liquidity for {symbol}")
                return None
            
            # Colocar orden principal
            main_order = self.place_market_order(symbol, side, quantity)
            if not main_order:
                return None
            
            orders = [main_order]
            
            # Colocar stop loss si se especifica
            if stop_loss:
                sl_side = 'sell' if side == 'buy' else 'buy'
                sl_order = self.place_stop_loss_order(symbol, sl_side, quantity, stop_loss)
                if sl_order:
                    orders.append(sl_order)
            
            # Colocar take profit si se especifica
            if take_profit:
                tp_side = 'sell' if side == 'buy' else 'buy'
                tp_order = self.place_take_profit_order(symbol, tp_side, quantity, take_profit)
                if tp_order:
                    orders.append(tp_order)
            
            return {
                'main_order': main_order,
                'stop_loss_order': orders[1] if len(orders) > 1 else None,
                'take_profit_order': orders[2] if len(orders) > 2 else None,
                'all_orders': orders
            }
            
        except Exception as e:
            logger.error(f"Error executing trade: {e}")
            return None
