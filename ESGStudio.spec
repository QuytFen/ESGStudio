# Build: .venv\Scripts\python.exe -m PyInstaller ESGStudio.spec --noconfirm
from pathlib import Path
import os
from PyInstaller.utils.hooks import collect_submodules, copy_metadata

root = Path(SPECPATH)
ocr = root / 'tools' / 'tesseract'
datas = [(str(root / 'danh_sach.csv'), '.'), (str(root / 'README.md'), '.')]
datas += [(str(root / filename), '.') for filename in ('GIOI_THIEU_APP.md', 'HUONG_DAN_SU_DUNG.md')]
for path in ocr.iterdir():
    if path.name == 'tesseract.exe' or path.suffix.lower() == '.dll':
        datas.append((str(path), 'tools/tesseract'))
for directory in ('tessdata', 'doc'):
    datas.append((str(ocr / directory), f'tools/tesseract/{directory}'))
for package in ('pypdfium2', 'pdfplumber', 'pytesseract', 'openpyxl', 'scikit-learn'):
    datas += copy_metadata(package)

a = Analysis(
    [str(root / 'app_entry.py')], pathex=[str(root)], binaries=[], datas=datas,
    hiddenimports=collect_submodules('sklearn.decomposition') + collect_submodules('scipy.special'),
    hookspath=[], hooksconfig={}, runtime_hooks=[],
    excludes=['underthesea', 'matplotlib', 'pytest', 'IPython', 'notebook'],
    noarchive=False,
)
pyz = PYZ(a.pure)
mode = os.environ.get('ESG_BUILD_ONEFILE', '0')
if mode in ('1', 'both'):
    exe = EXE(pyz, a.scripts, a.binaries, a.datas, [], name='ESGStudio',
              debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
              console=False, disable_windowed_traceback=False)
if mode != '1':
    exe = EXE(pyz, a.scripts, [], exclude_binaries=True, name='ESGStudio',
              debug=False, bootloader_ignore_signals=False, strip=False, upx=False,
              console=False, disable_windowed_traceback=False)
    coll = COLLECT(exe, a.binaries, a.datas, strip=False, upx=False, name='ESGStudio')
