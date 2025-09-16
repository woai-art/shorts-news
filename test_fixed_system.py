#!/usr/bin/env python3
"""
Тест исправленной системы без браузера
"""

import os
import sys
sys.path.append('scripts')

def test_fixed_system():
    """Тест исправленной системы"""
    print("🧪 ТЕСТИРОВАНИЕ ИСПРАВЛЕННОЙ СИСТЕМЫ")
    print("=" * 60)

    # Проверяем API ключ
    api_key = os.getenv('GOOGLE_API_KEY') or os.getenv('GEMINI_API_KEY')

    if not api_key:
        print("❌ API ключ не найден!")
        print("💡 Добавьте GOOGLE_API_KEY или GEMINI_API_KEY в переменные окружения")
        return False

    print(f"✅ API ключ найден (длина: {len(api_key)} символов)")

    # Тестируем прямой API провайдер
    try:
        print("\\n🔧 Тестирование прямого API провайдера...")
        from llm_direct_provider import GeminiDirectProvider

        provider = GeminiDirectProvider(api_key)
        test_text = "This is a test news about technology and AI."
        result = provider.summarize_for_video(test_text)

        if result and len(result) > 10:
            print(f"✅ Прямой API работает: {result[:50]}...")
        else:
            print("❌ Прямой API вернул пустой результат")
            return False

    except Exception as e:
        print(f"❌ Ошибка с прямым API провайдером: {e}")
        return False

    # Тестируем основной LLM процессор
    try:
        print("\\n🔧 Тестирование основного LLM процессора...")
        from llm_processor import GeminiProvider

        config = {
            'temperature': 0.7,
            'max_tokens': 2000,
            'enable_fact_checking': False  # Отключаем пока
        }

        processor = GeminiProvider(api_key, config=config)
        result = processor.summarize_for_video(test_text)

        if result and len(result) > 10:
            print(f"✅ Основной процессор работает: {result[:50]}...")
        else:
            print("❌ Основной процессор вернул пустой результат")
            return False

    except Exception as e:
        print(f"❌ Ошибка с основным процессором: {e}")
        return False

    # Тестируем генерацию SEO
    try:
        print("\\n🔧 Тестирование генерации SEO...")
        seo_result = processor.generate_seo_package(test_text)

        if seo_result and 'title' in seo_result:
            print(f"✅ SEO генерация работает: {seo_result['title'][:50]}...")
        else:
            print("❌ SEO генерация не работает")
            return False

    except Exception as e:
        print(f"❌ Ошибка с SEO генерацией: {e}")
        return False

    return True

def main():
    """Главная функция"""
    print("🚀 ЗАПУСК ТЕСТА ИСПРАВЛЕННОЙ СИСТЕМЫ")
    print("=" * 60)

    success = test_fixed_system()

    print("\\n" + "=" * 60)
    if success:
        print("🎉 ВСЕ ТЕСТЫ ПРОШЛИ УСПЕШНО!")
        print("✅ API ключ работает")
        print("✅ Прямой API провайдер работает")
        print("✅ Основной процессор работает")
        print("✅ SEO генерация работает")
        print("\\n🚀 Система готова к использованию!")
        print("💡 Теперь можно запускать основную систему без браузера")
    else:
        print("💥 НЕКОТОРЫЕ ТЕСТЫ НЕ ПРОШЛИ!")
        print("🔧 Проверьте:")
        print("1. Правильность API ключа")
        print("2. Доступность интернета")
        print("3. Версию Python и пакетов")

    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
