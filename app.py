import os
from io import BytesIO
from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify
from dotenv import load_dotenv
from database import init_db, save_box, get_box, get_box_by_hash, get_box_photo, get_all_boxes, generate_box_number
from hash_util import generate_hash
from qr_generator import build_qr_text, generate_qr_bytes
from pdf_generator import generate_full_pdf, generate_label_pdf

load_dotenv()

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(__name__,
            template_folder=os.path.join(BASE_DIR, 'templates'),
            static_folder=os.path.join(BASE_DIR, 'static'))
app.secret_key = os.getenv('SECRET_KEY', 'dev')

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
        'photo_data': None,
        'photo_ext': None,
    }

    # Handle photo upload
    photo = request.files.get('photo')
    if photo and photo.filename and allowed_file(photo.filename):
        ext = photo.filename.rsplit('.', 1)[1].lower()
        data['photo_data'] = photo.read()
        data['photo_ext'] = ext

    # Generate hash
    data['hash'] = generate_hash(data['box_number'], data['ship_date'], data['items'])

    # Save to DB
    save_box(data)

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
    data = get_box(box_number)
    if not data:
        return "Box not found", 404
    photo_bytes, _ = get_box_photo(box_number)
    buf = generate_full_pdf(data, photo_bytes=photo_bytes)
    return send_file(buf, as_attachment=True, download_name=f"{box_number}.pdf", mimetype='application/pdf')


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
    buf = generate_label_pdf(boxes)
    return send_file(buf, as_attachment=True, download_name="labels.pdf", mimetype='application/pdf')


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
    photo_bytes, photo_ext = get_box_photo(box_number)
    if not photo_bytes:
        return "No photo", 404
    mimetype = f'image/{"jpeg" if photo_ext == "jpg" else photo_ext}'
    return send_file(BytesIO(photo_bytes), mimetype=mimetype)


@app.route('/history')
def history():
    search = request.args.get('q', '')
    boxes = get_all_boxes(search if search else None)
    return render_template('history.html', boxes=boxes, search=search)


@app.route('/verify', methods=['GET', 'POST'])
def verify():
    result = None
    code = ''
    if request.method == 'POST':
        code = request.form.get('code', '').strip().lower()
        if code:
            data = get_box_by_hash(code)
            if data:
                result = {'valid': True, 'data': data}
            else:
                result = {'valid': False}
    return render_template('verify.html', result=result, code=code)


@app.route('/v/<code>')
def verify_direct(code):
    data = get_box_by_hash(code.strip().lower())
    if data:
        return render_template('verify.html', result={'valid': True, 'data': data}, code=code)
    return render_template('verify.html', result={'valid': False}, code=code)


try:
    init_db()
except Exception:
    pass

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
