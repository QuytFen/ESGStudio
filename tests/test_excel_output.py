import csv
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from openpyxl import load_workbook
from excel_output import EXCEL_NAME, create_excel, open_excel


class ExcelOutputTests(unittest.TestCase):
    def test_converts_saved_results_preserving_numbers_and_text(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            with (root / 'google_sheet.tsv').open('w', encoding='utf-8-sig', newline='') as stream:
                writer = csv.writer(stream, delimiter='\t')
                writer.writerow(['STT', 'Tên công ty'])
                writer.writerow([1, '=Công ty kiểm thử'])
            (root / 'chi_so_doanh_nghiep.csv').write_text(
                'ma,nam,SUBST_RATIO,E5_1000\nABC,2024,0.25,12.345\nDEF,2024,,0\n', encoding='utf-8')
            path = create_excel(root)
            self.assertEqual(path.name, EXCEL_NAME)
            book = load_workbook(path)
            try:
                self.assertEqual(book.sheetnames, ['Tổng hợp', 'Chỉ số'])
                self.assertEqual(book['Tổng hợp']['B2'].value, '=Công ty kiểm thử')
                self.assertEqual(book['Tổng hợp']['B2'].data_type, 's')
                sheet = book['Chỉ số']
                self.assertEqual(sheet['C2'].value, 0.25)
                self.assertEqual(sheet['C2'].number_format, '0.0%')
                self.assertIsNone(sheet['C3'].value)
                self.assertEqual(sheet['D3'].value, 0)
                self.assertEqual(sheet.freeze_panes, 'A2')
                self.assertEqual(sheet.auto_filter.ref, 'A1:D3')
            finally:
                book.close()

    def test_opens_excel_executable_instead_of_default_tsv_app(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / EXCEL_NAME
            path.touch()
            with patch('excel_output.find_excel', return_value=Path('C:/Office/EXCEL.EXE')), \
                 patch('excel_output.subprocess.Popen') as launch, patch('excel_output.os.startfile') as default:
                open_excel(path)
                self.assertEqual(launch.call_args.args[0], [str(Path('C:/Office/EXCEL.EXE')), str(path.resolve())])
                default.assert_not_called()
