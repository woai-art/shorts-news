#!/usr/bin/env python3
"""
Правильный тест для Gemini API с google-generativeai
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import google.generativeai as genai
import json

def test_gemini_correct():
    """Тестируем Gemini API с правильной библиотекой"""
    
    # Получаем API ключ
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ API ключ не найден в переменных окружения!")
        return
    
    print(f"✅ API ключ найден: {api_key[:4]}...{api_key[-4:]}")
    
    # Инициализируем клиент
    try:
        genai.configure(api_key=api_key)
        print("✅ Gemini API настроен успешно")
    except Exception as e:
        print(f"❌ Ошибка настройки API: {e}")
        return
    
    # Тестируем конкретные модели
    test_models = [
        "gemini-2.0-flash-001",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    for model_name in test_models:
        print(f"\n=== ТЕСТ МОДЕЛИ: {model_name} ===")
        try:
            model = genai.GenerativeModel(model_name)
            
            prompt = """Generate a JSON response with title and summary for this news:
            "Breaking: New technology breakthrough announced today"
            
            Return only valid JSON in this format:
            {
                "title": "short title",
                "summary": "detailed summary"
            }"""
            
            response = model.generate_content(prompt)
            print(f"✅ {model_name} работает!")
            print(f"Ответ: {response.text[:200]}...")
            
            # Пробуем парсить JSON
            try:
                import re
                match = re.search(r'\{.*\}', response.text, re.DOTALL)
                if match:
                    json_text = match.group(0)
                    parsed = json.loads(json_text)
                    print(f"✅ JSON успешно распарсен: {parsed}")
                else:
                    print("⚠️ JSON не найден в ответе")
            except Exception as e:
                print(f"⚠️ Ошибка парсинга JSON: {e}")
                
        except Exception as e:
            print(f"❌ {model_name} не работает: {e}")

if __name__ == "__main__":
    test_gemini_correct()
