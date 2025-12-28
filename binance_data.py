import requests
import logging
from typing import List, Dict, Optional

BASE_URL = "https://api.binance.com/api/v3/klines"

# Маппинг тикеров крипты на Binance (USD → USDT, цены идентичны)
SYMBOL_MAP = {
    "BTCUSD": "BTCUSDT",
    "ETHUSD": "ETHUSDT", 
    "BNBUSD": "BNBUSDT",
    "SOLUSD": "SOLUSDT",
    "XRPUSD": "XRPUSDT",
    "ADAUSD": "ADAUSDT",
    "DOGEUSD": "DOGEUSDT",
    "AVAXUSD": "AVAXUSDT",
    "DOTUSD": "DOTUSDT",
    "LTCUSD": "LTCUSDT",
}

# Маппинг таймфреймов (Binance не имеет 2m, используем ближайший или аггрегируем)
INTERVAL_MAP = {
    "1": "1m",
    "2": "3m",  # Ближайший к 2m
    "5": "5m",
    "10": "15m",  # Ближайший к 10m (можно доработать аггрегацию)
}

def get_candles(symbol: str, interval: str, outputsize: int = 60) -> Optional[List[Dict]]:
    """Получить свечи для крипто-символа из Binance API"""
    binance_symbol = SYMBOL_MAP.get(symbol.upper())
    if not binance_symbol:
        logging.warning(f"Тикер {symbol} не поддерживается Binance")
        return None
    
    binance_interval = INTERVAL_MAP.get(interval)
    if not binance_interval:
        logging.warning(f"TF {interval} не поддерживается Binance")
        return None
    
    params = {
        "symbol": binance_symbol,
        "interval": binance_interval,
        "limit": outputsize + 10,  # Берем чуть больше для безопасности
    }
    
    try:
        response = requests.get(BASE_URL, params=params, timeout=10)
        response.raise_for_status()
        data = response.json()
        
        if not data:
            logging.warning(f"Нет данных для {symbol} {interval}")
            return None
        
        # Парсим в формат свечей (OHLCV)
        candles = []
        for candle in data:
            candles.append({
                "open": float(candle[1]),
                "high": float(candle[2]),
                "low": float(candle[3]),
                "close": float(candle[4]),
                "volume": float(candle[5]),
            })
        
        # Нормализуем цены (делим на max high, как в CV)
        max_price = max(c["high"] for c in candles) if candles else 1.0
        for candle in candles:
            candle["open"] /= max_price
            candle["high"] /= max_price
            candle["low"] /= max_price
            candle["close"] /= max_price
        
        # Возвращаем последние N свечей (в обратном порядке: старые → новые)
        return candles[-outputsize:][::-1]  # Обрезаем и реверсим
        
    except Exception as e:
        logging.error(f"Binance API error для {symbol}: {e}")
        return None
