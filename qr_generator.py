import qrcode
from io import BytesIO


def build_qr_text(data):
    lines = [
        "ANTALA PACKING SLIP",
        "===================",
        f"Box #: {data['box_number']}",
        f"Date: {data['ship_date']}",
        f"Buyer: {data['buyer']}",
        f"Invoice: {data['invoice_number']}",
        "",
        "CONTENTS:",
    ]
    total_qty = 0
    for item in data['items']:
        qty = int(item['quantity'])
        total_qty += qty
        lines.append(f"- {item['name']} x {qty}")

    lines.append("")
    summary = f"Total: {total_qty} units"
    if data.get('total_weight'):
        summary += f" / {data['total_weight']}kg"
    lines.append(summary)
    lines.append(f"Packed by: {data.get('packed_by', 'Dowon')}")
    lines.append(f"Verify: {data['hash']}")

    return "\n".join(lines)


def generate_qr_image(text, box_size=10, border=2):
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=box_size,
        border=border,
    )
    qr.add_data(text)
    qr.make(fit=True)
    return qr.make_image(fill_color="black", back_color="white")


def generate_qr_bytes(text, box_size=10, border=2):
    img = generate_qr_image(text, box_size, border)
    buf = BytesIO()
    img.save(buf, format='PNG')
    buf.seek(0)
    return buf
