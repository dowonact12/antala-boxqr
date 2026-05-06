# ANTALA Box QR Tool

## 프로젝트 목적
화장품 수출 박스 패킹 정보를 QR 코드로 생성. 바이어가 QR 스캔 시 인터넷 없이 plain text로 내용물 확인 가능. 분쟁 대비 위변조 방지 해시 포함.

## 기술 스택
- Backend: Python 3.10+ / Flask
- DB: SQLite (`boxes.db`, 자동 생성)
- QR: `qrcode` + `Pillow`
- PDF: `reportlab`
- Frontend: HTML + Tailwind CDN

## 파일 구조
```
app.py              — Flask 메인 (라우트, 폼 처리)
database.py         — SQLite CRUD, box_number 자동생성
hash_util.py        — SHA256 해시 생성/검증 (.env SECRET_KEY 사용)
qr_generator.py     — QR 텍스트 빌드 + 이미지 생성
pdf_generator.py    — A4 전체 PDF + 라벨(2x3) PDF
templates/          — Jinja2 템플릿 (base, index, preview, history, verify)
output/             — 생성된 PDF 저장 위치
```

## 핵심 로직
- QR에는 URL이 아닌 plain text 직접 임베드 (오프라인 스캔 가능)
- 해시: `SHA256(box_number + ship_date + items_json + SECRET_KEY)[:8]`
- `/verify`에서 QR 텍스트 파싱 후 해시 재계산으로 위변조 검증

## 실행
```bash
pip install -r requirements.txt
python app.py  # → localhost:5000
```

## 다음 작업 후보
- [ ] 바이어별 제품 프리셋 (자주 보내는 조합 저장)
- [ ] 복수 박스 일괄 입력 (같은 인보이스 여러 박스)
- [ ] QR 스캔 로그 (웹 버전 - 바이어가 온라인일 때 스캔 기록)
- [ ] 엑셀/CSV 임포트 기능
- [ ] CIPL 연동 (cipl-auto에서 품목 가져오기)
