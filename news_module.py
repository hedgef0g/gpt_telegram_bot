import os
import requests
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CallbackQueryHandler
from bs4 import BeautifulSoup

# Функция для получения новостей по категории
def fetch_news(category_query):
    headers = {
        "User-Agent": "Mozilla/5.0"
    }
    search_url = f"https://www.google.com/search?q={category_query}&tbm=nws"
    response = requests.get(search_url, headers=headers)
    soup = BeautifulSoup(response.text, "html.parser")
    results = soup.find_all("div", class_="BVG0Nb")
    news_items = []
    for result in results[:2]:  # Получаем первые 2 новости
        title = result.find("div", class_="BNeawe vvjwJb AP7Wnd")
        link = result.find("a")["href"]
        if title and link:
            news_items.append(f"- {title.text} ({link})")
    return news_items

# Функция для получения подборки новостей
def get_news_summary(period: str):
    categories = {
        "Мировая политика": "world politics",
        "Российско-украинская война": "Russia Ukraine war",
        "Технологии": "technology news",
        "Новости искусственного интеллекта": "artificial intelligence news",
        "Новости финансов": "finance news"
    }
    summary = f"📰 *Подборка новостей за {period}:*\n\n"
    for category, query in categories.items():
        news = fetch_news(query)
        summary += f"*{category}:*\n" + "\n".join(news) + "\n\n"
    return summary

async def show_news_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("За сутки", callback_data="news:1d")],
        [InlineKeyboardButton("За неделю", callback_data="news:7d")],
        [InlineKeyboardButton("Выбери период", callback_data="news:custom")]
    ]
    await update.message.reply_text("Выберите период новостей:", reply_markup=InlineKeyboardMarkup(keyboard))

async def handle_news_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data.startswith("news:"):
        period_code = data.split(":")[1]
        if period_code == "1d":
            news_text = get_news_summary("последние 24 часа")
            await query.edit_message_text(text=news_text, parse_mode="Markdown")
        elif period_code == "7d":
            news_text = get_news_summary("последнюю неделю")
            await query.edit_message_text(text=news_text, parse_mode="Markdown")
        elif period_code == "custom":
            await query.edit_message_text("Функция выбора периода будет добавлена позже.")

# Возвращает хендлеры для подключения в main.py
def get_news_handlers():
    return [
        CallbackQueryHandler(handle_news_callback, pattern=r"^news:")
    ]
