import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from session_store import load_session, save_session


class SessionStoreTests(unittest.TestCase):
    def test_round_trip_and_atomic_failure_preserves_previous_session(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'state' / 'session.json'
            self.assertIsNone(load_session(path))
            state = {'version': 1, 'reports': [{'path': 'Báo cáo.pdf', 'ten_cong_ty': 'Công ty mẫu'}], 'settings': {}}
            save_session(path, state)
            self.assertEqual(load_session(path), state)
            original = path.read_bytes()
            with patch('session_store.Path.replace', side_effect=PermissionError('file locked')):
                with self.assertRaises(PermissionError):
                    save_session(path, {'version': 1, 'reports': [], 'settings': {}})
            self.assertEqual(path.read_bytes(), original)
            self.assertFalse(list(path.parent.glob('*.tmp')))

    def test_rejects_corrupt_or_unsupported_state(self):
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'session.json'
            for text in ('{broken', json.dumps({'version': 2}), json.dumps({'version': 1, 'reports': {}})):
                path.write_text(text, encoding='utf-8')
                with self.assertRaises(ValueError):
                    load_session(path)
