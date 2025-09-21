#!/usr/bin/env python3
"""
Тест загрузки медиа данных из БД
"""

import sqlite3
import sys
from pathlib import Path

# Добавляем путь к модулям
sys.path.insert(0, str(Path(__file__).parent))

def test_db_loading():
    """Тестирует загрузку медиа данных из БД"""
    
    try:
        from scripts.telegram_bot import NewsTelegramBot
        
        # Создаем экземпляр бота
        bot = NewsTelegramBot('config/config.yaml')
        
        # Загружаем новость 278
        news_data = bot.get_news_by_id(278)
        
        if not news_data:
            print("❌ Новость 278 не найдена")
            return False
        
        print(f"✅ Новость загружена: {news_data['title'][:50]}...")
        print(f"📹 Videos: {news_data.get('videos', [])}")
        print(f"🖼️ Images: {news_data.get('images', [])}")
        print(f"📁 Local Video Path: {news_data.get('local_video_path', 'НЕТ')}")
        print(f"👤 Avatar Path: {news_data.get('avatar_path', 'НЕТ')}")
        print(f"👤 Username: {news_data.get('username', 'НЕТ')}")
        
        # Проверяем что локальное видео добавлено в список видео
        videos = news_data.get('videos', [])
        local_video = news_data.get('local_video_path', '')
        
        if local_video and local_video in videos:
            print(f"✅ Локальное видео найдено в списке: {local_video}")
            return True
        else:
            print(f"❌ Локальное видео НЕ найдено в списке")
            print(f"   Local video: {local_video}")
            print(f"   Videos list: {videos}")
            return False
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Тестируем загрузку медиа данных из БД...")
    result = test_db_loading()
    if result:
        print("\n✅ Тест пройден успешно!")
    else:
        print("\n❌ Тест провален!")
