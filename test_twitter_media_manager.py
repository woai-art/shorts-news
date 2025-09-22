#!/usr/bin/env python3
"""
Тест для проверки TwitterMediaManager с данными новости 334
"""

import sys
sys.path.append('scripts')
sys.path.append('engines/twitter')

from telegram_bot import NewsTelegramBot
from twitter_media_manager import TwitterMediaManager
import yaml

def test_twitter_media_manager():
    """Тестируем TwitterMediaManager с данными новости 334"""
    
    # Загружаем конфигурацию
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # Создаем экземпляр бота
    bot = NewsTelegramBot('config/config.yaml')
    
    # Получаем новость 334
    news_data = bot.get_news_by_id(334)
    
    if not news_data:
        print("❌ Новость 334 не найдена")
        return
        
    print("📊 Исходные данные новости 334:")
    print(f"  Images: {news_data.get('images', [])}")
    print(f"  Videos: {news_data.get('videos', [])}")
    print(f"  Local video path: {news_data.get('local_video_path', '')}")
    print(f"  Avatar path: {news_data.get('avatar_path', '')}")
    
    # Создаем TwitterMediaManager
    media_manager = TwitterMediaManager(config)
    
    # Тестируем обработку медиа
    print("\n🔧 Тестируем TwitterMediaManager...")
    result = media_manager.process_news_media(news_data)
    
    print(f"\n📊 Результат обработки:")
    print(f"  Has media: {result.get('has_media', False)}")
    print(f"  Has images: {result.get('has_images', False)}")
    print(f"  Has videos: {result.get('has_videos', False)}")
    print(f"  Local video path: {result.get('local_video_path', '')}")
    print(f"  Local image path: {result.get('local_image_path', '')}")
    print(f"  Avatar path: {result.get('avatar_path', '')}")

if __name__ == "__main__":
    test_twitter_media_manager()
