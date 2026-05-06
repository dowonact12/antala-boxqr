# ANTALA Box QR Tool

화장품 수출 박스 패킹 정보를 QR 코드로 생성하는 도구.
바이어가 QR을 스캔하면 **인터넷 없이도** 박스 내용물이 텍스트로 바로 표시됩니다.

## 설치

```bash
cd ANTALA_BoxQR_Tool
pip install -r requirements.txt
```

## 설정

`.env` 파일을 생성하고 비밀 키를 설정합니다:

```
SECRET_KEY=your-secret-key-here
```

## 실행

```bash
python app.py
```

브라우저에서 `http://localhost:5000` 접속

## 페이지 구성

| 경로 | 기능 |
|------|------|
| `/` | 박스 정보 입력 폼 |
| `/preview/<box_number>` | 미리보기 + PDF 다운로드 |
| `/history` | 발급 이력 검색 |
| `/verify` | QR 텍스트 해시 검증 |

## 핵심 기능

- **QR 데이터 임베드**: URL이 아닌 plain text를 QR에 직접 저장 → 오프라인 스캔 가능
- **위변조 방지**: SHA256 해시 앞 8자리로 진위 검증
- **A4 PDF 출력**: 상단 육안 확인 영역 + 하단 대형 QR
- **라벨 모드**: A4 한 장에 6개 소형 QR (2×3 배치)

## 기술 스택

- Python / Flask
- SQLite (파일 기반 DB)
- qrcode + Pillow (QR 생성)
- ReportLab (PDF 생성)
- Tailwind CSS CDN (프론트엔드)
