"""PDF ảnh tổng hợp: kiểm tra bộ đọc tích hợp và OCR thật, không dùng Poppler."""
from pathlib import Path
import tempfile
import unittest
from ocr_runtime import BUNDLED, find_tesseract
from trich_xuat import trich_xuat


@unittest.skipUnless((BUNDLED / 'tesseract.exe').is_file(), 'Cần chuẩn bị OCR portable')
class IntegratedOCRTests(unittest.TestCase):
    def test_scanned_bilingual_pdf_without_poppler(self):
        from PIL import Image, ImageDraw, ImageFont
        font_path = Path('C:/Windows/Fonts/arial.ttf')
        if not font_path.is_file():
            self.skipTest('Cần font Arial để tạo ảnh tiếng Việt')
        image = Image.new('RGB', (1800, 700), 'white')
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype(str(font_path), 42)
        for index, line in enumerate([
            'Waste recycling and circular materials recovery.',
            'Chất thải nguy hại được xử lý và tái chế.',
            'Chi phí công nghệ và thiết bị xử lý chất thải.',
        ]):
            draw.text((60, 80 + index * 100), line, fill='black', font=font)
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp) / 'Báo cáo ảnh kiểm thử.pdf'
            image.save(path, 'PDF', resolution=150)
            image.close()
            result = trich_xuat(path)
        self.assertEqual(len(result), 1)
        self.assertTrue(result[0]['ocr'])
        self.assertIn('waste', result[0]['raw'].lower())
        self.assertIn('chất thải', result[0]['raw'].lower())

    def test_app_finds_its_own_runtime(self):
        self.assertEqual(find_tesseract(), BUNDLED / 'tesseract.exe')
