"""Tạo gói chia sẻ sạch; tùy chọn khôi phục phiên riêng trên máy đang build."""
import argparse
import hashlib
from pathlib import Path
import shutil
import zipfile

ROOT = Path(__file__).resolve().parent
GUIDE = '''ESG STUDIO 1.1.0 — WINDOWS 64-BIT
made by Quýt

BẢN MỘT FILE:
Nhấp đúp ESGStudio-Windows-x64.exe. Không cần cài Python hoặc OCR.
Lần mở đầu cần chờ giải nén thư viện. Đặt file trong thư mục bạn có quyền ghi.

BẢN PORTABLE ZIP:
Giải nén toàn bộ ZIP, mở thư mục ESGStudio rồi chạy ESGStudio.exe.
Giữ nguyên thư mục _internal, không lấy riêng file .exe ra ngoài.

SỬ DỤNG:
Thêm PDF, điền thông tin, chọn khoảng trang rồi bấm Bắt đầu phân tích.
Mặc định đếm cả chữ trong bảng. Có thể thay đổi ở Cài đặt.
Trong Cài đặt, sao chép bộ từ điển để sửa từ khóa Anh/Việt, nhập/xuất Excel.
Bấm Mở file Excel để xem kết quả. Sheet Từ khóa theo trang giúp đối chiếu.

DỮ LIỆU:
Phiên làm việc và kết quả được giữ trong du_lieu cạnh file chạy.
App nhớ đường dẫn PDF gốc. Nếu chuyển PDF, dùng Chọn lại PDF.
PDF được xử lý trên máy, không gửi nội dung lên mạng.
Kết quả cũ không tự thay đổi khi cập nhật app; cần phân tích lại khi đổi cách đếm.
'''


def package(personalize=False):
    release = ROOT / 'releases'
    release.mkdir(exist_ok=True)
    folder = ROOT / 'dist' / 'ESGStudio'
    if not (folder / 'ESGStudio.exe').is_file():
        raise FileNotFoundError('Cần build bản portable trước.')
    (folder / 'HUONG_DAN.txt').write_text(GUIDE, encoding='utf-8-sig')
    (release / 'HUONG_DAN.txt').write_text(GUIDE, encoding='utf-8-sig')
    docs = ('GIOI_THIEU_APP.md', 'HUONG_DAN_SU_DUNG.md')
    for filename in docs:
        shutil.copy2(ROOT / filename, folder / filename)
        shutil.copy2(ROOT / filename, release / filename)
    archive = release / 'ESGStudio-Windows-x64-portable.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
        for path in folder.rglob('*'):
            relative = path.relative_to(folder)
            if path.is_file() and relative.parts[0] in ('_internal', 'ESGStudio.exe', 'HUONG_DAN.txt', *docs):
                target.write(path, Path('ESGStudio') / relative)
    with zipfile.ZipFile(archive) as target:
        if any('/du_lieu/' in name or '/.app_state/' in name for name in target.namelist()):
            raise RuntimeError('Gói chia sẻ chứa phiên riêng; chưa được bàn giao.')
    products = [archive]
    single = ROOT / 'dist' / 'ESGStudio.exe'
    if single.is_file():
        product = release / 'ESGStudio-Windows-x64.exe'
        shutil.copy2(single, product)
        products.append(product)
    checksums = []
    for path in products:
        checksum = hashlib.sha256()
        with path.open('rb') as stream:
            while chunk := stream.read(1024 * 1024):
                checksum.update(chunk)
        checksums.append(f'{checksum.hexdigest()}  {path.name}')
    (release / 'SHA256SUMS.txt').write_text('\n'.join(checksums) + '\n', encoding='utf-8')
    if personalize:
        source = ROOT / '.app_state' / 'session.json'
        if source.is_file():
            # Tạo sau khi ZIP đã xong. Phiên riêng không nằm trong gói chia sẻ.
            for directory in (folder, release):
                destination = directory / 'du_lieu' / '.app_state' / 'session.json'
                if not destination.exists():
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, destination)
    return products


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--restore-local-session', action='store_true')
    args = parser.parse_args()
    for product in package(args.restore_local_session):
        print(f'{product.name}: {product.stat().st_size / 1024 / 1024:.1f} MB')
