import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from app import ESGApp
from session_store import load_session
from test_pipeline import make_pdf


@unittest.skipUnless(os.environ.get('ESG_GUI_TESTS') == '1', 'Cần phiên Tk trên Windows')
class SessionUITests(unittest.TestCase):
    def create_app(self, path):
        app = ESGApp(session_path=path)
        app.withdraw()
        def cleanup():
            try:
                if app.winfo_exists():
                    app.destroy()
            except tk.TclError:
                pass
        self.addCleanup(cleanup)
        return app

    def test_close_and_reopen_restores_files_inputs_pages_settings_and_results(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            state = root / 'session.json'
            first, second = root / 'first.pdf', root / 'second.pdf'
            make_pdf(first)
            make_pdf(second)
            app = self.create_app(state)
            with patch('app.filedialog.askopenfilenames', return_value=(str(first), str(second))):
                app._add()
            app.update()
            first_id, second_id = app.files.get_children()
            app.fields['ma'].set('ABC')
            app.fields['ten_cong_ty'].set('Công ty thứ nhất')
            app.fields['trang_dau'].set('2')
            app.fields['trang_cuoi'].set('4')
            app.files.selection_set(second_id)
            app.update()
            app.fields['ma'].set('XYZ')
            app.fields['ten_cong_ty'].set('Công ty đang nhập dở')
            app.fields['nganh'].set('')
            app.fields['trang_dau'].set('3')
            app.fields['trang_cuoi'].set('5')
            app.output_root.set(str(root / 'đầu ra'))
            app.include_tables.set(False)
            out = root / 'old_results'
            out.mkdir()
            (out / 'chi_so_doanh_nghiep.csv').write_text(
                'ma,nam,loai,so_trang,so_tu,SYMB_1000,SUBST_1000,E5_1000,SUBST_RATIO\nABC,2024,PTBV,3,100,10,20,30,0.5\n', encoding='utf-8')
            app.out = out
            # Đóng ngay, trước khi hết thời gian chờ tự lưu.
            app._close()
            self.assertTrue(state.is_file())
            restored = self.create_app(state)
            restored.update()
            self.assertEqual(len(restored.entries), 2)
            self.assertEqual(restored.current, second_id)
            self.assertEqual(restored.fields['ten_cong_ty'].get(), 'Công ty đang nhập dở')
            self.assertEqual(restored.fields['nganh'].get(), '')
            self.assertEqual((restored.fields['trang_dau'].get(), restored.fields['trang_cuoi'].get()), ('3', '5'))
            self.assertEqual((restored.entries[first_id].trang_dau, restored.entries[first_id].trang_cuoi), ('2', '4'))
            self.assertEqual(restored.output_root.get(), str(root / 'đầu ra'))
            self.assertFalse(restored.include_tables.get())
            self.assertEqual(restored.out, out)
            self.assertEqual(len(restored.result_table.get_children()), 1)
            restored._remove()
            restored._close()
            final = self.create_app(state)
            self.assertEqual(len(final.entries), 1)
            self.assertNotIn(second_id, final.entries)

    def test_autosave_runs_while_app_is_open(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            app = self.create_app(path)
            app.output_root.set(str(Path(temp) / 'new output'))
            app.after(650, app.quit)
            app.mainloop()
            self.assertEqual(load_session(path)['settings']['output_root'], app.output_root.get())
            self.assertFalse(app._session_dirty)

    def test_missing_pdf_keeps_metadata_and_can_be_relinked(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path, pdf = root / 'session.json', root / 'old.pdf'
            make_pdf(pdf)
            app = self.create_app(path)
            with patch('app.filedialog.askopenfilenames', return_value=(str(pdf),)):
                app._add()
            app.update()
            app.fields['ten_cong_ty'].set('Tên cần giữ')
            app._close()
            moved = root / 'moved.pdf'
            pdf.rename(moved)
            restored = self.create_app(path)
            restored.update()
            self.assertEqual(len(restored.entries), 1)
            self.assertIn(restored.current, restored.unavailable_files)
            self.assertEqual(restored.fields['ten_cong_ty'].get(), 'Tên cần giữ')
            self.assertEqual(str(restored.page_controls['trang_dau']['state']), 'disabled')
            with patch('app.filedialog.askopenfilename', return_value=str(moved)):
                restored._relink_pdf()
            self.assertFalse(restored.unavailable_files)
            self.assertEqual(restored.entries[restored.current].path, moved)
            self.assertEqual(restored.fields['ten_cong_ty'].get(), 'Tên cần giữ')
            self.assertEqual(str(restored.page_controls['trang_dau']['state']), 'readonly')

    def test_corrupt_state_is_preserved_and_save_failure_keeps_app_open(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            path = root / 'session.json'
            path.write_text('{broken', encoding='utf-8')
            app = self.create_app(path)
            app._close()
            self.assertEqual(path.read_text(encoding='utf-8'), '{broken')
            app = self.create_app(path)
            app.output_root.set(str(root / 'output'))
            with patch('app.save_session', side_effect=PermissionError('file locked')), patch('app.messagebox.showerror') as error:
                app._close()
                error.assert_called_once()
                self.assertTrue(app.winfo_exists())
            app._close()
            self.assertEqual(load_session(path)['settings']['output_root'], str(root / 'output'))
            self.assertEqual(len(list(root.glob('session_unreadable_*.json'))), 1)
