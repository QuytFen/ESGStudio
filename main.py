"""Chạy: python main.py --input bao_cao --out ket_qua."""
import argparse
import csv
from pathlib import Path
import re
import sys
from collections import Counter
from dem_tu import dem_tu
from lam_sach import lam_sach, ngon_ngu
from trich_xuat import trich_xuat, chon_trang
from lda import chay_lda
from xuat_ket_qua import export
from dictionary_store import default_dictionary, load_dictionary, dictionary_groups, fingerprint

def read_csv(path, required):
    with open(path, encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        missing = set(required)-set(reader.fieldnames or [])
        if missing:
            raise ValueError(f'{path}: thiếu cột {sorted(missing)}')
        return [{k: (v or '').strip() for k, v in row.items() if k} for row in reader]

def main():
    # Windows có thể dùng cp1252 khi chuyển hướng đầu ra: luôn xuất UTF-8.
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description='Phân tích công bố ESRS E5 từ PDF cục bộ; không tải báo cáo trên mạng.')
    parser.add_argument('--input', default='bao_cao')
    parser.add_argument('--out', default='ket_qua')
    parser.add_argument('--metadata', default='danh_sach.csv')
    parser.add_argument('--pages', default='trang_thu_cong.csv')
    parser.add_argument('--tesseract', help='Đường dẫn tesseract.exe nếu chưa có trong PATH')
    parser.add_argument('--poppler', help='Tương thích lệnh cũ; bộ đọc PDF tích hợp không cần Poppler')
    parser.add_argument('--exclude-tables', action='store_true', help='Chỉ đếm phần ngoài bảng có đường kẻ. Mặc định tính cả bảng.')
    parser.add_argument('--dictionary', help='Bản từ điển JSON xuất từ app')
    args = parser.parse_args()
    try:
        dictionary = load_dictionary(args.dictionary) if args.dictionary else default_dictionary()
        groups = dictionary_groups(dictionary)
        dictionary_hash = fingerprint(dictionary)
        print(f"Từ điển: {dictionary['name']} · SHA-256: {dictionary_hash}", flush=True)
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    folder = Path(args.input)
    if not folder.is_dir():
        parser.error(f'Không có thư mục {folder.resolve()}')
    files = sorted(p for p in folder.iterdir() if p.suffix.lower()=='.pdf')
    if not files:
        print(f'Chưa có PDF trong {folder.resolve()}. Hãy thêm báo cáo MA_NAM_LOAI.pdf rồi chạy lại.')
        return 2
    try:
        metadata = {}
        for row in read_csv(args.metadata, ['ma','ten_cong_ty','nganh','nam','ky_bao_cao']):
            key = (row['ma'].upper(), row['nam'])
            if key in metadata:
                raise ValueError(f'Metadata trùng mã/năm: {key}')
            metadata[key] = row
        overrides = {}
        if Path(args.pages).exists():
            for row in read_csv(args.pages, ['ma','nam','trang_dau','trang_cuoi']):
                kind = row.get('loai', '').upper()
                if kind and kind not in ('PTBV', 'ESG', 'BCTN'):
                    raise ValueError('Loại báo cáo trong khoảng trang phải là PTBV, ESG hoặc BCTN')
                key = (row['ma'].upper(), row['nam'], kind) if kind else (row['ma'].upper(), row['nam'])
                if key in overrides:
                    raise ValueError(f'Khoảng trang trùng mã/năm: {key}')
                overrides[key] = (int(row['trang_dau']), int(row['trang_cuoi']))
    except (OSError, ValueError) as exc:
        parser.error(str(exc))
    reports, errors = [], []
    for path in files:
        try:
            match = re.fullmatch(r'([A-Za-z0-9]+)_(\d{4})_(PTBV|ESG|BCTN)', path.stem, re.I)
            if not match:
                raise ValueError('Tên file phải là MA_NAM_PTBV/ESG/BCTN.pdf')
            ma, year, kind = match.groups()
            ma, kind = ma.upper(), kind.upper()
            if any(r['id']==f'{ma}_{year}_{kind}' for r in reports):
                raise ValueError('Báo cáo trùng mã/năm/loại')
            meta = metadata.get((ma, year))
            if meta is None:
                raise ValueError(f'Thiếu dòng {ma}/{year} trong danh_sach.csv')
            pages = trich_xuat(path, args.tesseract, args.poppler, include_tables=not args.exclude_tables)
            selected, selection = chon_trang(pages, kind, overrides.get((ma, year, kind), overrides.get((ma, year))))
            raw = '\n'.join(p['text'] for p in selected)
            language = ngon_ngu('\n'.join(p['raw'] for p in pages))
            total = sum(len(lam_sach(page['text']).split()) for page in selected)
            if not total:
                raise ValueError('Không có chữ trong phần đã chọn; kiểm tra OCR và khoảng trang')
            # Đếm độc lập từng trang để không ghép từ/cụm từ qua ranh giới trang.
            page_counts = {p['number']: dem_tu(p['text'], language, groups) for p in selected}
            counts = Counter(dem_tu('', language, groups))
            for values in page_counts.values():
                counts.update(values)
            totals = {g: sum(n for (group, _), n in counts.items() if group==g) for g in ('SYMB','SUBST','E5')}
            report = {**meta, 'ma': ma, 'nam': year, 'loai': kind, 'id': f'{ma}_{year}_{kind}',
                      'ngon_ngu': language, 'pages': selected, 'trang_dau': selected[0]['number'],
                      'trang_cuoi': selected[-1]['number'], 'so_trang': len(selected), 'so_tu': total,
                      'counts': counts, 'page_counts': page_counts,
                      'bo_tu_dien': dictionary['name'], 'ma_tu_dien': dictionary_hash,
                      'pham_vi_van_ban': 'Loại nội dung bảng' if args.exclude_tables else 'Gồm nội dung bảng',
                      'ocr': any(p['ocr'] for p in selected), 'selection': selection,
                      'SUBST_RATIO': totals['SUBST']/(totals['SUBST']+totals['SYMB']) if totals['SUBST']+totals['SYMB'] else None}
            for group, n in totals.items():
                report[group+'_1000'] = n*1000/total
            reports.append(report)
            print(f"{report['id']}: trang {report['trang_dau']}-{report['trang_cuoi']}, {total} từ/âm tiết, {language}, OCR={report['ocr']}; {selection}; {report['pham_vi_van_ban']}", flush=True)
        except Exception as exc:
            # Tiếp tục các PDF khác; mọi lỗi được ghi rõ và trả mã thoát khác 0.
            error = f'LỖI {path.name}: {exc}'
            print(error, file=sys.stderr, flush=True)
            errors.append(error)
    try:
        lda = chay_lda(reports) if reports else {'nhom': {}, 'ghi_chu': 'Không có báo cáo xử lý thành công'}
        export(reports, lda, args.out, errors, dictionary=dictionary)
    except Exception as exc:
        print(f'LỖI LDA/xuất kết quả: {exc}', file=sys.stderr)
        return 1
    print('\nMÃ/NĂM/LOẠI           SỐ TỪ      SYMB/1000   SUBST/1000   E5/1000    SUBST_RATIO')
    for r in reports:
        ratio = 'NA' if r['SUBST_RATIO'] is None else f"{r['SUBST_RATIO']:.2%}"
        print(f"{r['id']:<22} {r['so_tu']:>8} {r['SYMB_1000']:>12.3f} {r['SUBST_1000']:>12.3f} {r['E5_1000']:>10.3f} {ratio:>12}")
    for language, group in lda['nhom'].items():
        print(f"LDA {language}: {group['trang_thai']}")
    print(f'Kết quả: {Path(args.out).resolve()}')
    return 1 if errors else 0

if __name__ == '__main__':
    sys.exit(main())
