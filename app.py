import os
import json
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from dotenv import load_dotenv
from werkzeug.utils import secure_filename
from database import init_db, save_box, get_box, get_all_boxes, generate_box_number
from hash_util import generate_hash, verify_hash
from qr_generator import build_qr_text, generate_qr_bytes
from pdf_generator import generate_full_pdf, generate_label_pdf

load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('SECRET_KEY', 'dev')

BASE_DIR = os.path.dirname(__file__)
PHOTOS_DIR = os.path.join(BASE_DIR, 'photos')
OUTPUT_DIR = os.path.join(BASE_DIR, 'output')

os.makedirs(PHOTOS_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'webp'}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/box-number')
def api_box_number():
    return jsonify({'box_number': generate_box_number()})


@app.route('/submit', methods=['POST'])
def submit():
    items = []
    names = request.form.getlist('item_name[]')
    quantities = request.form.getlist('item_qty[]')
    for name, qty in zip(names, quantities):
        if name.strip() and qty.strip():
            items.append({
                'name': name.strip(),
                'quantity': int(qty)
            })

    data = {
        'box_number': request.form['box_number'],
        'ship_date': request.form['ship_date'],
        'buyer': request.form['buyer'],
        'invoice_number': request.form['invoice_number'],
        'items': items,
        'total_weight': request.form.get('total_weight') or None,
        'dimensions': request.form.get('dimensions') or None,
        'note': request.form.get('note') or None,
        'packed_by': request.form.get('packed_by') or 'Dowon',
        'photo_filename': None,
    }

    # Handle photo upload
    photo = request.files.get('photo')
    if photo and photo.filename and allowed_file(photo.filename):
        ext = photo.filename.rsplit('.', 1)[1].lower()
        photo_filename = f"{data['box_number']}.{ext}"
        photo.save(os.path.join(PHOTOS_DIR, photo_filename))
        data['photo_filename'] = photo_filename

    # Generate hash
    data['hash'] = generate_hash(data['box_number'], data['ship_date'], data['items'])

    # Save to DB
    save_box(data)

    # Generate PDF
    generate_full_pdf(data)

    return redirect(url_for('preview', box_number=data['box_number']))


@app.route('/preview/<box_number>')
def preview(box_number):
    data = get_box(box_number)
    if not data:
        return "Box not found", 404
    qr_text = build_qr_text(data)
    return render_template('preview.html', data=data, qr_text=qr_text)


@app.route('/download/<box_number>')
def download_pdf(box_number):
    filepath = os.path.join(OUTPUT_DIR, f"{box_number}.pdf")
    if not os.path.exists(filepath):
        data = get_box(box_number)
        if not data:
            return "Box not found", 404
        filepath = generate_full_pdf(data)
    return send_file(filepath, as_attachment=True, download_name=f"{box_number}.pdf")


@app.route('/download-labels', methods=['POST'])
def download_labels():
    box_numbers = request.form.getlist('box_numbers[]')
    boxes = []
    for bn in box_numbers:
        data = get_box(bn)
        if data:
            boxes.append(data)
    if not boxes:
        return "No boxes found", 404
    filepath = generate_label_pdf(boxes)
    return send_file(filepath, as_attachment=True, download_name="labels.pdf")


@app.route('/qr-image/<box_number>')
def qr_image(box_number):
    data = get_box(box_number)
    if not data:
        return "Box not found", 404
    qr_text = build_qr_text(data)
    buf = generate_qr_bytes(qr_text, box_size=10, border=2)
    return send_file(buf, mimetype='image/png')


@app.route('/photo/<box_number>')
def photo(box_number):
    data = get_box(box_number)
    if not data or not data.get('photo_filename'):
        return "No photo", 404
    return send_file(os.path.join(PHOTOS_DIR, data['photo_filename']))


@app.route('/history')
def history():
    search = request.args.get('q', '')
    boxes = get_all_boxes(search if search else None)
    return render_template('history.html', boxes=boxes, search=search)


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    result = None
    qr_text = ''
    if request.method == 'POST':
        qr_text = request.form.get('qr_text', '').strip()
        result = parse_and_verify(qr_text)
    return render_template('verify.html', result=result, qr_text=qr_text)


def parse_and_verify(qr_text):
    lines = qr_text.strip().split('\n')
    try:
        box_number = None
        ship_date = None
        items = []
        verify_hash_val = None
        in_contents = False

        for line in lines:
            line = line.strip()
            if line.startswith('Box #:'):
                box_number = line.split(':', 1)[1].strip()
            elif line.startswith('Date:'):
                ship_date = line.split(':', 1)[1].strip()
            elif line == 'CONTENTS:':
                in_contents = True
            elif line.startswith('- ') and in_contents:
                item_str = line[2:]
                parts = item_str.rsplit(' x ', 1)
                if len(parts) == 2:
                    name = parts[0].strip()
                    qty = int(parts[1].strip())
                    items.append({'name': name, 'quantity': qty})
            elif line.startswith('Total:'):
                in_contents = False
            elif line.startswith('Verify:'):
                verify_hash_val = line.split(':', 1)[1].strip()

        if not all([box_number, ship_date, items, verify_hash_val]):
            return {'valid': False, 'error': 'QR 텍스트 파싱 실패. 올바른 형식인지 확인하세요.'}

        is_valid = verify_hash(box_number, ship_date, items, verify_hash_val)
        return {
            'valid': is_valid,
            'box_number': box_number,
            'ship_date': ship_date,
            'items': items,
            'hash': verify_hash_val,
            'error': None if is_valid else '해시 불일치 - 위변조 가능성 있음'
        }
    except Exception as e:
        return {'valid': False, 'error': f'파싱 오류: {str(e)}'}


init_db()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
