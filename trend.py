import numpy as np

def trend_signal(candles):
    if len(candles) < 8:
        return 0.5, 0.0
    closes = np.array([c["close"] for c in candles[-8:]])
    trend_strength = np.corrcoef(np.arange(8), closes)[0,1]
    if np.isnan(trend_strength):
        return 0.5, 0.0
    prob_up = (trend_strength + 1) / 2
    confidence = abs(trend_strength)
    return prob_up, confidence