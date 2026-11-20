import copy
import csv
import json
from pathlib import Path
import queue
import tempfile
import unittest

from dictionary_store import (default_dictionary, dictionary_groups, validate_dictionary,
    save_dictionary, load_dictionary, export_dictionary_excel, import_dictionary_excel, fingerprint)
from dem_tu import dem_tu


def custom_dictionary():
    return {'version': 1, 'name': 'Ngành nhựa', 'entries': [
        {'group': 'E5', 'name': 'Nhựa', 'english': ['recycled plastic'],
         'vietnamese': ['nhựa tái sinh'], 'pattern': '', 'enabled': True},
        {'group': 'SYMB', 'name': 'Tạm tắt', 'english': ['plastic'],
         'vietnamese': ['nhựa'], 'pattern': '', 'enabled': False}]}


class DictionaryTests(unittest.TestCase):
    def test_default_count_parity_for_both_languages(self):
        data = default_dictionary()
        groups = dictionary_groups(data)
        for language in ('en', 'vi'):
            text = ' '.join(e['name'] + ' ' + ' '.join(e['vietnamese']) for e in data['entries'])
            text += ' policies assessments recycling pre-assessment nonrenewable renewable re-use'
            self.assertEqual(dem_tu(text, language), dem_tu(text, language, groups))

    def test_custom_literals_disabled_and_longest_match(self):
        data = custom_dictionary()
        data['entries'].append({'group': 'SUBST', 'name': 'Ngắn', 'english': ['plastic'],
            'vietnamese': ['nhựa'], 'pattern': '', 'enabled': True})
        groups = dictionary_groups(data)
        for language, text in [('en', 'Recycled plastic plastic'), ('vi', 'nhựa tái sinh nhựa')]:
            counts = dem_tu(text, language, groups)
            self.assertEqual(counts, {('E5', 'Nhựa'): 1, ('SUBST', 'Ngắn'): 1})

    def test_validation_and_warnings(self):
        data = custom_dictionary()
        other = copy.deepcopy(data['entries'][0])
        other.update(group='SUBST', name='Khác')
        data['entries'].append(other)
        self.assertTrue(validate_dictionary(data))
        data['entries'].append(copy.deepcopy(other))
        with self.assertRaises(ValueError):
            validate_dictionary(data)
        for pattern in ('[', 'a*'):
            data = custom_dictionary()
            data['entries'][0]['pattern'] = pattern
            with self.assertRaises(ValueError):
                validate_dictionary(data)

    def test_json_excel_roundtrip_and_formula_text(self):
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            data = default_dictionary()
            data['name'] = '=Bộ cá nhân'
            save_dictionary(root / 'dictionary.json', data)
            self.assertEqual(load_dictionary(root / 'dictionary.json'), data)
            export_dictionary_excel(root / 'dictionary.xlsx', data)
            loaded = import_dictionary_excel(root / 'dictionary.xlsx')
            self.assertEqual(loaded['entries'], data['entries'])
            book = load_workbook(root / 'dictionary.xlsx')
            self.assertEqual(book.sheetnames, ['Hướng dẫn', 'Từ điển'])
            self.assertEqual(book.active.title, 'Hướng dẫn')
            self.assertEqual(book['Hướng dẫn']['A1'].data_type, 's')
            self.assertEqual(book['Từ điển'].max_row, len(data['entries']) + 1)
            for row, field in enumerate(('nhom', 'ten', 'tieng_anh', 'tieng_viet', 'bat', 'mau_anh_nang_cao'), 7):
                self.assertEqual(book['Hướng dẫn'].cell(row, 1).value, field)
            self.assertIn('evaluated', book['Hướng dẫn']['C16'].value)
            book.close()

    def test_worker_uses_custom_dictionary_and_keeps_snapshot(self):
        from app import ReportInput, run_analysis
        from test_pipeline import make_pdf
        from openpyxl import load_workbook
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            pdf = root / 'report.pdf'
            make_pdf(pdf)
            data = custom_dictionary()
            data['entries'][0]['english'] = ['materials']
            data['entries'][0]['vietnamese'] = ['vật liệu']
            events = queue.Queue()
            out = root / 'out'
            report = ReportInput(pdf, 'ABC', 'Company', 'Testing', '2024', '2024', trang_dau='1', trang_cuoi='1')
            run_analysis([report], out, '', '', events, dictionary=data)
            messages = []
            while not events.empty():
                messages.append(events.get_nowait())
            self.assertEqual(messages[-1], ('done', (0, out)), messages)
            self.assertEqual(load_dictionary(out / 'tu_dien_da_dung.json'), data)
            with (out / 'tan_suat_tu_khoa.csv').open(encoding='utf-8-sig') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['tu_khoa'], 'Nhựa')
            self.assertEqual(rows[0]['so_lan'], '4')
            book = load_workbook(out / 'ket_qua_phan_tich.xlsx')
            sheet = book['Chỉ số']
            values = dict(zip((c.value for c in sheet[1]), (c.value for c in sheet[2])))
            self.assertEqual(values['bo_tu_dien'], data['name'])
            self.assertEqual(values['ma_tu_dien'], fingerprint(data))
            book.close()
            self.assertIn('[trang 1]', (out / 'bao_cao_kiem_tra.txt').read_text(encoding='utf-8'))
