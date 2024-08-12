#!/usr/bin/env python3
import traceback
import os
from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import QFrame, QLabel, QLineEdit, QPushButton
import requests


# This is just to get a meta.[...] command
class meta:
    def __init__(self, parent):
        self.parent = parent

    def setTitle(self, title):
        self.parent.navbar_title.setText(title)

    def setFavicon(self, url):
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

    def addScript(self, path):
        if path.startswith("/"):
            path = path.removeprefix("/")
            self.parent.scripts.append(
                self.parent.get_top_path(self.parent.history[self.parent.current_index])
                + path
            )
        elif (
            path.startswith("wpyp://")
            or path.startswith("wpyps://")
            or path.startswith("file://")
        ):
            self.parent.scripts.append(path)
        else:
            self.parent.scripts.append(
                os.path.split(self.parent.history[self.parent.current_index])[0]
                + "/"
                + path
            )


def run_script(parent, script_name: str, script_content: str):
    def error(text):
        for line in text.splitlines():
            parent.console.append(
                f'<span style="color: red">{str(line.replace(" ", "&nbsp;"))}</span>'
            )

    def header1(content, id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 24))
        parent.browser_structure.append({"widget": widget, "id": id, "type": "header1"})
        parent.web_layout.addWidget(widget)

    def header2(content, id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 21))
        parent.browser_structure.append({"widget": widget, "id": id, "type": "header2"})
        parent.web_layout.addWidget(widget)

    def header3(content, id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 18))
        parent.browser_structure.append({"widget": widget, "id": id, "type": "header3"})
        parent.web_layout.addWidget(widget)

    def paragraph(content, id=""):
        widget = QLabel(content)
        parent.browser_structure.append(
            {"widget": widget, "id": id, "type": "paragraph"}
        )
        parent.web_layout.addWidget(widget)

    def line_h(id=""):
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.HLine)
        widget.setLineWidth(3)
        parent.browser_structure.append({"widget": widget, "id": id, "type": "line_h"})
        parent.web_layout.addWidget(widget)

    def text_input(placeholder="", id=""):
        widget = QLineEdit()
        widget.setPlaceholderText(placeholder)
        parent.browser_structure.append(
            {"widget": widget, "id": id, "type": "text_input"}
        )
        parent.web_layout.addWidget(widget)

    def button(content, id=""):
        widget = QPushButton(content)
        parent.browser_structure.append({"widget": widget, "id": id, "type": "button"})
        parent.web_layout.addWidget(widget)

    restricted_globals = {
        "__builtins__": None,
        "meta": meta(parent),
        "engine": engine(parent),
        "header1": header1,
        "header2": header2,
        "header3": header3,
        "paragraph": paragraph,
        "lineH": line_h,
        "textInput": text_input,
        "button": button,
    }

    try:
        exec(script_content, restricted_globals)
    except Exception:
        tb = traceback.format_exc()
        error(f"[WPYM-K] Failed to render {script_name}:\n{tb}\n")
