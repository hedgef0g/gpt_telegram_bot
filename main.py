import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    CallbackQueryHandler, ContextTypes, filters
)
from openai import OpenAI

# Загрузка переменных окружения из Replit Secrets
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OWNER_ID = int(os.getenv("OWNER_ID"))

# Подключение к OpenAI
openai = OpenAI(api_key=OPENAI_API_KEY)

# Авторизованные пользователи
authorized_users = {OWNER_ID}
user_model = {}

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("Нет доступа.")
        return
    await update.message.reply_text("Привет! Я готов к работе. Введи вопрос или выбери модель.")

# Команда /adduser (только для владельца)
async def add_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("У вас нет прав.")
        return
    if not context.args:
        await update.message.reply_text("Пример: /adduser 123456789")
        return
    try:
        new_user = int(context.args[0])
        authorized_users.add(new_user)
        await update.message.reply_text(f"Пользователь {new_user} добавлен.")
    except ValueError:
        await update.message.reply_text("Неверный формат ID.")

# Выбор модели
async def choose_model(update: Update, context: ContextTypes.DEFAULT_TYPE):
    buttons = [
        [InlineKeyboardButton("GPT-3.5 (экономично)", callback_data="model:gpt-3.5-turbo")],
        [InlineKeyboardButton("GPT-4 (дорого)", callback_data="model:gpt-4")]
    ]
    await update.message.reply_text("Выбери модель:", reply_markup=InlineKeyboardMarkup(buttons))

# Обработка кнопок
async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data.startswith("model:"):
        model = query.data.split(":")[1]
        user_model[query.from_user.id] = model
        await query.edit_message_text(f"Модель выбрана: {model}")

# Основная логика: обработка текста
async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in authorized_users:
        await update.message.reply_text("Нет доступа.")
        return

    user_input = update.message.text.strip()

    if len(user_input) > 1500:
        await update.message.reply_text("Слишком длинный запрос. Пожалуйста, сократи текст.")
        return

    model = user_model.get(user_id, "gpt-3.5-turbo")

    try:
        completion = openai.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "Отвечай кратко."},
                {"role": "user", "content": user_input}
            ],
            max_tokens=300,
            temperature=0.7
        )

        reply = completion.choices[0].message.content.strip()
        await update.message.reply_text(reply)

    except Exception as e:
        print(f"Ошибка OpenAI: {e}")
        await update.message.reply_text("Произошла ошибка при обращении к OpenAI.")

# Запуск приложения
def main():
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("adduser", add_user))
    app.add_handler(CommandHandler("model", choose_model))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    print("Бот запущен.")
    app.run_polling()

if __name__ == "__main__":
    main()
