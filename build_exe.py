"""Build và giữ lại dữ liệu portable khi cập nhật bản .exe."""
import os
from pathlib import Path
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def build(onefile=False, both=False):
    modes = ('onefile', 'portable') if both else ('onefile',) if onefile else ('portable',)
    backups = []
    for mode in modes:
        destination = ROOT / 'dist' / ('du_lieu' if mode == 'onefile' else 'ESGStudio/du_lieu')
        backup = ROOT / 'build' / ('saved_data_' + mode)
        if destination.is_dir():
            shutil.copytree(destination, backup, dirs_exist_ok=True)
            backups.append((backup, destination))
    env = os.environ.copy()
    env['ESG_BUILD_ONEFILE'] = 'both' if both else '1' if onefile else '0'
    process = subprocess.run([sys.executable, '-m', 'PyInstaller', str(ROOT / 'ESGStudio.spec'),
                              '--noconfirm'], cwd=ROOT, env=env)
    for backup, destination in backups:
        shutil.copytree(backup, destination, dirs_exist_ok=True)
    return process.returncode


if __name__ == '__main__':
    raise SystemExit(build('onefile' in sys.argv[1:], 'both' in sys.argv[1:]))
