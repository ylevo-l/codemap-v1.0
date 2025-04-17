import sys
import subprocess
import curses
from typing import List, Tuple
from config.constants import COPY_FORMAT_PRESETS

def copy_text_to_clipboard(text: str) -> None:
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen("clip", stdin=subprocess.PIPE, shell=True).communicate(input=text.encode("utf-16"))
        elif sys.platform.startswith("darwin"):
            subprocess.Popen("pbcopy", stdin=subprocess.PIPE).communicate(input=text.encode("utf-8"))
        else:
            subprocess.Popen(["xclip", "-selection", "clipboard"], stdin=subprocess.PIPE).communicate(input=text.encode("utf-8"))
    except:
        pass

def copy_files_subloop(stdscr, files: List[Tuple[str, str]], fmt: str) -> str:
    copied_text = []
    for path, content in files:
        copied_text.append(
            COPY_FORMAT_PRESETS.get(fmt, COPY_FORMAT_PRESETS["blocks"]).format(
                path=path,
                content=content or "<Could not read file>"
            )
        )
    stdscr.refresh()
    return "".join(copied_text)
