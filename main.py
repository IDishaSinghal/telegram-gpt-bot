import os
import wikipediaapi
import requests
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes
from dotenv import load_dotenv

# Configure logging
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)

# Load API keys from .env file
load_dotenv()
TELEGRAM_API_KEY = os.getenv("TELEGRAM_API_KEY")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

if not TELEGRAM_API_KEY or not NEWS_API_KEY or not WEATHER_API_KEY:
    raise ValueError("One or more API keys are missing. Please check your .env file.")

# Start command handler with inline buttons
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Get News", callback_data="news")],
        [InlineKeyboardButton("Get Weather", callback_data="weather")],
        [InlineKeyboardButton("Search Wikipedia", callback_data="wiki")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Hello! I'm your smart assistant bot. Choose an option below:", reply_markup=reply_markup)

# Function to fetch news
async def get_news(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = f"https://newsapi.org/v2/top-headlines?country=us&apiKey={NEWS_API_KEY}"
    try:
        response = requests.get(url)
        data = response.json()
        if data["status"] == "ok":
            articles = data["articles"][:5]
            news = "\n\n".join([f"📰 {article['title']} - {article['source']['name']}" for article in articles])
            if update.callback_query:
                await update.callback_query.message.reply_text(f"Here are the top news headlines:\n\n{news}")
            elif update.message:
                await update.message.reply_text(f"Here are the top news headlines:\n\n{news}")
        else:
            error_message = "Sorry, I couldn't fetch the news at the moment."
            if update.callback_query:
                await update.callback_query.message.reply_text(error_message)
            elif update.message:
                await update.message.reply_text(error_message)
    except Exception as e:
        logger.error(f"Error fetching news: {e}")
        error_message = "An error occurred while fetching the news."
        if update.callback_query:
            await update.callback_query.message.reply_text(error_message)
        elif update.message:
            await update.message.reply_text(error_message)

# Function to fetch weather
async def get_weather(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    city = user_message.split(" ", 1)[1] if len(user_message.split()) > 1 else "Delhi"
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}&units=metric"
    try:
        response = requests.get(url)
        data = response.json()
        if data["cod"] == 200:
            city_name = data["name"]
            temp = data["main"]["temp"]
            weather_desc = data["weather"][0]["description"]
            await update.message.reply_text(f"🌤 Weather in {city_name}:\nTemperature: {temp}°C\nCondition: {weather_desc.capitalize()}")
        else:
            await update.message.reply_text("Sorry, I couldn't find the weather for that location.")
    except Exception as e:
        logger.error(f"Error fetching weather: {e}")
        await update.message.reply_text("An error occurred while fetching the weather.")

# Function to fetch Wikipedia summary
async def get_wikipedia_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_message = update.message.text
    topic = user_message.split(" ", 1)[1] if len(user_message.split()) > 1 else None
    if not topic:
        await update.message.reply_text("Please provide a topic to search. Example: /wiki Python")
        return
    wiki_wiki = wikipediaapi.Wikipedia(language='en', user_agent="SmartAssistantBot/1.0 (https://github.com/your-repo; contact@example.com)")
    page = wiki_wiki.page(topic)
    if page.exists():
        summary = page.summary[:1000]
        await update.message.reply_text(f"📚 Wikipedia summary for '{topic}':\n\n{summary}")
    else:
        await update.message.reply_text(f"Sorry, I couldn't find any information on '{topic}' in Wikipedia.")

# Callback query handler for inline buttons
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    if query.data == "news":
        await get_news(update, context)
    elif query.data == "weather":
        await query.edit_message_text("Please type your city name after /weather (e.g., /weather London).")
    elif query.data == "wiki":
        await query.edit_message_text("Please type your topic after /wiki (e.g., /wiki Python).")

# Main function to run the bot
def main():
    app = ApplicationBuilder().token(TELEGRAM_API_KEY).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("news", get_news))
    app.add_handler(CommandHandler("weather", get_weather))
    app.add_handler(CommandHandler("wiki", get_wikipedia_summary))
    app.add_handler(CallbackQueryHandler(button_handler))
    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
