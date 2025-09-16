#!/usr/bin/env python3
"""
Запуск Telegram бота с полной изоляцией процесса
"""

import multiprocessing
import os
import sys

def run_bot_process():
    """Функция для запуска бота в отдельном процессе"""
    # Настройка окружения
    os.chdir(os.path.dirname(__file__))
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))

    # Импорт и запуск
    from telegram_bot import NewsTelegramBot
    import asyncio

    async def main():
        try:
            bot = NewsTelegramBot('config/config.yaml')
            await bot.run_bot()
        except Exception as e:
            print(f"❌ Ошибка в процессе бота: {e}")

    # Запуск event loop
    asyncio.run(main())

def main():
    """Главная функция"""
    print("🚀 Запуск Telegram бота в изолированном процессе...")

    # Устанавливаем метод запуска для Windows
    if hasattr(multiprocessing, 'set_start_method'):
        try:
            multiprocessing.set_start_method('spawn', force=True)
        except RuntimeError:
            pass  # Метод уже установлен

    # Создаем и запускаем процесс
    bot_process = multiprocessing.Process(target=run_bot_process, name='TelegramBot')
    bot_process.daemon = False

    try:
        bot_process.start()
        print(f"✅ Бот запущен в процессе PID: {bot_process.pid}")
        print("Для остановки нажмите Ctrl+C")

        # Ждем завершения процесса
        bot_process.join()

    except KeyboardInterrupt:
        print("\n🛑 Остановка бота...")
        if bot_process.is_alive():
            bot_process.terminate()
            bot_process.join(timeout=5)
            if bot_process.is_alive():
                bot_process.kill()
        print("✅ Бот остановлен")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
        if bot_process.is_alive():
            bot_process.terminate()

if __name__ == "__main__":
    # Необходимая защита для Windows
    multiprocessing.freeze_support()
    main()
