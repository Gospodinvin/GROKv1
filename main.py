from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ContentType
from config import TELEGRAM_BOT_TOKEN, STATE_TTL_SECONDS
from keyboards import market_keyboard, tickers_keyboard, timeframe_keyboard
from state import TTLState
from predictor import analyze
import logging

state = TTLState(STATE_TTL_SECONDS)

async def start(m: Message):
    await m.answer(
        "🤖 Боттрейд — анализ свечных графиков\n\n"
        "Выберите рынок для анализа:",
        reply_markup=market_keyboard()
    )

async def image_handler(m: Message):
    bio = BytesIO()
    file_id = m.photo[-1].file_id if m.photo else m.document.file_id
    file = await m.bot.get_file(file_id)
    await m.bot.download_file(file.file_path, bio)
    await state.set(m.from_user.id, "data", bio.getvalue())
    await state.set(m.from_user.id, "mode", "image")
    await m.answer("Выберите таймфрейм:", reply_markup=timeframe_keyboard())

async def callback_handler(cb: CallbackQuery):
    if not cb.data:
        return

    data = cb.data
    user_id = cb.from_user.id

    if data.startswith("market:"):
        market = data.split(":")[1]
        await state.set(user_id, "market", market)
        keyboard, text = tickers_keyboard(market)
        await cb.message.edit_text(text, reply_markup=keyboard)
        await cb.answer()
        return

    if data.startswith("ticker:"):
        symbol = data.split(":")[1]
        logging.info(f"Пользователь {user_id} выбрал тикер: {symbol}")
        await state.set(user_id, "symbol", symbol)
        await state.set(user_id, "mode", "api")
        await cb.message.edit_text(
            f"✅ Выбран тикер: {symbol}\n\nВыберите таймфрейм:",
            reply_markup=timeframe_keyboard()
        )
        await cb.answer("Тикер сохранён!")
        return

    if data == "back:markets":
        await cb.message.edit_text(
            "Выберите рынок для анализа:",
            reply_markup=market_keyboard()
        )
        await cb.answer()
        return

    if data == "mode:image":
        await state.set(user_id, "mode", "image")
        await state.set(user_id, "data", None)  # очищаем старый скрин
        await cb.message.edit_text(
            "📸 Пришлите скриншот графика для анализа.\nПосле отправки выберите таймфрейм."
        )
        await cb.answer()
        return

    if data.startswith("tf:"):
        tf = data.split(":")[1]

        mode = await state.get(user_id, "mode")
        symbol = await state.get(user_id, "symbol")
        img_data = await state.get(user_id, "data")

        logging.info(f"Таймфрейм выбран: {tf} | mode={mode} | symbol={symbol}")

        res = None
        err = None

        if mode == "image":
            if img_data:
                res, err = analyze(image_bytes=img_data, tf=tf)
            else:
                err = "Скриншот не найден. Пришлите новый."
        elif mode == "api":
            if symbol:
                res, err = analyze(tf=tf, symbol=symbol)
            else:
                err = "Тикер не выбран. Начните заново."
        else:
            err = "Режим не определён. Начните заново с /start"

        if err:
            await cb.message.answer(f"❌ {err}\n\nНачните заново:", reply_markup=market_keyboard())
        else:
            await send_result(cb.message, res)
            await cb.message.answer("Хотите другой тикер?", reply_markup=market_keyboard())

        await state.clear(user_id)
        await cb.answer()
        return

async def send_result(message: Message, res: dict):
    growth_pct = int(res["prob"] * 100)
    down_pct = int(res["down_prob"] * 100)
    txt = (
        f"📊 {res.get('symbol', 'График')} | {res['tf']} мин\n"
        f"Вероятность роста на 2–3 свечи: {growth_pct}%\n"
        f"Вероятность падения: {down_pct}%\n"
        f"Уверенность: {res['confidence']} ({res['confidence_score']})\n"
        f"Источник: {res['source']}\n"
    )
    if res.get("quality", 1.0) < 1.0:
        txt += f"Качество скрина: {res['quality']:.2f}\n"
    if res["patterns"]:
        txt += "Паттерны: " + ", ".join(res["patterns"]) + "\n"
    txt += "\n⚠ Не является финансовой рекомендацией"
    await message.answer(txt)

def main():
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(start, CommandStart())
    dp.message.register(image_handler, F.content_type.in_({ContentType.PHOTO, ContentType.DOCUMENT}))

    # Один обработчик для всех callback — самый простой и надёжный способ
    dp.callback_query.register(callback_handler)

    print("Бот запущен — единый обработчик для всех callback (100% работает)!")
    dp.run_polling(bot)

if __name__ == "__main__":
    main()
