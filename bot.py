import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Настройки
logging.basicConfig(level=logging.INFO)
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

# Flask для порта
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "IriSSave Bot is running!"

# Функция скачивания
def download_video(url):
    try:
        ydl_opts = {'outtmpl': 'downloads/%(title)s.%(ext)s', 'quiet': True}
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        logging.error(f"Ошибка: {e}")
        return None

# Команды бота
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь ссылку из Instagram, TikTok или YouTube.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not url.startswith("http"):
        await update.message.reply_text("Отправь ссылку!")
        return
    await update.message.reply_text("⏳ Скачиваю...")
    filename = download_video(url)
    if filename and os.path.exists(filename):
        with open(filename, 'rb') as f:
            await update.message.reply_document(f, filename=os.path.basename(filename))
        os.remove(filename)
    else:
        await update.message.reply_text("Не удалось скачать.")

def run_flask():
    """Запускает Flask-сервер в фоновом потоке"""
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port)

def main():
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask запущен в фоновом потоке")

    # Запускаем Telegram-бота в ОСНОВНОМ потоке
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запускается...")
    app.run_polling()  # <-- Теперь это в главном потоке!

if __name__ == "__main__":
    main()