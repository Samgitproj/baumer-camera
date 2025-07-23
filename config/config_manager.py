import os
import sqlite3
import json

class ConfigManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Zet de database in dezelfde map als dit script (config/)
            base_dir = os.path.dirname(__file__)
            db_path = os.path.join(base_dir, 'settings.db')
        self.db_path = db_path
        self._ensure_db()

    def _ensure_db(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('''
            CREATE TABLE IF NOT EXISTS configs (
                name TEXT PRIMARY KEY,
                settings TEXT NOT NULL
            )
        ''')
        conn.commit()
        conn.close()

    def list_configs(self):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT name FROM configs')
        rows = c.fetchall()
        conn.close()
        return [row[0] for row in rows]

    def load(self, name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('SELECT settings FROM configs WHERE name = ?', (name,))
        row = c.fetchone()
        conn.close()
        if row:
            return json.loads(row[0])
        else:
            return None

    def save(self, name, settings):
        data = json.dumps(settings)
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('REPLACE INTO configs (name, settings) VALUES (?, ?)', (name, data))
        conn.commit()
        conn.close()

    def delete(self, name):
        conn = sqlite3.connect(self.db_path)
        c = conn.cursor()
        c.execute('DELETE FROM configs WHERE name = ?', (name,))
        conn.commit()
        conn.close()
