import csv
import tempfile
import unittest
import unicodedata
from pathlib import Path
from dem_tu import dem_tu
from trich_xuat import chon_trang
from tu_dien import GROUPS
from xuat_ket_qua import export, HEADERS

class CountingTests(unittest.TestCase):
    TEXT = 'Chất thải nguy hại được xử lý, chi phí tái chế, phía công ty thu phí'

    def test_required_counts(self):
        result = dem_tu(self.TEXT, 'vi')
        for key in [('E5','Waste'),('E5','Hazardous'),('SUBST','Treatment'),('SUBST','Cost'),('E5','Recycle'),('SUBST','Charge')]:
            self.assertEqual(result[key], 1, key)
        self.assertEqual(sum(result.values()), 6)

    def test_nfd(self):
        self.assertEqual(dem_tu(self.TEXT, 'vi'), dem_tu(unicodedata.normalize('NFD', self.TEXT), 'vi'))

    def test_longest_across_groups(self):
        counts = dem_tu('đánh giá sơ bộ, tái sản xuất, không tái tạo, tuần hoàn lại, lệ phí, được phối hợp', 'vi')
        for key in [('SYMB','Assessment'),('SYMB','Production'),('E5','Renewable'),('E5','Circular'),('SUBST','Charge'),('SYMB','Coordination')]:
            self.assertEqual(counts[key], 0, key)
        self.assertEqual(sum(counts.values()), 6)

    def test_english(self):
        counts = dem_tu('pre-assessments assessments materials non-renewable renewables re-use recycled technologies utilization utilisation costly', 'en')
        self.assertEqual(counts['SYMB','Pre-assessment'], 1)
        self.assertEqual(counts['SYMB','Assessment'], 1)
        self.assertEqual(counts['E5','Renewable'], 1)
        self.assertEqual(counts['SUBST','Cost'], 0)
        self.assertEqual(counts['SYMB','Utilization'], 1)
        self.assertEqual(counts['SUBST','Utilisation'], 1)
        self.assertEqual(counts['SUBST','Technology'], 1)

    def test_dictionary_sizes(self):
        self.assertEqual([len(v) for v in GROUPS.values()], [25,14,27])

class PageTests(unittest.TestCase):
    def test_toc_and_financial_boundary(self):
        pages = [{'raw': t, 'number': i+1} for i,t in enumerate([
            'MỤC LỤC\nPHÁT TRIỂN BỀN VỮNG ........ 40', 'BÁO CÁO PHÁT TRIỂN BỀN VỮNG\nNội dung',
            'Nội dung chương', 'BÁO CÁO TÀI CHÍNH\nThông tin'])]
        chosen, _ = chon_trang(pages, 'BCTN')
        self.assertEqual([p['number'] for p in chosen], [2,3])
        chosen, _ = chon_trang(pages, 'BCTN', (1,4))
        self.assertEqual(len(chosen), 4)
        with self.assertRaises(ValueError): chon_trang(pages, 'BCTN', (0,5))
        with self.assertRaises(ValueError): chon_trang([{'raw': 'không có tiêu đề'}], 'BCTN')

    def test_empty_exports_have_21_columns(self):
        with tempfile.TemporaryDirectory() as temp:
            export([], {'nhom': {}}, temp, [])
            with open(Path(temp)/'google_sheet.tsv', encoding='utf-8-sig', newline='') as f:
                self.assertEqual(next(csv.reader(f, delimiter='\t')), HEADERS)
                self.assertEqual(len(HEADERS), 21)

    def test_one_company_row_and_report_priority(self):
        counts = dem_tu('', 'en')
        base = {'ma':'ABC', 'ten_cong_ty':'Company\tABC\nname', 'nganh':'Testing',
                'ngon_ngu':'en', 'pages':[], 'trang_dau':1, 'trang_cuoi':2,
                'so_trang':2, 'so_tu':100, 'counts':counts, 'ocr':False,
                'selection':'toàn bộ báo cáo', 'SUBST_RATIO':None,
                'SYMB_1000':0, 'SUBST_1000':0, 'E5_1000':0}
        reports = [{**base,'nam':year,'ky_bao_cao':year,'loai':kind,'id':f'ABC_{year}_{kind}'}
                   for year,kind in [('2023','PTBV'),('2024','ESG'),('2024','PTBV')]]
        lda = {'nhom':{'en':{'chu_de':[], 'ty_trong_bao_cao':{}}}}
        with tempfile.TemporaryDirectory() as temp:
            export(reports, lda, temp, [])
            with open(Path(temp)/'google_sheet.tsv', encoding='utf-8-sig', newline='') as f:
                rows = list(csv.reader(f, delimiter='\t'))
            self.assertEqual(len(rows), 2)
            self.assertEqual(len(rows[1]), 21)
            self.assertIn('PTBV 2024', rows[1][2])
            self.assertIn('không xác định', rows[1][16])
            self.assertNotIn('\n', rows[1][2])
            self.assertNotIn('\t', rows[1][2])

if __name__=='__main__': unittest.main()
