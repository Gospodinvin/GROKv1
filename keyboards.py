from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def timeframe_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text="1 мин", callback_data="tf:1"),
        InlineKeyboardButton(text="2 мин", callback_data="tf:2"),
        InlineKeyboardButton(text="5 мин", callback_data="tf:5"),
        InlineKeyboardButton(text="10 мин", callback_data="tf:10"),
    ]])