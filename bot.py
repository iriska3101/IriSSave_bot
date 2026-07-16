import os
import logging
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logger.error("BOT_TOKEN не задан!")
    exit(1)

# Flask для порта
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "IriSSave Bot is running!"

# Скачивание
def download_video(url):
    try:
        os.makedirs('downloads', exist_ok=True)
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            return ydl.prepare_filename(info)
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

# Команды
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь ссылку из Instagram, TikTok или YouTube.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("Отправь ссылку!")
        return
    await update.message.reply_text("⏳ Скачиваю...")
    filename = download_video(url)
    if filename and os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                await update.message.reply_document(f, filename=os.path.basename(filename))
            os.remove(filename)
        except Exception as e:
            await update.message.reply_text(f"Ошибка: {e}")
    else:
        await update.message.reply_text("Не удалось скачать.")

# Запуск
def main():
    # Создаём приложение
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Запускаем поллинг с удалением вебхука
    logger.info("Бот запускается...")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    # Запускаем Flask в отдельном потоке
    import threading
    def run_flask():
        port = int(os.environ.get("PORT", 10000))
        app_flask.run(host='0.0.0.0', port=port)
    threading.Thread(target=run_flask, daemon=True).start()
    # Запускаем бота в главном потоке
    main()