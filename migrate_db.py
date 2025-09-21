#!/usr/bin/env python3
"""
Скрипт для миграции базы данных - замена разделителей запятых на |
"""

import sqlite3

def migrate_database():
    """Миграция базы данных"""
    conn = sqlite3.connect('data/user_news.db')
    cursor = conn.cursor()
    
    try:
        # Обновляем images
        cursor.execute("UPDATE user_news SET images = REPLACE(images, ',', '|') WHERE images IS NOT NULL")
        
        # Обновляем videos
        cursor.execute("UPDATE user_news SET videos = REPLACE(videos, ',', '|') WHERE videos IS NOT NULL")
        
        conn.commit()
        print("✅ Миграция базы данных завершена")
        
        # Проверяем результат
        cursor.execute("SELECT id, images FROM user_news WHERE id = 253")
        result = cursor.fetchone()
        if result:
            print(f"✅ Проверка: новость 253 - images: {result[1]}")
        
    except Exception as e:
        print(f"❌ Ошибка миграции: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
