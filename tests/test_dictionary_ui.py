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
            editor.term.set('Từ mới')
            editor.en.insert('1.0', 'custom phrase')
            editor.vi.insert('1.0', 'cụm từ mới')
            self.assertTrue(editor.apply())
            root.update()
            self.assertFalse(editor.form_dirty())
            editor.sample.insert('1.0', 'Cụm từ mới và cụm từ mới')
            editor.preview()
            self.assertIn('Từ mới: 2', editor.preview_text.get())
            editor.save()
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
