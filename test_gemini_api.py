#!/usr/bin/env python3
"""
Тест Gemini API для проверки корректности API ключа
"""

import os
import sys
sys.path.append('scripts')

def test_gemini_api():
    """Тест подключения к Gemini API"""
    print("🧪 ТЕСТИРОВАНИЕ GEMINI API")
    print("=" * 50)

    # Проверяем переменные окружения
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("❌ API ключ не найден!")
        print("Установите GOOGLE_API_KEY или GEMINI_API_KEY")
        return False

    print(f"✅ API ключ найден (длина: {len(api_key)} символов)")

    # Проверяем SDK
    try:
        from google import genai
        print("✅ Google AI SDK импортирован успешно")

        # Создаем клиент с явным указанием API ключа
        client = genai.Client(api_key=api_key)
        print("✅ Клиент Gemini создан успешно")

        # Пробуем простой запрос
        print("\\n📤 Тестирование простого запроса...")

        response = client.models.generate_content(
            model='models/gemini-2.0-flash',
            contents='Say "Hello, World!" in one word.'
        )

        if response and hasattr(response, 'text'):
            result = response.text.strip()
            print(f"✅ Ответ получен: {result}")
            return True
        else:
            print("❌ Пустой ответ от API")
            return False

    except Exception as e:
        print(f"❌ Ошибка при работе с Gemini API: {e}")
        print("\\n🔧 Возможные причины:")
        print("1. Неправильный API ключ")
        print("2. API ключ заблокирован")
        print("3. Проблемы с интернетом")
        print("4. SDK версия несовместима")
        return False

def main():
    """Главная функция"""
    success = test_gemini_api()

    if success:
        print("\\n🎉 Gemini API работает корректно!")
        print("Можно запускать основную систему.")
    else:
        print("\\n💥 Gemini API не работает!")
        print("Проверьте API ключ и повторите тест.")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
