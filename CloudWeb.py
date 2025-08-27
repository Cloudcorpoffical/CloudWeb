from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *
from PyQt6.QtPrintSupport import *
import os
import sys
import json
import socket
import subprocess
import atexit
import shutil
 
dir_path = os.path.dirname(os.path.realpath(__file__))

# -----------------------------
# Settings and Tor integration
# -----------------------------

def _get_settings_path():
	return os.path.join(dir_path, 'settings.json')


def load_settings():
	settings_path = _get_settings_path()
	if os.path.exists(settings_path):
		try:
			with open(settings_path, 'r', encoding='utf-8') as f:
				return json.load(f)
		except Exception:
			pass
	return {"tor_enabled": False}


def save_settings(settings: dict):
	try:
		with open(_get_settings_path(), 'w', encoding='utf-8') as f:
			json.dump(settings, f, ensure_ascii=False, indent=2)
	except Exception:
		pass


def _is_port_open(host: str, port: int) -> bool:
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(0.2)
	try:
		return s.connect_ex((host, port)) == 0
	finally:
		s.close()


class TorManager:
	"""Simple Tor process manager using system 'tor' binary.

	- Uses SOCKS at 127.0.0.1:9050
	- Creates a DataDirectory under app folder
	- Starts tor only if port is not already open
	"""

	def __init__(self, socks_host: str = '127.0.0.1', socks_port: int = 9050):
		self.socks_host = socks_host
		self.socks_port = socks_port
		self.process = None
		self.started_by_us = False
		self.tor_binary = shutil.which('tor')
		self.data_dir = os.path.join(dir_path, 'tor_data')
		os.makedirs(self.data_dir, exist_ok=True)

	def start(self):
		if _is_port_open(self.socks_host, self.socks_port):
			return True
		if not self.tor_binary:
			return False
		cmd = [
			self.tor_binary,
			f"--SOCKSPort", f"{self.socks_port}",
			f"--DataDirectory", self.data_dir,
		]
		try:
			self.process = subprocess.Popen(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
			self.started_by_us = True
			return True
		except Exception:
			self.process = None
			self.started_by_us = False
			return False

	def stop(self):
		if self.process and self.started_by_us:
			try:
				self.process.terminate()
			except Exception:
				pass
			self.process = None
			self.started_by_us = False


_settings = load_settings()
_tor_manager = TorManager()

# Apply Chromium proxy flag as early as possible (before QApplication / WebEngine init)
if _settings.get('tor_enabled', False):
	os.environ['QTWEBENGINE_CHROMIUM_FLAGS'] = '--proxy-server=socks5://127.0.0.1:9050'
	_tor_manager.start()

class MainWindow(QMainWindow):
    global menu
 

    def __init__(self, *args, **kwargs):
        global menu_btn
        super(MainWindow, self).__init__(*args, **kwargs)

        self.tabs = QTabWidget()
        self.tabs.setDocumentMode(True)
        self.tabs.tabBarDoubleClicked.connect(self.tab_open_doubleclick)
        self.tabs.currentChanged.connect(self.current_tab_changed)
        self.tabs.setTabsClosable(True)
        self.tabs.tabCloseRequested.connect(self.close_current_tab)
        self.setCentralWidget(self.tabs)

        self.status = QStatusBar()
        self.setStatusBar(self.status)
        navtb = QToolBar("Navigation")
        self.addToolBar(navtb)

        back_btn_icon = (dir_path + r'\back.png')
        back_btn = QAction("Back", self)
        back_btn.setIcon(QIcon(back_btn_icon))
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)

        forward_btn_icon = (dir_path + r'\forward.png')
        next_btn = QAction("Forward", self)
        next_btn.setIcon(QIcon(forward_btn_icon))
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)

        reload_btn_icon = (dir_path + r'\reload.png')
        reload_btn = QAction("Reload", self)
        reload_btn.setIcon(QIcon(reload_btn_icon))
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        home_btn_icon = (dir_path + r'\home.png')
        home_btn = QAction("Home", self)
        home_btn.setIcon(QIcon(home_btn_icon))
        home_btn.setStatusTip("Go home")
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)
        navtb.addSeparator()
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        settings_icon = (dir_path + r'\Settings_icon.png')


        menu_btn_icon = (dir_path + r'\menu_icon.png')
        menu_btn = QPushButton(self)
        menu_btn.setIcon(QIcon(menu_btn_icon))
        menu_btn.setIconSize(QSize(23, 23))
        menu_btn.setStatusTip("Открыть меню")

        menu = QMenu(menu_btn)
        settings = QAction()
        settings.setIcon(QIcon(settings_icon))
        settings.setText("Настройки")
        menu.addAction(settings)

        menu.addSeparator()
        self.tor_action = QAction("Использовать Tor", self)
        self.tor_action.setCheckable(True)
        self.tor_action.setChecked(_settings.get('tor_enabled', False))
        self.tor_action.setStatusTip("Маршрутизировать трафик через Tor (SOCKS5 127.0.0.1:9050)")
        self.tor_action.triggered.connect(self.on_toggle_tor)
        menu.addAction(self.tor_action)     

        def menu_func():
           menu.exec()   

        menu_btn.clicked.connect(menu_func)
        navtb.addWidget(menu_btn)

        self.add_new_tab(QUrl('http://google.com'), 'Homepage')
        self.show()
        self.setWindowTitle("CloudWeb")   
 
    
    def add_new_tab(self, qurl = None, label ="Blank"):
 
        if qurl is None:
            qurl = QUrl('http://google.com')

        browser = QWebEngineView()
        browser.setUrl(qurl)
        i = self.tabs.addTab(browser, label)
        self.tabs.setCurrentIndex(i)
        browser.urlChanged.connect(lambda qurl, browser = browser:
                                   self.update_urlbar(qurl, browser))
        browser.loadFinished.connect(lambda _, i = i, browser = browser:
                                     self.tabs.setTabText(i, browser.page().title()))

    def tab_open_doubleclick(self, i):
        if i == -1:
            self.add_new_tab(qurl=QUrl("http://dzen.ru"))

    
    def current_tab_changed(self, i):
        qurl = self.tabs.currentWidget().url()
        self.update_urlbar(qurl, self.tabs.currentWidget())
        self.update_title(self.tabs.currentWidget())

    def close_current_tab(self, i):
        if self.tabs.count() < 2:
            return
        self.tabs.removeTab(i)

    def update_title(self, browser):
        if browser != self.tabs.currentWidget():
            return
        title = self.tabs.currentWidget().page().title()
        self.setWindowTitle("% s - CloudWeb" % title)

    def navigate_home(self):
        self.tabs.currentWidget().setUrl(QUrl("http://google.com"))

    def navigate_to_url(self):
        q = QUrl(self.urlbar.text())
        if q.scheme() == "":
            q.setScheme("http")
        self.tabs.currentWidget().setUrl(q)

    def update_urlbar(self, q, browser = None):
        if browser != self.tabs.currentWidget():
            return
        self.urlbar.setText(q.toString())
        self.urlbar.setCursorPosition(0)

    def on_toggle_tor(self, checked: bool):
        _settings['tor_enabled'] = bool(checked)
        save_settings(_settings)
        if not checked:
            _tor_manager.stop()
        reply = QMessageBox.question(self, "CloudWeb",
                                     "Для применения настроек требуется перезапуск. Перезапустить сейчас?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.restart_app()

    def restart_app(self):
        try:
            QApplication.closeAllWindows()
        except Exception:
            pass
        python = sys.executable
        os.execl(python, python, *sys.argv)

app = QApplication(sys.argv)
app.setApplicationName("CloudWeb")
app.setStyle("Fusion")
window = MainWindow()
app.exec()
