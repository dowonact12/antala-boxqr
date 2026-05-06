import hashlib
import json
import os
from dotenv import load_dotenv

load_dotenv()

SECRET_KEY = os.getenv('SECRET_KEY', 'default-fallback-key')


def generate_hash(box_number, ship_date, items):
    items_json = json.dumps(items, ensure_ascii=False, sort_keys=True)
    raw = f"{box_number}{ship_date}{items_json}{SECRET_KEY}"
    full_hash = hashlib.sha256(raw.encode('utf-8')).hexdigest()
    return full_hash[:8]


def verify_hash(box_number, ship_date, items, provided_hash):
    expected = generate_hash(box_number, ship_date, items)
    return expected == provided_hash
