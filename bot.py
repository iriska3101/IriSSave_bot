import os
import logging
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
            # Отправляем файл
            with open(filename, 'rb') as f:
                await update.message.reply_document(document=f, filename=os.path.basename(filename))
            os.remove(filename)  # удаляем после отправки
        except Exception as e:
            await update.message.reply_text(f"Не удалось отправить файл: {e}")
            logger.error(f"Ошибка отправки: {e}")
    else:
        await update.message.reply_text("Не удалось скачать видео. Проверь ссылку или попробуй другую.")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    logger.info("Бот запущен!")
    app.run_polling()

if __name__ == "__main__":
    main()
