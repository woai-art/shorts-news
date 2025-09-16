#!/usr/bin/env python3
"""
Прямой вызов Gemini API через HTTP без SDK
Это обходной путь для проблемы с OAuth
"""

import os
import json
import requests
from typing import Optional, Dict, Any

class GeminiDirect:
    """Прямой клиент для Gemini API"""

    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://generativelanguage.googleapis.com/v1beta/models"
        self.session = requests.Session()
        self.session.headers.update({
            'Content-Type': 'application/json'
        })

    def generate_content(self, prompt: str, model: str = "gemini-2.0-flash") -> Optional[str]:
        """Генерация контента через прямой API вызов"""
        url = f"{self.base_url}/{model}:generateContent"
        params = {'key': self.api_key}

        data = {
            "contents": [{
                "parts": [{
                    "text": prompt
                }]
            }],
            "generationConfig": {
                "temperature": 0.7,
                "maxOutputTokens": 1000,
                "topP": 1,
                "topK": 1
            }
        }

        try:
            print(f"📡 Отправка запроса к {model}...")
            response = self.session.post(url, params=params, json=data, timeout=30)

            if response.status_code == 200:
                result = response.json()
                if 'candidates' in result and len(result['candidates']) > 0:
                    content = result['candidates'][0]['content']
                    if 'parts' in content and len(content['parts']) > 0:
                        return content['parts'][0]['text']

            print(f"❌ Ошибка API: {response.status_code}")
            print(f"Ответ: {response.text[:500]}...")
            return None

        except Exception as e:
            print(f"❌ Ошибка запроса: {e}")
            return None

def test_direct_api():
    """Тест прямого API вызова"""
    print("🧪 ТЕСТ ПРЯМОГО ВЫЗОВА GEMINI API")
    print("=" * 50)

    # Получаем API ключ
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("❌ API ключ не найден!")
        print("Установите GOOGLE_API_KEY или GEMINI_API_KEY в переменных окружения")
        return False

    print(f"✅ API ключ найден (длина: {len(api_key)} символов)")

    # Создаем клиент
    client = GeminiDirect(api_key)

    # Тестируем простой запрос
    test_prompt = "Say 'Hello from direct API!' in exactly 5 words."
    print(f"📤 Тестовый запрос: {test_prompt}")

    result = client.generate_content(test_prompt)

    if result:
        print(f"✅ Ответ получен: {result.strip()}")
        return True
    else:
        print("❌ Ответ не получен")
        return False

def main():
    """Главная функция"""
    success = test_direct_api()

    if success:
        print("\n🎉 ПРЯМОЙ API ВЫЗОВ РАБОТАЕТ!")
        print("✅ API ключ правильный")
        print("✅ Интернет соединение работает")
        print("✅ Gemini API доступен")
        print("\n💡 Теперь можно использовать прямой API вместо SDK")
    else:
        print("\n💥 ПРЯМОЙ API ВЫЗОВ НЕ РАБОТАЕТ!")
        print("🔧 Возможные причины:")
        print("1. Неправильный API ключ")
        print("2. Ключ заблокирован или истек")
        print("3. Проблемы с интернетом")
        print("4. API квота исчерпана")
        print("\n🔗 Проверьте ключ: https://makersuite.google.com/app/apikey")

    return success

if __name__ == "__main__":
    main()
