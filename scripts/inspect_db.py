import sqlite3
from pathlib import Path
p = Path('db.sqlite3')
print('DB path:', p.resolve())
print('Exists:', p.exists())
if not p.exists():
    raise SystemExit('DB file not found')
conn = sqlite3.connect(str(p))
c = conn.cursor()
c.execute("SELECT name FROM sqlite_master WHERE type='table'")
rows = [r[0] for r in c.fetchall()]
print('Tables:', rows)
print('guests_checkinsession present:', 'guests_checkinsession' in rows)
conn.close()
