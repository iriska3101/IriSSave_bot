import os
import logging
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Токен из переменной окружения
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    raise ValueError("BOT_TOKEN не задан! Добавьте переменную на Render.")

# Flask-приложение для порта (чтобы Render не ругался)
app_flask = Flask(__name__)

@app_flask.route('/')
def home():
    return "🤖 IriSSave Bot is running! Find me on Telegram."

# Функция скачивания
def download_video(url):
    try:
        # Создаём папку для загрузок, если её нет
        os.makedirs('downloads', exist_ok=True)
        ydl_opts = {
            'outtmpl': 'downloads/%(title)s.%(ext)s',
            'quiet': True,
            'no_warnings': True,
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        logger.error(f"Ошибка скачивания: {e}")
        return None

# Команда /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! 👋\n\n"
        "Отправь мне ссылку на видео из Instagram, TikTok, YouTube, и я скачаю его для тебя.\n"
        "Поддерживаются также фото и музыка."
    )

# Обработка любого текста (ссылки)
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()
    if not url.startswith(("http://", "https://")):
        await update.message.reply_text("Пожалуйста, отправь ссылку, начинающуюся с http:// или https://")
        return

    await update.message.reply_text("⏳ Скачиваю... Подожди немного.")
    filename = download_video(url)

    if filename and os.path.exists(filename):
        try:
            with open(filename, 'rb') as f:
                await update.message.reply_document(
                    document=f,
                    filename=os.path.basename(filename),
                    caption="✅ Готово!"
                )
            os.remove(filename)  # удаляем после отправки
        except Exception as e:
            await update.message.reply_text(f"❌ Не удалось отправить файл: {e}")
            logger.error(f"Ошибка отправки: {e}")
    else:
        await update.message.reply_text(
            "❌ Не удалось скачать видео.\n"
            "Проверь ссылку (она должна быть публичной) или попробуй другую."
        )

# Функция для запуска Flask в фоновом потоке
def run_flask():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host='0.0.0.0', port=port, debug=False)

# Основная функция
def main():
    # Запускаем Flask в фоне
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info("Flask-сервер запущен в фоновом потоке")

    # Создаём приложение Telegram-бота
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Бот запускается...")
    # drop_pending_updates=True сбрасывает старые вебхуки и игнорирует накопившиеся сообщения
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()