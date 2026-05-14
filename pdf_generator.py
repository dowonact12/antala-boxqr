import os
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from qr_generator import build_qr_text, generate_qr_image


def register_fonts():
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "C:/Windows/Fonts/malgun.ttf",
        "C:/Windows/Fonts/gulim.ttc",
    ]
    for fp in font_paths:
        if os.path.exists(fp):
            try:
                pdfmetrics.registerFont(TTFont('Korean', fp))
                return 'Korean'
            except:
                continue
    return 'Helvetica'


def generate_full_pdf(data, photo_bytes=None):
    font_name = register_fonts()
    buf = BytesIO()

    w, h = A4
    c = canvas.Canvas(buf, pagesize=A4)

    # === PAGE 1: Info + QR ===
    mid_y = h / 2
    y = h - 2 * cm

    c.setFont(font_name, 18)
    c.drawString(2 * cm, y, "ANTALA PACKING SLIP")
    y -= 1 * cm

    c.setFont(font_name, 10)
    c.drawString(2 * cm, y, f"Box #: {data['box_number']}")
    c.drawString(10 * cm, y, f"Date: {data['ship_date']}")
    y -= 0.6 * cm
    c.drawString(2 * cm, y, f"Buyer: {data['buyer']}")
    c.drawString(10 * cm, y, f"Invoice: {data['invoice_number']}")
    y -= 0.6 * cm
    c.drawString(2 * cm, y, f"Packed by: {data.get('packed_by', 'Dowon')}")
    if data.get('total_weight'):
        c.drawString(10 * cm, y, f"Weight: {data['total_weight']} kg")
    y -= 0.6 * cm
    if data.get('dimensions'):
        c.drawString(2 * cm, y, f"Dimensions: {data['dimensions']}")
        y -= 0.6 * cm
    if data.get('note'):
        c.drawString(2 * cm, y, f"Note: {data['note']}")
        y -= 0.6 * cm

    y -= 0.5 * cm

    # Items table
    c.setFont(font_name, 10)
    c.drawString(2 * cm, y, "No.")
    c.drawString(3 * cm, y, "Product")
    c.drawString(15 * cm, y, "Qty")
    y -= 0.2 * cm
    c.line(2 * cm, y, 18 * cm, y)
    y -= 0.5 * cm

    c.setFont(font_name, 9)
    total_qty = 0
    for i, item in enumerate(data['items'], 1):
        if y < mid_y + 1 * cm:
            break
        c.drawString(2 * cm, y, str(i))
        c.drawString(3 * cm, y, item['name'][:40])
        qty = int(item['quantity'])
        total_qty += qty
        c.drawString(15 * cm, y, str(qty))
        y -= 0.5 * cm

    y -= 0.2 * cm
    c.line(2 * cm, y, 18 * cm, y)
    y -= 0.5 * cm
    c.setFont(font_name, 10)
    c.drawString(2 * cm, y, f"Total: {total_qty} units")

    # === BOTTOM: QR Code ===
    qr_text = build_qr_text(data)
    qr_img = generate_qr_image(qr_text, box_size=8, border=2)
    qr_buf = BytesIO()
    qr_img.save(qr_buf, format='PNG')
    qr_buf.seek(0)
    img_reader = ImageReader(qr_buf)

    qr_size = 8 * cm
    qr_x = (w - qr_size) / 2
    qr_y = mid_y - qr_size - 1.5 * cm

    c.drawImage(img_reader, qr_x, qr_y, width=qr_size, height=qr_size)

    c.setFont(font_name, 12)
    text_y = qr_y - 0.8 * cm
    c.drawCentredString(w / 2, text_y, f"Box #: {data['box_number']}")
    text_y -= 0.6 * cm
    c.drawCentredString(w / 2, text_y, f"Verify: {data['hash']}")
    text_y -= 0.8 * cm
    c.setFont(font_name, 8)
    c.drawCentredString(w / 2, text_y, "Scan with any QR reader app (not with mobile phone camera)")

    # === PAGE 2: Photo (if exists) ===
    if photo_bytes:
        try:
            c.showPage()
            y = h - 2 * cm
            c.setFont(font_name, 14)
            c.drawString(2 * cm, y, f"PHOTO - Box #: {data['box_number']}")
            y -= 0.5 * cm
            c.setFont(font_name, 9)
            c.drawString(2 * cm, y, f"{data['buyer']} / {data['invoice_number']} / {data['ship_date']}")

            max_w = w - 4 * cm
            max_h = h - 5 * cm
            photo_reader = ImageReader(BytesIO(photo_bytes))
            img_w, img_h = photo_reader.getSize()
            ratio = min(max_w / img_w, max_h / img_h)
            draw_w = img_w * ratio
            draw_h = img_h * ratio
            x_pos = (w - draw_w) / 2
            y_pos = (h - 4 * cm - draw_h) / 2
            c.drawImage(photo_reader, x_pos, y_pos, width=draw_w, height=draw_h)
        except:
            c.drawString(2 * cm, h / 2, "Photo could not be loaded")

    c.save()
    buf.seek(0)
    return buf


def generate_label_pdf(boxes_data):
    font_name = register_fonts()
    buf = BytesIO()

    w, h = A4
    c = canvas.Canvas(buf, pagesize=A4)

    col_w = w / 2
    row_h = h / 3
    qr_size = 5 * cm

    positions = [
        (0, 2), (1, 2),
        (0, 1), (1, 1),
        (0, 0), (1, 0),
    ]

    for idx, data in enumerate(boxes_data[:6]):
        col, row = positions[idx]
        cx = col * col_w + col_w / 2
        cy = row * row_h + row_h / 2

        qr_text = build_qr_text(data)
        qr_img = generate_qr_image(qr_text, box_size=6, border=1)
        qr_buf = BytesIO()
        qr_img.save(qr_buf, format='PNG')
        qr_buf.seek(0)
        img_reader = ImageReader(qr_buf)

        c.drawImage(img_reader, cx - qr_size / 2, cy - qr_size / 2 + 0.5 * cm,
                    width=qr_size, height=qr_size)

        c.setFont(font_name, 8)
        c.drawCentredString(cx, cy - qr_size / 2, data['box_number'])
        c.drawCentredString(cx, cy - qr_size / 2 - 0.4 * cm, f"Verify: {data['hash']}")

    c.save()
    buf.seek(0)
    return buf
