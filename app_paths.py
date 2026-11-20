"""Tách tài nguyên đóng gói khỏi dữ liệu người dùng cần giữ qua các lần mở."""
import os
from pathlib import Path
import sys

APP_VERSION = '1.1.1'
FROZEN = bool(getattr(sys, 'frozen', False))
RESOURCE_ROOT = Path(__file__).resolve().parent
APP_ROOT = Path(sys.executable).resolve().parent if FROZEN else RESOURCE_ROOT
override = os.environ.get('ESG_STUDIO_DATA_DIR')
DATA_ROOT = Path(override).expanduser().resolve() if override else (APP_ROOT / 'du_lieu' if FROZEN else APP_ROOT)
