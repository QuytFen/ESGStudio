"""Chuẩn hóa văn bản; tiếng Việt được đếm theo âm tiết."""
import re
import unicodedata

DAU_VIET = set('ăâđêôơưáàảãạắằẳẵặấầẩẫậéèẻẽẹếềểễệíìỉĩịóòỏõọốồổỗộớờởỡợúùủũụứừửữựýỳỷỹỵ')

def ngon_ngu(text):
    text = unicodedata.normalize('NFC', text).lower()
    letters = [c for c in text if c.isalpha()]
    return 'vi' if sum(c in DAU_VIET for c in letters) / max(len(letters), 1) >= 0.015 else 'en'

def lam_sach(text):
    text = unicodedata.normalize('NFC', text).lower()
    text = re.sub(r'(?<=\w)-\s*\n\s*(?=\w)', '', text)
    text = re.sub(r'https?://\S+|www\.\S+|[\w.+-]+@[\w.-]+\.[a-z]+', ' ', text)
    # Bỏ chữ số và dấu câu; dấu gạch nối trở thành khoảng trắng.
    text = ''.join(c if c.isalpha() or c.isspace() else ' ' for c in text)
    return ' '.join(text.split())
