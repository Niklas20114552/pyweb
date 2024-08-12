#!/usr/bin/env python3
import traceback
import re
import json
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
    class Element:
        def __init__(self, element_json: dict):
            self._element_json = element_json

        def id(self) -> str:
            return self._element_json["id"]

        def setId(self, id: str) -> None:
            self._element_json["id"] = id

    class TextElement(Element):
        def text(self) -> str:
            return self._element_json["widget"].text()

        def setText(self, text: str) -> None:
            self._element_json["widget"].setText(text)

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
                self._element_json["widget"].returnPressed.connect(func)
            elif event == "textChanged":
                self._element_json["widget"].textChanged.connect(func)
            else:
                warning("[WPYS-E] Tried to assign invalid event type to TextInput.")

    class Header1(TextElement):
        pass

    class Header2(TextElement):
        pass

    class Header3(TextElement):
        pass

    class Paragraph(TextElement):
        pass

    class Button(EventedTextElement):
        def _processEvent(self, event, func):
            if event == "clicked":
                self._element_json["widget"].clicked.connect(func)
            else:
                warning(
                    "[WPYS-E] Tried to assign invalid event type to Button element."
                )

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
            parent.console.insertPlainText(str(line))

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
        if parent.ask_execution(script_name, object):
            exec(object, restricted_globals, locals)
        else:
            warning("[WPYS-E] User denied execution of code")

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
        return [
            element_register[element["type"]](element)
            for element in parent.browser_structure
            if element["id"] == id
        ]

    def _get_type(element_type: str):
        element_json = None
        for element in parent.browser_structure:
            if element["type"] == element_type:
                element_json = element

        if element_json:
            return element_register[element_json["type"]](element_json)

    def _get_types(element_type: str):
        return [
            element_register[element["type"]](element)
            for element in parent.browser_structure
            if element["type"] == element_type
        ]

    element_register = {
        "header1": Header1,
        "header2": Header2,
        "header3": Header3,
        "paragraph": Paragraph,
        "button": Button,
        "textInput": TextInput,
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
    del restricted_globals["__builtins__"]["getattr"]

    try:
        exec(script_content, restricted_globals)
    except Exception:
        tb = traceback.format_exc()
        error(f"[WPYS-E] Exception occured in {script_name}:\n{tb}\n")
