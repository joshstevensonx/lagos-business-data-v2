"""Structured append-only run logger."""
import json
from datetime import datetime, timezone
from pathlib import Path
from threading import Lock

class RunLogger:
    def __init__(self, path):
        self.path = Path(path); self.path.parent.mkdir(parents=True, exist_ok=True); self.lock = Lock()
    def log(self, event, **fields):
        row = {'timestamp':datetime.now(timezone.utc).isoformat(),'event':event,**fields}
        with self.lock, self.path.open('a',encoding='utf-8') as stream:
            stream.write(json.dumps(row,ensure_ascii=False,default=str)+'\n'); stream.flush()
