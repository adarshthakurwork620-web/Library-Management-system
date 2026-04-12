import sqlite3

conn = sqlite3.connect("library.db")
cur = conn.cursor()

cur.executescript("""
-- paste upar wala SQL yaha
""")

conn.commit()
conn.close()

print("DB created ✅")