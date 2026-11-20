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
    info = book.create_sheet('Hướng dẫn')
    for text in [data['name'], 'Mỗi dòng là một mục. Các biến thể trong ô cách nhau bằng xuống dòng (Alt+Enter).',
                 'bat: 1 = dùng, 0 = tạm tắt. Giữ nguyên hàng tiêu đề.',
                 'mau_anh_nang_cao: regex có sẵn; có thể để trống và nhập các biến thể tiếng Anh.',
                 'Nhập lại Excel sẽ tạo một bộ mới, không ghi đè bộ cũ.']:
        cell = info.cell(info.max_row + 1 if info['A1'].value else 1, 1, text)
        cell.data_type = 's'
    info.column_dimensions['A'].width = 110
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
