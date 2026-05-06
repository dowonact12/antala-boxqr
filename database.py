import sqlite3
import json
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), 'boxes.db')


def get_db():
    conn = sqlite3.connect(DB_PATH, timeout=10)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS boxes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            box_number TEXT UNIQUE NOT NULL,
            ship_date TEXT NOT NULL,
            buyer TEXT NOT NULL,
            invoice_number TEXT NOT NULL,
            items TEXT NOT NULL,
            total_weight REAL,
            dimensions TEXT,
            note TEXT,
            packed_by TEXT NOT NULL DEFAULT 'Dowon',
            photo_filename TEXT,
            hash TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
        )
    ''')
    conn.commit()
    conn.close()


def generate_box_number():
    today = datetime.now().strftime('%Y-%m%d')
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) as cnt FROM boxes WHERE box_number LIKE ?",
        (f"{today}-%",)
    ).fetchone()
    seq = (row['cnt'] or 0) + 1
    conn.close()
    return f"{today}-{seq:03d}"


def save_box(data):
    conn = get_db()
    conn.execute('''
        INSERT INTO boxes (box_number, ship_date, buyer, invoice_number, items,
                          total_weight, dimensions, note, packed_by, photo_filename, hash)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data['box_number'],
        data['ship_date'],
        data['buyer'],
        data['invoice_number'],
        json.dumps(data['items'], ensure_ascii=False),
        data.get('total_weight'),
        data.get('dimensions'),
        data.get('note'),
        data.get('packed_by', 'Dowon'),
        data.get('photo_filename'),
        data['hash']
    ))
    conn.commit()
    conn.close()


def get_box(box_number):
    conn = get_db()
    row = conn.execute("SELECT * FROM boxes WHERE box_number = ?", (box_number,)).fetchone()
    conn.close()
    if row:
        result = dict(row)
        result['items'] = json.loads(result['items'])
        return result
    return None


def get_all_boxes(search=None):
    conn = get_db()
    if search:
        rows = conn.execute(
            "SELECT * FROM boxes WHERE box_number LIKE ? OR buyer LIKE ? OR invoice_number LIKE ? ORDER BY created_at DESC",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        ).fetchall()
    else:
        rows = conn.execute("SELECT * FROM boxes ORDER BY created_at DESC").fetchall()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        r['items'] = json.loads(r['items'])
        results.append(r)
    return results
