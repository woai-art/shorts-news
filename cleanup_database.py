#!/usr/bin/env python3
"""
Скрипт для очистки базы данных от тестовых записей
"""

import sqlite3
import os
from pathlib import Path

def cleanup_database():
    """Очищает базу данных от тестовых записей"""
    
    # Путь к базе данных
    db_path = "data/user_news.db"
    
    if not os.path.exists(db_path):
        print("❌ База данных не найдена")
        return
    
    try:
        # Подключаемся к базе
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Получаем количество записей до очистки
        cursor.execute("SELECT COUNT(*) FROM user_news")
        count_before = cursor.fetchone()[0]
        
        print(f"📊 Записей в базе до очистки: {count_before}")
        
        # Удаляем все записи с тестовым URL
        test_url = "https://x.com/EricLDaugh/status/1969037987330621441"
        cursor.execute("DELETE FROM user_news WHERE url = ?", (test_url,))
        deleted_count = cursor.rowcount
        
        # Удаляем записи без медиа (нет images и videos)
        cursor.execute("DELETE FROM user_news WHERE (images IS NULL OR images = '') AND (videos IS NULL OR videos = '')")
        no_media_count = cursor.rowcount
        
        # Удаляем записи старше 1 дня (используем received_at)
        try:
            cursor.execute("DELETE FROM user_news WHERE received_at < datetime('now', '-1 day')")
            old_count = cursor.rowcount
        except:
            old_count = 0
        
        # Получаем количество записей после очистки
        cursor.execute("SELECT COUNT(*) FROM user_news")
        count_after = cursor.fetchone()[0]
        
        # Сохраняем изменения
        conn.commit()
        conn.close()
        
        print(f"✅ Очистка завершена:")
        print(f"  - Удалено записей с тестовым URL: {deleted_count}")
        print(f"  - Удалено записей без медиа: {no_media_count}")
        print(f"  - Удалено старых записей: {old_count}")
        print(f"  - Записей в базе после очистки: {count_after}")
        
    except Exception as e:
        print(f"❌ Ошибка очистки базы: {e}")

if __name__ == "__main__":
    cleanup_database()
