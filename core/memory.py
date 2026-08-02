import json
import sqlite3
import threading
import time


class Memory:
    """Single SQLite store: chat, facts, token usage, cache, skills, reminders, audit."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.conn = sqlite3.connect(str(cfg.data / "db" / "cryous.db"), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.RLock()
        with self.lock:
            self.conn.executescript("""
            CREATE TABLE IF NOT EXISTS chat(id INTEGER PRIMARY KEY, role TEXT, content TEXT, ts REAL, session TEXT);
            CREATE TABLE IF NOT EXISTS facts(id INTEGER PRIMARY KEY, key TEXT, value TEXT, ts REAL);
            CREATE TABLE IF NOT EXISTS usage(id INTEGER PRIMARY KEY, provider TEXT, tier TEXT, ptok INT, ctok INT, ts REAL);
            CREATE TABLE IF NOT EXISTS cache(k TEXT PRIMARY KEY, v TEXT, ts REAL);
            CREATE TABLE IF NOT EXISTS skills(id INTEGER PRIMARY KEY, pattern TEXT, action TEXT, hits INT DEFAULT 0, ok INT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS reminders(id INTEGER PRIMARY KEY, at REAL, text TEXT, done INT DEFAULT 0);
            CREATE TABLE IF NOT EXISTS provider_stats(provider TEXT PRIMARY KEY, latency REAL DEFAULT 0.6, success REAL DEFAULT 1.0);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY, kind TEXT, detail TEXT, ts REAL);
            """)
            self.conn.commit()

    # ── chat ──
    def add_chat(self, role, content, session="ui"):
        with self.lock:
            self.conn.execute("INSERT INTO chat(role,content,ts,session) VALUES(?,?,?,?)",
                              (role, content, time.time(), session))
            self.conn.execute("DELETE FROM chat WHERE id NOT IN (SELECT id FROM chat ORDER BY id DESC LIMIT 400)")
            self.conn.commit()

    def history(self, n=8):
        with self.lock:
            rows = self.conn.execute("SELECT role,content FROM chat ORDER BY id DESC LIMIT ?", (n,)).fetchall()
        return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]

    # ── facts (preferences / long-term memory) ──
    def set_fact(self, key, value):
        with self.lock:
            self.conn.execute("DELETE FROM facts WHERE key=?", (key,))
            self.conn.execute("INSERT INTO facts(key,value,ts) VALUES(?,?,?)", (key, value, time.time()))
            self.conn.commit()

    def facts(self, limit=8):
        with self.lock:
            rows = self.conn.execute("SELECT key,value FROM facts ORDER BY ts DESC LIMIT ?", (limit,)).fetchall()
        return [f"{r['key']}: {r['value']}" for r in rows]

    def forget(self, key):
        with self.lock:
            self.conn.execute("DELETE FROM facts WHERE key LIKE ?", (f"%{key}%",))
            self.conn.commit()

    # ── token usage ──
    def log_usage(self, provider, tier, ptok, ctok):
        with self.lock:
            self.conn.execute("INSERT INTO usage(provider,tier,ptok,ctok,ts) VALUES(?,?,?,?,?)",
                              (provider, tier, ptok, ctok, time.time()))
            self.conn.execute("DELETE FROM usage WHERE ts < ?", (time.time() - 90 * 86400,))
            self.conn.commit()

    def tokens_since(self, ts):
        with self.lock:
            r = self.conn.execute("SELECT COALESCE(SUM(ptok+ctok),0) s FROM usage WHERE ts>=?", (ts,)).fetchone()
        return int(r["s"])

    # ── response cache ──
    def cache_get(self, k, ttl=21600):
        with self.lock:
            r = self.conn.execute("SELECT v,ts FROM cache WHERE k=?", (k,)).fetchone()
        return r["v"] if r and time.time() - r["ts"] < ttl else None

    def cache_set(self, k, v):
        with self.lock:
            self.conn.execute("INSERT OR REPLACE INTO cache(k,v,ts) VALUES(?,?,?)", (k, v, time.time()))
            self.conn.execute("DELETE FROM cache WHERE ts < ?", (time.time() - 86400,))
            self.conn.commit()

    # ── learned skills (zero-token shortcuts) ──
    def add_skill(self, pattern, action):
        with self.lock:
            self.conn.execute("INSERT INTO skills(pattern,action) VALUES(?,?)",
                              (pattern.lower(), json.dumps(action)))
            self.conn.commit()

    def match_skill(self, text):
        tokens = set(text.lower().split())
        best, bs = None, 0.0
        with self.lock:
            rows = self.conn.execute("SELECT id,pattern,action,hits,ok FROM skills").fetchall()
        for r in rows:
            p = set(r["pattern"].split())
            if p and p <= tokens:
                s = len(p) + r["ok"] / (r["hits"] + 1)
                if s > bs:
                    bs, best = s, r
        return (dict(best), json.loads(best["action"])) if best else None

    def bump_skill(self, sid, ok=True):
        with self.lock:
            self.conn.execute("UPDATE skills SET hits=hits+1, ok=ok+? WHERE id=?", (1 if ok else 0, sid))
            self.conn.commit()

    # ── reminders ──
    def add_reminder(self, at, text):
        with self.lock:
            self.conn.execute("INSERT INTO reminders(at,text) VALUES(?,?)", (at, text))
            self.conn.commit()

    def due_reminders(self):
        with self.lock:
            return [dict(r) for r in self.conn.execute(
                "SELECT id,text FROM reminders WHERE done=0 AND at<=?", (time.time(),)).fetchall()]

    def mark_reminder(self, rid):
        with self.lock:
            self.conn.execute("UPDATE reminders SET done=1 WHERE id=?", (rid,))
            self.conn.commit()

    # ── provider health (EMA) ──
    def provider_feedback(self, name, latency, ok):
        with self.lock:
            r = self.conn.execute("SELECT latency,success FROM provider_stats WHERE provider=?", (name,)).fetchone()
            if r:
                lat = r["latency"] * 0.7 + latency * 0.3
                suc = r["success"] * 0.8 + (1.0 if ok else 0.0) * 0.2
                self.conn.execute("UPDATE provider_stats SET latency=?, success=? WHERE provider=?", (lat, suc, name))
            else:
                self.conn.execute("INSERT INTO provider_stats(provider,latency,success) VALUES(?,?,?)",
                                  (name, latency, 1.0 if ok else 0.0))
            self.conn.commit()

    def provider_scores(self):
        with self.lock:
            return {r["provider"]: (r["latency"], r["success"])
                    for r in self.conn.execute("SELECT provider,latency,success FROM provider_stats")}

    # ── audit ──
    def audit(self, kind, detail):
        with self.lock:
            self.conn.execute("INSERT INTO audit(kind,detail,ts) VALUES(?,?,?)", (kind, str(detail)[:500], time.time()))
            self.conn.execute("DELETE FROM audit WHERE id NOT IN (SELECT id FROM audit ORDER BY id DESC LIMIT 500)")
            self.conn.commit()

    def close(self):
        self.conn.close()