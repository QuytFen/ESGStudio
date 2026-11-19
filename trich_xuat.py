"""Trích chữ toàn trang, tùy chọn bỏ bảng, OCR và chọn phần PTBV."""
import re
import unicodedata
from ocr_runtime import configure_tesseract

START = ['báo cáo phát triển bền vững', 'sustainability report', 'sustainability commitment', 'phát triển bền vững']
END = ['báo cáo tài chính', 'financial statements', 'bảng cân đối kế toán', 'balance sheet', 'independent auditor']

def trich_xuat(path, tesseract=None, poppler=None, include_tables=True):
    import pdfplumber
    pages = []
    with pdfplumber.open(path) as pdf:
        for index, page in enumerate(pdf.pages, 1):
            raw = page.extract_text() or ''
            ocr = len(raw.split()) < 30
            if ocr:
                import pytesseract
                config = configure_tesseract(tesseract)
                # pdfplumber dùng PDFium đi kèm thư viện, không cần Poppler/PATH.
                image = page.to_image(resolution=200).original
                try:
                    raw = pytesseract.image_to_string(image, lang='vie+eng', config=config)
                finally:
                    image.close()
                prose = raw  # Bảng OCR không có tọa độ đáng tin cậy: ghi cờ để kiểm tra.
            elif include_tables:
                prose = raw
            else:
                tables = page.find_tables()
                boxes = [t.bbox for t in tables]
                prose = page.filter(lambda obj: not any(
                    obj.get('x0', -1) >= x0 and obj.get('x1', -1) <= x1
                    and obj.get('top', -1) >= top and obj.get('bottom', -1) <= bottom
                    for x0, top, x1, bottom in boxes)).extract_text() or ''
            pages.append({'number': index, 'raw': raw, 'text': prose, 'ocr': ocr})
    return pages

def chon_trang(pages, kind, override=None):
    if not pages:
        raise ValueError('PDF không có trang.')
    if override:
        start, end = override
        if not 1 <= start <= end <= len(pages):
            raise ValueError(f'Khoảng trang thủ công {start}-{end} không hợp lệ (PDF có {len(pages)} trang).')
        return pages[start-1:end], 'thủ công'
    if kind != 'BCTN':
        return pages, 'toàn bộ báo cáo'
    def headings(page):
        lines = unicodedata.normalize('NFC', page['raw']).lower().splitlines()
        # Tránh mục lục và các câu văn chỉ nhắc đến phát triển bền vững.
        return [line.strip() for line in lines[:18] if len(line.strip()) <= 110
                and not re.search(r'\.{2,}|\d\s*$', line)]
    start = next((i for i, p in enumerate(pages) if any(
        re.match(re.escape(s) + r'\b', h) for h in headings(p) for s in START)), None)
    if start is None:
        raise ValueError('Không tìm được chương PTBV; hãy khai báo trang_thu_cong.csv.')
    end = next((i for i in range(start+1, len(pages)) if any(
        re.match(re.escape(s) + r'\b', h) for h in headings(pages[i]) for s in END)), len(pages))
    return pages[start:end], 'tự động; cần kiểm tra khoảng trang'
