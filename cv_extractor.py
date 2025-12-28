import cv2
import numpy as np

def screen_quality_score(img):
    edges = cv2.Canny(img, 50, 150)
    edge_density = edges.mean() / 255.0
    contrast = img.std() / 255.0
    return round((edge_density + contrast) / 2, 2)

def extract_candles(image_bytes, max_candles=40):
    img = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_GRAYSCALE)
    h, w = img.shape

    crop = img[int(h*0.15):int(h*0.85), int(w*0.05):int(w*0.95)]
    clahe = cv2.createCLAHE(2.0,(8,8))
    crop = clahe.apply(crop)

    edges = cv2.Canny(crop,50,150)
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT,(3,15))
    verticals = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    contours,_ = cv2.findContours(verticals, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    ch,cw = crop.shape
    candles=[]

    for c in contours:
        x,y,w_,h_ = cv2.boundingRect(c)
        if h_<ch*0.08 or w_>cw*0.05 or h_/max(w_,1)<2: continue
        candles.append({
            "open": (y+h_*0.25)/ch,
            "close": (y+h_*0.75)/ch,
            "high": y/ch,
            "low": (y+h_)/ch,
        })

    return candles[-max_candles:], screen_quality_score(crop)