import os
from cloudweb.settings import load_settings
from cloudweb.tor_manager import TorManager


def apply_proxy_and_start_tor(settings):
    if settings.get('tor_enabled', False):
        os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--proxy-server=socks5://127.0.0.1:9050'
        TorManager().start()


def main():
    settings = load_settings()
    apply_proxy_and_start_tor(settings)
    from PyQt6.QtWidgets import QApplication
    from cloudweb.main_window import MainWindow
    app = QApplication([])
    app.setApplicationName("CloudWeb")
    app.setStyle("Fusion")
    window = MainWindow()
    app.exec()


if __name__ == '__main__':
    main()

