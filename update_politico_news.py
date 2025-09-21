#!/usr/bin/env python3
"""Обновление новости Politico с исправленным изображением"""

import sqlite3

conn = sqlite3.connect('data/user_news.db')
cursor = conn.cursor()

# Обновляем новость с исправленным изображением
cursor.execute('UPDATE user_news SET images = ?, processed = 0 WHERE url LIKE "%epstein-case%"', 
               ('https://images.unsplash.com/photo-1586339949916-3e9457bef6d3?w=1280&h=720&fit=crop&crop=center',))

conn.commit()
print('✅ Новость обновлена с исправленным изображением')

# Проверяем результат
cursor.execute('SELECT id, title, images, processed FROM user_news WHERE url LIKE "%epstein-case%"')
result = cursor.fetchone()
if result:
    print(f'📰 ID: {result[0]}, Title: {result[1][:50]}..., Images: {result[2]}, Processed: {result[3]}')

conn.close()
