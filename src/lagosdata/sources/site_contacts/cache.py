import hashlib, json, sqlite3

class URLCache:
    def __init__(self,path):
        self.db=sqlite3.connect(path); self.db.execute('CREATE TABLE IF NOT EXISTS cache(url TEXT PRIMARY KEY, body TEXT, fetched_at TEXT DEFAULT CURRENT_TIMESTAMP)'); self.db.commit()
    def get(self,url):
        row=self.db.execute('SELECT body FROM cache WHERE url=?',(url,)).fetchone(); return json.loads(row[0]) if row else None
    def put(self,url,value):
        self.db.execute('INSERT OR REPLACE INTO cache(url,body) VALUES(?,?)',(url,json.dumps(value,ensure_ascii=False))); self.db.commit()
