from cv_extractor import extract_candles
from features import build_features
from patterns import detect_patterns
from trend import trend_signal
from confidence import confidence_from_probs
from model_registry import get_model
from config import MIN_QUALITY_SCORE
import numpy as np

def analyze(image_bytes, tf):
    candles, quality = extract_candles(image_bytes)
    if quality < MIN_QUALITY_SCORE:
        return None, "Низкое качество скрина"

    if len(candles) < 12:
        return None, "Недостаточно свечей (нужно минимум 12)"

    model = get_model(tf)
    X = build_features(candles, tf)

    # 1. ML signal
    if len(X) >= 4:
        y = (X[:,1] > 0).astype(int)
        model.fit(X[:-3], y[:-3])
        ml_probs = model.predict(X[-3:])[:,1]
        ml_prob = ml_probs.mean()
        ml_conf = 1 - abs(ml_prob - 0.5) * 2
    else:
        ml_prob, ml_conf = 0.5, 0.0

    # 2. Pattern signal
    patterns, pattern_score = detect_patterns(candles[-8:])
    pattern_prob = 0.5 + pattern_score * 0.4
    pattern_conf = pattern_score

    # 3. Trend signal
    trend_prob, trend_conf = trend_signal(candles)

    # Confidence-weighted ensemble
    weights = [ml_conf, pattern_conf, trend_conf]
    total_weight = sum(weights) + 1e-6
    final_prob = (ml_prob * ml_conf + pattern_prob * pattern_conf + trend_prob * trend_conf) / total_weight

    # Confidence from dispersion of the three predictions
    ensemble_probs = [ml_prob, pattern_prob, trend_prob]
    conf_label, conf_score = confidence_from_probs(ensemble_probs)

    return {
        "prob": round(final_prob, 3),
        "confidence": conf_label,
        "confidence_score": conf_score,
        "quality": quality,
        "patterns": patterns,
        "tf": tf
    }, None