import os


PACKAGE_DIR = os.path.dirname(os.path.realpath(__file__))
ROOT_DIR = os.path.dirname(PACKAGE_DIR)
ASSETS_DIR = os.path.join(ROOT_DIR, 'assets')
ICONS_DIR = os.path.join(ASSETS_DIR, 'icons')
DATA_DIR = os.path.join(ROOT_DIR, 'data')

os.makedirs(ASSETS_DIR, exist_ok=True)
os.makedirs(ICONS_DIR, exist_ok=True)
os.makedirs(DATA_DIR, exist_ok=True)

