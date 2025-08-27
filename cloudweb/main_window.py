from PyQt6.QtCore import *
from PyQt6.QtWidgets import *
from PyQt6.QtGui import *
from PyQt6.QtWebEngineWidgets import *

import os
import sys

from .paths import ICONS_DIR
from .settings import load_settings, save_settings


class MainWindow(QMainWindow):
    global menu

    def __init__(self, *args, **kwargs):
        global menu_btn
        super(MainWindow, self).__init__(*args, **kwargs)

        self.settings = load_settings()

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

        back_btn_icon = os.path.join(ICONS_DIR, 'back.png')
        back_btn = QAction("Back", self)
        back_btn.setIcon(QIcon(back_btn_icon))
        back_btn.setStatusTip("Back to previous page")
        back_btn.triggered.connect(lambda: self.tabs.currentWidget().back())
        navtb.addAction(back_btn)

        forward_btn_icon = os.path.join(ICONS_DIR, 'forward.png')
        next_btn = QAction("Forward", self)
        next_btn.setIcon(QIcon(forward_btn_icon))
        next_btn.setStatusTip("Forward to next page")
        next_btn.triggered.connect(lambda: self.tabs.currentWidget().forward())
        navtb.addAction(next_btn)

        reload_btn_icon = os.path.join(ICONS_DIR, 'reload.png')
        reload_btn = QAction("Reload", self)
        reload_btn.setIcon(QIcon(reload_btn_icon))
        reload_btn.setStatusTip("Reload page")
        reload_btn.triggered.connect(lambda: self.tabs.currentWidget().reload())
        navtb.addAction(reload_btn)

        home_btn_icon = os.path.join(ICONS_DIR, 'home.png')
        home_btn = QAction("Home", self)
        home_btn.setIcon(QIcon(home_btn_icon))
        home_btn.setStatusTip("Go home")
        home_btn.triggered.connect(self.navigate_home)
        navtb.addAction(home_btn)
        navtb.addSeparator()
        self.urlbar = QLineEdit()
        self.urlbar.returnPressed.connect(self.navigate_to_url)
        navtb.addWidget(self.urlbar)

        settings_icon = os.path.join(ICONS_DIR, 'Settings_icon.png')

        menu_btn_icon = os.path.join(ICONS_DIR, 'menu_icon.png')
        menu_btn = QPushButton(self)
        menu_btn.setIcon(QIcon(menu_btn_icon))
        menu_btn.setIconSize(QSize(23, 23))
        menu_btn.setStatusTip("Открыть меню")

        menu = QMenu(menu_btn)
        settings_action = QAction()
        settings_action.setIcon(QIcon(settings_icon))
        settings_action.setText("Настройки")
        settings_action.triggered.connect(self.open_settings_dialog)
        menu.addAction(settings_action)

        menu.addSeparator()
        self.tor_action = QAction("Использовать Tor", self)
        self.tor_action.setCheckable(True)
        self.tor_action.setChecked(self.settings.get('tor_enabled', False))
        self.tor_action.setStatusTip("Маршрутизировать трафик через Tor (SOCKS5 127.0.0.1:9050)")
        self.tor_action.triggered.connect(self.on_toggle_tor)
        menu.addAction(self.tor_action)

        def menu_func():
            menu.exec()

        menu_btn.clicked.connect(menu_func)
        navtb.addWidget(menu_btn)

        self.add_new_tab(QUrl(self.settings.get('homepage', 'http://google.com')), 'Homepage')
        self.show()
        self.setWindowTitle("CloudWeb")

    def add_new_tab(self, qurl = None, label ="Blank"):
        if qurl is None:
            qurl = QUrl(self.settings.get('homepage', 'http://google.com'))
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
            self.add_new_tab(qurl=QUrl(self.settings.get('homepage', 'http://google.com')))

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
        self.tabs.currentWidget().setUrl(QUrl(self.settings.get('homepage', 'http://google.com')))

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
        self.settings['tor_enabled'] = bool(checked)
        save_settings(self.settings)
        reply = QMessageBox.question(self, "CloudWeb",
                                     "Для применения настроек требуется перезапуск. Перезапустить сейчас?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            self.restart_app()

    def open_settings_dialog(self):
        previous_tor = bool(self.settings.get('tor_enabled', False))
        dialog = SettingsDialog(self.settings, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.settings = dialog.get_settings()
            save_settings(self.settings)
            self.navigate_home()
            if bool(self.settings.get('tor_enabled', False)) != previous_tor:
                reply = QMessageBox.question(self, "CloudWeb",
                                             "Изменение настройки Tor требует перезапуска. Перезапустить сейчас?",
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


class SettingsDialog(QDialog):
    def __init__(self, settings: dict, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Настройки")
        self._settings = dict(settings)

        layout = QFormLayout(self)

        self.homepage_edit = QLineEdit(self)
        self.homepage_edit.setText(self._settings.get('homepage', 'http://google.com'))
        layout.addRow("Домашняя страница:", self.homepage_edit)

        self.tor_checkbox = QCheckBox("Использовать Tor (SOCKS5 127.0.0.1:9050)", self)
        self.tor_checkbox.setChecked(self._settings.get('tor_enabled', False))
        layout.addRow(self.tor_checkbox)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel, self)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addRow(buttons)

    def accept(self):
        self._settings['homepage'] = self.homepage_edit.text().strip() or 'http://google.com'
        self._settings['tor_enabled'] = self.tor_checkbox.isChecked()
        super().accept()

    def get_settings(self) -> dict:
        return dict(self._settings)

