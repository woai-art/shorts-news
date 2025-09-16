#!/usr/bin/env python3
"""
Простой тест Telegram Publisher
"""

import os
import sys
import asyncio
import logging

# Настройка логирования
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def test_basic_message():
    """Тест отправки простого сообщения"""
    try:
        from telegram import Bot

        # Токен бота
        bot_token = os.getenv("PUBLISH_BOT_TOKEN", "YOUR_PUBLISH_BOT_TOKEN_HERE")
        channel = "@tubepush_bot"
        channel_id = "-1002685642224"  # Используем числовой ID

        bot = Bot(token=bot_token)

        # Простое тестовое сообщение
        message = "🚀 Простой тест от Shorts News System"

        logger.info(f"Отправка сообщения в канал {channel} (ID: {channel_id})...")
        await bot.send_message(
            chat_id=channel_id,
            text=message
        )

        logger.info("✅ Сообщение отправлено успешно!")

    except Exception as e:
        logger.error(f"❌ Ошибка: {e}")
        logger.info("Возможные причины:")
        logger.info("1. Бот не добавлен как администратор канала")
        logger.info("2. Канал не существует")
        logger.info("3. Неправильный токен бота")
        logger.info("4. Проблемы с интернет-соединением")

async def test_get_chat_info():
    """Получение информации о канале"""
    try:
        from telegram import Bot

        bot_token = os.getenv("PUBLISH_BOT_TOKEN", "YOUR_PUBLISH_BOT_TOKEN_HERE")
        channel = "@tubepush_bot"
        channel_id = "-1002685642224"

        bot = Bot(token=bot_token)

        logger.info(f"Получение информации о канале {channel} (ID: {channel_id})...")
        chat = await bot.get_chat(chat_id=channel_id)

        logger.info("✅ Информация о канале получена:")
        logger.info(f"  ID: {chat.id}")
        logger.info(f"  Название: {chat.title}")
        logger.info(f"  Тип: {chat.type}")

        # Можно использовать chat.id вместо username
        logger.info(f"\n💡 Рекомендуется использовать ID канала: {chat.id}")
        logger.info("Обновите config.yaml:")
        logger.info(f'  channel_id: "{chat.id}"')

    except Exception as e:
        logger.error(f"❌ Ошибка получения информации о канале: {e}")
        logger.info("\n🔧 ИНСТРУКЦИИ ПО НАСТРОЙКЕ:")
        logger.info("1. Создайте канал в Telegram")
        logger.info("2. Добавьте бота @tubepush_bot как администратора")
        logger.info("3. Дайте боту права на публикацию сообщений")
        logger.info("4. Убедитесь, что имя канала правильное (@tubepush_bot)")
        logger.info("5. Или получите числовой ID канала и укажите его в config.yaml")

async def main():
    """Главная функция тестирования"""
    print("🧪 ТЕСТИРОВАНИЕ TELEGRAM PUBLISHER")
    print("=" * 50)

    choice = input("Выберите тест:\n1. Отправить простое сообщение\n2. Получить информацию о канале\n3. Оба теста\nВаш выбор: ")

    if choice in ['1', '3']:
        print("\n📤 Тест 1: Отправка сообщения...")
        await test_basic_message()
        print()

    if choice in ['2', '3']:
        print("\n📋 Тест 2: Получение информации о канале...")
        await test_get_chat_info()
        print()

    print("✅ Тестирование завершено!")

if __name__ == "__main__":
    asyncio.run(main())
