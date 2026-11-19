"""Tự tìm bộ OCR riêng của app; không sửa PATH hoặc cài vào hệ thống."""
import os
from pathlib import Path
import shutil
from app_paths import RESOURCE_ROOT, DATA_ROOT

ROOT = DATA_ROOT
BUNDLED = RESOURCE_ROOT / 'tools' / 'tesseract'


def find_tesseract(explicit=None):
    if explicit:
        return Path(explicit) if Path(explicit).is_file() else None
    candidates = [BUNDLED / 'tesseract.exe']
    for variable in ('ProgramFiles', 'LOCALAPPDATA'):
        base = os.environ.get(variable)
        if base:
            candidates.append(Path(base) / 'Tesseract-OCR' / 'tesseract.exe')
    for path in candidates:
        if path.is_file():
            return path
    command = shutil.which('tesseract')
    return Path(command) if command else None


def configure_tesseract(explicit=None):
    import pytesseract
    executable = find_tesseract(explicit)
    if executable is None:
        raise RuntimeError('OCR chưa sẵn sàng. Vào Cài đặt & hướng dẫn, bấm Chuẩn bị OCR tự động rồi chạy lại.')
    pytesseract.pytesseract.tesseract_cmd = str(executable)
    data = executable.parent / 'tessdata'
    if all((data / f'{lang}.traineddata').is_file() for lang in ('vie', 'eng')):
        # Biến môi trường của tiến trình app, không thay đổi cấu hình Windows.
        # Tránh lỗi dấu nháy trong cách pytesseract tách config trên Windows.
        os.environ['TESSDATA_PREFIX'] = str(data)
        return ''
    if executable.parent == BUNDLED:
        raise RuntimeError('Bộ OCR thiếu tiếng Việt/Anh. Bấm Chuẩn bị OCR tự động để tải bổ sung.')
    return ''
