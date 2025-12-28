import cv2
import numpy as np

def screen_quality_score(img):
    edges = cv2.Canny(img, 50, 150)
    edge_density = edges.mean() / 255.0
    contrast = img.std() / 255.0
    return round((edge_density + contrast) / 2, 2)

def dynamic_crop(img):
    # Вычисляем вертикальную проекцию (сумма по строкам) для поиска области свечей
    edges = cv2.Canny(img, 50, 150)
    projection = np.sum(edges, axis=1)
    threshold = np.max(projection) * 0.1  # 10% от макс для отсечения шума
    
    # Находим верх и низ где проекция > threshold
    non_zero_rows = np.where(projection > threshold)[0]
    if len(non_zero_rows) == 0:
        return img  # fallback
    top = max(0, non_zero_rows[0] - 20)  # буфер 20px
    bottom = min(img.shape[0], non_zero_rows[-1] + 20)
    
    # Обрезаем по ширине стандартно
    w = img.shape[1]
    return img[top:bottom, int(w*0.05):int(w*0.95)]

def extract_candles(image_bytes, max_candles=40):
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    h, w = img.shape

    # Начальный crop для удаления очевидных панелей
    initial_crop = img[int(h*0.1):int(h*0.9), int(w*0.05):int(w*0.95)]
    
    # Улучшение: Gaussian blur для снижения шума
    initial_crop = cv2.GaussianBlur(initial_crop, (3, 3), 0)
    
    clahe = cv2.createCLAHE(2.0, (8, 8))
    enhanced = clahe.apply(initial_crop)
    
    # Динамический crop вокруг свечей
    crop = dynamic_crop(enhanced)
    
    edges = cv2.Canny(crop, 50, 150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 15))
    verticals = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours, _ = cv2.findContours(verticals, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ch, cw = crop.shape
    candles = []

    for c in contours:
        x, y, w_, h_ = cv2.boundingRect(c)
        if h_ < ch * 0.08 or w_ > cw * 0.05 or h_ / max(w_, 1) < 2: continue
        candles.append({
            "open": (y + h_ * 0.25) / ch,
            "close": (y + h_ * 0.75) / ch,
            "high": y / ch,
            "low": (y + h_) / ch,
        })

    quality = screen_quality_score(crop)
    return candles[-max_candles:], quality
