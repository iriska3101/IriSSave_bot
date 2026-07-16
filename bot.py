def main():
    # Запускаем Flask в фоновом потоке
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logging.info("Flask запущен в фоновом потоке")

    # Запускаем Telegram-бота в ОСНОВНОМ потоке
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logging.info("Бот запускается и сбрасывает старые вебхуки...")
    # ЭТА СТРОЧКА РЕШАЕТ ПРОБЛЕМУ: drop_pending_updates=True удаляет вебхук и старые сообщения
    app.run_polling(drop_pending_updates=True)