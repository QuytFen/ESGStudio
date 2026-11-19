"""Giao diện desktop tiếng Việt cho bộ phân tích ESRS E5 cục bộ."""
import csv
from dataclasses import dataclass
from datetime import datetime
import importlib.util
import json
import os
from pathlib import Path
import queue
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import tkinter as tk
from tkinter import font as tkfont
from tkinter import filedialog, messagebox, ttk
from uuid import uuid4
from ocr_runtime import find_tesseract
from setup_ocr import prepare_ocr
from excel_output import EXCEL_NAME, create_excel, open_excel
from ui_layout import FlowButtons, ScrollablePage, WheelRouter
from session_store import DEFAULT_SESSION, load_session, save_session
from app_paths import APP_VERSION, DATA_ROOT, RESOURCE_ROOT, FROZEN

ROOT = DATA_ROOT
META_FIELDS = ['ma', 'ten_cong_ty', 'nganh', 'nam', 'ky_bao_cao']
PAGE_FIELDS = ['ma', 'nam', 'loai', 'trang_dau', 'trang_cuoi']


def pdf_page_count(path):
    import pypdfium2
    try:
        with pypdfium2.PdfDocument(str(path)) as pdf:
            count = len(pdf)
    except Exception as exc:
        raise ValueError(f'Không đọc được số trang PDF: {exc}') from exc
    if count < 1:
        raise ValueError('PDF không có trang.')
    return count


@dataclass
class ReportInput:
    path: Path
    ma: str = ''
    ten_cong_ty: str = ''
    nganh: str = ''
    nam: str = ''
    ky_bao_cao: str = ''
    loai: str = 'PTBV'
    trang_dau: str = ''
    trang_cuoi: str = ''
    so_trang_pdf: int = 0

    @property
    def filename(self):
        return f'{self.ma.upper()}_{self.nam}_{self.loai}.pdf'


def validate_reports(reports):
    """Kiểm tra trước khi sao chép/chạy; cấu hình mã/năm phải nhất quán."""
    if not reports:
        raise ValueError('Hãy thêm ít nhất một báo cáo PDF.')
    seen, companies = set(), {}
    for r in reports:
        prefix = f'{r.path.name}: '
        if not r.path.is_file() or r.path.suffix.lower() != '.pdf':
            raise ValueError(prefix + 'Không tìm thấy file PDF.')
        if not re.fullmatch(r'[A-Za-z0-9]+', r.ma):
            raise ValueError(prefix + 'Mã công ty chỉ gồm chữ cái không dấu và số.')
        if not re.fullmatch(r'\d{4}', r.nam) or r.loai not in ('PTBV', 'ESG', 'BCTN'):
            raise ValueError(prefix + 'Năm phải có 4 chữ số; loại là PTBV, ESG hoặc BCTN.')
        if not all((r.ten_cong_ty, r.nganh, r.ky_bao_cao)):
            raise ValueError(prefix + 'Hãy nhập tên công ty, ngành và kỳ báo cáo.')
        if r.filename in seen:
            raise ValueError(prefix + 'Trùng mã công ty, năm và loại báo cáo.')
        seen.add(r.filename)
        key = (r.ma.upper(), r.nam)
        meta = (r.ten_cong_ty, r.nganh, r.ky_bao_cao)
        if key in companies and companies[key] != meta:
            raise ValueError(prefix + 'Các báo cáo cùng mã/năm cần cùng thông tin công ty và kỳ báo cáo.')
        companies[key] = meta
        page_range = (r.trang_dau, r.trang_cuoi)
        if any(page_range):
            if not all(re.fullmatch(r'[0-9]+', p) for p in page_range):
                raise ValueError(prefix + 'Nhập cả trang đầu và trang cuối bằng số nguyên dương.')
            if not 1 <= int(r.trang_dau) <= int(r.trang_cuoi):
                raise ValueError(prefix + 'Khoảng trang không hợp lệ.')
            if r.so_trang_pdf and int(r.trang_cuoi) > pdf_page_count(r.path):
                raise ValueError(prefix + 'Trang kết thúc vượt quá số trang PDF. Hãy thêm lại file nếu PDF đã thay đổi.')


def write_inputs(reports, folder):
    folder = Path(folder)
    folder.mkdir(parents=True, exist_ok=True)
    metadata, pages = {}, {}
    for r in reports:
        key = (r.ma.upper(), r.nam)
        metadata[key] = {f: getattr(r, f) for f in META_FIELDS}
        metadata[key]['ma'] = r.ma.upper()
        if r.trang_dau:
            pages[(*key, r.loai)] = dict(zip(PAGE_FIELDS, (*key, r.loai, r.trang_dau, r.trang_cuoi)))
    for name, fields, rows in [('danh_sach.csv', META_FIELDS, metadata.values()),
                                ('trang_thu_cong.csv', PAGE_FIELDS, pages.values())]:
        with (folder / name).open('w', encoding='utf-8-sig', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=fields)
            writer.writeheader()
            writer.writerows(rows)


def run_analysis(reports, out, tesseract, poppler, events, include_tables=True):
    """Luồng nền chỉ gửi sự kiện; mọi cập nhật Tk thực hiện trên luồng chính."""
    try:
        validate_reports(reports)
        out = Path(out)
        out.mkdir(parents=True, exist_ok=False)
        config = out / 'dau_vao'
        write_inputs(reports, config)
        with tempfile.TemporaryDirectory(prefix='esg_') as temp:
            for r in reports:
                events.put(('log', f'Chuẩn bị: {r.path.name}\n'))
                shutil.copyfile(r.path, Path(temp) / r.filename)
            python = Path(sys.executable)
            if python.name.lower() == 'pythonw.exe':
                python = python.with_name('python.exe')
            arguments = ['--input', temp, '--out', str(out), '--metadata', str(config / 'danh_sach.csv'),
                         '--pages', str(config / 'trang_thu_cong.csv')]
            if tesseract:
                arguments += ['--tesseract', tesseract]
            if poppler:
                arguments += ['--poppler', poppler]
            if not include_tables:
                arguments += ['--exclude-tables']
            flags = subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0
            if FROZEN:
                log_path = out / 'nhat_ky_xu_ly.txt'
                log_path.touch()
                command = [sys.executable, '--pipeline', str(log_path), *arguments]
                with subprocess.Popen(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                      creationflags=flags) as process, log_path.open(encoding='utf-8', errors='replace') as stream:
                    while True:
                        line = stream.readline()
                        if line:
                            events.put(('log', line))
                        elif process.poll() is not None:
                            for line in stream:
                                events.put(('log', line))
                            code = process.returncode
                            break
                        else:
                            time.sleep(0.08)
            else:
                command = [str(python), '-u', str(RESOURCE_ROOT / 'main.py'), *arguments]
                with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                      text=True, encoding='utf-8', errors='replace',
                                      creationflags=flags) as process:
                    for line in process.stdout:
                        events.put(('log', line))
                    code = process.wait()
        events.put(('done', (code, out)))
    except Exception as exc:
        events.put(('failed', str(exc)))


class ESGApp(tk.Tk):
    def __init__(self, session_path=DEFAULT_SESSION):
        super().__init__()
        self._destroying = False
        self.session_path = Path(session_path) if session_path is not None else None
        self._restoring_session = True
        self._session_dirty = False
        self._session_save_id = None
        self._session_load_error = False
        self.unavailable_files = {}
        self.title(f'ESG Studio {APP_VERSION} • Phân tích báo cáo ESRS E5')
        width = min(1240, self.winfo_screenwidth() - 60)
        height = min(760, self.winfo_screenheight() - 140)
        self.geometry(f'{width}x{height}')
        self.minsize(min(480, width), min(360, height))
        self.configure(bg='#eef3f8')
        self.entries = {}
        self.current = None
        self.busy = False
        self._updating_pages = False
        self.out = None
        self.events = queue.Queue()
        self.fields = {key: tk.StringVar() for key in [*META_FIELDS, 'loai', 'trang_dau', 'trang_cuoi']}
        self.output_root = tk.StringVar(value=str(ROOT / 'ket_qua'))
        self.tesseract = tk.StringVar()
        self.poppler = tk.StringVar()
        self.include_tables = tk.BooleanVar(value=True)
        self.status = tk.StringVar(value='Thêm PDF để bắt đầu')
        self.summary = tk.StringVar(value='Chưa có kết quả • Chọn báo cáo ở tab Chuẩn bị')
        self.save_status = tk.StringVar(value='Tự động lưu phiên làm việc trên máy')
        self._style()
        self._build()
        self.wheel_router = WheelRouter(self)
        for key in ('trang_dau', 'trang_cuoi'):
            self.fields[key].trace_add('write', self._refresh_pages)
        for variable in (*self.fields.values(), self.output_root, self.tesseract, self.poppler, self.include_tables):
            variable.trace_add('write', self._queue_session_save)
        self._restore_session()
        self._restoring_session = False
        self._refresh_pages()
        self.protocol('WM_DELETE_WINDOW', self._close)
        self.after(120, self._poll)

    def _queue_session_save(self, *_):
        if self.session_path is None or self._restoring_session or self._destroying:
            return
        self._session_dirty = True
        self.save_status.set('Đang lưu thay đổi…')
        if self._session_save_id is not None:
            self.after_cancel(self._session_save_id)
        self._session_save_id = self.after(450, self._save_session)

    def _save_session(self):
        if self._session_save_id is not None:
            self.after_cancel(self._session_save_id)
            self._session_save_id = None
        if self.session_path is None or not self._session_dirty:
            return True
        self._save_current()
        state = {
            'version': 1,
            'reports': [dict(vars(report), path=str(report.path.resolve()), id=uid)
                        for uid, report in self.entries.items()],
            'selected': self.current,
            'settings': {'output_root': self.output_root.get(), 'tesseract': self.tesseract.get(),
                         'poppler': self.poppler.get(), 'include_tables': self.include_tables.get()},
            'last_result': str(self.out) if self.out else None,
        }
        try:
            if self._session_load_error and self.session_path.exists():
                backup = self.session_path.with_name('session_unreadable_' + datetime.now().strftime('%Y%m%d_%H%M%S_%f') + '.json')
                shutil.copy2(self.session_path, backup)
                self._session_load_error = False
            save_session(self.session_path, state)
        except (OSError, ValueError) as exc:
            self.save_status.set(f'Chưa lưu được phiên: {exc}')
            return False
        self._session_dirty = False
        self.save_status.set('Đã tự động lưu • Mở lại app sẽ khôi phục')
        return True

    def _restore_session(self):
        if self.session_path is None:
            return
        try:
            state = load_session(self.session_path)
        except (OSError, ValueError) as exc:
            self._session_load_error = True
            self.save_status.set(f'Không đọc được phiên cũ; file vẫn được giữ lại: {exc}')
            return
        if state is None:
            return
        skipped = 0
        for row in state['reports']:
            if not isinstance(row, dict) or not isinstance(row.get('path'), str) or not row['path']:
                skipped += 1
                continue
            values = {key: row.get(key, '') for key in (*META_FIELDS, 'loai', 'trang_dau', 'trang_cuoi')}
            if not all(isinstance(value, str) for value in values.values()):
                skipped += 1
                continue
            report = ReportInput(Path(row['path']), **values)
            previous_max = row.get('so_trang_pdf', 0)
            report.so_trang_pdf = previous_max if isinstance(previous_max, int) and previous_max > 0 else 0
            uid = row.get('id')
            if not isinstance(uid, str) or not uid or uid in self.entries:
                uid = uuid4().hex
            try:
                report.so_trang_pdf = pdf_page_count(report.path)
                start = min(report.so_trang_pdf, max(1, int(report.trang_dau or '1')))
                end = min(report.so_trang_pdf, max(start, int(report.trang_cuoi or report.so_trang_pdf)))
                report.trang_dau, report.trang_cuoi = str(start), str(end)
            except (OSError, ValueError):
                self.unavailable_files[uid] = True
            self.entries[uid] = report
            self.files.insert('', 'end', iid=uid)
            self._render_report(uid)
        settings = state.get('settings', {})
        if isinstance(settings.get('include_tables'), bool):
            self.include_tables.set(settings['include_tables'])
        for key, variable in (('output_root', self.output_root), ('tesseract', self.tesseract), ('poppler', self.poppler)):
            value = settings.get(key)
            if isinstance(value, str):
                variable.set(value)
        selected = state.get('selected')
        if not isinstance(selected, str) or selected not in self.entries:
            selected = next(iter(self.entries), None)
        if selected is not None:
            self.files.selection_set(selected)
            self._select()
        result = state.get('last_result')
        if isinstance(result, str) and (Path(result) / 'chi_so_doanh_nghiep.csv').is_file():
            try:
                self.out = Path(result)
                count = self._populate_result_table(self.out)
                self.summary.set(f'Kết quả lần trước • {count} báo cáo • {self._loaded_scope}')
                for button in self.output_buttons:
                    button.configure(state='normal')
            except (OSError, ValueError, KeyError):
                self.out = None
        missing = len(self.unavailable_files)
        self.status.set(f'Đã khôi phục {len(self.entries)} báo cáo' + (f' • {missing} PDF cần chọn lại' if missing else ''))
        self.save_status.set('Đã khôi phục phiên trước' + (f' • Bỏ qua {skipped} mục không hợp lệ' if skipped else ''))

    def _render_report(self, uid):
        report = self.entries[uid]
        missing = uid in self.unavailable_files
        name = ('[Chọn lại PDF] ' if missing else '') + report.path.name
        self.files.item(uid, values=(name, f'{report.ma} / {report.nam}', report.loai),
                        tags=('missing',) if missing else ())

    def _relink_pdf(self):
        if self.current not in self.entries:
            messagebox.showinfo('Chọn báo cáo', 'Chọn báo cáo trong danh sách trước.', parent=self)
            return
        selected = filedialog.askopenfilename(parent=self, title='Chọn lại PDF của báo cáo này', filetypes=[('Báo cáo PDF', '*.pdf')])
        if not selected:
            return
        path = Path(selected).resolve()
        if any(uid != self.current and report.path.resolve() == path for uid, report in self.entries.items()):
            messagebox.showerror('PDF đã có trong danh sách', 'Hãy chọn PDF khác hoặc xóa dòng trùng trước.', parent=self)
            return
        try:
            maximum = pdf_page_count(path)
        except ValueError as exc:
            messagebox.showerror('Không đọc được PDF', str(exc), parent=self)
            return
        self._save_current()
        report = self.entries[self.current]
        report.path, report.so_trang_pdf = path, maximum
        self.unavailable_files.pop(self.current, None)
        self._refresh_pages()
        self._render_report(self.current)
        self._queue_session_save()

    def _style(self):
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure('.', font=('Segoe UI', 11), background='#eef3f8', foreground='#192b43')
        style.configure('TFrame', background='#eef3f8')
        style.configure('Card.TFrame', background='#ffffff')
        style.configure('Card.TLabel', background='#ffffff')
        style.configure('Title.TLabel', font=('Segoe UI', 25, 'bold'))
        style.configure('Heading.TLabel', font=('Segoe UI', 14, 'bold'))
        style.configure('Muted.TLabel', foreground='#52657b')
        style.configure('TButton', padding=(14, 9), background='#ffffff')
        style.configure('Accent.TButton', background='#147d70', foreground='#ffffff', font=('Segoe UI', 11, 'bold'))
        style.map('Accent.TButton', background=[('active', '#11685d'), ('disabled', '#c8d5d5')])
        style.configure('TEntry', padding=7, fieldbackground='white')
        style.configure('TCombobox', padding=7)
        style.configure('Treeview', rowheight=35, fieldbackground='white', background='white')
        style.configure('Treeview.Heading', font=('Segoe UI', 10, 'bold'), padding=8)
        style.map('Treeview', background=[('selected', '#d9eee9')], foreground=[('selected', '#123e36')])
        style.configure('TNotebook.Tab', padding=(22, 11))

    def _build(self):
        header = ttk.Frame(self, padding=(16, 10, 16, 4))
        header.pack(fill='x')
        ttk.Label(header, text='ESG Studio', style='Title.TLabel').pack(anchor='w')
        self.subtitle = ttk.Label(header, text='Phân tích công bố ESRS E5 • Từ báo cáo PDF đến bảng kết quả', style='Muted.TLabel')
        self.subtitle.pack(anchor='w', pady=(4, 0))
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill='both', expand=True, padx=16, pady=8)
        self.pages = [ScrollablePage(self.tabs) for _ in range(3)]
        for page, title in zip(self.pages, ('Chuẩn bị báo cáo', 'Kết quả phân tích', 'Cài đặt & hướng dẫn')):
            self.tabs.add(page, text=title)
        self._prepare(self.pages[0].content)
        self._results(self.pages[1].content)
        self._settings(self.pages[2].content)
        footer = ttk.Frame(self, padding=(16, 2, 16, 8))
        footer.pack(side='bottom', fill='x', before=self.tabs)
        footer.columnconfigure(0, weight=1)
        self.footer_status = ttk.Label(footer, textvariable=self.status, style='Muted.TLabel')
        self.footer_status.grid(row=0, column=0, sticky='w', padx=(0, 12))
        self.author_credit = ttk.Label(footer, text='made by Quýt', style='Muted.TLabel',
                                       font=('Segoe UI', 10, 'italic'))
        self.author_credit.grid(row=0, column=1, sticky='se')
        self._layout_pending = None
        self.bind('<Configure>', self._schedule_layout, add='+')
        for page in self.pages:
            page.canvas.bind('<Configure>', self._schedule_layout, add='+')
        self.after_idle(self._relayout)

    def _schedule_layout(self, event=None):
        if self._destroying:
            return
        if event is not None:
            parent = event.widget
            while parent is not None:
                if isinstance(parent, ScrollablePage):
                    parent._schedule()
                    break
                parent = getattr(parent, 'master', None)
        targets = (self, self.prepare_body, self.report_form, *(page.canvas for page in self.pages))
        if event is not None and event.widget not in targets:
            return
        if self._layout_pending is None:
            self._layout_pending = self.after_idle(self._relayout)

    def _relayout(self):
        if self._destroying:
            return
        self._layout_pending = None
        width = max(200, self.winfo_width() - 40)
        self.subtitle.configure(wraplength=width)
        self.footer_status.configure(wraplength=max(120, width - self.author_credit.winfo_reqwidth() - 16))
        font = tkfont.Font(font=ttk.Style(self).lookup('.', 'font'))
        titles = ('Chuẩn bị báo cáo', 'Kết quả phân tích', 'Cài đặt & hướng dẫn')
        if self.tabs.winfo_width() < sum(font.measure(title) + 50 for title in titles):
            titles = ('Báo cáo', 'Kết quả', 'Cài đặt')
        for page, title in zip(self.pages, titles):
            self.tabs.tab(page, text=title)
        field_width = max(control.winfo_reqwidth() for control in self.form_controls)
        body_width = self.prepare_body.winfo_width()
        wide = body_width >= field_width * 2 + 400
        self.file_panel.grid_configure(row=0, column=0, padx=(0, 14) if wide else 0, pady=(0, 0) if wide else (0, 14))
        self.report_form.grid_configure(row=0 if wide else 1, column=1 if wide else 0)
        self.prepare_body.columnconfigure(1, weight=1 if wide else 0)
        self.prepare_body.rowconfigure(0, weight=1 if wide else 0)
        self.prepare_body.rowconfigure(1, weight=0 if wide else 1)
        paired = self.report_form.winfo_width() >= field_width * 2 + 56
        self.report_form.columnconfigure(1, weight=1 if paired else 0)
        for index, (label, control) in enumerate(self.form_rows):
            row = 1 + (index // 2 if paired else index) * 2
            column = index % 2 if paired else 0
            label.grid_configure(row=row, column=column)
            control.grid_configure(row=row + 1, column=column)
        self.page_hint_label.grid_configure(row=9 if paired else 17, columnspan=2 if paired else 1)
        def wrap_labels(parent):
            for widget in parent.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.configure(wraplength=max(120, parent.winfo_width() - 40))
                wrap_labels(widget)
        for page in self.pages:
            wrap_labels(page.content)
            page._schedule()

    def _prepare(self, parent):
        toolbar = ttk.Frame(parent)
        toolbar.pack(fill='x', pady=(0, 12))
        ttk.Label(toolbar, text='Báo cáo của bạn', style='Heading.TLabel').pack(anchor='w', pady=(0, 8))
        toolbar_actions = FlowButtons(toolbar)
        toolbar_actions.pack(fill='x')
        self.add_button = ttk.Button(toolbar_actions, text='+ Thêm PDF', command=self._add, style='Accent.TButton')
        toolbar_actions.add(self.add_button)
        self.remove_button = ttk.Button(toolbar_actions, text='Xóa khỏi danh sách', command=self._remove)
        toolbar_actions.add(self.remove_button)
        self.relink_button = ttk.Button(toolbar_actions, text='Chọn lại PDF', command=self._relink_pdf)
        toolbar_actions.add(self.relink_button)
        body = ttk.Frame(parent)
        body.pack(fill='both', expand=True)
        self.prepare_body = body
        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)
        left = ttk.Frame(body)
        self.file_panel = left
        left.grid(row=0, column=0, sticky='nsew', padx=(0, 14))
        self.files = self._tree(left, [('file', 'File PDF', 220), ('company', 'Mã / năm', 110), ('kind', 'Loại', 70)])
        self.files.bind('<<TreeviewSelect>>', self._select)
        self.files.tag_configure('missing', foreground='#b42318')
        self.file_help = ttk.Label(left, text='Chọn báo cáo để sửa thông tin. File gốc được giữ nguyên.', style='Muted.TLabel')
        self.file_help.pack(anchor='w', fill='x', pady=10)
        form = ttk.Frame(body, style='Card.TFrame', padding=18)
        self.report_form = form
        form.grid(row=0, column=1, sticky='nsew')
        form.columnconfigure(0, weight=1)
        form.columnconfigure(1, weight=1)
        ttk.Label(form, text='Thông tin báo cáo', style='Card.TLabel', font=('Segoe UI', 14, 'bold')).grid(row=0, column=0, columnspan=2, sticky='w', pady=(0, 8))
        controls = [('ma', 'Mã công ty', 1, 0), ('nam', 'Năm báo cáo', 1, 1),
                    ('ten_cong_ty', 'Tên công ty', 3, 0), ('nganh', 'Ngành', 3, 1),
                    ('loai', 'Loại báo cáo', 5, 0), ('ky_bao_cao', 'Kỳ báo cáo', 5, 1),
                    ('trang_dau', 'Từ trang', 7, 0), ('trang_cuoi', 'Đến trang', 7, 1)]
        self.form_controls = []
        self.form_rows = []
        self.page_controls = {}
        for key, label, row, col in controls:
            span = 1
            field_label = ttk.Label(form, text=label, style='Card.TLabel')
            field_label.grid(row=row, column=col, columnspan=span, sticky='w', padx=(0, 10), pady=(5, 3))
            if key == 'loai':
                control = ttk.Combobox(form, textvariable=self.fields[key], values=('PTBV', 'ESG', 'BCTN'), state='readonly', width=12)
            elif key in ('trang_dau', 'trang_cuoi'):
                control = ttk.Combobox(form, textvariable=self.fields[key], state='disabled', width=12, height=12)
                self.page_controls[key] = control
            else:
                control = ttk.Entry(form, textvariable=self.fields[key], width=17)
            control.grid(row=row+1, column=col, columnspan=span, sticky='ew', padx=(0, 10))
            self.form_controls.append(control)
            self.form_rows.append((field_label, control))
        self.page_hint = tk.StringVar(value='Thêm PDF để chọn khoảng trang.')
        self.page_hint_label = ttk.Label(form, textvariable=self.page_hint, style='Card.TLabel', foreground='#52657b')
        self.page_hint_label.grid(row=9, column=0, columnspan=2, sticky='w', pady=8)
        bottom = ttk.Frame(parent)
        bottom.pack(side='bottom', fill='x', pady=(14, 0), before=body)
        self.progress = ttk.Progressbar(bottom, mode='indeterminate', length=100)
        self.progress.pack(side='left')
        self.run_button = ttk.Button(bottom, text='Bắt đầu phân tích', style='Accent.TButton', command=self._start)
        self.run_button.pack(side='right')

    def _tree(self, parent, columns):
        frame = ttk.Frame(parent)
        frame.pack(fill='both', expand=True)
        tree = ttk.Treeview(frame, columns=[c[0] for c in columns], show='headings', selectmode='browse', height=6)
        for key, label, width in columns:
            tree.heading(key, text=label)
            tree.column(key, width=width, minwidth=60)
        vertical = ttk.Scrollbar(frame, orient='vertical', command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient='horizontal', command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky='nsew')
        vertical.grid(row=0, column=1, sticky='ns')
        horizontal.grid(row=1, column=0, sticky='ew')
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        return tree

    def _results(self, parent):
        self.summary_label = ttk.Label(parent, textvariable=self.summary, style='Heading.TLabel')
        self.summary_label.pack(anchor='w', pady=(0, 10))
        self.result_table = self._tree(parent, [('ma', 'Mã', 75), ('nam', 'Năm', 60), ('loai', 'Loại', 65),
            ('so_trang', 'Số trang', 75), ('so_tu', 'Từ / âm tiết', 100), ('SYMB_1000', 'SYMB / 1.000', 110),
            ('SUBST_1000', 'SUBST / 1.000', 115), ('E5_1000', 'E5 / 1.000', 100), ('SUBST_RATIO', 'Tỷ lệ SUBST', 110)])
        self.result_help = ttk.Label(parent, text='SYMB: từ hình thức  •  SUBST: từ thực chất  •  E5: tài nguyên & kinh tế tuần hoàn\nTỷ lệ SUBST = SUBST / (SUBST + SYMB). Chỉ số mô tả, cần đối chiếu bằng chứng.', style='Muted.TLabel')
        self.result_help.pack(anchor='w', pady=10)
        actions = FlowButtons(parent)
        actions.pack(fill='x', pady=(0, 10))
        self.output_buttons = []
        for text, filename in [('Mở thư mục kết quả', None), ('Mở bảng chỉ số', 'chi_so_doanh_nghiep.csv'),
                               ('Mở file Excel', EXCEL_NAME), ('Xem bằng chứng', 'bao_cao_kiem_tra.txt')]:
            button = ttk.Button(actions, text=text, command=lambda f=filename: self._open_output(f), state='normal' if filename == EXCEL_NAME else 'disabled')
            actions.add(button)
            self.output_buttons.append(button)
        ttk.Label(parent, text='Nhật ký xử lý', style='Heading.TLabel').pack(anchor='w', pady=(4, 6))
        log_frame = ttk.Frame(parent)
        log_frame.pack(fill='both', expand=True)
        self.log = tk.Text(log_frame, height=6, bg='#15283e', fg='#e0ecf5', font=('Consolas', 10), wrap='word', relief='flat', padx=12, pady=10, state='disabled')
        scroll = ttk.Scrollbar(log_frame, command=self.log.yview)
        self.log.configure(yscrollcommand=scroll.set)
        self.log.pack(side='left', fill='both', expand=True)
        scroll.pack(side='right', fill='y')
        # Chia không gian cho bảng và nhật ký; không để bảng đẩy nhật ký ra ngoài.
        for widget in parent.winfo_children():
            widget.pack_forget()
        for index, widget in enumerate(parent.winfo_children()):
            widget.grid(row=index, column=0, sticky='nsew' if index in (1, 5) else 'ew', pady=(0, 8))
        parent.columnconfigure(0, weight=1)
        parent.rowconfigure(1, weight=3)
        parent.rowconfigure(5, weight=2, minsize=100)

    def _settings(self, parent):
        ttk.Label(parent, text='Phạm vi đếm từ', style='Heading.TLabel').pack(anchor='w', pady=(0, 8))
        self.tables_check = ttk.Checkbutton(parent, text='Đếm cả nội dung trong bảng', variable=self.include_tables)
        self.tables_check.pack(anchor='w', pady=(0, 6))
        ttk.Label(parent, text='Mặc định bật để đếm toàn bộ chữ trong các trang đã chọn. Nếu tắt, app loại bảng có đường kẻ. Số từ và tần suất luôn tính trên cùng phạm vi; Excel có sheet Từ khóa theo trang để đối chiếu.', style='Muted.TLabel').pack(anchor='w', fill='x', pady=(0, 18))
        ttk.Label(parent, text='Phiên làm việc được lưu tự động', style='Heading.TLabel').pack(anchor='w', pady=(0, 8))
        ttk.Label(parent, text='App nhớ danh sách PDF, thông tin đã nhập, khoảng trang và kết quả gần nhất. Giữ PDF tại vị trí cũ; nếu đã chuyển file, dùng Chọn lại PDF.', style='Muted.TLabel').pack(anchor='w', fill='x', pady=(0, 6))
        ttk.Label(parent, textvariable=self.save_status, style='Muted.TLabel').pack(anchor='w', fill='x', pady=(0, 18))
        ttk.Label(parent, text='Nơi lưu kết quả', style='Heading.TLabel').pack(anchor='w', pady=(0, 8))
        self._path_control(parent, self.output_root, 'Chọn thư mục', directory=True)
        ttk.Label(parent, text='Mỗi lần chạy tạo một thư mục riêng, giữ lại các kết quả trước.', style='Muted.TLabel').pack(anchor='w', pady=(6, 20))
        ttk.Label(parent, text='Đọc PDF & nhận dạng chữ tự động', style='Heading.TLabel').pack(anchor='w')
        ttk.Label(parent, text='Bộ đọc PDF tích hợp sẵn. App tự dùng OCR tiếng Việt/Anh khi gặp trang scan.', style='Muted.TLabel', wraplength=850).pack(anchor='w', pady=(6, 10))
        self.ocr_status = tk.StringVar(value='OCR đã sẵn sàng' if find_tesseract() else 'Bấm nút bên dưới để chuẩn bị OCR lần đầu')
        ttk.Label(parent, textvariable=self.ocr_status).pack(anchor='w', pady=4)
        self.ocr_button = ttk.Button(parent, text='Chuẩn bị OCR tự động', command=self._prepare_ocr)
        self.ocr_button.pack(anchor='w', pady=6)
        ttk.Label(parent, text='Nếu cần tải bổ sung, app chỉ tải công cụ OCR. Nội dung PDF luôn ở trên máy.', style='Muted.TLabel', wraplength=850).pack(anchor='w', pady=4)
        ttk.Separator(parent).pack(fill='x', pady=22)
        ttk.Label(parent, text='Bắt đầu trong 3 bước', style='Heading.TLabel').pack(anchor='w')
        text = ('1. Thêm một hoặc nhiều PDF ở tab Chuẩn bị báo cáo.\n'
                '2. Chọn từng file, nhập mã, tên công ty, ngành, năm và kỳ báo cáo.\n'
                '3. Bấm Bắt đầu phân tích. Xem chỉ số và mở bảng kết quả ở tab Kết quả.\n\n'
                'PTBV = báo cáo phát triển bền vững; ESG = báo cáo ESG; BCTN = báo cáo thường niên.\n'
                'Mặc định phân tích từ trang 1 đến hết PDF. Chọn khoảng trang để giới hạn phần PTBV.\n'
                'Trang kết thúc chỉ chọn được từ trang bắt đầu đến trang cuối PDF.\n'
                'LDA chỉ chạy khi đủ dữ liệu; lý do bỏ qua nằm trong nhật ký và chu_de_lda.json.\n'
                'Dữ liệu chỉ được xử lý trên máy. PDF gốc không bị thay đổi.')
        ttk.Label(parent, text=text, justify='left', wraplength=1000).pack(anchor='w', pady=10)

    def _path_control(self, parent, variable, text, directory):
        row = ttk.Frame(parent)
        row.pack(fill='x', pady=4)
        row.columnconfigure(0, weight=1)
        ttk.Entry(row, textvariable=variable, width=12).grid(row=0, column=0, sticky='ew', padx=(0, 10))
        def choose():
            path = filedialog.askdirectory(parent=self) if directory else filedialog.askopenfilename(parent=self, filetypes=[('Tesseract', '*.exe'), ('Tất cả', '*.*')])
            if path:
                variable.set(path)
        ttk.Button(row, text=text, command=choose).grid(row=0, column=1, sticky='e')

    def _save_current(self):
        if self.current in self.entries:
            report = self.entries[self.current]
            for key, value in self.fields.items():
                setattr(report, key, value.get().strip())
            report.ma = report.ma.upper()
            self._render_report(self.current)

    def _select(self, event=None):
        self._save_current()
        selection = self.files.selection()
        self.current = selection[0] if selection else None
        report = self.entries.get(self.current)
        self._updating_pages = True
        try:
            for key, var in self.fields.items():
                var.set(getattr(report, key) if report else '')
        finally:
            self._updating_pages = False
        self._refresh_pages()
        self._queue_session_save()

    def _refresh_pages(self, *_):
        if self._updating_pages:
            return
        self._updating_pages = True
        try:
            report = self.entries.get(self.current)
            if self.current in self.unavailable_files:
                for control in self.page_controls.values():
                    control.configure(values=(), state='disabled')
                self.page_hint.set('PDF không có sẵn • Bấm Chọn lại PDF')
                return
            maximum = report.so_trang_pdf if report else 0
            if not maximum:
                for control in self.page_controls.values():
                    control.configure(values=(), state='disabled')
                self.page_hint.set('Thêm PDF để chọn khoảng trang.')
                return
            def bounded(value, default):
                return max(1, min(maximum, int(value))) if value.isdigit() else default
            start = bounded(self.fields['trang_dau'].get(), 1)
            end = max(start, bounded(self.fields['trang_cuoi'].get(), maximum))
            self.fields['trang_dau'].set(str(start))
            self.fields['trang_cuoi'].set(str(end))
            state = 'disabled' if self.busy else 'readonly'
            self.page_controls['trang_dau'].configure(values=tuple(range(1, maximum + 1)), state=state)
            self.page_controls['trang_cuoi'].configure(values=tuple(range(start, maximum + 1)), state=state)
            report.trang_dau, report.trang_cuoi = str(start), str(end)
            self.page_hint.set(f'PDF có {maximum} trang • Đang chọn {end - start + 1} trang')
        finally:
            self._updating_pages = False

    def _add(self):
        paths = filedialog.askopenfilenames(parent=self, title='Chọn báo cáo PDF', filetypes=[('Báo cáo PDF', '*.pdf')])
        self._save_current()
        metadata = {}
        try:
            metadata_path = ROOT / 'danh_sach.csv'
            if not metadata_path.exists():
                metadata_path = RESOURCE_ROOT / 'danh_sach.csv'
            with metadata_path.open(encoding='utf-8-sig', newline='') as stream:
                metadata = {(r['ma'].upper(), r['nam']): r for r in csv.DictReader(stream)}
        except (OSError, KeyError):
            pass
        errors = []
        for name in paths:
            path = Path(name).resolve()
            if any(r.path == path for r in self.entries.values()):
                continue
            try:
                maximum = pdf_page_count(path)
            except Exception as exc:
                errors.append(f'{path.name}: không đọc được số trang PDF ({exc})')
                continue
            r = ReportInput(path, nam=str(datetime.now().year), ky_bao_cao=str(datetime.now().year),
                            trang_dau='1', trang_cuoi=str(maximum), so_trang_pdf=maximum)
            match = re.fullmatch(r'([A-Za-z0-9]+)_(\d{4})_(PTBV|ESG|BCTN)', path.stem, re.I)
            if match:
                r.ma, r.nam, r.loai = (x.upper() for x in match.groups())
                r.ky_bao_cao = r.nam
                for key, value in metadata.get((r.ma, r.nam), {}).items():
                    if key in META_FIELDS:
                        setattr(r, key, value)
            uid = uuid4().hex
            self.entries[uid] = r
            self.files.insert('', 'end', iid=uid, values=(path.name, f'{r.ma} / {r.nam}', r.loai))
        if self.entries and not self.files.selection():
            self.files.selection_set(next(iter(self.entries)))
        self.status.set(f'{len(self.entries)} báo cáo • Kiểm tra thông tin trước khi phân tích')
        self._queue_session_save()
        if errors:
            messagebox.showerror('Không thêm được một số PDF', '\n'.join(errors), parent=self)

    def _remove(self):
        selected = self.files.selection()
        self.current = None
        for uid in selected:
            self.files.delete(uid)
            self.entries.pop(uid, None)
            self.unavailable_files.pop(uid, None)
        if self.entries:
            self.files.selection_set(next(iter(self.entries)))
        self._select()
        self.status.set(f'{len(self.entries)} báo cáo trong danh sách')

    def _set_busy(self, busy):
        self.busy = busy
        for control in (self.add_button, self.remove_button, self.relink_button, self.run_button, self.ocr_button, self.tables_check, *self.form_controls):
            control.configure(state='disabled' if busy else ('readonly' if isinstance(control, ttk.Combobox) else 'normal'))
        if busy:
            self.progress.start(12)
        else:
            self.progress.stop()
        self._refresh_pages()

    def _prepare_ocr(self):
        if self.busy:
            return
        self._set_busy(True)
        self.ocr_status.set('Đang chuẩn bị OCR…')
        self.status.set('Đang chuẩn bị bộ OCR • Có thể cần Internet lần đầu')
        def work():
            try:
                prepare_ocr(lambda line: self.events.put(('log', line)))
                self.events.put(('ocr_ready', None))
            except Exception as exc:
                self.events.put(('ocr_failed', str(exc)))
        threading.Thread(target=work, daemon=True).start()

    def _start(self):
        if self.busy:
            return
        self._save_current()
        self._queue_session_save()
        self._save_session()
        reports = [ReportInput(**vars(r)) for r in self.entries.values()]
        try:
            validate_reports(reports)
            missing = [m for m in ('pdfplumber', 'pytesseract', 'pypdfium2', 'numpy', 'pandas', 'sklearn', 'openpyxl') if importlib.util.find_spec(m) is None]
            if missing:
                raise ValueError('Thiếu thư viện: ' + ', '.join(missing) + '\nHãy chạy Cai_dat_app.cmd trong thư mục ứng dụng.')
            if not self.output_root.get().strip():
                raise ValueError('Chọn nơi lưu kết quả trong tab Cài đặt & hướng dẫn.')
            for label, value, is_file in [('Tesseract', self.tesseract.get().strip(), True), ('Poppler', self.poppler.get().strip(), False)]:
                if value and not (Path(value).is_file() if is_file else Path(value).is_dir()):
                    raise ValueError(f'Đường dẫn {label} không tồn tại.')
        except ValueError as exc:
            messagebox.showerror('Cần kiểm tra thông tin', str(exc), parent=self)
            return
        out = Path(self.output_root.get().strip()).expanduser().resolve() / datetime.now().strftime('%Y-%m-%d_%H-%M-%S_%f')
        self.out = None
        self.result_table.delete(*self.result_table.get_children())
        for button in self.output_buttons:
            button.configure(state='disabled')
        self.log.configure(state='normal')
        self.log.delete('1.0', 'end')
        self.log.configure(state='disabled')
        self.summary.set(f'Đang phân tích {len(reports)} báo cáo…')
        self.status.set('Đang xử lý • Có thể theo dõi tiến trình trong nhật ký')
        self.tabs.select(1)
        self._set_busy(True)
        threading.Thread(target=run_analysis, args=(reports, out, self.tesseract.get().strip(), self.poppler.get().strip(), self.events, self.include_tables.get()), daemon=True).start()

    def _append_log(self, text):
        self.log.configure(state='normal')
        self.log.insert('end', text)
        self.log.see('end')
        self.log.configure(state='disabled')

    def _poll(self):
        try:
            while True:
                kind, value = self.events.get_nowait()
                if kind == 'log':
                    self._append_log(value)
                elif kind in ('ocr_ready', 'ocr_failed'):
                    self._set_busy(False)
                    if kind == 'ocr_ready':
                        self.ocr_status.set('OCR tiếng Việt/Anh đã sẵn sàng')
                        self.status.set('Sẵn sàng • Thêm PDF và bấm Bắt đầu phân tích')
                    else:
                        self.ocr_status.set('Chưa chuẩn bị xong OCR • Kiểm tra kết nối rồi thử lại')
                        self.status.set('Chuẩn bị OCR chưa hoàn tất')
                        messagebox.showerror('Chuẩn bị OCR', value, parent=self)
                elif kind == 'failed':
                    self._set_busy(False)
                    self.summary.set('Chưa hoàn tất • Xem lỗi bên dưới')
                    self.status.set('Xử lý gặp lỗi • Kiểm tra thông tin rồi thử lại')
                    self._append_log('\nLỖI: ' + value + '\n')
                    messagebox.showerror('Không thể hoàn tất', value, parent=self)
                elif kind == 'done':
                    code, self.out = value
                    self._set_busy(False)
                    try:
                        count = self._populate_result_table(self.out)
                        label = 'Hoàn tất' if code == 0 else 'Có báo cáo lỗi • Xem nhật ký để sửa và chạy lại'
                        self.summary.set(f'{count} / {len(self.entries)} báo cáo thành công • {label} • {self._loaded_scope}')
                        self.status.set(f'Kết quả đã lưu: {self.out.name}')
                        for button in self.output_buttons:
                            button.configure(state='normal')
                        lda_path = self.out / 'chu_de_lda.json'
                        if lda_path.exists():
                            lda = json.loads(lda_path.read_text(encoding='utf-8'))
                            for language, group in lda.get('nhom', {}).items():
                                self._append_log(f"LDA {language}: {group['trang_thai']}\n")
                        self._queue_session_save()
                    except (OSError, ValueError, KeyError) as exc:
                        self.summary.set('Chưa đọc được kết quả • Xem nhật ký')
                        self.status.set('Phân tích chưa hoàn tất')
                        self._append_log(f'Không đọc được bảng kết quả: {exc}\n')
        except queue.Empty:
            pass
        self.after(120, self._poll)

    def _populate_result_table(self, folder):
        with (Path(folder) / 'chi_so_doanh_nghiep.csv').open(encoding='utf-8-sig', newline='') as stream:
            rows = list(csv.DictReader(stream))
        scopes = {row.get('pham_vi_van_ban') or 'Kết quả cũ: chưa ghi phạm vi đếm' for row in rows}
        self._loaded_scope = '; '.join(sorted(scopes)) if scopes else 'Chưa có báo cáo thành công'
        self.result_table.delete(*self.result_table.get_children())
        for row in rows:
            values = []
            for key in self.result_table['columns']:
                value = row[key]
                if key == 'SUBST_RATIO':
                    value = f'{float(value):.1%}' if value else 'Không xác định'
                elif key.endswith('_1000'):
                    value = f'{float(value):.3f}'
                values.append(value)
            self.result_table.insert('', 'end', values=values)
        return len(rows)

    def _open_output(self, filename):
        if filename == EXCEL_NAME:
            try:
                if self.out:
                    path = self.out / EXCEL_NAME
                    if not path.is_file():
                        path = create_excel(self.out)
                else:
                    folders = sorted((ROOT / 'ket_qua').glob('*/' ), reverse=True)
                    initial = next((p for p in folders if (p / EXCEL_NAME).is_file()), ROOT / 'ket_qua')
                    selected = filedialog.askopenfilename(parent=self, title='Chọn kết quả Excel đã lưu',
                        initialdir=str(initial), filetypes=[('File Excel', '*.xlsx')])
                    if not selected:
                        return
                    path = Path(selected)
                open_excel(path)
            except (OSError, ValueError, ImportError) as exc:
                messagebox.showerror('Không mở được Excel', str(exc), parent=self)
            return
        if self.out:
            path = self.out / filename if filename else self.out
            try:
                os.startfile(str(path))
            except OSError as exc:
                messagebox.showerror('Không mở được file', f'{path}\n\n{exc}', parent=self)

    def _close(self):
        if self.busy:
            messagebox.showinfo('Đang phân tích', 'Hãy chờ xử lý hoàn tất trước khi đóng app để giữ đầy đủ kết quả.', parent=self)
        else:
            if not self._save_session():
                messagebox.showerror('Chưa lưu được phiên', self.save_status.get() + '\nApp vẫn mở để bạn không mất thông tin.', parent=self)
                return
            self.destroy()

    def destroy(self):
        if hasattr(self, 'session_path'):
            self._save_session()
        self._destroying = True
        # Các lịch cập nhật thuộc riêng cửa sổ này; không để chạy sau khi đóng.
        for callback in self.tk.call('after', 'info'):
            # Mỗi widget tự xóa Tcl command của nó trong destroy().
            self.tk.call('after', 'cancel', callback)
        super().destroy()


if __name__ == '__main__':
    ESGApp().mainloop()
