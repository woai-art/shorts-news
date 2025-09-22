#!/usr/bin/env python3
"""
Тест для отладки LLM процессора
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.llm_processor import GeminiProvider

def test_llm_debug():
    """Тестируем LLM процессор с отладкой"""
    
    # Инициализируем провайдер напрямую
    import os
    api_key = os.getenv('GEMINI_API_KEY') or os.getenv('GOOGLE_API_KEY')
    processor = GeminiProvider(api_key, 'gemini-2.0-flash-001', {})
    
    # Моковые данные новости (как в БД)
    news_data = {
        'id': 338,
        'title': 'NOW: The true scope of the crowd for Charlie Kirk in Arizona — WOW.',
        'description': 'NOW: The true scope of the crowd for Charlie Kirk in Arizona — WOW. Original estimates of 100K bumped to up to *300,000.*',
        'content': 'NOW: The true scope of the crowd for Charlie Kirk in Arizona — WOW. Original estimates of 100K bumped to up to *300,000.*',
        'source': 'TWITTER',
        'url': 'https://x.com/EricLDaugh/status/1969746992378130444',
        'username': 'EricLDaugh'
    }
    
    print("=== ТЕСТ LLM ПРОЦЕССОРА ===")
    print(f"News data: {news_data}")
    
    try:
        # Генерируем video package
        result = processor.generate_video_package(news_data)
        
        print(f"\n=== РЕЗУЛЬТАТ LLM ===")
        print(f"Result: {result}")
        
        if result and 'video_content' in result:
            video_content = result['video_content']
            title = video_content.get('title', '')
            summary = video_content.get('summary', '')
            
            print(f"\n=== VIDEO CONTENT ===")
            print(f"Title: '{title}' (длина: {len(title)})")
            print(f"Summary: '{summary}' (длина: {len(summary)})")
            
            if len(title) == 0:
                print("❌ ПРОБЛЕМА: Title пустой!")
            if len(summary) == 0:
                print("❌ ПРОБЛЕМА: Summary пустой!")
        else:
            print("❌ ПРОБЛЕМА: video_content отсутствует в результате!")
            
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_llm_debug()
