#!/usr/bin/env python3
"""
Тест обработки медиа в медиа менеджере
"""

import sys
sys.path.append('scripts')
from telegram_bot import NewsTelegramBot
from media_manager import MediaManager
import yaml

def test_media_processing():
    """Тестируем обработку медиа"""
    
    print("🔍 Тестируем обработку медиа:")
    print("=" * 50)
    
    # Инициализируем бота
    bot = NewsTelegramBot('config/config.yaml')
    
    # Получаем новость
    news_data = bot.get_news_by_id(190)
    
    if news_data:
        print(f"ID: {news_data.get('id')}")
        print(f"Title: {news_data.get('title', '')[:50]}...")
        print(f"Images: {news_data.get('images', [])}")
        print(f"Videos: {news_data.get('videos', [])}")
        
        # Инициализируем медиа менеджер
        with open('config/config.yaml', 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)
        media_manager = MediaManager(config)
        
        # Тестируем обработку медиа
        print("\n🎬 Тестируем обработку видео:")
        for video_url in news_data.get('videos', []):
            print(f"  Video URL: {video_url}")
            video_path = media_manager._download_and_process_video(video_url, news_data.get('title', 'Test'))
            if video_path:
                print(f"  ✅ Скачано: {video_path}")
            else:
                print(f"  ❌ Не скачано")
                
    else:
        print("❌ Новость не найдена")

if __name__ == "__main__":
    test_media_processing()
