#!/usr/bin/env python3
import sqlite3

conn = sqlite3.connect('data/user_news.db')
cursor = conn.cursor()
cursor.execute("PRAGMA table_info(user_news)")
columns = cursor.fetchall()
print("Columns in user_news table:")
for col in columns:
    print(f"  {col[1]} ({col[2]})")

conn.close()
