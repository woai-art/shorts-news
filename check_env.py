#!/usr/bin/env python3
"""
Проверка переменных окружения без импорта SDK
"""

import os
import sys

def check_environment():
    """Проверка переменных окружения"""
    print("🔍 ПРОВЕРКА СРЕДЫ ВЫПОЛНЕНИЯ")
    print("=" * 50)

    # Проверяем переменные окружения
    google_key = os.getenv('GOOGLE_API_KEY')
    gemini_key = os.getenv('GEMINI_API_KEY')

    print("📋 ПЕРЕМЕННЫЕ ОКРУЖЕНИЯ:")
    print(f"  GOOGLE_API_KEY: {'✅ УСТАНОВЛЕНА' if google_key else '❌ НЕТ'}")
    print(f"  GEMINI_API_KEY: {'✅ УСТАНОВЛЕНА' if gemini_key else '❌ НЕТ'}")

    if google_key:
        print(f"  Длина GOOGLE_API_KEY: {len(google_key)} символов")
        print(f"  Начинается с: {google_key[:20]}..." if len(google_key) > 20 else f"  Полностью: {google_key}")

    if gemini_key:
        print(f"  Длина GEMINI_API_KEY: {len(gemini_key)} символов")
        print(f"  Начинается с: {gemini_key[:20]}..." if len(gemini_key) > 20 else f"  Полностью: {gemini_key}")

    # Проверяем .env файл
    env_file = 'config/.env'
    if os.path.exists(env_file):
        print(f"\n📄 АНАЛИЗ .env ФАЙЛА: {env_file}")
        try:
            with open(env_file, 'r', encoding='utf-8') as f:
                content = f.read()

            lines = content.split('\n')
            found_keys = {}

            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()

                    if key in ['GOOGLE_API_KEY', 'GEMINI_API_KEY']:
                        found_keys[key] = {
                            'line': i,
                            'length': len(value),
                            'preview': value[:20] + '...' if len(value) > 20 else value,
                            'empty': len(value) == 0
                        }

            if found_keys:
                for key, info in found_keys.items():
                    status = '❌ ПУСТОЙ' if info['empty'] else f"✅ {info['length']} символов"
                    print(f"  Строка {info['line']}: {key} = {status}")
                    print(f"    Значение: {info['preview']}")
            else:
                print("  ❌ Ключи API не найдены в .env файле")

        except Exception as e:
            print(f"  ❌ Ошибка чтения .env файла: {e}")
    else:
        print(f"\n❌ Файл .env не найден: {env_file}")

    # Проверяем версию Python
    print(f"\n🐍 ВЕРСИЯ PYTHON: {sys.version}")

    # Проверяем наличие SDK файлов
    print("
🔧 ПРОВЕРКА SDK:"    try:
        import google
        print("  ✅ google package найден")
    except ImportError:
        print("  ❌ google package НЕ найден")

    # Проверяем установленные пакеты
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'list'], capture_output=True, text=True, timeout=10)
        packages = result.stdout.lower()

        sdk_found = {
            'google-genai': 'google-genai' in packages,
            'google-generativeai': 'google-generativeai' in packages,
            'google-auth': 'google-auth' in packages
        }

        print("
📦 УСТАНОВЛЕННЫЕ ПАКЕТЫ:"        for package, found in sdk_found.items():
            print(f"  {package}: {'✅' if found else '❌'}")

    except Exception as e:
        print(f"  ❌ Ошибка проверки пакетов: {e}")

    return google_key or gemini_key

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ПРОВЕРКИ СИСТЕМЫ")
    print("=" * 50)

    has_api_key = check_environment()

    print("\n" + "=" * 50)
    if has_api_key:
        print("✅ API КЛЮЧ НАЙДЕН")
        print("💡 Попробуйте запустить: python test_gemini_api.py")
        print("🔧 Если браузер открывается - проблема в OAuth настройках")
    else:
        print("❌ API КЛЮЧ НЕ НАЙДЕН")
        print("📝 Добавьте в .env файл:")
        print("   GOOGLE_API_KEY=ваш_ключ_здесь")
        print("   или")
        print("   GEMINI_API_KEY=ваш_ключ_здесь")
        print("🔗 Получите ключ: https://makersuite.google.com/app/apikey")

    print("\n🛠️  РЕШЕНИЯ ПРОБЛЕМЫ:")
    print("1. Проверьте что API ключ правильный")
    print("2. Убедитесь что ключ активен в Google Cloud Console")
    print("3. Попробуйте перезапустить систему")
    print("4. Проверьте версию google-genai пакета")

if __name__ == "__main__":
    main()
