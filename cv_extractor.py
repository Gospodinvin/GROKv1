import cv2
import numpy as np

def compute_quality(crop, num_candles):
    # Новый quality: комбинация найденных свечей (основной фактор) + контраст/края
    base_from_candles = min(num_candles / 50.0, 1.0)  # нормируем, 50 свечей = max
    edges = cv2.Canny(crop, 50, 150)
    edge_density = edges.mean() / 255.0
    contrast = crop.std() / 255.0
    technical = (edge_density + contrast) / 2
    return round(0.6 * base_from_candles + 0.4 * technical, 2)

def dynamic_crop(img):
    edges = cv2.Canny(img, 50, 150)
    projection = np.sum(edges, axis=1)
    threshold = np.max(projection) * 0.05 if np.max(projection) > 0 else 0
    non_zero_rows = np.where(projection > threshold)[0]
    if len(non_zero_rows) == 0:
        return img
    top = max(0, non_zero_rows[0] - 30)
    bottom = min(img.shape[0], non_zero_rows[-1] + 30)
    w = img.shape[1]
    return img[top:bottom, int(w*0.03):int(w*0.97)]

def extract_candles(image_bytes, max_candles=50):
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    if img is None:
        raise ValueError("Не удалось декодировать изображение")
    h, w = img.shape

    # Предварительный crop от панелей
    initial_crop = img[int(h*0.1):int(h*0.9), int(w*0.03):int(w*0.97)]

    # Улучшения
    blurred = cv2.GaussianBlur(initial_crop, (5, 5), 0)
    clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8,8))
    enhanced = clahe.apply(blurred)

    # Динамический crop вокруг свечей
    crop = dynamic_crop(enhanced)

    # Детекция вертикальных линий
    edges = cv2.Canny(crop, 40, 120)  # чуть мягче thresholds
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 20))
    verticals = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)
    verticals = cv2.dilate(verticals, kernel, iterations=1)

    contours, _ = cv2.findContours(verticals, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ch, cw = crop.shape
    candles = []

    for c in contours:
        x, y, w_, h_ = cv2.boundingRect(c)
        if h_ < ch * 0.06 or w_ > cw * 0.06 or h_ / max(w_, 1) < 3: continue
        candles.append({
            "open": (y + h_ * 0.25) / ch,
            "close": (y + h_ * 0.75) / ch,
            "high": y / ch,
            "low": (y + h_) / ch,
        })

    quality = compute_quality(crop, len(candles))
    return candles[-max_candles:], quality
