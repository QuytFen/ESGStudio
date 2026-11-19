"""Lưu phiên cục bộ bằng JSON, thay file nguyên tử để tránh ghi dở."""
import json
import os
from pathlib import Path
import tempfile
from app_paths import DATA_ROOT

DEFAULT_SESSION = DATA_ROOT / '.app_state' / 'session.json'


def load_session(path):
    path = Path(path)
    if not path.exists():
        return None
    with path.open(encoding='utf-8') as stream:
        state = json.load(stream)
    if not isinstance(state, dict) or state.get('version') != 1:
        raise ValueError('Phiên làm việc không đúng định dạng hoặc phiên bản.')
    if not isinstance(state.get('reports'), list) or not isinstance(state.get('settings', {}), dict):
        raise ValueError('Danh sách báo cáo/cài đặt đã lưu không hợp lệ.')
    return state


def save_session(path, state):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', suffix='.tmp',
                                         dir=path.parent, delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(state, stream, ensure_ascii=False, indent=2, allow_nan=False)
            stream.flush()
            os.fsync(stream.fileno())
        temporary.replace(path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
