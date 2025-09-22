#!/usr/bin/env python3
"""
Тест для проверки fallback video package
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.telegram_bot import NewsTelegramBot
from scripts.llm_direct_provider import GeminiDirectProvider

def test_fallback_package():
    """Тестируем fallback video package для ID 336"""
    
    # Инициализируем бот
    bot = NewsTelegramBot('config/config.yaml')
    
    # Получаем новость ID 337
    news_data = bot.get_news_by_id(337)
    
    if news_data:
        print("=== NEWS_DATA ===")
        print(f"Title: '{news_data.get('title', 'НЕТ')}'")
        print(f"Description: '{news_data.get('description', 'НЕТ')}'")
        
        # Инициализируем LLM провайдер
        provider = GeminiDirectProvider('config/config.yaml')
        
        # Генерируем fallback package
        fallback_package = provider._generate_fallback_video_package(news_data)
        
        print("\n=== FALLBACK VIDEO PACKAGE ===")
        print(f"Package: {fallback_package}")
        
        # Проверяем структуру
        video_content = fallback_package.get('video_content', {})
        print(f"\n=== VIDEO CONTENT ===")
        print(f"Title: '{video_content.get('title', 'НЕТ')}'")
        print(f"Summary: '{video_content.get('summary', 'НЕТ')}'")
        
        # Проверяем длины
        title_len = len(video_content.get('title', ''))
        summary_len = len(video_content.get('summary', ''))
        
        print(f"\n=== АНАЛИЗ ДЛИН ===")
        print(f"Title length: {title_len}")
        print(f"Summary length: {summary_len}")
        
        if title_len == 0:
            print("\n❌ ПРОБЛЕМА: Title в video_content пустой!")
        if summary_len == 0:
            print("\n❌ ПРОБЛЕМА: Summary в video_content пустой!")
        
    else:
        print("❌ Новость ID 336 не найдена!")

if __name__ == "__main__":
    test_fallback_package()
