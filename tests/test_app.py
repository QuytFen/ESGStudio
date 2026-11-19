"""Kiểm tra đầu vào app và luồng phân tích PDF thực tế."""
import csv
from pathlib import Path
import queue
import tempfile
import unittest
from app import ReportInput, run_analysis, validate_reports, pdf_page_count
from test_pipeline import make_pdf, READY


class AppInputTests(unittest.TestCase):
    def test_validates_conflicts_and_page_ranges(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / 'any name.pdf'
            pdf.touch()
            report = ReportInput(pdf, 'ABC', 'Company', 'Industry', '2024', '2024')
            validate_reports([report])
            with self.assertRaisesRegex(ValueError, 'Trùng mã'):
                validate_reports([report, report])
            report.trang_dau, report.trang_cuoi = '0', '2'
            with self.assertRaisesRegex(ValueError, 'Khoảng trang'):
                validate_reports([report])
            report.trang_dau = ''
            with self.assertRaisesRegex(ValueError, 'Nhập cả'):
                validate_reports([report])

    def test_rejects_conflicting_metadata_but_allows_independent_ranges(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / 'report.pdf'
            pdf.touch()
            a = ReportInput(pdf, 'ABC', 'Company', 'Industry', '2024', '2024')
            b = ReportInput(pdf, 'ABC', 'Other', 'Industry', '2024', '2024', 'ESG')
            with self.assertRaisesRegex(ValueError, 'cùng thông tin'):
                validate_reports([a, b])
            b.ten_cong_ty = a.ten_cong_ty
            b.trang_dau, b.trang_cuoi = '1', '2'
            validate_reports([a, b])

    def test_page_count_and_upper_bound(self):
        with tempfile.TemporaryDirectory() as temp:
            pdf = Path(temp) / 'report.pdf'
            make_pdf(pdf)
            self.assertEqual(pdf_page_count(pdf), 6)
            report = ReportInput(pdf, 'ABC', 'Company', 'Testing', '2024', '2024',
                                 trang_dau='1', trang_cuoi='7', so_trang_pdf=6)
            with self.assertRaisesRegex(ValueError, 'vượt quá'):
                validate_reports([report])

    @unittest.skipUnless(READY, 'Cần cài requirements.txt')
    def test_worker_accepts_original_filename_and_preserves_pdf(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdf = root / 'Báo cáo công ty bất kỳ.pdf'
            make_pdf(pdf)
            original = pdf.read_bytes()
            report = ReportInput(pdf, 'ABC', 'Company', 'Testing', '2024', '2024', trang_dau='1', trang_cuoi='2')
            events = queue.Queue()
            out = root / 'results'
            run_analysis([report], out, '', '', events)
            messages = []
            while not events.empty():
                messages.append(events.get_nowait())
            self.assertEqual(messages[-1], ('done', (0, out)), messages)
            self.assertEqual(pdf.read_bytes(), original)
            with (out / 'chi_so_doanh_nghiep.csv').open(encoding='utf-8-sig', newline='') as stream:
                row = next(csv.DictReader(stream))
            self.assertEqual((row['ma'], row['nam'], row['so_trang']), ('ABC', '2024', '2'))
            self.assertTrue((out / 'dau_vao' / 'danh_sach.csv').exists())

    @unittest.skipUnless(READY, 'Cần cài requirements.txt')
    def test_worker_uses_separate_ranges_for_same_company(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdf = root / 'report.pdf'
            make_pdf(pdf)
            a = ReportInput(pdf, 'ABC', 'Company', 'Testing', '2024', '2024',
                            'PTBV', '2', '3', 6)
            b = ReportInput(pdf, 'ABC', 'Company', 'Testing', '2024', '2024',
                            'BCTN', '5', '6', 6)
            events = queue.Queue()
            out = root / 'results'
            run_analysis([a, b], out, '', '', events)
            messages = []
            while not events.empty():
                messages.append(events.get_nowait())
            self.assertEqual(messages[-1], ('done', (0, out)), messages)
            with (out / 'chi_so_doanh_nghiep.csv').open(encoding='utf-8-sig', newline='') as stream:
                rows = {row['loai']: row for row in csv.DictReader(stream)}
            self.assertEqual((rows['PTBV']['trang_dau'], rows['PTBV']['trang_cuoi']), ('2', '3'))
            self.assertEqual((rows['BCTN']['trang_dau'], rows['BCTN']['trang_cuoi']), ('5', '6'))
