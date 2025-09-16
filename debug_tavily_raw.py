#!/usr/bin/env python3
"""
Отладка сырого ответа Tavily API
"""

import sys
sys.path.append('scripts')
from web_parser import TavilyParser
import logging

logging.basicConfig(level=logging.INFO)

def debug_tavily_raw():
    """Отладка сырого ответа Tavily"""
    
    print("🔍 Отладка сырого ответа Tavily API:")
    print("=" * 80)
    
    # Инициализируем Tavily парсер
    tavily_parser = TavilyParser()
    
    # URL статьи
    test_url = "https://www.politico.com/news/2025/09/16/cruz-says-first-amendment-absolutely-protects-hate-speech-in-wake-of-charlie-kirk-killing-00566448"
    
    print(f"URL: {test_url}")
    print("=" * 80)
    
    # Делаем прямой поиск через Tavily
    try:
        results = tavily_parser._search_tavily(test_url)
        
        print(f"📊 Количество результатов: {len(results)}")
        
        for i, result in enumerate(results):
            print(f"\n📄 Результат {i+1}:")
            print(f"  Type: {type(result)}")
            
            if isinstance(result, dict):
                print(f"  Title: {result.get('title', 'N/A')}")
                print(f"  URL: {result.get('url', 'N/A')}")
                print(f"  Content length: {len(result.get('content', ''))}")
                print(f"  HTML length: {len(result.get('html', ''))}")
                
                # Показываем ключи
                print(f"  Keys: {list(result.keys())}")
                
                # Ищем Brightcove в content
                content = result.get('content', '')
                if 'brightcove' in content.lower():
                    print("  ✅ Найден 'brightcove' в content!")
                else:
                    print("  ❌ 'brightcove' не найден в content")
                    
                # Ищем Brightcove в HTML
                html = result.get('html', '')
                if 'brightcove' in html.lower():
                    print("  ✅ Найден 'brightcove' в HTML!")
                else:
                    print("  ❌ 'brightcove' не найден в HTML")
                    
                # Показываем первые 200 символов content
                if content:
                    print(f"  Content preview: {content[:200]}...")
                    
                # Показываем первые 200 символов HTML
                if html:
                    print(f"  HTML preview: {html[:200]}...")
            else:
                print(f"  Content: {str(result)[:200]}...")
                
    except Exception as e:
        print(f"❌ Ошибка при поиске через Tavily: {e}")

if __name__ == "__main__":
    debug_tavily_raw()
