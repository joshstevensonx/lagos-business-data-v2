"""SQLite-backed resumable search state and append-only raw JSONL."""
from __future__ import annotations
import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

def now(): return datetime.now(timezone.utc).isoformat()

class RunState:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(self.path)
        self.db.row_factory = sqlite3.Row
        self.db.execute('''CREATE TABLE IF NOT EXISTS searches (
            id INTEGER PRIMARY KEY, source TEXT NOT NULL, term TEXT NOT NULL, area TEXT NOT NULL,
            status TEXT NOT NULL, raw_count INTEGER DEFAULT 0, kept_count INTEGER DEFAULT 0,
            started_at TEXT, finished_at TEXT, error TEXT, UNIQUE(source,term,area))''')
        self.db.commit()

    def should_run(self, source, term, area, *, force=False):
        row = self.db.execute('SELECT status FROM searches WHERE source=? AND term=? AND area=?',(source,term,area)).fetchone()
        return force or row is None or row['status'] != 'done'

    def start(self, source, term, area, *, force=False):
        stamp = now()
        self.db.execute('''INSERT INTO searches(source,term,area,status,started_at,finished_at,error)
            VALUES(?,?,?,'running',?,NULL,NULL) ON CONFLICT(source,term,area) DO UPDATE SET
            status='running',started_at=excluded.started_at,finished_at=NULL,error=NULL''',(source,term,area,stamp))
        self.db.commit()

    def finish(self, source, term, area, status, raw_count=0, kept_count=0, error=''):
        if status not in {'done','failed','skipped','pending'}: raise ValueError(status)
        self.db.execute('''UPDATE searches SET status=?,raw_count=?,kept_count=?,finished_at=?,error=?
            WHERE source=? AND term=? AND area=?''',(status,raw_count,kept_count,now(),error or None,source,term,area))
        self.db.commit()

    def searches(self): return [dict(r) for r in self.db.execute('SELECT * FROM searches ORDER BY id')]
    def close(self): self.db.commit(); self.db.close()

def append_raw(run_dir: str | Path, source: str, records):
    raw_dir = Path(run_dir) / 'raw'; raw_dir.mkdir(parents=True, exist_ok=True)
    path = raw_dir / f'{source}.jsonl'
    with path.open('a', encoding='utf-8') as out:
        for row in records:
            out.write(json.dumps(row, ensure_ascii=False, default=str) + '\n')
            out.flush()
    return path
