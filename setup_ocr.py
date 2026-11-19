"""Chuẩn bị OCR portable từ nguồn chính thức, không chạy trình cài hệ thống."""
import hashlib
import os
from pathlib import Path
import subprocess
import sys
import urllib.request

from ocr_runtime import BUNDLED, ROOT, configure_tesseract

CACHE = ROOT / 'tools' / 'downloads'
ASSETS = {
    '7zr.exe': ('https://www.7-zip.org/a/7zr.exe', '256feca8e274e5da655e2a284fabafd9f554365eb164862089dacd4e8276d282'),
    '7zip-setup.exe': ('https://www.7-zip.org/a/7z2301-x64.exe', '26cb6e9f56333682122fafe79dbcdfd51e9f47cc7217dccd29ac6fc33b5598cd'),
    'tesseract-setup.exe': ('https://github.com/tesseract-ocr/tesseract/releases/download/5.5.3/tesseract-ocr-w64-setup-5.5.3.20260724.exe', 'bee9e3434bd94fd65387d9be28cd467a41f61b1275383b55b0f59a1331270ae4'),
    'eng.traineddata': ('https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/eng.traineddata', '7d4322bd2a7749724879683fc3912cb542f19906c83bcc1a52132556427170b2'),
    'vie.traineddata': ('https://raw.githubusercontent.com/tesseract-ocr/tessdata_fast/main/vie.traineddata', '79df64caf7bcfb2a27df5042ecb6121e196eada34da774956995747636d5bfa1'),
}


def digest(path):
    checksum = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1024 * 1024):
            checksum.update(chunk)
    return checksum.hexdigest()


def download(name, destination, log):
    url, expected = ASSETS[name]
    destination = Path(destination)
    if destination.is_file() and digest(destination) == expected:
        return destination
    log(f'Đang tải {name}…\n')
    destination.parent.mkdir(parents=True, exist_ok=True)
    partial = destination.with_name(destination.name + '.part')
    try:
        request = urllib.request.Request(url, headers={'User-Agent': 'ESG-Studio/1.0'})
        with urllib.request.urlopen(request, timeout=60) as response, partial.open('wb') as stream:
            while chunk := response.read(1024 * 1024):
                stream.write(chunk)
        if digest(partial) != expected:
            raise RuntimeError(f'File {name} không khớp SHA-256; chưa sử dụng file tải về.')
        partial.replace(destination)
    finally:
        partial.unlink(missing_ok=True)
    return destination


def prepare_ocr(log=print):
    if os.name != 'nt':
        configure_tesseract()
        return
    flags = subprocess.CREATE_NO_WINDOW
    if not (BUNDLED / 'tesseract.exe').is_file():
        small = download('7zr.exe', CACHE / '7zr.exe', log)
        archive = download('7zip-setup.exe', CACHE / '7zip-setup.exe', log)
        extractor = CACHE / '7zip'
        subprocess.run([str(small), 'x', str(archive), f'-o{extractor}', '-y'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=flags)
        installer = download('tesseract-setup.exe', CACHE / 'tesseract-setup.exe', log)
        log('Đang giải nén bộ OCR riêng của app…\n')
        subprocess.run([str(extractor / '7z.exe'), 'x', str(installer), f'-o{BUNDLED}', '-y'], check=True,
                       stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, creationflags=flags)
    for language in ('eng', 'vie'):
        download(f'{language}.traineddata', BUNDLED / 'tessdata' / f'{language}.traineddata', log)
    config = configure_tesseract(str(BUNDLED / 'tesseract.exe'))
    import pytesseract
    languages = pytesseract.get_languages(config=config)
    if not {'eng', 'vie'}.issubset(languages):
        raise RuntimeError('Bộ OCR chưa nhận đủ tiếng Việt/Anh. Hãy thử chuẩn bị lại.')
    log('OCR tiếng Việt và tiếng Anh đã sẵn sàng.\n')


if __name__ == '__main__':
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, 'reconfigure'):
            stream.reconfigure(encoding='utf-8')
    prepare_ocr()
