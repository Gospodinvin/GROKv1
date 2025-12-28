from cv_extractor import extract_candles
from features import build_features
from patterns import detect_patterns
from trend import trend_signal
from confidence import confidence_from_probs
from model_registry import get_model
import numpy as np

def analyze(image_bytes, tf):
    candles, quality = extract_candles(image_bytes)

    if len(candles) < 12:
        return None, f"Обнаружено только {len(candles)} свечей (нужно минимум 12).\nСовет: увеличьте масштаб или покажите больше истории на графике (прокрутите влево)."

    model = get_model(tf)
    X = build_features(candles, tf)

    # ML сигнал с защитой от ошибки
    ml_prob = 0.5
    ml_conf = 0.0  # низкая уверенность по умолчанию
    if len(X) >= 7:  # нужно минимум 4 для обучения + 3 для предсказания
        y = (X[:,1] > 0).astype(int)
        train_y = y[:-3]
        if len(np.unique(train_y)) >= 2:  # есть оба класса
            try:
                model.fit(X[:-3], train_y)
                ml_probs = model.predict(X[-3:])[:,1]
                ml_prob = ml_probs.mean()
                ml_conf = 1 - abs(ml_prob - 0.5) * 2  # уверенность от отклонения от 0.5
            except ValueError:
                # На всякий случай (хотя проверка выше должна поймать)
                ml_prob = 0.5
                ml_conf = 0.0
        # else: только один класс — оставляем ml_prob=0.5, ml_conf=0.0

    # Паттерны
    patterns, pattern_score = detect_patterns(candles[-8:])
    pattern_prob = 0.5 + pattern_score * 0.4
    pattern_conf = pattern_score

    # Тренд
    trend_prob, trend_conf = trend_signal(candles)

    # Ансамбль (ML вес 0, если не обучился)
    weights = [ml_conf, pattern_conf, trend_conf]
    total_weight = sum(weights) + 1e-6
    final_prob = (ml_prob * ml_conf + pattern_prob * pattern_conf + trend_prob * trend_conf) / total_weight

    ensemble_probs = [ml_prob if ml_conf > 0 else (pattern_prob + trend_prob)/2, pattern_prob, trend_prob]
    conf_label, conf_score = confidence_from_probs(ensemble_probs)

    return {
        "prob": round(final_prob, 3),
        "confidence": conf_label,
        "confidence_score": conf_score,
        "quality": quality,
        "patterns": patterns,
        "tf": tf
    }, None
