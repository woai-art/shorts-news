import sqlite3

DB_PATH = 'data/user_news.db'

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    # Remove specific test rows
    cur.execute('DELETE FROM user_news WHERE id IN (206,208)')
    # Remove generic test rows by title prefix
    cur.execute("DELETE FROM user_news WHERE title LIKE 'Test News%'")
    con.commit()

    # Show pending items after cleanup
    cur.execute('SELECT id, title, processed FROM user_news WHERE processed = 0 ORDER BY id DESC LIMIT 20')
    rows = cur.fetchall()
    print('Pending after cleanup:')
    for r in rows:
        title = r[1] or ''
        print(r[0], '|', (title[:50] + ('...' if len(title) > 50 else '')), '| processed=', r[2])

    con.close()

if __name__ == '__main__':
    main()


