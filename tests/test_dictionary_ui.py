import os
from pathlib import Path
import tempfile
import tkinter as tk
import unittest
from unittest.mock import patch

from dictionary_ui import DictionaryPanel, DictionaryEditor
from dictionary_store import default_dictionary, load_dictionary


@unittest.skipUnless(os.environ.get('ESG_GUI_TESTS') == '1', 'Cần phiên Tk trên Windows')
class DictionaryUITests(unittest.TestCase):
    def setUp(self):
        patcher = patch('dictionary_ui.messagebox.showinfo')
        self.info = patcher.start()
        self.addCleanup(patcher.stop)

    def test_edit_save_reopen_and_preview(self):
        with tempfile.TemporaryDirectory() as temp:
            root = tk.Tk()
            root.withdraw()
            self.addCleanup(root.destroy)
            panel = DictionaryPanel(root, temp, lambda: None)
            data = default_dictionary()
            data['name'] = 'Bộ thử'
            panel.persist(data, 'test')
            editor = DictionaryEditor(panel, 'test', data)
            root.update()
            editor.new()
            self.assertEqual(self.info.call_args.args[0], 'Mục mới')
            editor.term.set('Từ mới')
            editor.en.insert('1.0', 'custom phrase')
            editor.vi.insert('1.0', 'cụm từ mới')
            self.assertTrue(editor.apply())
            self.assertEqual(self.info.call_args.args[0], 'Đã áp dụng mục')
            root.update()
            self.assertFalse(editor.form_dirty())
            editor.sample.insert('1.0', 'Cụm từ mới và cụm từ mới')
            editor.preview()
            self.assertIn('Từ mới: 2', editor.preview_text.get())
            editor.save()
            self.assertEqual(self.info.call_args.args[0], 'Đã lưu bộ từ điển')
            saved = load_dictionary(Path(temp) / 'test.json')
            self.assertEqual(saved['entries'][-1]['vietnamese'], ['cụm từ mới'])
            reopened = DictionaryPanel(root, temp, lambda: None)
            reopened.restore_selection('test')
            self.assertEqual(reopened.current_dictionary(), saved)
            self.assertEqual(reopened.profiles['default'], default_dictionary())

    def test_cancel_selection_preserves_unsaved_form(self):
        with tempfile.TemporaryDirectory() as temp:
            root = tk.Tk()
            root.withdraw()
            self.addCleanup(root.destroy)
            panel = DictionaryPanel(root, temp, lambda: None)
            editor = DictionaryEditor(panel, 'test', default_dictionary())
            editor.table.selection_set('0')
            root.update()
            editor.term.set('Chưa áp dụng')
            with patch('dictionary_ui.messagebox.askyesno', return_value=False):
                editor.table.selection_set('1')
                root.update()
            self.assertEqual(editor.active, 0)
            self.assertEqual(editor.term.get(), 'Chưa áp dụng')
            editor.destroy()

    def test_footer_stays_visible_when_scrolling_and_resizing(self):
        with tempfile.TemporaryDirectory() as temp:
            root = tk.Tk()
            root.withdraw()
            self.addCleanup(root.destroy)
            panel = DictionaryPanel(root, temp, lambda: None)
            editor = DictionaryEditor(panel, 'test', default_dictionary())
            editor.transient('')
            self.addCleanup(editor.destroy)
            for size in ('880x720', '480x360', '880x720'):
                editor.geometry(size)
                root.update()
                before = [(button.winfo_rootx(), button.winfo_rooty()) for button in editor.actions.buttons]
                editor.page.canvas.yview_moveto(1)
                root.update()
                self.assertEqual(before, [(button.winfo_rootx(), button.winfo_rooty()) for button in editor.actions.buttons])
                for button in editor.actions.buttons:
                    self.assertGreaterEqual(button.winfo_rooty(), editor.page.winfo_rooty() + editor.page.winfo_height())
                    self.assertLessEqual(button.winfo_rooty() + button.winfo_height(), editor.winfo_rooty() + editor.winfo_height())
                    self.assertGreaterEqual(button.winfo_rootx(), editor.winfo_rootx())
                    self.assertLessEqual(button.winfo_rootx() + button.winfo_width(), editor.winfo_rootx() + editor.winfo_width())
                save = editor.actions.buttons[-1]
                self.assertEqual(save.winfo_rootx() + save.winfo_width(), editor.winfo_rootx() + editor.winfo_width() - 12)
            editor.table.selection_set('0')
            root.update()
            editor.remove()
            self.assertEqual(self.info.call_args.args[0], 'Đã xóa mục')
