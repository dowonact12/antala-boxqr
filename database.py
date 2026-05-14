import os
import json
import psycopg2
import psycopg2.extras
from datetime import datetime

DATABASE_URL = os.environ.get('POSTGRES_URL') or os.environ.get('DATABASE_URL', '')
if DATABASE_URL.startswith('postgres://'):
    DATABASE_URL = DATABASE_URL.replace('postgres://', 'postgresql://', 1)


def _connect():
    conn = psycopg2.connect(DATABASE_URL, cursor_factory=psycopg2.extras.RealDictCursor)
    conn.autocommit = True
    return conn


def init_db():
    if not DATABASE_URL:
        return
    conn = _connect()
    cur = conn.cursor()
    cur.execute('''
        CREATE TABLE IF NOT EXISTS boxes (
            id SERIAL PRIMARY KEY,
            box_number TEXT UNIQUE NOT NULL,
            ship_date TEXT NOT NULL,
            buyer TEXT NOT NULL,
            invoice_number TEXT NOT NULL,
            items TEXT NOT NULL,
            total_weight REAL,
            dimensions TEXT,
            note TEXT,
            packed_by TEXT NOT NULL DEFAULT 'Dowon',
            photo_data BYTEA,
            photo_ext TEXT,
            hash TEXT NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT NOW()
        )
    ''')
    cur.close()
    conn.close()


def generate_box_number():
    today = datetime.now().strftime('%Y-%m%d')
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT COUNT(*) as cnt FROM boxes WHERE box_number LIKE %s",
        (f"{today}-%",)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    seq = (row['cnt'] or 0) + 1
    return f"{today}-{seq:03d}"


def save_box(data):
    conn = _connect()
    cur = conn.cursor()
    photo_data = data.get('photo_data')
    if photo_data:
        photo_data = psycopg2.Binary(photo_data)
    cur.execute('''
        INSERT INTO boxes (box_number, ship_date, buyer, invoice_number, items,
                          total_weight, dimensions, note, packed_by, photo_data, photo_ext, hash)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (box_number) DO UPDATE SET
            ship_date = EXCLUDED.ship_date,
            buyer = EXCLUDED.buyer,
            invoice_number = EXCLUDED.invoice_number,
            items = EXCLUDED.items,
            total_weight = EXCLUDED.total_weight,
            dimensions = EXCLUDED.dimensions,
            note = EXCLUDED.note,
            packed_by = EXCLUDED.packed_by,
            photo_data = EXCLUDED.photo_data,
            photo_ext = EXCLUDED.photo_ext,
            hash = EXCLUDED.hash
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
        photo_data,
        data.get('photo_ext'),
        data['hash']
    ))
    cur.close()
    conn.close()


def get_box(box_number):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, box_number, ship_date, buyer, invoice_number, items, total_weight, "
        "dimensions, note, packed_by, photo_ext, hash, created_at "
        "FROM boxes WHERE box_number = %s",
        (box_number,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        result = dict(row)
        result['items'] = json.loads(result['items'])
        return result
    return None


def get_box_photo(box_number):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT photo_data, photo_ext FROM boxes WHERE box_number = %s AND photo_data IS NOT NULL",
        (box_number,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row and row['photo_data']:
        return bytes(row['photo_data']), row['photo_ext']
    return None, None


def get_box_by_hash(hash_code):
    conn = _connect()
    cur = conn.cursor()
    cur.execute(
        "SELECT id, box_number, ship_date, buyer, invoice_number, items, total_weight, "
        "dimensions, note, packed_by, photo_ext, hash, created_at "
        "FROM boxes WHERE hash = %s",
        (hash_code,)
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        result = dict(row)
        result['items'] = json.loads(result['items'])
        return result
    return None


def get_all_boxes(search=None):
    conn = _connect()
    cur = conn.cursor()
    if search:
        cur.execute(
            "SELECT id, box_number, ship_date, buyer, invoice_number, items, total_weight, "
            "dimensions, note, packed_by, photo_ext, hash, created_at "
            "FROM boxes WHERE box_number LIKE %s OR buyer LIKE %s OR invoice_number LIKE %s "
            "ORDER BY created_at DESC",
            (f"%{search}%", f"%{search}%", f"%{search}%")
        )
    else:
        cur.execute(
            "SELECT id, box_number, ship_date, buyer, invoice_number, items, total_weight, "
            "dimensions, note, packed_by, photo_ext, hash, created_at "
            "FROM boxes ORDER BY created_at DESC"
        )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    results = []
    for row in rows:
        r = dict(row)
        r['items'] = json.loads(r['items'])
        results.append(r)
    return results
