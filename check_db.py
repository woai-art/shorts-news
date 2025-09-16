import sqlite3
import os

db_path = 'data/user_news.db'
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Удаляем все новости с CAPTCHA
    cursor.execute("DELETE FROM user_news WHERE description LIKE '%Проверяем, человек ли вы%'")
    deleted = cursor.rowcount
    conn.commit()
    
    print(f'Удалено {deleted} новостей с CAPTCHA')
    
    # Проверяем оставшиеся новости
    cursor.execute('SELECT id, title, url FROM user_news ORDER BY id DESC LIMIT 3')
    rows = cursor.fetchall()
    
    print('Оставшиеся новости:')
    for row in rows:
        print(f'ID: {row[0]}, Title: {row[1][:50]}..., URL: {row[2][:50]}...')
    
    conn.close()
else:
    print('База данных не найдена')
