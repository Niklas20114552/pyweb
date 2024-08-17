#!/usr/bin/env python3
import sys
import requests
from PyQt6.QtCore import QTimer
from PyQt6.QtGui import QFont, QPixmap
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
    def conv_wpy_url_to_http(self, url: str) -> str:
        parsed = urlparse.urlparse(url)
        parsed_list = list(parsed)
        if parsed.scheme not in ("wpyp", "wpyps"):
            return url

        if parsed.hostname.endswith(".wpyh"):
            host = parsed.hostname.removesuffix(".wpyh")
            response = requests.get("https://gnuhobbyhub.de:8952/" + host)
            parsed_list[0] = "wpyp"
            if not parsed.port or parsed.port == 8951:
                parsed_list[1] = response.text + ":8950"
            else:
                parsed_list[1] = f"{response.text}:{parsed.port}"
            parsed = urlparse.urlparse(urlparse.urlunparse(parsed_list))
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

    def navigate_to(self, url: str = "", historize=True):
        if not url:
            url = self.navbar_bar.text()

        if historize:
            if self.history[-1] != url:
                self.current_index += 1
            if self.current_index != len(self.history):
                if url != self.history[self.current_index]:
                    self.history = self.history[: self.current_index]

            if self.history[-1] != url:
                self.history.append(url)

        self.navbar_bar.setText(url)
        self.render_page(url)

    def navigate_to_rel(self, path):
        if path.startswith("/"):
            path = path.removeprefix("/")
            self.navigate_to(self.get_top_path(self.history[self.current_index]) + path)
        elif (
            path.startswith("wpyp://")
            or path.startswith("wpyps://")
            or path.startswith("file://")
        ):
            self.navigate_to(path)
        else:
            self.navigate_to(
                os.path.split(self.history[self.current_index])[0] + "/" + path
            )

    def navigate_next(self):
        if len(self.history) != self.current_index + 1:
            self.current_index += 1
            self.navigate_to(self.history[self.current_index], historize=False)

    def navigate_back(self):
        if self.current_index + 1 != 1:
            self.current_index -= 1
            self.navigate_to(self.history[self.current_index], historize=False)

    def __init__(self) -> None:
        super().__init__()
        self.browser_structure = []
        self.scripts = []
        self.history = [""]
        self.web_widget = None
        self.web_layout = None
        self.current_index = 0

        self.setWindowTitle("WPY-Browser")
        self.setMinimumSize(800, 600)
        self.showMaximized()

        self.widget = QWidget()
        self.main_layout = QVBoxLayout()
        self.navbar_layout = QHBoxLayout()

        self.nav_back = QPushButton("<-")
        self.nav_back.setFixedSize(40, 30)
        self.nav_back.clicked.connect(self.navigate_back)
        self.nav_back.setToolTip("Prev.")
        self.nav_next = QPushButton("->")
        self.nav_next.setFixedSize(40, 30)
        self.nav_next.setToolTip("Next")
        self.nav_next.clicked.connect(self.navigate_next)
        self.nav_reload = QPushButton("@")
        self.nav_reload.setFixedSize(40, 30)
        self.nav_reload.setToolTip("Reload")
        self.nav_reload.clicked.connect(
            lambda: self.render_page(self.history[self.current_index])
        )

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
        self.console.setFont(QFont("Monospace"))
        self.console.setReadOnly(True)
        self.console.hide()
        self.console.setMaximumHeight(200)

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
        for line in text.splitlines():
            self.console.append(
                f'<span style="color: red">{str(line.replace(" ", "&nbsp;"))}</span>'
            )

    def show_console(self):
        if self.console.isVisible():
            self.console.hide()
        else:
            self.console.show()

    def get_wpyp(self, url: str) -> tuple[str, str]:
        if url.startswith("file://"):
            surl = url.removeprefix("file://")
            if os.path.exists(surl):
                return open(surl, "r").read(), url
            else:
                self.error("[WPYM-K] Failed to get file: " + url)
        elif url.startswith("wpyp://") or url.startswith("wpyps://"):
            try:
                response = requests.get(self.conv_wpy_url_to_http(url), timeout=5)
                if response.status_code == 200:
                    purl = urlparse.urlparse(url)
                    turl = urlparse.urlparse(response.url)
                    turl_list = list(turl)
                    if purl.port == 8951 or turl.scheme == "https":
                        turl_list[0] = "wpyps"
                    else:
                        turl_list[0] = "wpyp"

                    if purl.hostname.endswith(".wpyh"):
                        turl_list[1] = purl.netloc
                    else:
                        turl_list[1] = purl.netloc
                    return response.text, urlparse.urlunparse(turl_list)
                else:
                    self.error(
                        "[WPYM-K] Failed to get: " + self.conv_wpy_url_to_http(url)
                    )
            except Exception as e:
                self.error(
                    f"[WPYM-K] Error occured while trying to connect to: {self.conv_wpy_url_to_http(url)}. Error: {e.__class__.__name__}:{str(e)}"
                )
        return "", ""

    def get_top_path(self, url: str) -> str:
        parsed_list = list(urlparse.urlparse(url))
        parsed_list[2] = "/"
        return urlparse.urlunparse(parsed_list)

    def render_page(self, path: str):
        self.console.setPlainText("")

        s_path = os.path.split(path)
        self.navbar_title.setText("(°-°)")
        self.navbar_icon.setPixmap(QPixmap())

        self.browser_structure = []
        self.scripts = []

        self.web_layout = QVBoxLayout()
        self.web_widget = QWidget()
        self.web_widget.setLayout(self.web_layout)
        self.website.setWidget(self.web_widget)

        wpyp = self.get_wpyp(path)
        self.navbar_bar.setText(wpyp[1])
        wpym_kit.run_script(self, s_path[1], wpyp[0])
        self.web_layout.addStretch()
        for script in self.scripts:
            wpys_engine.run_script(
                self, os.path.split(script)[1], self.get_wpyp(script)[0]
            )

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
