#!/usr/bin/env python3
"""
Скрипт для проверки URL изображений в разных движках
"""

import sqlite3

def check_urls():
    """Проверяем URL изображений в разных движках"""
    conn = sqlite3.connect('data/user_news.db')
    cursor = conn.cursor()
    
    try:
        # Получаем последние 5 новостей с изображениями
        cursor.execute("""
            SELECT id, source, images 
            FROM user_news 
            WHERE images IS NOT NULL AND images != '' 
            ORDER BY id DESC 
            LIMIT 5
        """)
        
        results = cursor.fetchall()
        
        for row in results:
            news_id, source, images = row
            print(f"\n=== ID {news_id}, Source: {source} ===")
            print(f"Images: {images[:200]}...")
            
            # Проверяем, есть ли запятые в URL
            if ',' in images:
                print("⚠️  Содержит запятые в URL!")
            else:
                print("✅ Нет запятых в URL")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    check_urls()
