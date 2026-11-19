"""Chạy kiểm tra Tk trên Windows với ESG_GUI_TESTS=1, cửa sổ luôn ẩn."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from app import ESGApp
from test_pipeline import make_pdf


@unittest.skipUnless(os.environ.get('ESG_GUI_TESTS') == '1', 'Cần phiên Tk trên Windows')
class PageControlTests(unittest.TestCase):
    def test_defaults_limits_file_switch_and_busy_state(self):
        from PIL import Image
        with tempfile.TemporaryDirectory() as temp:
            first = Path(temp) / 'six_pages.pdf'
            second = Path(temp) / 'one_page.pdf'
            make_pdf(first)
            with Image.new('RGB', (100, 100), 'white') as image:
                image.save(second, 'PDF')
            app = ESGApp(session_path=None)
            app.withdraw()
            try:
                self.assertEqual(str(app.page_controls['trang_dau']['state']), 'disabled')
                with patch('app.filedialog.askopenfilenames', return_value=(str(first), str(second))):
                    app._add()
                app.update()
                first_id, second_id = app.files.get_children()
                self.assertEqual(app.fields['trang_dau'].get(), '1')
                self.assertEqual(app.fields['trang_cuoi'].get(), '6')
                self.assertEqual(tuple(map(int, app.page_controls['trang_dau']['values'])), tuple(range(1, 7)))
                self.assertEqual(str(app.page_controls['trang_dau']['state']), 'readonly')
                app.fields['trang_cuoi'].set('2')
                app.fields['trang_dau'].set('4')
                self.assertEqual(app.fields['trang_cuoi'].get(), '4')
                self.assertEqual(tuple(map(int, app.page_controls['trang_cuoi']['values'])), (4, 5, 6))
                app.fields['trang_dau'].set('2')
                self.assertEqual(app.fields['trang_cuoi'].get(), '4')
                self.assertEqual(tuple(map(int, app.page_controls['trang_cuoi']['values'])), (2, 3, 4, 5, 6))
                app.fields['trang_dau'].set('99')
                self.assertEqual((app.fields['trang_dau'].get(), app.fields['trang_cuoi'].get()), ('6', '6'))
                app.fields['trang_dau'].set('2')
                app.fields['trang_cuoi'].set('5')
                app.files.selection_set(second_id)
                app.update()
                self.assertEqual((app.fields['trang_dau'].get(), app.fields['trang_cuoi'].get()), ('1', '1'))
                self.assertEqual(tuple(map(int, app.page_controls['trang_cuoi']['values'])), (1,))
                app.files.selection_set(first_id)
                app.update()
                self.assertEqual((app.fields['trang_dau'].get(), app.fields['trang_cuoi'].get()), ('2', '5'))
                app._set_busy(True)
                self.assertEqual(str(app.page_controls['trang_cuoi']['state']), 'disabled')
                app._set_busy(False)
                self.assertEqual(str(app.page_controls['trang_cuoi']['state']), 'readonly')
            finally:
                app.destroy()
