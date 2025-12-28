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
        "🤖 Анализатор свечных графиков\n\n"
        "Варианты использования:\n"
        "📸 Пришли скриншот графика → выбери таймфрейм\n"
        "💹 Напиши тикер + TF (например: BTCUSD 5m или eurusd 1m)"
    )

async def image_handler(m: Message):
    bio = BytesIO()
    file_id = m.photo[-1].file_id if m.photo else m.document.file_id
    file = await m.bot.get_file(file_id)
    await m.bot.download_file(file.file_path, bio)
    await state.set(m.from_user.id, "data", bio.getvalue())
    await state.set(m.from_user.id, "mode", "image")
    await m.answer("Выбери таймфрейм:", reply_markup=timeframe_keyboard())

async def text_handler(m: Message):
    text = m.text.strip().upper()
    match = re.match(r"([A-Z]{3,12})\s*(\d+)?\s*(M|MIN)?", text)
    if match:
        symbol = match.group(1)
        tf = match.group(2)
        if tf not in ["1", "2", "5", "10"]:
            await m.answer("Поддерживаемые TF: 1, 2, 5, 10 минут")
            return
        res, err = analyze(tf=tf, symbol=symbol)
        if err:
            await m.answer(f"❌ {err}")
        else:
            await send_result(m, res)
    else:
        await m.answer("Формат: ТИКЕР TF (например: BTCUSD 5)")

async def tf_callback(cb: CallbackQuery):
    tf = cb.data.split(":")[1]
    mode = await state.get(cb.from_user.id, "mode")

    if mode == "image":
        img = await state.get(cb.from_user.id, "data")
        res, err = analyze(image_bytes=img, tf=tf)
    else:
        # Если режим не image — возможно, был тикер, но состояние устарело
        await cb.message.answer("Сессия истекла. Пришли новый скрин или тикер.")
        await cb.answer()
        return

    if err:
        await cb.message.answer(f"❌ {err}")
    else:
        await send_result(cb.message, res)
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
    txt += "\n⚠ Не финансовая рекомендация. Торгуйте осознанно."
    await message.answer(txt)

def main():
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()

    dp.message.register(start, CommandStart())
    dp.message.register(image_handler, F.content_type.in_({ContentType.PHOTO, ContentType.DOCUMENT}))
    dp.message.register(text_handler, F.text)  # Обрабатывает тикеры
    dp.callback_query.register(tf_callback, F.data.startswith("tf:"))

    print("Бот запущен...")
    dp.run_polling(bot)

if __name__ == "__main__":
    main()
