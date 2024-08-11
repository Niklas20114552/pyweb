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
        parent.console.append(str(text))

    def warning(text):
        parent.console.append(f'<span style="color: yellow">{str(text)}</span>')

    def error(text):
        parent.console.append(f'<span style="color: red">{str(text)}</span>')

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
    del restricted_globals["__builtins__"]["getattr"]

    try:
        exec(script_content, restricted_globals)
    except Exception:
        tb_lines = traceback.format_exc().splitlines()
        exception_pattern = r"^  File \"<string>\", line (\d+), in <module>$"
        line_number = re.match(exception_pattern, tb_lines[3]).groups()[0]

        error(f"[WPYS-E] {tb_lines[-1]} (at line {line_number} in {script_name})")
