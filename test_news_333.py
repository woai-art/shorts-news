#!/usr/bin/env python3
"""
Тест для проверки данных новости 333 из БД
"""

import sqlite3
import sys
from pathlib import Path

def test_news_333():
    """Проверяем что загружается из БД для новости 333"""
    db_path = 'data/user_news.db'
    
    if not Path(db_path).exists():
        print(f"❌ База данных не найдена: {db_path}")
        return
    
    with sqlite3.connect(db_path) as conn:
        conn.row_factory = sqlite3.Row
        
        # Получаем данные новости 333
        cursor = conn.execute('''
            SELECT * FROM user_news
            WHERE id = ?
        ''', (333,))
        
        news_row = cursor.fetchone()
        if not news_row:
            print("❌ Новость 333 не найдена в БД")
            return
            
        news_dict = dict(news_row)
        
        print("📊 Данные новости 333 из БД:")
        print(f"  ID: {news_dict.get('id')}")
        print(f"  Title: {news_dict.get('title', '')[:50]}...")
        print(f"  URL: {news_dict.get('url', '')[:50]}...")
        print(f"  Username: {news_dict.get('username', '')}")
        print(f"  Images (raw): {news_dict.get('images', '')}")
        print(f"  Videos (raw): {news_dict.get('videos', '')}")
        print(f"  Local video path: {news_dict.get('local_video_path', '')}")
        print(f"  Local image path: {news_dict.get('local_image_path', '')}")
        print(f"  Avatar path: {news_dict.get('avatar_path', '')}")
        
        # Проверяем файлы
        local_video = news_dict.get('local_video_path', '')
        if local_video:
            exists = Path(local_video).exists()
            print(f"  🎬 Локальное видео существует: {exists} - {local_video}")
        
        local_image = news_dict.get('local_image_path', '')
        if local_image:
            exists = Path(local_image).exists()
            print(f"  🖼️ Локальное изображение существует: {exists} - {local_image}")
            
        avatar_path = news_dict.get('avatar_path', '')
        if avatar_path:
            exists = Path(avatar_path).exists()
            print(f"  👤 Аватар существует: {exists} - {avatar_path}")

if __name__ == "__main__":
    test_news_333()
