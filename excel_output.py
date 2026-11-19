"""Xuất kết quả thành workbook Excel và mở trực tiếp bằng Microsoft Excel."""
import csv
import os
from pathlib import Path
import subprocess
import tempfile

EXCEL_NAME = 'ket_qua_phan_tich.xlsx'
NUMBERS = {'STT', 'Năm', 'nam', 'trang', 'trang_dau', 'trang_cuoi', 'so_trang', 'so_tu',
           'SYMB_1000', 'SUBST_1000', 'E5_1000', 'SUBST_RATIO', 'so_lan',
           'tren_1000', 'k', 'umass', 'chu_de', 'ty_trong'}


def create_excel(folder):
    from openpyxl import Workbook
    from openpyxl.styles import Alignment, Font, PatternFill
    from openpyxl.utils import get_column_letter
    folder = Path(folder)
    book = Workbook()
    book.remove(book.active)
    sources = [('Tổng hợp', 'google_sheet.tsv', '\t'),
               ('Chỉ số', 'chi_so_doanh_nghiep.csv', ','),
               ('Từ khóa', 'tan_suat_tu_khoa.csv', ','),
               ('Chủ đề LDA', 'chu_de_lda.csv', ','),
               ('Từ khóa theo trang', 'tu_khoa_theo_trang.csv', ',')]
    for title, filename, delimiter in sources:
        source = folder / filename
        if not source.is_file():
            continue
        with source.open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.reader(stream, delimiter=delimiter))
        if not rows:
            continue
        sheet = book.create_sheet(title)
        headers = rows[0]
        for index, row in enumerate(rows, 1):
            for column, value in enumerate(row, 1):
                cell = sheet.cell(index, column)
                header = headers[column - 1] if column <= len(headers) else ''
                if index > 1 and header in NUMBERS and value:
                    try:
                        cell.value = float(value) if any(c in value.lower() for c in '.e') else int(value)
                    except ValueError:
                        cell.value = value
                else:
                    cell.value = value or None
                # Văn bản PDF/metadata được giữ là text, kể cả khi bắt đầu bằng '='.
                if isinstance(cell.value, str):
                    cell.data_type = 's'
                cell.font = Font(name='Calibri', size=11, color='192B43')
                cell.alignment = Alignment(vertical='top', wrap_text=True)
                if index == 1:
                    cell.font = Font(name='Calibri', size=11, bold=True, color='FFFFFF')
                    cell.fill = PatternFill('solid', fgColor='147D70')
                elif header in ('SUBST_RATIO', 'ty_trong'):
                    cell.number_format = '0.0%'
                elif header.endswith('_1000') or header in ('tren_1000', 'umass'):
                    cell.number_format = '0.000'
                elif isinstance(cell.value, (int, float)):
                    cell.number_format = '#,##0'
        sheet.freeze_panes = 'A2'
        sheet.auto_filter.ref = sheet.dimensions
        sheet.sheet_view.showGridLines = False
        sheet.row_dimensions[1].height = 48
        for column, header in enumerate(headers, 1):
            long_text = title == 'Tổng hợp' and column not in (1, 5, 6, 11)
            sheet.column_dimensions[get_column_letter(column)].width = 44 if long_text else max(14, min(32, len(header) + 4))
        for index, row in enumerate(rows[1:], 2):
            # Đủ chiều cao cho nội dung dài, có giới hạn để cuộn bảng thuận tiện.
            lines = max((sum(max(1, (len(part) + 39) // 40) for part in value.split('\n')) for value in row), default=1)
            sheet.row_dimensions[index].height = min(360, max(30, lines * 17))
    if not book.worksheets:
        raise ValueError('Thư mục này chưa có bảng kết quả để xuất Excel.')
    destination = folder / EXCEL_NAME
    # Ghi file tạm để không làm hỏng bản cũ nếu Excel đang giữ file hoặc xuất lỗi.
    handle, temporary = tempfile.mkstemp(suffix='.xlsx', dir=folder)
    os.close(handle)
    try:
        book.save(temporary)
        Path(temporary).replace(destination)
    finally:
        book.close()
        Path(temporary).unlink(missing_ok=True)
    return destination


def find_excel():
    if os.name != 'nt':
        return None
    import winreg
    key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\App Paths\excel.exe'
    for hive in (winreg.HKEY_CURRENT_USER, winreg.HKEY_LOCAL_MACHINE):
        for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
            try:
                with winreg.OpenKey(hive, key, 0, winreg.KEY_READ | view) as registry:
                    path = Path(winreg.QueryValueEx(registry, '')[0].strip('"'))
                if path.is_file():
                    return path
            except OSError:
                continue
    for variable in ('ProgramFiles', 'ProgramFiles(x86)'):
        base = os.environ.get(variable)
        if base:
            for version in ('root/Office16', 'Office16', 'Office15'):
                path = Path(base) / 'Microsoft Office' / version / 'EXCEL.EXE'
                if path.is_file():
                    return path
    return None


def open_excel(path):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f'Không tìm thấy file Excel: {path}')
    executable = find_excel()
    if executable:
        subprocess.Popen([str(executable), str(path)])
    else:
        os.startfile(str(path))
