#!/usr/bin/env python3
from posix import error
import sys
import requests
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QPixmap
from urllib import parse as urlparse
import wpym_kit
import wpys_engine
import os
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QWidget,
    QVBoxLayout,
    QLineEdit,
    QTextEdit,
)


def conv_wpy_url_to_http(url: str) -> str:
    parsed = urlparse.urlparse(url)
    parsed_list = list(parsed)
    if not parsed.port and parsed.scheme == "wpyp":
        parsed_list[1] = f"{parsed.hostname}:8950"
    elif not parsed.port and parsed.scheme == "wpyps":
        parsed_list[1] = f"{parsed.hostname}:8951"
    else:
        parsed_list[1] = f"{parsed.hostname}:{parsed.port}"

    if parsed.scheme == "wpyp":
        parsed_list[0] = "http"
    else:
        parsed_list[0] = "https"

    return urlparse.urlunparse(parsed_list)


class AskCodeDialog(QDialog):
    def __init__(self, name, code: str):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.setWindowTitle("Allow code execution")

        self.label = QLabel(f"{name} want's to execute the following code.")
        self.label2 = QLabel("Do you allow the execution?")

        self.preview = QTextEdit(code)
        self.preview.setReadOnly(True)

        self.yesno = QHBoxLayout()
        self.yes = QPushButton("Yes")
        self.yes.clicked.connect(self.accept)
        self.no = QPushButton("No")
        self.no.clicked.connect(self.reject)
        self.yesno.addWidget(self.yes)
        self.yesno.addWidget(self.no)

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.label2)
        self.main_layout.addWidget(self.preview)
        self.main_layout.addLayout(self.yesno)

        self.setLayout(self.main_layout)


class AskInputDialog(QDialog):
    def __init__(self, name, question):
        super().__init__()
        self.main_layout = QVBoxLayout()
        self.setWindowTitle("Code Question")

        self.label = QLabel(f"{name} askes the following:")
        self.label2 = QLabel(question)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Your answer")
        self.input.returnPressed.connect(self.accept)

        self.main_layout.addWidget(self.label)
        self.main_layout.addWidget(self.label2)
        self.main_layout.addWidget(self.input)

        self.setLayout(self.main_layout)


class Browser(QMainWindow):
    def navigate_to(self):
        url = self.navbar_bar.text()
        self.current_path = url
        self.render_page(url)

    def __init__(self) -> None:
        super().__init__()
        self.browser_structure = []
        self.scripts = []
        self.web_widget = None
        self.web_layout = None
        self.current_path = ""

        self.setWindowTitle("WPY-Browser")
        self.setMinimumSize(800, 600)

        self.widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.navbar_layout = QHBoxLayout()

        self.nav_back = QPushButton("<-")
        self.nav_back.setFixedSize(40, 30)
        self.nav_next = QPushButton("->")
        self.nav_next.setFixedSize(40, 30)
        self.nav_reload = QPushButton("@")
        self.nav_reload.setFixedSize(40, 30)
        self.nav_reload.clicked.connect(lambda: self.render_page(self.current_path))

        self.navbar_icon = QLabel()
        self.navbar_title = QLabel()
        self.navbar_bar = QLineEdit()
        self.navbar_bar.setPlaceholderText("Navigate the PyWeb")
        self.navbar_bar.returnPressed.connect(self.navigate_to)
        self.toggle_console = QPushButton("Console")
        self.toggle_console.clicked.connect(self.show_console)

        self.navbar_layout.addWidget(self.navbar_icon)
        self.navbar_layout.addWidget(self.navbar_title)
        self.navbar_layout.addWidget(self.nav_back)
        self.navbar_layout.addWidget(self.nav_next)
        self.navbar_layout.addWidget(self.nav_reload)
        self.navbar_layout.addWidget(self.navbar_bar)
        self.navbar_layout.addWidget(self.toggle_console)

        self.website = QScrollArea()
        self.website.setWidgetResizable(True)
        self.website.setFrameShape(QFrame.Shape.NoFrame)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.hide()

        self.main_layout.addLayout(self.navbar_layout)
        self.main_layout.addWidget(self.website)
        self.main_layout.addWidget(self.console)

        self.widget.setLayout(self.main_layout)
        self.setCentralWidget(self.widget)

        QTimer.singleShot(
            0,
            lambda: self.render_page(""),
        )

    def error(self, text):
        self.console.append(f'<span style="color: red">{str(text)}</span>')

    def show_console(self):
        if self.console.isVisible():
            self.console.hide()
        else:
            self.console.show()

    def get_wpyp(self, url: str) -> str:
        if url.startswith("file://"):
            url = url.removeprefix("file://")
            if os.path.exists(url):
                return open(url, "r").read()
            else:
                self.error("[WPYM-K] Failed to get file: " + url)
        elif url.startswith("wpyp://") or url.startswith("wpyps://"):
            response = requests.get(conv_wpy_url_to_http(url))
            if response.status_code == 200:
                return response.text
            else:
                error("[WPYM-K] Failed to get: " + conv_wpy_url_to_http(url))
        return ""

    def get_top_path(self, url: str) -> str:
        parsed_list = list(urlparse.urlparse(url))
        parsed_list[2] = "/"
        return urlparse.urlunparse(parsed_list)

    def render_page(self, path: str):
        self.console.setPlainText("")

        s_path = os.path.split(path)
        self.navbar_title.setText(">-<>-<")
        self.navbar_icon.setPixmap(QPixmap())

        self.browser_structure = []
        self.scripts = []

        self.web_layout = QVBoxLayout()
        self.web_widget = QWidget()
        self.web_widget.setLayout(self.web_layout)
        self.website.setWidget(self.web_widget)

        wpym_kit.run_script(self, s_path[1], self.get_wpyp(path))
        self.web_layout.addStretch()
        for script in self.scripts:
            wpys_engine.run_script(
                self, os.path.split(script)[1], self.get_wpyp(script)
            )

    def ask_execution(self, name, code):
        dialog = AskCodeDialog(name, code)
        return dialog.exec()

    def ask_question(self, name, question):
        dialog = AskInputDialog(name, question)
        dialog.exec()
        return dialog.input.text()


def main(argv):
    app = QApplication(sys.argv)
    app.setDesktopFileName("wpy-browser")

    browser = Browser()
    browser.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
