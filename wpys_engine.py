#!/usr/bin/env python3
import traceback
import re
import json
from typing import Text
from PyQt6.QtWidgets import QLineEdit
import requests
import math
import hashlib
import base64


def is_math_expression(expr: str) -> bool:
    return bool(re.search(r"^[\d \+\-\*\/\(\)%]*$", expr))


class SandboxViolation(Exception):
    pass


class EngineLimitation(Exception):
    pass


def run_script(parent, script_name: str, script_content: str):
    def _excepted_func_call(event_type: str, widget_type: str, func):
        try:
            func()
        except Exception:
            tb = traceback.format_exc().splitlines()
            match = re.match(r"^  File \"[^\"]*\", line (\d*), in .*$", tb[-2])
            line_number = "?"
            if match:
                line_number = match.group(0)
            error(
                f"[WPYS-E] Exception occured while processing event {event_type} in {widget_type} (at line {line_number}):\n{tb[-1]}\n"
            )

    class Element:
        def __init__(self, element_json: dict):
            self._Element__element_json = element_json

        def id(self) -> str:
            return self._Element__element_json["id"]

        def setId(self, id: str) -> None:
            self._Element__element_json["id"] = id

    class TextElement(Element):
        def text(self) -> str:
            return self._Element__element_json["widget"].text()

        def setText(self, text: str) -> None:
            self._Element__element_json["widget"].setText(text)

    class EventedTextElement(TextElement):
        def __call__(self, func=None, *, event: str = ""):
            if func is None:

                def wrapper(func):
                    self._processEvent(event, func)
                    return func

                return wrapper
            return func

        def _processEvent(self, event, func):
            pass

    class TextInput(EventedTextElement):
        def _processEvent(self, event, func):
            if event == "returnPressed":
                self._Element__element_json["widget"].returnPressed.connect(
                    lambda: _excepted_func_call(event, "TextInput", func)
                )
            elif event == "textChanged":
                self._Element__element_json["widget"].textChanged.connect(
                    lambda: _excepted_func_call(event, "TextInput", func)
                )
            else:
                warning("[WPYS-E] Tried to assign invalid event type to TextInput.")

        def placeholderText(self) -> str:
            return self._Element__element_json["widget"].placeholderText()

        def setPlaceholderText(self, placeholderText: str) -> None:
            self._Element__element_json["widget"].setPlaceholderText(placeholderText)

        def isPassword(self) -> bool:
            return (
                self._Element__element_json["widget"].echoMode()
                == QLineEdit.EchoMode.Password
            )

        def setPassword(self, password: bool) -> None:
            if password:
                echo = QLineEdit.EchoMode.Password
            else:
                echo = QLineEdit.EchoMode.Normal
            self._Element__element_json["widget"].setEchoMode(echo)

    class Header1(TextElement):
        pass

    class Header2(TextElement):
        pass

    class Header3(TextElement):
        pass

    class Paragraph(TextElement):
        pass

    class Link(TextElement):
        def target(self) -> str:
            return self._Element__element_json["target"]

        def setTarget(self, target: str):
            self._Element__element_json["target"] = target
            self._Element__element_json["widget"].mousePressEvent = (
                lambda event: parent.navigate_to_rel(target)
            )

    class Button(EventedTextElement):
        def _processEvent(self, event, func):
            if event == "clicked":
                self._Element__element_json["widget"].clicked.connect(
                    lambda: _excepted_func_call(event, "Button", func)
                )
            else:
                warning(
                    "[WPYS-E] Tried to assign invalid event type to Button element."
                )

        def isEnabled(self) -> bool:
            return self._Element__element_json["widget"].isEnabled()

        def setDisabled(self, disabled: bool) -> None:
            self._Element__element_json["widget"].setDisabled(disabled)

    class TextDropdown(EventedTextElement):
        def _processEvent(self, event, func):
            if event == "activated":
                self._Element__element_json["widget"].activated.connect(
                    lambda: _excepted_func_call(event, "TextDropdown", func)
                )
            else:
                warning(
                    "[WPYS-E] Tried to assign invalid event type to TextDropdown element."
                )

        def placeholderText(self) -> str:
            return self._Element__element_json["widget"].placeholderText()

        def setPlaceholderText(self, placeholderText: str) -> None:
            self._Element__element_json["widget"].setPlaceholderText(placeholderText)

        def items(self) -> list[str]:
            return [
                self._Element__element_json["widget"].itemText(index)
                for index in range(self._Element__element_json["widget"].count())
            ]

        def setItems(self, items: list[str]) -> None:
            self._Element__element_json["widget"].clear()
            self._Element__element_json["widget"].addItems(items)

    class GroupBox(Element):
        def title(self) -> str:
            return self._Element__element_json["widget"].title()

        def setTitle(self, title: str) -> None:
            self._Element__element_json["widget"].setTitle(title)

    def _print(*args, **kwargs):
        raise EngineLimitation("Use log(), warn() or error() instead")

    def _import(*args, **kwargs):
        raise SandboxViolation("Importing modules is not allowed")

    def _open(*args, **kwargs):
        raise SandboxViolation(
            "Opening files is not allowed. Use a upload form instead or download the file"
        )

    def _exit():
        raise EngineLimitation("Can't exit or quit a running script")

    def log(text):
        for line in text.splitlines():
            parent.console.append(f"<span>{str(line).replace(' ', '&nbsp;')}</span>")

    def warning(text):
        for line in text.splitlines():
            parent.console.append(
                f'<span style="color: yellow">{str(line.replace(" ", "&nbsp;"))}</span>'
            )

    def error(text):
        for line in text.splitlines():
            parent.console.append(
                f'<span style="color: red">{str(line.replace(" ", "&nbsp;"))}</span>'
            )

    def _eval(expression):
        if not isinstance(expression, str):
            raise TypeError("eval() arg 1 must be a string")
        if is_math_expression(expression):
            restricted_globals = {"__builtins__": None}
            restricted_locals = {}
            return eval(expression, restricted_globals, restricted_locals)
        else:
            raise SandboxViolation("Eval can only process mathematical expressions")

    def _exec(object: str, locals=None):
        exec(object, restricted_globals, locals)

    def _input(prompt: str):
        return parent.ask_question(script_name, prompt)

    def _get_id(id: str):
        element_json = None
        for element in parent.browser_structure:
            if element["id"] == id:
                element_json = element

        if element_json:
            return element_register[element_json["type"]](element_json)

    def _get_ids(id: str):
        return tuple(
            element_register[element["type"]](element)
            for element in parent.browser_structure
            if element["id"] == id
        )

    def _get_type(element_type: str):
        element_json = None
        for element in parent.browser_structure:
            if element["type"] == element_type:
                element_json = element

        if element_json:
            return element_register[element_json["type"]](element_json)

    def _get_types(element_type: str):
        return tuple(
            element_register[element["type"]](element)
            for element in parent.browser_structure
            if element["type"] == element_type
        )

    def _navigate_to(target: str):
        parent.navigate_to_rel(target)

    def _href():
        return parent.history[parent.current_index]

    element_register = {
        "header1": Header1,
        "header2": Header2,
        "header3": Header3,
        "paragraph": Paragraph,
        "button": Button,
        "textInput": TextInput,
        "link": Link,
        "textDropdown": TextDropdown,
        "groupBox": GroupBox,
    }

    if __name__ == "__main__":
        builtins_copy = __builtins__.__dict__.copy()
    else:
        builtins_copy = __builtins__.copy()

    restricted_globals = {
        "__builtins__": builtins_copy,
        "re": re,
        "json": json,
        "requests": requests,
        "math": math,
        "hashlib": hashlib,
        "base64": base64,
    }

    restricted_globals["__builtins__"]["__import__"] = _import
    restricted_globals["__builtins__"]["print"] = _print
    restricted_globals["__builtins__"]["open"] = _open
    restricted_globals["__builtins__"]["exit"] = _exit
    restricted_globals["__builtins__"]["quit"] = _exit
    restricted_globals["__builtins__"]["log"] = log
    restricted_globals["__builtins__"]["warning"] = warning
    restricted_globals["__builtins__"]["error"] = error
    restricted_globals["__builtins__"]["eval"] = _eval
    restricted_globals["__builtins__"]["exec"] = _exec
    restricted_globals["__builtins__"]["input"] = _input
    restricted_globals["__builtins__"]["getId"] = _get_id
    restricted_globals["__builtins__"]["getIds"] = _get_ids
    restricted_globals["__builtins__"]["getType"] = _get_type
    restricted_globals["__builtins__"]["getTypes"] = _get_types
    restricted_globals["__builtins__"]["navigateTo"] = _navigate_to
    restricted_globals["__builtins__"]["currentHref"] = _href
    restricted_globals["__builtins__"]["convWPYPtoHTTP"] = parent.conv_wpy_url_to_http
    del restricted_globals["__builtins__"]["getattr"]

    try:
        exec(script_content.replace("._Element", "."), restricted_globals)
    except Exception:
        tb = traceback.format_exc()
        error(f"[WPYS-E] Exception occured in {script_name}:\n{tb}\n")
        print("Exception occurred. Please check console")
