"""Kiểm tra cửa sổ nhỏ, cỡ chữ lớn và cuộn các vùng lồng nhau."""
import os
import tkinter as tk
from tkinter import ttk
import unittest

from app import ESGApp


@unittest.skipUnless(os.environ.get('ESG_GUI_TESTS') == '1', 'Cần phiên Tk trên Windows')
class ResponsiveUITests(unittest.TestCase):
    def make_app(self, scale=1.33333):
        class ScaledApp(ESGApp):
            def _style(app):
                app.tk.call('tk', 'scaling', scale)
                super()._style()
        app = ScaledApp(session_path=None)
        self.addCleanup(app.destroy)
        errors = []
        app.report_callback_exception = lambda *exc: errors.append(exc)
        return app, errors

    def assert_content_fits(self, parent, content):
        for widget in parent.winfo_children():
            if isinstance(widget, (ttk.Button, ttk.Entry, ttk.Combobox, ttk.Label)):
                right = widget.winfo_rootx() - content.winfo_rootx() + widget.winfo_width()
                self.assertLessEqual(right, content.winfo_width() + 2, str(widget))
            self.assert_content_fits(widget, content)

    def test_resize_and_scale_keep_controls_reachable(self):
        for scale in (1.33333, 2.0):
            app, errors = self.make_app(scale)
            for size in ('1280x900', '640x480', '480x360', '1280x900'):
                app.geometry(size)
                app.update()
                for page in app.pages:
                    app.tabs.select(page)
                    app.update()
                    self.assert_content_fits(page.content, page.content)
                    self.assertGreaterEqual(page.content.winfo_height(), page.content.winfo_reqheight(),
                                            (scale, size, app.pages.index(page)))
                    page.canvas.yview_moveto(1)
                    app.update()
                    self.assertAlmostEqual(page.canvas.yview()[1], 1, places=3)
                self.assertLessEqual(app.footer_status.winfo_rooty() - app.winfo_rooty() + app.footer_status.winfo_height(), app.winfo_height())
                self.assertEqual(app.author_credit['text'], 'made by Quýt')
                self.assertLessEqual(app.author_credit.winfo_rootx() - app.winfo_rootx() + app.author_credit.winfo_width(), app.winfo_width())
                self.assertLessEqual(app.author_credit.winfo_rooty() - app.winfo_rooty() + app.author_credit.winfo_height(), app.winfo_height())
            self.assertFalse(errors, errors)
            app.destroy()
            self._cleanups.pop()

    def test_wheel_scrolls_parent_native_regions_and_horizontal_table(self):
        app, errors = self.make_app()
        app.geometry('640x480')
        app.update()
        prepare = app.pages[0]
        prepare.canvas.yview_moveto(0)
        app.wheel_router.route(app.form_controls[0], 3)
        self.assertGreater(prepare.canvas.yview()[0], 0)
        # Khi bảng rỗng không còn gì để cuộn, con lăn chuyển sang cuộn trang.
        prepare.canvas.yview_moveto(0)
        app.wheel_router.route(app.files, 3)
        self.assertGreater(prepare.canvas.yview()[0], 0)
        app.tabs.select(1)
        for i in range(50):
            app.result_table.insert('', 'end', values=[str(i)] * 9)
        app._append_log('Dòng nhật ký\n' * 100)
        app.update()
        results = app.pages[1]
        results.canvas.yview_moveto(0)
        app.result_table.yview_moveto(0)
        app.wheel_router.route(app.result_table, 3)
        self.assertGreater(app.result_table.yview()[0], 0)
        self.assertEqual(results.canvas.yview()[0], 0)
        app.result_table.xview_moveto(0)
        app.wheel_router.route(app.result_table, 3, 'x')
        self.assertGreater(app.result_table.xview()[0], 0)
        app.log.yview_moveto(0)
        app.wheel_router.route(app.log, 3)
        self.assertGreater(app.log.yview()[0], 0)
        app.tabs.select(2)
        app.update()
        settings = app.pages[2]
        settings.canvas.yview_moveto(0)
        # Sự kiện con lăn qua bindtag, không chỉ gọi trực tiếp hàm cuộn.
        app.ocr_button.event_generate('<MouseWheel>', delta=-120, x=2, y=2)
        app.update()
        self.assertGreater(settings.canvas.yview()[0], 0)
        self.assertFalse(errors, errors)
