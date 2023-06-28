import os
import sys


def is_exe():
    return getattr(sys, 'frozen', False)


def get_path(is_data, add_path=""):
    if is_exe():
        return os.path.dirname(sys.executable) + ("/data/" if is_data else "")
    else:
        return os.path.dirname(__file__) + add_path
