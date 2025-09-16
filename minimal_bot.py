мне #!/usr/bin/env python3
"""
Минимальный Telegram бот без сложных зависимостей
"""

import os
import sys
import time
import requests
import json

class MinimalTelegramBot:
    """Простой Telegram бот без asyncio"""

    def __init__(self, token, channel_id):
        self.token = token
        self.channel_id = channel_id
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.last_update_id = 0

    def send_message(self, text):
        """Отправка сообщения"""
        url = f"{self.base_url}/sendMessage"
        data = {
            "chat_id": self.channel_id,
            "text": text,
            "parse_mode": "HTML"
        }

        try:
            response = requests.post(url, json=data, timeout=10)
            return response.json()
        except Exception as e:
            print(f"❌ Ошибка отправки: {e}")
            return None

    def get_updates(self):
        """Получение обновлений"""
        url = f"{self.base_url}/getUpdates"
        params = {
            "offset": self.last_update_id + 1,
            "timeout": 30
        }

        try:
            response = requests.get(url, params=params, timeout=35)
            data = response.json()

            if data.get("ok") and data.get("result"):
                for update in data["result"]:
                    self.last_update_id = update["update_id"]
                    yield update
        except Exception as e:
            print(f"❌ Ошибка получения обновлений: {e}")

    def handle_message(self, message):
        """Обработка сообщения"""
        text = message.get("text", "").strip()
        chat_id = message.get("chat", {}).get("id")

        print(f"📨 Новое сообщение из {chat_id}: {text[:50]}...")

        # Проверяем, из нашего ли канала сообщение
        if str(chat_id) == str(self.channel_id):
            print("✅ Сообщение из канала мониторинга")

            # Ищем ссылки
            import re
            urls = re.findall(r'https?://[^\s]+', text)

            if urls:
                response = f"🔄 Получено {len(urls)} ссылок для обработки:\n"
                for i, url in enumerate(urls[:3], 1):
                    response += f"{i}. {url}\n"

                response += "\n⏳ Начинаю обработку..."
                self.send_message(response)
                print("✅ Ответ отправлен")
            else:
                print("⚠️ В сообщении нет ссылок")
        else:
            print(f"⚠️ Сообщение из другого канала: {chat_id}")

    def run(self):
        """Основной цикл бота"""
        print("🤖 Запуск минимального Telegram бота...")
        print(f"📡 Мониторинг канала: {self.channel_id}")
        print("Для остановки нажмите Ctrl+C")

        while True:
            try:
                for update in self.get_updates():
                    if "message" in update:
                        self.handle_message(update["message"])

                time.sleep(1)  # Небольшая пауза

            except KeyboardInterrupt:
                print("\n🛑 Бот остановлен пользователем")
                break
            except Exception as e:
                print(f"❌ Ошибка в цикле: {e}")
                time.sleep(5)  # Пауза перед повтором

def main():
    """Запуск бота"""
    # Настройки из конфига
    config_path = "config/config.yaml"

    try:
        import yaml
        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        token = os.getenv("TELEGRAM_BOT_TOKEN", "YOUR_TELEGRAM_BOT_TOKEN_HERE")
        channel_id = os.getenv("MONITOR_CHANNEL_ID", "YOUR_MONITOR_CHANNEL_ID_HERE")

        print(f"🔑 Токен: {token[:10]}...")
        print(f"📱 Канал ID: {channel_id}")

        bot = MinimalTelegramBot(token, channel_id)
        bot.run()

    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")

if __name__ == "__main__":
    main()
