"""Chạy thủ công: python tests/check_packaged_app.py DUONG_DAN_EXE."""
import csv
import json
import os
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont
from test_pipeline import make_pdf


def check(executable):
    executable = Path(executable).resolve()
    root = Path(__file__).resolve().parents[1] / 'build' / 'qa' / executable.parent.name
    root.mkdir(parents=True, exist_ok=True)
    inputs = root / 'pdfs'
    inputs.mkdir(exist_ok=True)
    make_pdf(inputs / 'TEST_2024_PTBV.pdf')
    with Image.new('RGB', (1800, 700), 'white') as image:
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('C:/Windows/Fonts/arial.ttf', 42)
        for index, text in enumerate(['Chất thải nguy hại được xử lý và tái chế.',
                                      'Chi phí công nghệ và thiết bị xử lý chất thải.',
                                      'Waste recycling and circular materials recovery.']):
            draw.text((60, 80 + index * 100), text, font=font, fill='black')
        image.save(inputs / 'SCAN_2024_ESG.pdf', 'PDF', resolution=150)
    metadata = root / 'metadata.csv'
    metadata.write_text('ma,ten_cong_ty,nganh,nam,ky_bao_cao\nTEST,Fixture company,Testing,2024,2024\nSCAN,Scan fixture,Testing,2024,2024\n', encoding='utf-8')
    pages = root / 'pages.csv'
    pages.write_text('ma,nam,loai,trang_dau,trang_cuoi\nTEST,2024,PTBV,1,6\nSCAN,2024,ESG,1,1\n', encoding='utf-8')
    output = root / 'results'
    log = root / 'worker.log'
    env = os.environ.copy()
    # Không dựa vào Python, Tesseract hoặc công cụ nào trong PATH của máy build.
    env['PATH'] = str(Path(os.environ.get('SystemRoot', 'C:/Windows')) / 'System32')
    env.pop('PYTHONPATH', None)
    env.pop('TESSDATA_PREFIX', None)
    env['ESG_STUDIO_DATA_DIR'] = str(root / 'user_data')
    process = subprocess.run([str(executable), '--pipeline', str(log), '--input', str(inputs),
                              '--out', str(output), '--metadata', str(metadata), '--pages', str(pages)],
                             cwd=root, env=env, timeout=240)
    if process.returncode:
        raise RuntimeError(log.read_text(encoding='utf-8') if log.exists() else f'Exit {process.returncode}; no worker log')
    with (output / 'chi_so_doanh_nghiep.csv').open(encoding='utf-8-sig', newline='') as stream:
        rows = {r['ma']: r for r in csv.DictReader(stream)}
    assert rows['TEST']['so_tu'] == '288', rows
    assert rows['SCAN']['ngon_ngu'] == 'vi', rows
    assert rows['SCAN']['pham_vi_van_ban'] == 'Gồm nội dung bảng', rows
    lda = json.loads((output / 'chu_de_lda.json').read_text(encoding='utf-8'))
    assert lda['nhom']['en']['trang_thai'] == 'OK', lda
    from openpyxl import load_workbook
    book = load_workbook(output / 'ket_qua_phan_tich.xlsx', read_only=True)
    assert 'Từ khóa theo trang' in book.sheetnames
    book.close()
    print(f'PASS: {executable.name} — PDF text, OCR vie+eng, LDA, XLSX; PATH không có Python/Tesseract', flush=True)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    check(sys.argv[1])
