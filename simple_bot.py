#!/usr/bin/env python3
"""
Простой запуск Telegram бота без event loop проблем
"""

import os
import sys
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

def main():
    """Простой запуск бота"""
    logger.info("🤖 Запуск простого Telegram бота...")

    # Импортируем только необходимое
    sys.path.append('scripts')

    from telegram_bot import NewsTelegramBot
    import asyncio

    async def run_bot():
        try:
            bot = NewsTelegramBot('config/config.yaml')
            await bot.run_bot()
        except Exception as e:
            logger.error(f"❌ Ошибка бота: {e}")

    # Запускаем бота
    try:
        asyncio.run(run_bot())
    except KeyboardInterrupt:
        logger.info("🛑 Бот остановлен пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")

if __name__ == "__main__":
    main()
