import csv
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from test_pipeline import READY, make_pdf


@unittest.skipUnless(READY, 'Cần cài requirements.txt')
class EntryPointTests(unittest.TestCase):
    def test_worker_entry_writes_utf8_log_without_starting_gui(self):
        entry = Path(__file__).resolve().parents[1] / 'app_entry.py'
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / 'pdf'
            source.mkdir()
            make_pdf(source / 'TEST_2024_PTBV.pdf')
            metadata = root / 'metadata.csv'
            metadata.write_text('ma,ten_cong_ty,nganh,nam,ky_bao_cao\nTEST,Công ty kiểm thử,Testing,2024,2024\n', encoding='utf-8')
            pages = root / 'pages.csv'
            pages.write_text('ma,nam,trang_dau,trang_cuoi\nTEST,2024,1,2\n', encoding='utf-8')
            out, log = root / 'results', root / 'worker.log'
            process = subprocess.run([sys.executable, str(entry), '--pipeline', str(log),
                                      '--input', str(source), '--out', str(out),
                                      '--metadata', str(metadata), '--pages', str(pages)], cwd=root, timeout=90)
            self.assertEqual(process.returncode, 0, log.read_text(encoding='utf-8'))
            self.assertIn('Gồm nội dung bảng', log.read_text(encoding='utf-8'))
            with (out / 'chi_so_doanh_nghiep.csv').open(encoding='utf-8-sig', newline='') as stream:
                self.assertEqual(next(csv.DictReader(stream))['so_trang'], '2')
