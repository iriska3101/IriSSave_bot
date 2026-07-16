import os
import logging
import threading
from flask import Flask, render_template_string
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен бота берём из переменной окружения (её добавим на Render)
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не задан!")

# Создаём Flask-приложение для веб-сервера (чтобы Render не ругался на отсутствие порта)
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>IriSSave Bot</title></head>
    <body>
        <h1>🤖 Бот работает!</h1>
        <p>Найди меня в Telegram и отправь ссылку на видео.</p>
    </body>
    </html>
    ''')

# Функция скачивания
def download_video(url):
    ydl_opts = {
        'outtmpl': 'downloads/%(title)s.%(ext)s',
        'quiet': True,
        'no_warnings': True,
    }
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет! Отправь мне ссылку на видео из Instagram, TikTok, YouTube, и я скачаю его для тебя.")

# Обработка ссылок
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text
    if not (url.startswith("http")):
        await update.message.reply_text("Пожалуйста, отправь ссылку, начинающуюся с http:// или https://")
        return

    await update.message.reply_text("⏳ Скачиваю... Подожди немного.")
    filename = download_video(url)

    if filename and os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                await update.message.reply_document(document=f, filename=os.path.basename(filename))
            os.remove(filename)
        except Exception as e:
            await update.message.reply_text(f"Не удалось отправить файл: {e}")
            logger.error(f"Ошибка отправки: {e}")
    else:
        await update.message.reply_text("Не удалось скачать видео. Проверь ссылку или попробуй другую.")

def run_bot():
    """Запускает Telegram-бота в отдельном потоке"""
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен и работает...")
    app.run_polling()

def main():
    # Запускаем бота в фоновом потоке
    bot_thread = threading.Thread(target=run_bot)
    bot_thread.daemon = True
    bot_thread.start()

    # Запускаем веб-сервер Flask (он займёт порт, чтобы Render не ругался)
    port = int(os.environ.get("PORT", 10000))
    logger.info(f"Веб-сервер запущен на порту {port}")
    app_flask.run(host='0.0.0.0', port=port)

if __name__ == "__main__":
    main()