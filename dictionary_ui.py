"""Giao diện chỉnh từ điển; bộ mặc định luôn chỉ đọc."""
import copy
from pathlib import Path
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, simpledialog
from uuid import uuid4

from dem_tu import dem_tu
from dictionary_store import (default_dictionary, load_dictionary, save_dictionary,
    validate_dictionary, dictionary_groups, export_dictionary_excel, import_dictionary_excel)
from ui_layout import FlowButtons, ScrollablePage


class DictionaryPanel(ttk.LabelFrame):
    def __init__(self, parent, folder, on_change):
        super().__init__(parent, text='Bộ từ điển', padding=10)
        self.folder, self.on_change = Path(folder), on_change
        self.profiles = {'default': default_dictionary()}
        errors = []
        if self.folder.exists():
            for path in sorted(self.folder.glob('*.json')):
                if path.stem == 'default':
                    continue
                try:
                    self.profiles[path.stem] = load_dictionary(path)
                except (OSError, ValueError) as exc:
                    errors.append(f'{path.name}: {exc}')
        self.choice = ttk.Combobox(self, state='readonly')
        self.choice.pack(fill='x', pady=(0, 8))
        self._refresh('default')
        self.choice.bind('<<ComboboxSelected>>', lambda _: self.on_change())
        buttons = FlowButtons(self)
        buttons.pack(fill='x')
        for label, command in [('Xem / chỉnh từ điển', self.edit), ('Sao chép thành bộ riêng', self.clone),
                               ('Nhập Excel', self.import_excel), ('Xuất Excel / mẫu', self.export_excel)]:
            buttons.add(ttk.Button(buttons, text=label, command=command))
        ttk.Label(self, text='Giữ nguyên ba nhóm SYMB/SUBST/E5. Kết quả cũ không tự tính lại.',
                  wraplength=390).pack(anchor='w', pady=(6, 0))
        if errors:
            self.after_idle(lambda: messagebox.showwarning('Không đọc được một số từ điển',
                '\n'.join(errors) + '\nCác file lỗi vẫn được giữ lại.', parent=self))

    def selected_id(self):
        index = self.choice.current()
        return list(self.profiles)[index if index >= 0 else 0]

    def current_dictionary(self):
        return copy.deepcopy(self.profiles[self.selected_id()])

    def _refresh(self, uid):
        self.choice['values'] = [f'{v["name"]} ({k[:8]})' if k != 'default' else v['name']
                                 for k, v in self.profiles.items()]
        self.choice.current(list(self.profiles).index(uid))

    def restore_selection(self, uid):
        self._refresh(uid if uid in self.profiles else 'default')
        if uid not in self.profiles:
            self.after_idle(lambda: messagebox.showwarning('Từ điển đã chọn không còn tồn tại',
                'Đang chọn bộ Mặc định. Hãy kiểm tra bộ từ điển trước khi chạy.', parent=self))

    def persist(self, data, uid=None):
        warnings = validate_dictionary(data)
        if warnings and not messagebox.askyesno('Biến thể trùng nhau',
                '\n'.join(warnings[:15]) + '\nApp ưu tiên cụm dài; cùng đoạn chữ chỉ đếm một lần. Nếu cùng độ dài/vị trí, ưu tiên SYMB → SUBST → E5 rồi thứ tự mục. Vẫn lưu?', parent=self):
            return False
        uid = uid or uuid4().hex
        save_dictionary(self.folder / f'{uid}.json', data)
        self.profiles[uid] = copy.deepcopy(data)
        self._refresh(uid)
        self.on_change()
        return True

    def clone(self):
        data = self.current_dictionary()
        name = simpledialog.askstring('Bộ từ điển mới', 'Tên bộ riêng:',
                                     initialvalue=data['name'] + ' - bản riêng', parent=self)
        if name:
            data['name'] = name.strip()
            try:
                if self.persist(data):
                    self.edit()
            except (OSError, ValueError) as exc:
                messagebox.showerror('Chưa lưu được', str(exc), parent=self)

    def import_excel(self):
        path = filedialog.askopenfilename(parent=self, filetypes=[('Từ điển Excel', '*.xlsx')])
        if path:
            try:
                data = import_dictionary_excel(path)
                name = simpledialog.askstring('Nhập thành bộ mới', 'Tên bộ từ điển:', initialvalue=data['name'], parent=self)
                if name:
                    data['name'] = name.strip()
                    self.persist(data)
            except Exception as exc:
                messagebox.showerror('Không nhập được Excel', str(exc), parent=self)

    def export_excel(self):
        path = filedialog.asksaveasfilename(parent=self, defaultextension='.xlsx',
            initialfile='tu_dien.xlsx', filetypes=[('Excel', '*.xlsx')])
        if path:
            try:
                export_dictionary_excel(path, self.current_dictionary())
                messagebox.showinfo('Đã xuất từ điển', 'Sửa trong sheet Từ điển; xem sheet Hướng dẫn để nhập lại.', parent=self)
            except Exception as exc:
                messagebox.showerror('Không xuất được Excel', str(exc), parent=self)

    def edit(self):
        DictionaryEditor(self, self.selected_id(), self.current_dictionary())


class DictionaryEditor(tk.Toplevel):
    def __init__(self, panel, uid, data):
        super().__init__(panel)
        self.panel, self.uid, self.data = panel, uid, data
        self.original = copy.deepcopy(data)
        self.title('Quản lý từ điển — ' + data['name'])
        self.geometry('880x720')
        self.minsize(480, 360)
        self.transient(panel.winfo_toplevel())
        self.grab_set()
        self.protocol('WM_DELETE_WINDOW', self.close)
        page = ScrollablePage(self)
        page.pack(fill='both', expand=True)
        body = page.content
        self.name = tk.StringVar(value=data['name'])
        ttk.Label(body, text='Tên bộ từ điển').pack(anchor='w')
        ttk.Entry(body, textvariable=self.name).pack(fill='x')
        ttk.Label(body, text='Bộ mặc định chỉ đọc. Hãy sao chép thành bộ riêng để sửa.' if uid == 'default'
                  else 'Chọn mục để sửa. Bấm Áp dụng mục trước khi chuyển sang mục khác.', wraplength=400).pack(anchor='w', pady=6)
        frame = ttk.Frame(body)
        frame.pack(fill='x')
        self.table = ttk.Treeview(frame, columns=('group', 'name', 'enabled'), show='headings', height=7, selectmode='browse')
        for key, title, width in [('group', 'Nhóm', 80), ('name', 'Từ khóa', 210), ('enabled', 'Dùng', 60)]:
            self.table.heading(key, text=title)
            self.table.column(key, width=width, minwidth=50)
        scroll = ttk.Scrollbar(frame, command=self.table.yview)
        self.table.configure(yscrollcommand=scroll.set)
        self.table.pack(side='left', fill='x', expand=True)
        scroll.pack(side='right', fill='y')
        self.table.bind('<<TreeviewSelect>>', self.select)
        row = ttk.Frame(body)
        row.pack(fill='x', pady=6)
        self.group = tk.StringVar(value='E5')
        ttk.Combobox(row, textvariable=self.group, values=('SYMB', 'SUBST', 'E5'), state='readonly', width=9).pack(side='left')
        self.term = tk.StringVar()
        ttk.Entry(row, textvariable=self.term).pack(side='left', fill='x', expand=True, padx=6)
        self.enabled = tk.BooleanVar(value=True)
        ttk.Checkbutton(row, text='Dùng', variable=self.enabled).pack(side='left')
        self.en = self.text_field(body, 'Biến thể tiếng Anh — mỗi dòng một cụm')
        self.vi = self.text_field(body, 'Biến thể tiếng Việt — mỗi dòng một cụm')
        ttk.Label(body, text='Mẫu tiếng Anh nâng cao (regex); để trống nếu dùng các biến thể bên trên', wraplength=400).pack(anchor='w')
        self.pattern = tk.StringVar()
        ttk.Entry(body, textvariable=self.pattern).pack(fill='x')
        buttons = FlowButtons(body)
        buttons.pack(fill='x', pady=6)
        for label, command in [('Mục mới', self.new), ('Áp dụng mục', self.apply), ('Xóa mục', self.remove), ('Lưu bộ từ điển', self.save)]:
            button = ttk.Button(buttons, text=label, command=command)
            buttons.add(button)
            if uid == 'default':
                button.configure(state='disabled')
        ttk.Separator(body).pack(fill='x', pady=8)
        self.sample = self.text_field(body, 'Thử đoạn văn — dùng các mục đã áp dụng, không lưu thay đổi')
        self.language = tk.StringVar(value='vi')
        ttk.Combobox(body, textvariable=self.language, values=('vi', 'en'), state='readonly', width=10).pack(anchor='w')
        ttk.Button(body, text='Thử đếm', command=self.preview).pack(anchor='w', pady=5)
        self.preview_text = tk.StringVar()
        ttk.Label(body, textvariable=self.preview_text, wraplength=400).pack(fill='x')
        self.active = None
        self.refresh()
        router = getattr(panel.winfo_toplevel(), 'wheel_router', None)
        if router is not None:
            router.register(self)

    def form_entry(self):
        return {'group': self.group.get(), 'name': self.term.get().strip(), 'enabled': self.enabled.get(),
                'pattern': self.pattern.get().strip(),
                'english': [v.strip() for v in self.en.get('1.0', 'end').splitlines() if v.strip()],
                'vietnamese': [v.strip() for v in self.vi.get('1.0', 'end').splitlines() if v.strip()]}

    def form_dirty(self):
        if self.uid == 'default':
            return False
        entry = self.form_entry()
        if self.active is None:
            return bool(entry['name'] or entry['english'] or entry['vietnamese'] or entry['pattern'])
        return entry != self.data['entries'][self.active]

    @staticmethod
    def text_field(parent, title):
        ttk.Label(parent, text=title, wraplength=400).pack(anchor='w')
        text = tk.Text(parent, height=3, wrap='word', font=('Segoe UI', 10), undo=True)
        text.pack(fill='x', pady=(0, 5))
        return text

    def refresh(self, selection=None):
        self.table.delete(*self.table.get_children())
        for i, e in enumerate(self.data['entries']):
            self.table.insert('', 'end', iid=str(i), values=(e['group'], e['name'], 'Có' if e['enabled'] else 'Tắt'))
        if selection is not None:
            self.table.selection_set(str(selection))

    def select(self, _=None):
        selection = self.table.selection()
        if not selection:
            return
        next_index = int(selection[0])
        if next_index == self.active:
            return
        if next_index != self.active and self.form_dirty():
            if not messagebox.askyesno('Mục chưa áp dụng', 'Bỏ chỉnh sửa của mục đang nhập để chọn mục khác?', parent=self):
                if self.active is not None:
                    self.table.selection_set(str(self.active))
                else:
                    self.table.selection_remove(*selection)
                return
        self.active = next_index
        e = self.data['entries'][self.active]
        self.group.set(e['group'])
        self.term.set(e['name'])
        self.enabled.set(e['enabled'])
        self.pattern.set(e.get('pattern', ''))
        for widget, field in ((self.en, 'english'), (self.vi, 'vietnamese')):
            widget.delete('1.0', 'end')
            widget.insert('1.0', '\n'.join(e[field]))

    def new(self):
        if self.form_dirty() and not messagebox.askyesno('Mục chưa áp dụng', 'Bỏ chỉnh sửa của mục đang nhập?', parent=self):
            return
        self.clear_form()

    def clear_form(self):
        self.active = None
        self.table.selection_remove(*self.table.selection())
        self.term.set('')
        self.enabled.set(True)
        self.pattern.set('')
        for widget in (self.en, self.vi):
            widget.delete('1.0', 'end')

    def apply(self):
        if self.uid == 'default':
            return False
        entry = self.form_entry()
        draft = copy.deepcopy(self.data)
        if self.active is None:
            draft['entries'].append(entry)
            index = len(draft['entries']) - 1
        else:
            index = self.active
            draft['entries'][index] = entry
        try:
            validate_dictionary(draft)
        except ValueError as exc:
            messagebox.showerror('Kiểm tra mục từ', str(exc), parent=self)
            return False
        self.data = draft
        self.active = index
        self.refresh(index)
        return True

    def remove(self):
        if self.uid != 'default' and self.active is not None:
            del self.data['entries'][self.active]
            self.clear_form()
            self.refresh()

    def save(self):
        if self.uid == 'default':
            return
        if (self.active is not None or self.term.get().strip()) and not self.apply():
            return
        self.data['name'] = self.name.get().strip()
        try:
            if self.panel.persist(self.data, self.uid):
                self.destroy()
        except (OSError, ValueError) as exc:
            messagebox.showerror('Chưa lưu được', str(exc), parent=self)

    def preview(self):
        try:
            groups = dictionary_groups(self.data)
            counts = dem_tu(self.sample.get('1.0', 'end'), self.language.get(), groups)
            self.preview_text.set('\n'.join(f'{g} / {n}: {c}' for (g, n), c in counts.items() if c) or 'Không có từ khóa khớp.')
        except ValueError as exc:
            messagebox.showerror('Kiểm tra từ điển', str(exc), parent=self)

    def close(self):
        if self.uid != 'default' and (self.data != self.original or self.name.get() != self.original['name'] or self.form_dirty()):
            if not messagebox.askyesno('Đóng trình sửa', 'Đóng và bỏ các thay đổi chưa lưu?', parent=self):
                return
        self.destroy()
