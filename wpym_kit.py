#!/usr/bin/env python3
import traceback
import re
import os
from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton
import requests


# This is just to get a meta.[...] command
class meta:
    def __init__(self, parent):
        self.parent = parent

    def set_title(self, title):
        self.parent.navbar_title.setText(title)

    def set_favicon(self, url):
        response = requests.get(url)
        if response.status_code != 200:
            print("Failed to download Favicon!")
            return
        pixmap = QPixmap()
        pixmap.loadFromData(QByteArray(response.content))
        self.parent.navbar_icon.setPixmap(pixmap)


class engine:
    def __init__(self, parent):
        self.parent = parent

    def add_script(self, path):
        if path.startswith("/"):
            path = path.removeprefix("/")
            self.parent.scripts.append(
                self.parent.get_top_path(self.parent.current_path) + path
            )
        elif (
            path.startswith("wpyp://")
            or path.startswith("wpyps://")
            or path.startswith("file://")
        ):
            self.parent.scripts.append(path)
        else:
            self.parent.scripts.append(
                os.path.split(self.parent.current_path)[0] + "/" + path
            )


def run_script(parent, script_name: str, script_content: str):
    def error(text):
        parent.console.append(f'<span style="color: red">{str(text)}</span>')

    def header1(content, id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 24))
        parent.browser_structure.append({"widget": widget, "id": id})
        parent.web_layout.addWidget(widget)

    def header2(content, id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 21))
        parent.browser_structure.append({"widget": widget, "id": id})
        parent.web_layout.addWidget(widget)

    def header3(content, id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 18))
        parent.browser_structure.append({"widget": widget, "id": id})
        parent.web_layout.addWidget(widget)

    def paragraph(content, id=""):
        widget = QLabel(content)
        parent.browser_structure.append({"widget": widget, "id": id})
        parent.web_layout.addWidget(widget)

    def line_h(id=""):
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.HLine)
        widget.setLineWidth(3)
        parent.browser_structure.append({"widget": widget, "id": id})
        parent.web_layout.addWidget(widget)

    def text_input(placeholder="", id=""):
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        parent.browser_structure.append({"widget": widget, "id": id})
        parent.web_layout.addWidget(widget)

    def button(content, id=""):
        widget = QPushButton(content)
        parent.browser_structure.append({"widget": widget, "id": id})
        parent.web_layout.addWidget(widget)

    restricted_globals = {
        "__builtins__": None,
        "meta": meta(parent),
        "engine": engine(parent),
        "header1": header1,
        "header2": header2,
        "header3": header3,
        "paragraph": paragraph,
        "line_h": line_h,
        "text_input": text_input,
        "button": button,
    }

    try:
        exec(script_content, restricted_globals)
    except Exception:
        tb_lines = traceback.format_exc().splitlines()
        exception_pattern = r"^  File \"<string>\", line (\d+), in <module>$"
        line_number = re.match(exception_pattern, tb_lines[3]).groups()[0]

        error(f"[WPYM-K] {tb_lines[-1]} (at line {line_number} in {script_name})")
