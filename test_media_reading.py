#!/usr/bin/env python3
"""
Тест чтения медиа из БД
"""

import sys
sys.path.append('scripts')
from telegram_bot import NewsTelegramBot

def test_media_reading():
    """Тестируем чтение медиа из БД"""
    
    print("🔍 Тестируем чтение медиа из БД:")
    print("=" * 50)
    
    # Инициализируем бота
    bot = NewsTelegramBot('config/config.yaml')
    
    # Получаем конкретную новость
    news_data = bot.get_news_by_id(190)
    
    if news_data:
        print(f"ID: {news_data.get('id')}")
        print(f"Title: {news_data.get('title', '')[:50]}...")
        print(f"Images: {news_data.get('images', [])}")
        print(f"Videos: {news_data.get('videos', [])}")
        print(f"Type images: {type(news_data.get('images', []))}")
        print(f"Type videos: {type(news_data.get('videos', []))}")
        
        # Проверяем содержимое
        if news_data.get('videos'):
            print(f"Videos count: {len(news_data.get('videos', []))}")
            for i, video in enumerate(news_data.get('videos', [])):
                print(f"  Video {i+1}: {video}")
        else:
            print("❌ Видео не найдено")
            
    else:
        print("❌ Новости не найдены")

if __name__ == "__main__":
    test_media_reading()
