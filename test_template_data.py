#!/usr/bin/env python3
"""
Тест данных для шаблона
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from scripts.telegram_bot import NewsTelegramBot

def test_template_data():
    """Тестируем данные для шаблона"""
    
    # Инициализируем бота
    bot = NewsTelegramBot('config/config.yaml')
    
    # Получаем последнюю новость
    news_data = bot.get_news_by_id(344)
    if not news_data:
        print("❌ Новость 344 не найдена")
        return
    
    print("=== ДАННЫЕ НОВОСТИ ===")
    print(f"Title: {news_data.get('title', '')}")
    print(f"Images: {news_data.get('images', [])}")
    print(f"Videos: {news_data.get('videos', [])}")
    print(f"Local video path: {news_data.get('local_video_path', '')}")
    print(f"Avatar path: {news_data.get('avatar_path', '')}")
    
    # Тестируем media manager
    from engines.twitter.twitter_media_manager import TwitterMediaManager
    from config import config
    
    with open('config/config.yaml', 'r', encoding='utf-8') as f:
        import yaml
        config_data = yaml.safe_load(f)
    
    media_manager = TwitterMediaManager(config_data)
    media_result = media_manager.process_news_media(news_data)
    
    print(f"\n=== РЕЗУЛЬТАТ MEDIA MANAGER ===")
    print(f"Has media: {media_result.get('has_media', False)}")
    print(f"Local video path: {media_result.get('local_video_path', '')}")
    print(f"Avatar path: {media_result.get('avatar_path', '')}")
    print(f"Video path: {media_result.get('video_path', '')}")

if __name__ == "__main__":
    test_template_data()
