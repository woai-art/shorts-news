#!/usr/bin/env python3
"""
Миграция для добавления колонки avatar_url в таблицу user_news
"""

import sqlite3
import os

def add_avatar_url_column():
    """Добавляет колонку avatar_url в таблицу user_news"""
    
    db_path = os.path.join('data', 'user_news.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Проверяем, существует ли колонка
        cursor.execute("PRAGMA table_info(user_news)")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'avatar_url' not in columns:
            print("Добавляем колонку avatar_url...")
            cursor.execute("ALTER TABLE user_news ADD COLUMN avatar_url TEXT")
            conn.commit()
            print("✅ Колонка avatar_url добавлена")
        else:
            print("✅ Колонка avatar_url уже существует")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ Ошибка при добавлении колонки: {e}")

if __name__ == "__main__":
    add_avatar_url_column()
