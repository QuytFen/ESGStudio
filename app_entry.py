"""Điểm vào cho ESGStudio.exe: giao diện hoặc tiến trình phân tích nền."""
import multiprocessing
from pathlib import Path
import sys
import traceback


def run():
    multiprocessing.freeze_support()
    if len(sys.argv) > 2 and sys.argv[1] == '--pipeline':
        log_path = Path(sys.argv[2])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open('w', encoding='utf-8', buffering=1) as stream:
            sys.stdout = sys.stderr = stream
            sys.argv = [sys.argv[0], *sys.argv[3:]]
            try:
                from main import main
                return main()
            except Exception:
                traceback.print_exc()
                return 1
    try:
        from app import ESGApp
        ESGApp().mainloop()
        return 0
    except Exception:
        from app_paths import DATA_ROOT
        DATA_ROOT.mkdir(parents=True, exist_ok=True)
        path = DATA_ROOT / 'loi_khoi_dong.txt'
        path.write_text(traceback.format_exc(), encoding='utf-8')
        import tkinter.messagebox
        tkinter.messagebox.showerror('ESG Studio', f'Không mở được app. Chi tiết lỗi: {path}')
        return 1


if __name__ == '__main__':
    raise SystemExit(run())
