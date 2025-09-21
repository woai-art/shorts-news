#!/usr/bin/env python3
"""
Скрипт для исправления неполных URL изображений NBC News в базе данных
"""

import sqlite3

def fix_nbc_urls():
    """Исправляем неполные URL изображений NBC News"""
    conn = sqlite3.connect('data/user_news.db')
    cursor = conn.cursor()
    
    try:
        # Получаем новость 253
        cursor.execute("SELECT id, images FROM user_news WHERE id = 253")
        result = cursor.fetchone()
        
        if result:
            news_id, images = result
            print(f"🔍 Текущие изображения для новости {news_id}:")
            print(f"   {images}")
            
            # Исправляем URL изображений
            fixed_images = images.replace(
                'https://media-cldnry.s-nbcnews.com/image/upload/t_focal-760x428',
                'https://media-cldnry.s-nbcnews.com/image/upload/t_focal-760x428,f_auto,q_auto:best/mpx/2704722219/2025_09/1758207929783_now_brk_trump_china_tiktok_250918_1920x1080-rxrtl8.jpg'
            ).replace(
                'https://media-cldnry.s-nbcnews.com/image/upload/t_focal-60x60',
                'https://media-cldnry.s-nbcnews.com/image/upload/t_focal-60x60,f_auto,q_auto:best/newscms/2023_08/3595832/rebecca-shabad-byline-jm-1.jpg'
            )
            
            print(f"🔧 Исправленные изображения:")
            print(f"   {fixed_images}")
            
            # Обновляем в базе данных
            cursor.execute("UPDATE user_news SET images = ? WHERE id = ?", (fixed_images, news_id))
            conn.commit()
            
            print("✅ URL изображений исправлены в базе данных")
        else:
            print("❌ Новость 253 не найдена")
        
    except Exception as e:
        print(f"❌ Ошибка: {e}")
        conn.rollback()
    finally:
        conn.close()

if __name__ == "__main__":
    fix_nbc_urls()
