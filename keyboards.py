from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import datetime

# Рекомендуемые тикеры по сессиям (расширенный список)
SESSION_TICKERS = {
    "asian": ["AUDUSD", "NZDUSD", "USDJPY", "AUDJPY", "USDCNH", "EURJPY", "GBPAUD", "CHFJPY", "AUDNZD", "NZDJPY"],
    "london": ["EURUSD", "GBPUSD", "EURGBP", "EURJPY", "GBPJPY", "USDCHF", "EURCAD", "GBPCAD", "EURCHF", "GBPCHF"],
    "newyork": ["EURUSD", "GBPUSD", "USDCAD", "XAUUSD", "US30", "USDJPY", "AUDCAD", "SPX500", "XAGUSD", "USOIL"],
    "overlap": ["EURUSD", "GBPUSD", "XAUUSD", "USDCAD", "USDJPY", "EURCHF", "GBPCHF", "XAGUSD", "GBPJPY", "EURJPY"]  # Лондон+НЙ
}

def get_current_session():
    # Московское время (UTC+3)
    msk_hour = (datetime.datetime.utcnow() + datetime.timedelta(hours=3)).hour
    
    if 3 <= msk_hour < 11:
        return "asian", "🌏 Азиатская сессия (03:00–11:00 MSK)"
    elif 11 <= msk_hour < 16:
        return "london", "🇬🇧 Лондонская сессия (11:00–19:00 MSK)"
    elif 16 <= msk_hour < 19:
        return "overlap", "🔥 Пересечение Лондон + Нью-Йорк (16:00–19:00 MSK) — максимальная волатильность!"
    elif 19 <= msk_hour < 24 or 0 <= msk_hour < 3:
        return "newyork", "🇺🇸 Нью-Йоркская сессия (16:00–00:00 MSK)"
    else:
        return "closed", "🌙 Рынок спит (выходные или ночь)"

def session_keyboard():
    session_key, session_text = get_current_session()
    
    if session_key == "closed":
        keyboard = [[InlineKeyboardButton(text="📸 Анализ по скриншоту", callback_data="mode:image")]]
        info = f"Текущая сессия: {session_text}\n\nВыберите режим:"
    else:
        tickers = SESSION_TICKERS.get(session_key, SESSION_TICKERS["newyork"])
        buttons = []
        row = []
        for t in tickers:
            row.append(InlineKeyboardButton(text=t, callback_data=f"ticker:{t}"))
            if len(row) == 3:  # 3 столбца для удобства
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)
        
        buttons.append([InlineKeyboardButton(text="📸 Анализ по скриншоту", callback_data="mode:image")])
        
        keyboard = buttons
        info = f"Текущая сессия: {session_text}\nРекомендуемые пары:\n\nВыберите тикер:"
    
    return InlineKeyboardMarkup(inline_keyboard=keyboard), info

def timeframe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="1 минута", callback_data="tf:1"),
            InlineKeyboardButton(text="2 минуты", callback_data="tf:2"),
            InlineKeyboardButton(text="5 минут", callback_data="tf:5"),
        ],
        [
            InlineKeyboardButton(text="10 минут", callback_data="tf:10"),
        ]
    ])
