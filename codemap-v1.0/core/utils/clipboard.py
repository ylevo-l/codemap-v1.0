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
    my, mx = stdscr.getmaxyx()
    total = len(files)
    for idx, (path, content) in enumerate(files, 1):
        copied_text.append(
            COPY_FORMAT_PRESETS.get(fmt, COPY_FORMAT_PRESETS["blocks"]).format(
                path=path,
                content=content or "<Could not read file>"
            )
        )
        progress_bar_length = max(10, mx - 30)
        progress = int((idx / total) * progress_bar_length)
        progress_bar = "#" * progress + "-" * (progress_bar_length - progress)
        status = f"Copying {idx}/{total} files: [{progress_bar}]"
        try:
            stdscr.addstr(my - 1, 0, status[:mx-1], curses.color_pair(7))
        except:
            pass
        stdscr.refresh()
    return ''.join(copied_text)
