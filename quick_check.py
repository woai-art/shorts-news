#!/usr/bin/env python3
"""
Быстрая проверка API ключа без импорта SDK
"""

import os
import sys

def main():
    print("⚡ БЫСТРАЯ ПРОВЕРКА API КЛЮЧА")
    print("=" * 40)

    # Проверяем переменные окружения
    google_key = os.getenv('GOOGLE_API_KEY', '').strip()
    gemini_key = os.getenv('GEMINI_API_KEY', '').strip()

    # Проверяем .env файл
    env_file = 'config/.env'
    env_keys = {}

    if os.path.exists(env_file):
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#') and '=' in line:
                        key, value = line.split('=', 1)
                        env_keys[key.strip()] = value.strip()
        except Exception as e:
            print(f"❌ Ошибка чтения .env: {e}")

    print("🔑 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    print(f"  GOOGLE_API_KEY: {'✅' if google_key else '❌'} ({len(google_key)} chars)"    print(f"  GEMINI_API_KEY: {'✅' if gemini_key else '❌'} ({len(gemini_key)} chars)"
    print("
📄 .ENV ФАЙЛ:"    for key in ['GOOGLE_API_KEY', 'GEMINI_API_KEY']:
        if key in env_keys:
            value = env_keys[key]
            status = '✅' if value else '❌'
            print(f"  {key}: {status} ({len(value)} chars)")
        else:
            print(f"  {key}: ❌ НЕ НАЙДЕН")

    # Выбираем рабочий ключ
    api_key = google_key or gemini_key

    print("
🎯 РЕЗУЛЬТАТ:"    if api_key:
        print("✅ API КЛЮЧ НАЙДЕН И ГОТОВ К ИСПОЛЬЗОВАНИЮ"        print(f"   Длина ключа: {len(api_key)} символов")
        print(f"   Начинается с: {api_key[:15]}..." if len(api_key) > 15 else f"   Ключ: {api_key}")
        print("
🚀 СИСТЕМА ГОТОВА К ЗАПУСКУ!"        print("💡 Используйте: python test_fixed_system.py")
        return True
    else:
        print("❌ API КЛЮЧ НЕ НАЙДЕН"        print("
📝 Добавьте в .env файл:"        print("   GOOGLE_API_KEY=ваш_ключ_здесь")
        print("   или")
        print("   GEMINI_API_KEY=ваш_ключ_здесь")
        print("
🔗 Получите ключ: https://makersuite.google.com/app/apikey"        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
