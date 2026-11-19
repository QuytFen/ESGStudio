"""PDF tổng hợp chỉ phục vụ kiểm thử, không phải dữ liệu doanh nghiệp."""
import csv
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch, MagicMock

READY = all(importlib.util.find_spec(m) for m in ('pdfplumber','sklearn','pytesseract','pypdfium2'))

def make_pdf(path):
    """Tạo PDF chữ tiếng Anh bằng thư viện chuẩn, hai nhóm chủ đề x 3 trang."""
    clusters = [
        'materials packaging recycled waste landfill hazardous anaerobic incineration recovery circular durable maintenance',
        'governance management stakeholders policy development assessment awareness compliance benefits research education coordination',
    ]
    objects = [b'<< /Type /Catalog /Pages 2 0 R >>', b'', b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>']
    kids = []
    for i in range(6):
        page_id = len(objects)+1
        kids.append(f'{page_id} 0 R')
        objects.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents {page_id+1} 0 R >>'.encode())
        lines = clusters[i//3].split()
        content = 'BT /F1 12 Tf 40 750 Td 18 TL\n'
        for _ in range(4):
            content += '('+' '.join(lines[:6])+') Tj T*\n'
            content += '('+' '.join(lines[6:])+') Tj T*\n'
        content += 'ET'
        data = content.encode('ascii')
        objects.append(f'<< /Length {len(data)} >>\nstream\n'.encode()+data+b'\nendstream')
    objects[1] = f"<< /Type /Pages /Count 6 /Kids [{' '.join(kids)}] >>".encode()
    data, offsets = b'%PDF-1.4\n', [0]
    for i, obj in enumerate(objects, 1):
        offsets.append(len(data))
        data += f'{i} 0 obj\n'.encode()+obj+b'\nendobj\n'
    xref = len(data)
    data += f'xref\n0 {len(objects)+1}\n0000000000 65535 f \n'.encode()
    data += b''.join(f'{offset:010d} 00000 n \n'.encode() for offset in offsets[1:])
    data += f'trailer\n<< /Size {len(objects)+1} /Root 1 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()
    path.write_bytes(data)

@unittest.skipUnless(READY, 'Cần cài requirements.txt để chạy kiểm thử PDF/LDA')
class PipelineTests(unittest.TestCase):
    def test_pdf_to_all_outputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            (root/'bao_cao').mkdir()
            make_pdf(root/'bao_cao'/'TEST_2024_PTBV.pdf')
            (root/'danh_sach.csv').write_text('ma,ten_cong_ty,nganh,nam,ky_bao_cao\nTEST,Fixture company,Testing,2024,2024\n', encoding='utf-8')
            process = subprocess.run([sys.executable, str(Path(__file__).resolve().parents[1]/'main.py'), '--input','bao_cao','--out','ket_qua'], cwd=root, capture_output=True, text=True, encoding='utf-8')
            self.assertEqual(process.returncode, 0, process.stderr+process.stdout)
            self.assertIn('TEST_2024_PTBV', process.stdout)
            out = root/'ket_qua'
            self.assertEqual(len(list(out.iterdir())), 9)
            with (out/'chi_so_doanh_nghiep.csv').open(encoding='utf-8-sig', newline='') as f:
                report = next(csv.DictReader(f))
            self.assertEqual(report['so_tu'], '288')
            self.assertEqual(report['so_trang'], '6')
            self.assertEqual(report['ngon_ngu'], 'en')
            self.assertAlmostEqual(float(report['E5_1000']), 500)
            self.assertEqual(report['pham_vi_van_ban'], 'Gồm nội dung bảng')
            with (out/'tu_khoa_theo_trang.csv').open(encoding='utf-8-sig', newline='') as f:
                page_counts = list(csv.DictReader(f))
            with (out/'tan_suat_tu_khoa.csv').open(encoding='utf-8-sig', newline='') as f:
                totals = list(csv.DictReader(f))
            for row in totals:
                subtotal = sum(int(p['so_lan']) for p in page_counts
                               if (p['nhom'], p['tu_khoa']) == (row['nhom'], row['tu_khoa']))
                self.assertEqual(subtotal, int(row['so_lan']))
            lda = json.loads((out/'chu_de_lda.json').read_text(encoding='utf-8'))
            self.assertEqual(len(lda['nhom']['en']['thu_k']), 9)
            self.assertIn('TEST_2024_PTBV', lda['nhom']['en']['ty_trong_bao_cao'])
            with (out/'google_sheet.tsv').open(encoding='utf-8-sig', newline='') as f:
                rows = list(csv.reader(f, delimiter='\t'))
            self.assertEqual([len(row) for row in rows], [21,21])
            self.assertEqual(rows[1][-3:], ['','',''])

    def test_ocr_configuration(self):
        from trich_xuat import trich_xuat
        page = MagicMock()
        page.extract_text.return_value = ''
        pdf = MagicMock()
        pdf.__enter__.return_value.pages = [page]
        image = page.to_image.return_value.original
        with patch('pdfplumber.open', return_value=pdf), patch('trich_xuat.configure_tesseract', return_value='') as configure, patch('pytesseract.image_to_string', return_value='chất thải tái chế') as ocr:
            result = trich_xuat(Path('scan.pdf'))
        self.assertTrue(result[0]['ocr'])
        page.to_image.assert_called_once_with(resolution=200)
        image.close.assert_called_once()
        self.assertEqual(ocr.call_args.kwargs['lang'], 'vie+eng')

    def test_table_text_is_counted_by_default_and_exclusion_is_explicit(self):
        from trich_xuat import trich_xuat
        from dem_tu import dem_tu
        page = MagicMock()
        page.extract_text.return_value = 'assessment ' * 35
        page.find_tables.return_value = [MagicMock(bbox=(0, 0, 600, 800))]
        page.filter.return_value.extract_text.return_value = 'outside table'
        pdf = MagicMock()
        pdf.__enter__.return_value.pages = [page]
        with patch('pdfplumber.open', return_value=pdf):
            included = trich_xuat(Path('table.pdf'))
            page.find_tables.assert_not_called()
            excluded = trich_xuat(Path('table.pdf'), include_tables=False)
        self.assertEqual(dem_tu(included[0]['text'], 'en')['SYMB', 'Assessment'], 35)
        self.assertEqual(dem_tu(excluded[0]['text'], 'en')['SYMB', 'Assessment'], 0)

    def test_vietnamese_lda(self):
        from lda import chay_lda
        clusters = [
            'chất thải nguy hại tái chế nguyên liệu vật liệu bao bì thu hồi chôn lấp bảo trì độ bền tuổi thọ kỵ khí',
            'quản trị quản lý chính sách phát triển nhận thức giáo dục nghiên cứu tuân thủ phối hợp giám sát đánh giá toàn diện',
        ]
        reports = [{'id': f'VI{i}', 'ngon_ngu':'vi', 'pages':[{'text': (text+' ')*3} for _ in range(3)]}
                   for i,text in enumerate(clusters)]
        result = chay_lda(reports)['nhom']['vi']
        self.assertEqual(result['trang_thai'], 'OK')
        self.assertEqual(len(result['thu_k']), 9)
        self.assertAlmostEqual(sum(result['ty_trong_bao_cao']['VI0']), 1)

if __name__=='__main__': unittest.main()
