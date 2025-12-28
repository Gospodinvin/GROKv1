from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ContentType
from config import TELEGRAM_BOT_TOKEN, STATE_TTL_SECONDS
from keyboards import timeframe_keyboard
from state import TTLState
from predictor import analyze
import re

state = TTLState(STATE_TTL_SECONDS)

async def start(m: Message):
    await m.answer(
        "🤖 Анализатор свечных паттернов\n\n"
        "Способы использования:\n"
        "📸 Пришли скриншот графика\n"
        "💹 Или напиши тикер + таймфрейм (например: BTCUSD 5m)"
    )

async def image(m: Message):
    bio = BytesIO()
    f = await m.bot.get_file((m.photo[-1] if m.photo else m.document).file_id)
    await m.bot.download_file(f.file_path, bio)
    await state.set(m.from_user.id, "img", bio.getvalue())
    await state.set(m.from_user.id, "mode", "image")
    await m.answer("Выбери таймфрейм", reply_markup=timeframe_keyboard())

async def ticker(m: Message):
    """Парсинг тикера из текста"""
    text = m.text.strip().upper()
    # Паттерн: BTCUSD 5m или EURUSD5m
    match = re.match(r"([A-Z]{3,12})(?:\s+)?(\d+)M?", text)
    if match:
        symbol, tf = match.groups()
        tf = tf.zfill(1)  # 5 → "5"
        if tf in ["1", "2", "5", "10"]:
            await state.set(m.from_user.id, "symbol", symbol)
            await state.set(m.from_user.id, "tf", tf)
            await state.set(m.from_user.id, "mode", "api")
            res, err = analyze(None, tf, symbol)
            
            if err:
                await m.answer(err)
            else:
                growth_pct = int(res['prob'] * 100)
                txt = (
                    f"📊 {symbol} | {tf} мин\n"
                    f"Вероятность роста: {growth_pct}%\n"
                    f"Уверенность: {res['confidence']} ({res['confidence_score']})\n"
                    f"Источник: {res['source']}\n"
                )
                if res["patterns"]:
                    txt += "Паттерны: " + ", ".join(res["patterns"]) + "\n"
                txt += "\n⚠ Не является финансовой рекомендацией"
                await m.answer(txt)
            await state.clear(m.from_user.id)
        else:
            await m.answer("Поддерживаемые таймфреймы: 1m, 2m, 5m, 10m")
    else:
        await m.answer("Формат: ТИКЕР ТФ (например: BTCUSD 5m)")

async def tf(cb: CallbackQuery):
    tf = cb.data.split(":")[1]
    mode = await state.get(cb.from_user.id, "mode")
    
    if mode == "image":
        img = await state.get(cb.from_user.id, "img")
        res, err = analyze(img, tf)
    elif mode == "api":
        symbol = await state.get(cb.from_user.id, "symbol")
        res, err = analyze(None, tf, symbol)
    else:
        await cb.answer("Ошибка состояния")
        return

    if err:
        await cb.message.answer(err)
    else:
        growth_pct = int(res['prob'] * 100)
        txt = (
            f"📊 {res.get('symbol', 'График')} | {tf} мин\n"
            f"Вероятность роста: {growth_pct}%\n"
            f"Уверенность: {res['confidence']} ({res['confidence_score']})\n"
            f"Качество: {res['quality']}\n"
            f"Источник: {res['source']}\n"
        )
        if res["patterns"]:
            txt += "Паттерны: " + ", ".join(res["patterns"]) + "\n"
        txt += "\n⚠ Не является финансовой рекомендацией"
        await cb.message.answer(txt)

    await state.clear(cb.from_user.id)
    await cb.answer()

def main():
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    
    # Регистрация обработчиков
    dp.message.register(start, CommandStart())
    dp.message.register(image, F.content_type.in_({ContentType.PHOTO, ContentType.DOCUMENT}))
    dp.message.register(ticker, F.text)  # Новый: обработка тикеров
    dp.callback_query.register(tf, F.data.startswith("tf:"))
    
    dp.run_polling(bot)

if __name__ == "__main__":
    main()
