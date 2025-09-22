#!/usr/bin/env python3
"""
Тест для проверки содержимого news_data для ID 336
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.telegram_bot import NewsTelegramBot
import yaml

def test_news_336_content():
    """Тестируем содержимое news_data для ID 336"""
    
    # Загружаем конфигурацию
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Инициализируем бот
    bot = NewsTelegramBot('config/config.yaml')
    
    # Получаем новость ID 336
    news_data = bot.get_news_by_id(336)
    
    if news_data:
        print("=== СОДЕРЖИМОЕ NEWS_DATA ДЛЯ ID 336 ===")
        print(f"ID: {news_data.get('id')}")
        print(f"Title: '{news_data.get('title', 'НЕТ')}'")
        print(f"Description: '{news_data.get('description', 'НЕТ')}'")
        print(f"Content: '{news_data.get('content', 'НЕТ')}'")
        print(f"Source: '{news_data.get('source', 'НЕТ')}'")
        print(f"URL: '{news_data.get('url', 'НЕТ')}'")
        print(f"Username: '{news_data.get('username', 'НЕТ')}'")
        print(f"Published: '{news_data.get('published', 'НЕТ')}'")
        print(f"Images: {news_data.get('images', [])}")
        print(f"Videos: {news_data.get('videos', [])}")
        print(f"Local video path: '{news_data.get('local_video_path', 'НЕТ')}'")
        print(f"Local image path: '{news_data.get('local_image_path', 'НЕТ')}'")
        print(f"Avatar path: '{news_data.get('avatar_path', 'НЕТ')}'")
        
        # Проверяем длину полей
        title_len = len(news_data.get('title', ''))
        desc_len = len(news_data.get('description', ''))
        content_len = len(news_data.get('content', ''))
        
        print(f"\n=== АНАЛИЗ ДЛИН ===")
        print(f"Title length: {title_len}")
        print(f"Description length: {desc_len}")
        print(f"Content length: {content_len}")
        
        if title_len == 0 and desc_len == 0 and content_len == 0:
            print("\n❌ ПРОБЛЕМА: Все текстовые поля пустые!")
        elif title_len == 0:
            print("\n⚠️ Title пустой, но есть description или content")
        elif desc_len == 0 and content_len == 0:
            print("\n⚠️ Description и content пустые, но есть title")
        
    else:
        print("❌ Новость ID 336 не найдена!")

if __name__ == "__main__":
    test_news_336_content()
