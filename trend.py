import numpy as np

def trend_signal(candles):
    if len(candles) < 8:
        return 0.5, 0.0
    closes = np.array([c["close"] for c in candles[-8:]])
    
    # Вычисляем корреляцию вручную, чтобы избежать деления на ноль
    x = np.arange(8)
    mean_x = np.mean(x)
    mean_y = np.mean(closes)
    
    cov = np.sum((x - mean_x) * (closes - mean_y))
    std_x = np.std(x)
    std_y = np.std(closes)
    
    if std_x == 0 or std_y == 0:
        trend_strength = 0.0  # нет вариации → нет тренда
    else:
        trend_strength = cov / (std_x * std_y * 8)  # нормализованная корреляция (-1 до 1)
    
    prob_up = (trend_strength + 1) / 2
    confidence = abs(trend_strength)
    return prob_up, confidence
