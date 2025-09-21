#!/usr/bin/env python3
"""Проверка новостей Politico в БД"""

import sqlite3

conn = sqlite3.connect('data/user_news.db')
cursor = conn.cursor()
cursor.execute('SELECT id, title, images, videos, processed FROM user_news WHERE url LIKE "%epstein-case%"')
results = cursor.fetchall()

print('📰 Последние новости Politico:')
for row in results:
    print(f'ID: {row[0]}, Title: {row[1][:50]}..., Images: {row[2]}, Videos: {row[3]}, Processed: {row[4]}')

conn.close()
