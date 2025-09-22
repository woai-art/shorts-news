#!/usr/bin/env python3
"""
Тест для проверки работы Gemini API
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from google import genai
from google.genai import types
import json

def test_gemini_api():
    """Тестируем Gemini API"""
    
    # Получаем API ключ
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    if not api_key:
        print("❌ API ключ не найден в переменных окружения!")
        return
    
    print(f"✅ API ключ найден: {api_key[:4]}...{api_key[-4:]}")
    
    # Инициализируем клиент для Gemini Developer API (не Vertex AI)
    try:
        client = genai.Client(api_key=api_key)
        print("✅ Gemini SDK Client инициализирован успешно")
    except Exception as e:
        print(f"❌ Ошибка инициализации клиента: {e}")
        return
    
    # Тестируем доступные модели
    print("\n=== ДОСТУПНЫЕ МОДЕЛИ ===")
    try:
        models = client.models.list()
        for model in models:
            print(f"  - {model.name}")
    except Exception as e:
        print(f"❌ Ошибка получения списка моделей: {e}")
    
    # Тестируем конкретные модели
    test_models = [
        "gemini-2.0-flash-001",
        "gemini-1.5-flash",
        "gemini-1.5-pro"
    ]
    
    for model_name in test_models:
        print(f"\n=== ТЕСТ МОДЕЛИ: {model_name} ===")
        try:
            config = types.GenerateContentConfig(
                response_mime_type="application/json",
                temperature=0.5,
                max_output_tokens=100
            )
            
            prompt = "Generate a simple JSON with title and summary for this news: 'Test news about technology'"
            
            response = client.models.generate_content(
                model=model_name,
                contents=prompt,
                config=config
            )
            
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
    test_gemini_api()
