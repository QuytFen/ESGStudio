"""Bộ từ điển cá nhân và bản chụp tái lập cho mỗi lần phân tích."""
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile

from lam_sach import lam_sach
from tu_dien import GROUPS

GROUP_NAMES = ('SYMB', 'SUBST', 'E5')
DEFAULT_ID = 'default'


def default_dictionary():
    return {'version': 1, 'name': 'Mặc định', 'entries': [
        {'group': group, 'name': name, 'english': [], 'pattern': pattern,
         'vietnamese': list(vi), 'enabled': True}
        for group, entries in GROUPS.items() for name, pattern, vi in entries]}


def validate_dictionary(data):
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('Phiên bản từ điển không hợp lệ.')
    if not isinstance(data.get('name'), str) or not data['name'].strip():
        raise ValueError('Hãy đặt tên bộ từ điển.')
    if not isinstance(data.get('entries'), list) or not data['entries']:
        raise ValueError('Từ điển cần ít nhất một mục.')
    names, phrases, warnings = set(), {}, []
    for entry in data['entries']:
        if not isinstance(entry, dict):
            raise ValueError('Mục từ khóa không hợp lệ.')
        group, name = entry.get('group'), entry.get('name')
        if group not in GROUP_NAMES or not isinstance(name, str) or not name.strip():
            raise ValueError('Mỗi mục cần tên và nhóm SYMB/SUBST/E5.')
        key = (group, name.strip().casefold())
        if key in names:
            raise ValueError(f'Trùng tên trong nhóm {group}: {name}')
        names.add(key)
        if not isinstance(entry.get('enabled'), bool):
            raise ValueError(f'{name}: trạng thái bật/tắt không hợp lệ.')
        for field in ('english', 'vietnamese'):
            values = entry.get(field)
            if not isinstance(values, list) or any(not isinstance(v, str) or not lam_sach(v) for v in values):
                raise ValueError(f'{name}: các biến thể phải là cụm từ có chữ.')
        pattern = entry.get('pattern', '')
        if not isinstance(pattern, str):
            raise ValueError(f'{name}: mẫu tiếng Anh không hợp lệ.')
        if pattern:
            try:
                compiled = re.compile(pattern)
                if compiled.search(''):
                    raise ValueError(f'{name}: mẫu không được khớp chuỗi rỗng.')
            except re.error as exc:
                raise ValueError(f'{name}: mẫu tiếng Anh bị lỗi: {exc}') from exc
        if not pattern and not entry['english'] and not entry['vietnamese']:
            raise ValueError(f'{name}: cần ít nhất một biến thể Anh hoặc Việt.')
        if entry['enabled']:
            variants = [('en', lam_sach(v)) for v in entry['english']]
            variants += [('vi', lam_sach(v)) for v in entry['vietnamese']]
            if pattern:
                variants.append(('pattern', pattern))
            for variant in variants:
                if variant in phrases:
                    warnings.append(f'{name} ({group}) trùng biến thể với {phrases[variant]}: {variant[1]}')
                else:
                    phrases[variant] = f'{name} ({group})'
    if not any(e['enabled'] for e in data['entries']):
        raise ValueError('Cần bật ít nhất một mục từ khóa.')
    return list(dict.fromkeys(warnings))


def dictionary_groups(data):
    validate_dictionary(data)
    groups = {group: [] for group in GROUP_NAMES}
    for entry in data['entries']:
        if entry['enabled']:
            patterns = [re.escape(lam_sach(v)) for v in entry['english']]
            if entry.get('pattern'):
                patterns.insert(0, entry['pattern'])
            pattern = '|'.join(f'(?:{p})' for p in patterns) or r'(?!)'
            groups[entry['group']].append((entry['name'], pattern, entry['vietnamese']))
    return groups


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()


def save_dictionary(path, data):
    validate_dictionary(data)
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    handle, temporary = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(handle, 'w', encoding='utf-8') as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
        Path(temporary).replace(path)
    finally:
        Path(temporary).unlink(missing_ok=True)


def load_dictionary(path):
    data = json.loads(Path(path).read_text(encoding='utf-8'))
    validate_dictionary(data)
    return data


def export_dictionary_excel(path, data):
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill
    from openpyxl.worksheet.datavalidation import DataValidation
    validate_dictionary(data)
    book = Workbook()
    sheet = book.active
    sheet.title = 'Từ điển'
    sheet.append(['nhom', 'ten', 'tieng_anh', 'tieng_viet', 'bat', 'mau_anh_nang_cao'])
    for e in data['entries']:
        sheet.append([e['group'], e['name'], '\n'.join(e['english']), '\n'.join(e['vietnamese']),
                      1 if e['enabled'] else 0, e.get('pattern', '')])
    for row in sheet:
        for cell in row:
            if isinstance(cell.value, str):
                cell.data_type = 's'
    for cell in sheet[1]:
        cell.font = Font(bold=True, color='FFFFFF')
        cell.fill = PatternFill('solid', fgColor='147D70')
    from openpyxl.styles import Alignment
    for row in sheet.iter_rows(min_row=2):
        for cell in row:
            cell.alignment = Alignment(wrap_text=True, vertical='top')
    for col, width in zip('ABCDEF', (14, 25, 35, 45, 10, 40)):
        sheet.column_dimensions[col].width = width
    sheet.freeze_panes = 'A2'
    sheet.auto_filter.ref = sheet.dimensions
    validation = DataValidation(type='list', formula1='"SYMB,SUBST,E5"')
    sheet.add_data_validation(validation)
    validation.add('A2:A1048576')
    info = book.create_sheet('Hướng dẫn', 0)
    book.active = 0
    info.sheet_view.showGridLines = False
    info.freeze_panes = 'B7'
    for col in 'ABCDEF':
        info.column_dimensions[col].width = 22

    def guide_cell(row, column, text, end_column=None, heading=False):
        if end_column is not None:
            info.merge_cells(start_row=row, start_column=column, end_row=row, end_column=end_column)
        cell = info.cell(row, column, text)
        cell.data_type = 's'
        cell.font = Font(name='Calibri', size=11, bold=heading, color='FFFFFF' if heading else '192B43')
        cell.alignment = Alignment(wrap_text=True, vertical='top')
        cell.fill = PatternFill('solid', fgColor='147D70' if heading else ('EEF5F4' if row % 2 else 'FFFFFF'))

    guide_cell(1, 1, 'HƯỚNG DẪN NHẬP BỘ TỪ ĐIỂN', 6, heading=True)
    info.row_dimensions[1].height = 30
    guide_cell(2, 1, f'Bộ được xuất: {data["name"]}', 6)
    guide_cell(3, 1, 'Bắt đầu tại đây: đọc cách điền từng cột bên dưới, sau đó chuyển sang sheet Từ điển để sửa hoặc thêm mục.', 6)
    guide_cell(4, 1, 'Mỗi dòng trong sheet Từ điển là một mục. Giữ nguyên tên sheet, 6 cột và hàng tiêu đề; không chèn dòng hướng dẫn vào bảng dữ liệu.', 6)
    for row in (2, 3, 4):
        info.row_dimensions[row].height = 32
    guide_cell(6, 1, 'Cột trong sheet Từ điển', heading=True)
    guide_cell(6, 2, 'Ý nghĩa và cách điền', 4, heading=True)
    guide_cell(6, 5, 'Ví dụ nội dung trong một ô', 6, heading=True)
    info.row_dimensions[6].height = 32
    fields = [
        ('nhom', 'Bắt buộc. Chọn đúng SYMB, SUBST hoặc E5. SYMB: từ khóa về công bố hình thức; SUBST: công bố thực chất; E5: tài nguyên và kinh tế tuần hoàn.', 'E5', 68),
        ('ten', 'Bắt buộc. Tên mục dùng để gộp số đếm và hiển thị trong kết quả. Tên không tự trở thành từ cần tìm; hãy nhập các dạng cần tìm vào cột biến thể hoặc regex. Không trùng tên trong cùng nhóm.', 'Tái chế nhựa', 78),
        ('tieng_anh', 'Các từ/cụm tiếng Anh cần tìm. Mỗi biến thể một dòng trong CÙNG ô (Alt+Enter trên Windows). Không ngăn cách bằng dấu phẩy. App không tự thêm đuôi -ed, -ing, -ion hoặc số nhiều. Có thể để trống nếu chỉ dùng tiếng Việt hoặc regex.', 'evaluate\nevaluates\nevaluated\nevaluating\nevaluation\nevaluations', 112),
        ('tieng_viet', 'Các từ/cụm tiếng Việt có dấu cần tìm; mỗi biến thể một dòng trong cùng ô (Alt+Enter). Có thể để trống nếu chỉ dùng tiếng Anh. Các biến thể trong một dòng dữ liệu được cộng vào cùng tên mục.', 'tái chế nhựa\nnhựa tái chế', 78),
        ('bat', 'Bắt buộc. Điền số 1 để dùng mục, số 0 để tạm tắt; không để trống. Cần giữ ít nhất một mục đang bật trong toàn bộ bộ từ điển.', '1', 56),
        ('mau_anh_nang_cao', 'Tùy chọn, dành cho regex tiếng Anh. Để trống nếu đã liệt kê các dạng ở tieng_anh. Ví dụ bên cạnh gộp evaluate, evaluates, evaluated, evaluating, evaluation, evaluations. Với bộ mặc định, giữ mẫu có sẵn nếu vẫn muốn dùng quy tắc gộp đó.', r'evaluat(?:e|es|ed|ing|ion|ions)', 90),
    ]
    for row, (field, instructions, example, height) in enumerate(fields, 7):
        guide_cell(row, 1, field)
        guide_cell(row, 2, instructions, 4)
        guide_cell(row, 5, example, 6)
        info.row_dimensions[row].height = height
    guide_cell(14, 1, 'MỘT DÒNG MẪU HOÀN CHỈNH — chỉ minh họa, không tự nhập vào app', 6, heading=True)
    info.row_dimensions[14].height = 28
    for column, header in enumerate(('nhom', 'ten', 'tieng_anh', 'tieng_viet', 'bat', 'mau_anh_nang_cao'), 1):
        guide_cell(15, column, header, heading=True)
    info.row_dimensions[15].height = 32
    for column, value in enumerate(('SYMB', 'Evaluate', 'evaluate\nevaluates\nevaluated\nevaluating\nevaluation\nevaluations', 'đánh giá\nthẩm định', '1', ''), 1):
        guide_cell(16, column, value)
    info.row_dimensions[16].height = 112
    guide_cell(18, 1, 'LƯU VÀ NHẬP LẠI VÀO APP', 6, heading=True)
    info.row_dimensions[18].height = 28
    notes = [
        '1. Sang sheet Từ điển để sửa hoặc thêm dòng. Ví dụ trên sheet Hướng dẫn không được nhập tự động. Ít nhất một trong ba cột tieng_anh, tieng_viet, mau_anh_nang_cao phải có nội dung cho mỗi mục.',
        '2. Lưu file dưới định dạng .xlsx. Vào Cài đặt & hướng dẫn → Bộ từ điển → Nhập Excel, chọn file và đặt tên bộ mới. Các bộ cũ được giữ lại.',
        '3. Chọn bộ mới, mở Quản lý từ điển và dùng Thử đếm với đúng ngôn ngữ vi/en để kiểm tra. Muốn áp dụng cho báo cáo, chạy phân tích lại; kết quả cũ không tự thay đổi.',
        'Lưu ý trùng biến thể: nếu thêm Evaluate theo ví dụ, hãy tạm tắt hoặc chỉnh mục Evaluation cũ để tránh tranh khớp. App khớp nguyên từ/cụm, ưu tiên cụm dài và chỉ đếm cùng đoạn chữ một lần.',
    ]
    for row, text in enumerate(notes, 19):
        guide_cell(row, 1, text, 6)
        info.row_dimensions[row].height = 46
    info.print_options.horizontalCentered = True
    info.sheet_properties.pageSetUpPr.fitToPage = True
    info.page_setup.orientation = 'landscape'
    info.page_setup.paperSize = info.PAPERSIZE_A4
    info.page_setup.fitToWidth = 1
    info.page_setup.fitToHeight = 0
    info.print_area = 'A1:F22'
    try:
        book.save(path)
    finally:
        book.close()


def import_dictionary_excel(path):
    from openpyxl import load_workbook
    book = load_workbook(path, read_only=True, data_only=False)
    try:
        sheet = book['Từ điển']
        rows = sheet.iter_rows(values_only=True)
        headers = next(rows)
        expected = ('nhom', 'ten', 'tieng_anh', 'tieng_viet', 'bat', 'mau_anh_nang_cao')
        if tuple(headers) != expected:
            raise ValueError('Sai cột Excel. Hãy xuất file mẫu từ app để chỉnh sửa.')
        data = {'version': 1, 'name': Path(path).stem, 'entries': []}
        for number, row in enumerate(rows, 2):
            if not any(v is not None for v in row):
                continue
            group, name, en, vi, enabled, pattern = row
            if str(enabled).strip() not in ('0', '1'):
                raise ValueError(f'Dòng {number}: cột bat phải là 0 hoặc 1.')
            data['entries'].append({'group': str(group or '').strip(), 'name': str(name or '').strip(),
                'english': [v.strip() for v in str(en or '').splitlines() if v.strip()],
                'vietnamese': [v.strip() for v in str(vi or '').splitlines() if v.strip()],
                'enabled': str(enabled).strip() == '1', 'pattern': str(pattern or '').strip()})
        validate_dictionary(data)
        return data
    except (KeyError, StopIteration) as exc:
        raise ValueError('Không tìm thấy bảng Từ điển hợp lệ.') from exc
    finally:
        book.close()
