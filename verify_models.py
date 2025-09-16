#!/usr/bin/env python3
"""
Проверка того, что все модели используют gemini-2.0-flash
"""

import os
import re

def check_file_for_models(filename, expected_model):
    """Проверка файла на использование правильной модели"""
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()

        # Ищем все упоминания gemini моделей
        gemini_models = re.findall(r'gemini-[0-9]+\.[0-9]+-flash', content)
        models_mentions = re.findall(r'models/gemini-[0-9]+\.[0-9]+-flash', content)

        all_models = gemini_models + models_mentions

        # Проверяем, что все модели соответствуют ожидаемой
        correct_models = [m for m in all_models if expected_model in m or f'models/{expected_model}' in m]
        incorrect_models = [m for m in all_models if expected_model not in m and f'models/{expected_model}' not in m]

        return {
            'filename': filename,
            'total_models': len(all_models),
            'correct_models': correct_models,
            'incorrect_models': incorrect_models,
            'has_issues': len(incorrect_models) > 0
        }

    except Exception as e:
        return {
            'filename': filename,
            'error': str(e),
            'has_issues': True
        }

def main():
    """Главная функция проверки"""
    print("🔍 ПРОВЕРКА ИСПОЛЬЗОВАНИЯ МОДЕЛЕЙ GEMINI-2.0-FLASH")
    print("=" * 60)

    expected_model = "gemini-2.0-flash"

    # Список файлов для проверки
    files_to_check = [
        'config/config.yaml',
        'scripts/llm_processor.py',
        'scripts/llm_direct_provider.py',
        'test_gemini_api.py',
        'gemini_direct.py',
        'test_fixed_system.py'
    ]

    all_good = True
    results = []

    for filename in files_to_check:
        if os.path.exists(filename):
            result = check_file_for_models(filename, expected_model)
            results.append(result)

            if result.get('has_issues', False):
                all_good = False

                if 'error' in result:
                    print(f"❌ {filename}: Ошибка чтения - {result['error']}")
                else:
                    print(f"⚠️  {filename}:")
                    if result['incorrect_models']:
                        print(f"    ❌ Неправильные модели: {result['incorrect_models']}")
                    print(f"    📊 Всего моделей: {result['total_models']}")
            else:
                if result['total_models'] > 0:
                    print(f"✅ {filename}: Все модели корректны ({result['total_models']} найдено)")
                else:
                    print(f"ℹ️  {filename}: Модели не найдены")
        else:
            print(f"❌ {filename}: Файл не найден")
            all_good = False

    print("\\n" + "=" * 60)
    if all_good:
        print("🎉 ВСЕ ФАЙЛЫ ИСПОЛЬЗУЮТ ПРАВИЛЬНЫЕ МОДЕЛИ!")
        print(f"✅ Модель {expected_model} используется везде")
    else:
        print("⚠️  НАЙДЕНЫ ПРОБЛЕМЫ С МОДЕЛЯМИ!")
        print("🔧 Проверьте файлы выше и исправьте модели")

    print("\\n📋 РЕЗУЛЬТАТЫ ПОДРОБНО:")
    for result in results:
        if not result.get('has_issues', True):
            continue
        print(f"\\n🔍 {result['filename']}:")
        if 'error' in result:
            print(f"  ❌ Ошибка: {result['error']}")
        else:
            if result['correct_models']:
                print(f"  ✅ Правильные: {result['correct_models']}")
            if result['incorrect_models']:
                print(f"  ❌ Неправильные: {result['incorrect_models']}")
            print(f"  📊 Всего: {result['total_models']}")

if __name__ == "__main__":
    main()
