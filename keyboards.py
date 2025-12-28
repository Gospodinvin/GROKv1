from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton

# Кнопки для выбора тикера
def ticker_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="BTCUSD", callback_data="ticker:BTCUSD"),
            InlineKeyboardButton(text="ETHUSD", callback_data="ticker:ETHUSD"),
        ],
        [
            InlineKeyboardButton(text="EURUSD", callback_data="ticker:EURUSD"),
            InlineKeyboardButton(text="GBPUSD", callback_data="ticker:GBPUSD"),
        ],
        [
            InlineKeyboardButton(text="GOLD (XAUUSD)", callback_data="ticker:XAUUSD"),
            InlineKeyboardButton(text="US30", callback_data="ticker:US30"),
        ],
        [
            InlineKeyboardButton(text="📸 Анализ по скриншоту", callback_data="mode:image"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

# Кнопки для выбора таймфрейма (остаётся как было, но улучшим текст)
def timeframe_keyboard():
    buttons = [
        [
            InlineKeyboardButton(text="1 минута", callback_data="tf:1"),
            InlineKeyboardButton(text="2 минуты", callback_data="tf:2"),
        ],
        [
            InlineKeyboardButton(text="5 минут", callback_data="tf:5"),
            InlineKeyboardButton(text="10 минут", callback_data="tf:10"),
        ]
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)
