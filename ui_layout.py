"""Bố cục co giãn và cuộn cho các tab của app Tkinter."""
import tkinter as tk
from tkinter import ttk


class ScrollablePage(ttk.Frame):
    def __init__(self, parent, padding=16):
        super().__init__(parent)
        self.canvas = tk.Canvas(self, bg='#eef3f8', highlightthickness=0,
                                width=1, height=1, yscrollincrement=24)
        self.scrollbar = ttk.Scrollbar(self, orient='vertical', command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        self.canvas.grid(row=0, column=0, sticky='nsew')
        self.scrollbar.grid(row=0, column=1, sticky='ns')
        self.rowconfigure(0, weight=1)
        self.columnconfigure(0, weight=1)
        self.content = ttk.Frame(self.canvas, padding=padding)
        self.window = self.canvas.create_window((0, 0), window=self.content, anchor='nw')
        self._pending = None
        self.canvas.bind('<Configure>', self._schedule)
        self.content.bind('<Configure>', self._schedule)

    def _schedule(self, event=None):
        if self._pending is None:
            self._pending = self.after_idle(self._sync)

    def _sync(self):
        self._pending = None
        width = max(1, self.canvas.winfo_width())
        height = max(self.content.winfo_reqheight(), self.canvas.winfo_height())
        self.canvas.itemconfigure(self.window, width=width, height=height)
        self.canvas.configure(scrollregion=(0, 0, width, height))

    def reveal(self, widget):
        if self.canvas.yview() == (0.0, 1.0):
            return
        top = widget.winfo_rooty() - self.canvas.winfo_rooty()
        bottom = top + widget.winfo_height()
        visible = self.canvas.winfo_height()
        if top < 0 or bottom > visible:
            position = widget.winfo_rooty() - self.content.winfo_rooty()
            if bottom > visible:
                position -= visible - widget.winfo_height() - 16
            self.canvas.yview_moveto(max(0, position - 12) / max(1, self.content.winfo_height()))


class FlowButtons(ttk.Frame):
    """Các nút tự xuống hàng khi cửa sổ hoặc cỡ chữ thay đổi."""
    def __init__(self, parent, align='left'):
        super().__init__(parent)
        self.align = align
        self.buttons = []
        self._pending = None
        self.bind('<Configure>', self._schedule)

    def add(self, button):
        self.buttons.append(button)
        self._schedule()

    def destroy(self):
        if self._pending is not None:
            self.after_cancel(self._pending)
            self._pending = None
        super().destroy()

    def _schedule(self, event=None):
        if self._pending is None:
            self._pending = self.after_idle(self._layout)

    def _layout(self):
        self._pending = None
        width = max(1, self.winfo_width())
        if self.align == 'right':
            sizes = [button.winfo_reqwidth() + 8 for button in self.buttons]
            columns = max(1, len(sizes))
            while columns > 1 and (len(sizes) % columns or
                    sum(max(sizes[i::columns], default=0) for i in range(columns)) > width):
                columns -= 1
            self.grid_anchor('e')
            for index, button in enumerate(self.buttons):
                button.grid(row=index // columns, column=index % columns, sticky='e', padx=(8, 0), pady=(0, 6))
            return
        row = column = used = 0
        for button in self.buttons:
            size = button.winfo_reqwidth() + 8
            if used and used + size > width:
                row, column, used = row + 1, 0, 0
            button.grid(row=row, column=column, sticky='w', padx=(0, 8), pady=(0, 6))
            used += size
            column += 1


def scroll_widget(widget, units, axis='y'):
    """Trả False ở mép để con lăn có thể chuyển sang cuộn trang cha."""
    view = getattr(widget, axis + 'view', None)
    scroll = getattr(widget, axis + 'view_scroll', None)
    if view is None or scroll is None:
        return False
    try:
        first, last = view()
        if (units < 0 and first <= 0) or (units > 0 and last >= 1):
            return False
        scroll(units, 'units')
        return True
    except tk.TclError:
        return False


class WheelRouter:
    """Cuộn vùng dưới chuột; chặn cuộn chuột làm đổi ô chọn trang."""
    def __init__(self, root):
        self.root = root
        self.tag = f'ESGWheel{id(self)}'
        for sequence in ('<MouseWheel>', '<Shift-MouseWheel>', '<Button-4>', '<Button-5>'):
            root.bind_class(self.tag, sequence, self._wheel)
        root.bind_class(self.tag, '<FocusIn>', self._focus)
        self.register(root)

    def register(self, widget):
        tags = widget.bindtags()
        if self.tag not in tags:
            widget.bindtags((self.tag, *tags))
        for child in widget.winfo_children():
            self.register(child)

    def _wheel(self, event):
        target = self.root.winfo_containing(event.x_root, event.y_root) or event.widget
        if getattr(event, 'num', None) in (4, 5):
            units = -3 if event.num == 4 else 3
        else:
            delta = getattr(event, 'delta', 0)
            if not delta:
                return 'break'
            units = -max(1, abs(delta) // 120) * 3 if delta > 0 else max(1, abs(delta) // 120) * 3
        axis = 'x' if event.state & 1 else 'y'
        return self.route(target, units, axis)

    def route(self, target, units, axis='y'):
        widget = target
        while widget is not None:
            if isinstance(widget, (ttk.Treeview, tk.Text, tk.Listbox)):
                if scroll_widget(widget, units, axis):
                    return 'break'
            if isinstance(widget, ScrollablePage):
                if scroll_widget(widget.canvas, units, axis):
                    return 'break'
            widget = getattr(widget, 'master', None)
        return 'break'

    def _focus(self, event):
        widget = event.widget
        if not isinstance(widget, (ttk.Entry, ttk.Combobox, ttk.Button, ttk.Treeview, tk.Text)):
            return
        parent = widget.master
        while parent is not None:
            if isinstance(parent, ScrollablePage):
                parent.after_idle(lambda p=parent, w=widget: p.reveal(w) if w.winfo_exists() else None)
                break
            parent = getattr(parent, 'master', None)
