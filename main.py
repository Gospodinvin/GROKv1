from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ContentType
from config import TELEGRAM_BOT_TOKEN, STATE_TTL_SECONDS
from keyboards import session_keyboard, timeframe_keyboard
from state import TTLState
from predictor import analyze
import re

state = TTLState(STATE_TTL_SECONDS)

async def start(m: Message):
    keyboard, text = session_keyboard()
    await m.answer(
        "🤖 Боттрейд — анализ свечных графиков\n\n"
        f"{text}",
        reply_markup=keyboard
    )

async def image_handler(m: Message):
    bio = BytesIO()
    file_id = m.photo[-1].file_id if m.photo else m.document.file_id
    file = await m.bot.get_file(file_id)
    await m.bot.download_file(file.file_path, bio)
    await state.set(m.from_user.id, "data", bio.getvalue())
    await state.set(m.from_user.id, "mode", "image")
    await m.answer("Выберите таймфрейм:", reply_markup=timeframe_keyboard())

# Обработка выбора тикера
async def ticker_callback(cb: CallbackQuery):
    if cb.data.startswith("ticker:"):
        symbol = cb.data.split(":")[1]
        await state.set(cb.from_user.id, "symbol", symbol)
        await state.set(cb.from_user.id, "mode", "api")
        await cb.message.edit_text(
            f"✅ Выбран тикер: {symbol}\n\nВыберите таймфрейм:",
            reply_markup=timeframe_keyboard()
        )
    elif cb.data == "mode:image":
        await cb.message.edit_text(
            "📸 Пришлите скриншот графика для анализа.\nПосле отправки выберите таймфрейм."
        )
    await cb.answer()

# Обработка выбора таймфрейма
async def tf_callback(cb: CallbackQuery):
    tf = cb.data.split(":")[1]
    mode = await state.get(cb.from_user.id, "mode")

    res = None
    err = None

    if mode == "image":
        img = await state.get(cb.from_user.id, "data")
        if img:
            res, err = analyze(image_bytes=img, tf=tf)
        else:
            err = "Скриншот не найден. Пришлите новый."
    elif mode == "api":
        symbol = await state.get(cb.from_user.id, "symbol")
        if symbol:
            res, err = analyze(tf=tf, symbol=symbol)
        else:
            err = "Тикер не выбран."
    else:
        err = "Режим не определён. Начните заново с /start"

    if err:
        await cb.message.answer(f"❌ {err}\n\nНачните заново:", reply_markup=session_keyboard()[0])
    else:
        await send_result(cb.message, res)
        # Предлагаем продолжить
        await cb.message.answer("Хотите проанализировать другой тикер?", reply_markup=session_keyboard()[0])

    await state.clear(cb.from_user.id)
    await cb.answer()

async def send_result(message: Message, res: dict):
    growth_pct = int(res["prob"] * 100)
    txt = (
        f"📊 {res.get('symbol', 'График')} | {res['tf']} мин\n"
        f"Вероятность роста на 2–3 свечи: {growth_pct}%\n"
        f"Уверенность: {res['confidence']} ({res['confidence_score']})\n"
        f"Источник: {res['source']}\n"
    )
    if res.get("quality", 1.0) < 1.0:
        txt += f"Качество скрина: {res['quality']}\n"
    if res["patterns"]:
        txt += "Паттерны: " + ", ".join(res["patterns"]) + "\n"
    txt += "\n⚠ Не является финансовой рекомендацией"
    await message.answer(txt)

def main():
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(start, CommandStart())
    dp.message.register(image_handler, F.content_type.in_({ContentType.PHOTO, ContentType.DOCUMENT}))
    
    # Новые обработчики
    dp.callback_query.register(ticker_callback, F.data.startswith("ticker:") | F.data == "mode:image")
    dp.callback_query.register(tf_callback, F.data.startswith("tf:"))

    print("Бот запущен с кнопками!")
    dp.run_polling(bot)

if __name__ == "__main__":
    main()
