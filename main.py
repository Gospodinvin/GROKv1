from io import BytesIO
from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import CommandStart
from aiogram.enums import ContentType
from config import TELEGRAM_BOT_TOKEN, STATE_TTL_SECONDS
from keyboards import timeframe_keyboard
from state import TTLState
from predictor import analyze

state = TTLState(STATE_TTL_SECONDS)

async def start(m: Message):
    await m.answer("Пришли скрин графика и выбери таймфрейм")

async def image(m: Message):
    bio = BytesIO()
    f = await m.bot.get_file((m.photo[-1] if m.photo else m.document).file_id)
    await m.bot.download_file(f.file_path, bio)
    await state.set(m.from_user.id, "img", bio.getvalue())
    await m.answer("Выбери таймфрейм", reply_markup=timeframe_keyboard())

async def tf(cb: CallbackQuery):
    tf = cb.data.split(":")[1]
    img = await state.get(cb.from_user.id, "img")
    res, err = analyze(img, tf)

    if err:
        await cb.message.answer(err)
    else:
        growth_pct = int(res['prob'] * 100)
        txt = (
            f"Таймфрейм: {tf} мин\n"
            f"Вероятность роста на 2–3 свечи: {growth_pct}%\n"
            f"Уверенность модели: {res['confidence']} ({res['confidence_score']})\n"
            f"Качество скрина: {res['quality']}\n"
        )
        if res["patterns"]:
            txt += "Обнаруженные паттерны: " + ", ".join(res["patterns"]) + "\n"
        txt += "\n⚠ Не является финансовой рекомендацией. Торгуйте на свой страх и риск."
        await cb.message.answer(txt)

    await state.clear(cb.from_user.id)
    await cb.answer()

def main():
    bot = Bot(TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.message.register(start, CommandStart())
    dp.message.register(image, F.content_type.in_({ContentType.PHOTO, ContentType.DOCUMENT}))
    dp.callback_query.register(tf, F.data.startswith("tf:"))
    dp.run_polling(bot)

if __name__ == "__main__":
    main()