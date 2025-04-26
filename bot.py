from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import TELEGRAM_TOKEN
from nlp_module import SentimentAnalyzer
from myth_quiz import MythQuiz
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from db import init_db, save_feedback_to_db

bot = Bot(token=TELEGRAM_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

async def on_startup(_):
    init_db()
    print('Бот успешно запущен!')

class FeedbackStates(StatesGroup):
    waiting_for_feedback = State()

@dp.message_handler(commands=['start'])
async def welcome(message: types.Message):
    start_buttons = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton("▶️ Начать квиз", callback_data="quiz:start")]
    ])
    await message.answer("👋Привет! Это НейроСправочник, твой помощник в изучении машинного обучения и нейронных сетей!\n"
                         "Давай с тобой пройдем небольшой квиз по мифам о нейронных сетях. \n\n"
                         "Готов проверить насколько хорошо ты знаешь нейронки?😉", parse_mode="Markdown",
        reply_markup=start_buttons)

myth_quiz = MythQuiz("data/myth_data.csv")
user_sessions = {}
sentiment_analyzer = SentimentAnalyzer()

@dp.callback_query_handler(lambda c: c.data == "leave_feedback")
async def process_feedback_button(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id

    #флаг ожидания отзыва
    user_sessions[user_id] = {"awaiting_feedback": True}

    await FeedbackStates.waiting_for_feedback.set()
    await callback_query.message.answer("Напиши свой отзыв, пожалуйста! 💬")
    await callback_query.answer()

@dp.callback_query_handler(lambda c: c.data == "quiz:start")
async def quiz_start_handler(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_sessions[user_id] = {"score": 0, "index": 0}
    await send_next_question(user_id, callback)

async def send_next_question(user_id, message_or_callback):
    session = user_sessions[user_id]
    index = session["index"]

    if index >= myth_quiz.get_total():
        score = session["score"]
        del user_sessions[user_id]
        markup = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton("📝 Оставить отзыв", callback_data="leave_feedback")],
            [InlineKeyboardButton("🔄 Пройти заново", callback_data="quiz:restart")]
        ])
        await message_or_callback.message.answer(f"🎉 Квиз завершён!\nВаш результат: {score} баллов.\n\n"
                                                 f"Нажми на кнопку ниже и оставь, пожалуйста, отзыв в двух словах, понравился тебе квиз?😊", reply_markup=markup)
        user_sessions[user_id] = {"awaiting_feedback": True}
        return

    idx, statement, is_true, explanation = myth_quiz.get_question(index)
    keyboard = myth_quiz.get_keyboard(idx)

    if isinstance(message_or_callback, types.CallbackQuery):
        await message_or_callback.message.answer(f"❓ {statement}", reply_markup=keyboard)
    else:
        await message_or_callback.answer(f"❓ {statement}", reply_markup=keyboard)

@dp.callback_query_handler(lambda c: c.data == "quiz:restart")
async def restart_quiz(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    user_sessions[user_id] = {"score": 0, "index": 0}
    await callback.message.delete()
    await send_next_question(user_id, callback)

@dp.callback_query_handler(lambda c: c.data.startswith("quiz:"))

async def handle_quiz_answer(callback: types.CallbackQuery):
    user_id = callback.from_user.id
    _, question_index, user_answer = callback.data.split(":")
    correct_answer, explanation = myth_quiz.get_question(int(question_index))[2:]

    session = user_sessions[user_id]
    if user_answer == correct_answer:
        session["score"] += 1
        result = "✅ Верно!"
    else:
        result = "❌ Неверно."

    await callback.message.edit_text(f"{result}\n\nℹ️ {explanation}")
    session["index"] += 1
    await send_next_question(user_id, callback)

@dp.message_handler(state=FeedbackStates.waiting_for_feedback)
async def handle_feedback_input(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    text = message.text.strip()
    label, confidence, emoji = sentiment_analyzer.analyze(text)
    feedback_reply = sentiment_analyzer.generate_response(label)
    save_feedback_to_db(user_id, text, label, confidence)

    await message.reply(
        f"{feedback_reply}\n(определено как *{label}*, уверенность: {confidence:.2f})",
        parse_mode="Markdown"
    )

    await state.finish()

if __name__ == '__main__':
    executor.start_polling(dp, on_startup=on_startup)