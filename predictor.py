from cv_extractor import extract_candles
from features import build_features
from patterns import detect_patterns
from trend import trend_signal
from confidence import confidence_from_probs
from model_registry import get_model
from twelve_data import get_client
from binance_data import get_candles as binance_get_candles  # Новый импорт
import numpy as np

def analyze(image_bytes=None, tf=None, symbol=None):
    """
    Универсальная функция анализа:
    - Если symbol указан — используем Twelve Data API (для forex/metals/stocks) или Binance (для crypto)
    - Если image_bytes — используем CV из скриншота
    """
    candles = None
    quality = 1.0
    source = "скриншот"

    # Режим API
    if symbol:
        # Определяем рынок по символу (простая проверка: если содержит USD и не XAU/XAG — крипта)
        is_crypto = any(coin in symbol.upper() for coin in ["BTC", "ETH", "BNB", "SOL", "XRP", "ADA", "DOGE", "AVAX", "DOT", "LTC"])
        
        if is_crypto:
            # Используем Binance для крипты
            candles = binance_get_candles(symbol.upper(), tf, 60)
            if not candles:
                return None, f"Ошибка Binance API для {symbol} ({tf}m). Попробуйте скриншот."
            source = "Binance API"
        else:
            # Twelve Data для forex, metals, stocks
            client = get_client()
            if not client:
                return None, "Twelve Data API не настроен (ключ не найден). Используйте скриншот."
            
            try:
                candles = client.get_candles(symbol.upper(), f"{tf}min", 60)
            except Exception as e:
                return None, f"Ошибка Twelve Data API: {str(e)}. Попробуйте позже или используйте скриншот."
            
            if not candles or len(candles) < 12:
                return None, f"Данные для {symbol} ({tf}m) недоступны или недостаточно свечей ({len(candles) if candles else 0}). Проверьте тикер или подключение."
            source = "Twelve Data API"

    # Режим скриншота
    elif image_bytes:
        candles, quality = extract_candles(image_bytes)
        if len(candles) < 12:
            return None, f"Обнаружено только {len(candles)} свечей (нужно минимум 12). Покажите больше истории."
        source = "скриншот"
    else:
        return None, "Нет данных: укажите скриншот или тикер."

    # Основной анализ (без изменений)
    model = get_model(tf)
    X = build_features(candles, tf)

    # ML сигнал с защитой
    ml_prob = 0.5
    ml_conf = 0.0
    if len(X) >= 7:
        y = (X[:,1] > 0).astype(int)
        train_y = y[:-3]
        if len(np.unique(train_y)) >= 2:
            try:
                model.fit(X[:-3], train_y)
                ml_probs = model.predict(X[-3:])[:,1]
                ml_prob = ml_probs.mean()
                ml_conf = 1 - abs(ml_prob - 0.5) * 2
            except Exception:
                pass

    # Паттерны и тренд
    patterns, pattern_score = detect_patterns(candles[-8:])
    pattern_prob = 0.5 + pattern_score * 0.4
    pattern_conf = pattern_score

    trend_prob, trend_conf = trend_signal(candles)

    # Ансамбль
    weights = [ml_conf, pattern_conf, trend_conf]
    total_weight = sum(weights) + 1e-6
    final_prob = (ml_prob * ml_conf + pattern_prob * pattern_conf + trend_prob * trend_conf) / total_weight

    # Добавляем вероятность падения
    down_prob = 1.0 - final_prob

    ensemble_probs = [ml_prob if ml_conf > 0 else (pattern_prob + trend_prob)/2, pattern_prob, trend_prob]
    conf_label, conf_score = confidence_from_probs(ensemble_probs)

    return {
        "prob": round(final_prob, 3),
        "down_prob": round(down_prob, 3),
        "confidence": conf_label,
        "confidence_score": conf_score,
        "quality": quality,
        "patterns": patterns,
        "tf": tf,
        "source": source,
        "symbol": symbol.upper() if symbol else None
    }, None
