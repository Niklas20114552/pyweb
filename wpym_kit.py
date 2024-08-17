#!/usr/bin/env python3
import traceback
import os
from PyQt6.QtCore import QByteArray
from PyQt6.QtGui import QFont, QPixmap
from PyQt6.QtWidgets import (
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QComboBox,
    QVBoxLayout,
    QWidget,
    QSizePolicy,
)
import requests


# This is just to get a meta.[...] command
class meta:
    def __init__(self, parent):
        self.parent = parent

    def setTitle(self, title):
        self.parent.navbar_title.setText(title)

    def setFavicon(self, url):
        response = requests.get(self.parent.conv_wpy_url_to_http(url))
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

    def append_element(widget, id, type, append: dict = {}):
        elementStr = {"widget": widget, "id": id, "type": type, **append}
        parent.browser_structure.append(elementStr)
        parent.web_layout.addWidget(widget)
        return elementStr

    def append_layout(layout, id, type):
        elementStr = {"layout": layout, "id": id, "type": type}
        parent.browser_structure.append(elementStr)
        parent.web_layout.addLayout(layout)
        return elementStr

    def header1(content="", id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 24))
        return append_element(widget, id, "header1")

    def header2(content="", id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 21))
        return append_element(widget, id, "header2")

    def header3(content="", id=""):
        widget = QLabel(content)
        widget.setFont(QFont(widget.font().family(), 18))
        return append_element(widget, id, "header3")

    def paragraph(content="", id=""):
        widget = QLabel(content)
        widget.setWordWrap(True)
        return append_element(widget, id, "paragraph")

    def line_h(id=""):
        widget = QFrame()
        widget.setFrameShape(QFrame.Shape.HLine)
        widget.setLineWidth(3)
        return append_element(widget, id, "lineH")

    def text_input(placeholder="", id="", password=False):
        widget = QLineEdit()
        if password:
            widget.setEchoMode(QLineEdit.EchoMode.Password)
        widget.setPlaceholderText(placeholder)
        return append_element(widget, id, "textInput")

    def button(content="", disabled=False, id=""):
        widget = QPushButton(content)
        widget.setDisabled(disabled)
        return append_element(widget, id, "button")

    def link(content, target="", id=""):
        widget = QLabel(content)
        widget.mousePressEvent = lambda event: parent.navigate_to_rel(target)
        widget.setStyleSheet("text-decoration: underline; color: lightblue;")
        return append_element(widget, id, "header2", append={"target": target})

    def text_dropdown(values=[], placeholder="", id=""):
        widget = QComboBox()
        widget.addItems(values)
        widget.setPlaceholderText(placeholder)
        return append_element(widget, id, "textDropdown")

    def stretch(id=""):
        widget = QWidget()
        widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        return append_element(widget, id, "stretch")

    def h_box(content: list | tuple, id=""):
        layout = QHBoxLayout()
        for element in content:
            if "layout" in element:
                element["layout"].parent().removeItem(element["layout"])
                layout.addLayout(element["layout"])
            elif "widget" in element:
                layout.addWidget(element["widget"])
        return append_layout(layout, id, "vBox")

    def group_box(content: list | tuple, title="", id=""):
        widget = QGroupBox()
        widget.setTitle(title)
        layout = QVBoxLayout()
        widget.setLayout(layout)
        for element in content:
            if "layout" in element:
                element["layout"].parent().removeItem(element["layout"])
                layout.addLayout(element["layout"])
            elif "widget" in element:
                layout.addWidget(element["widget"])
        return append_element(widget, id, "groupBox", append={"layout": layout})

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
        "link": link,
        "hBox": h_box,
        "textDropdown": text_dropdown,
        "groupBox": group_box,
        "stretch": stretch,
    }

    try:
        exec(script_content, restricted_globals)
    except Exception:
        tb = traceback.format_exc()
        error(f"[WPYM-K] Failed to render {script_name}:\n{tb}\n")
        print("Exception occurred. Please check console")
