from typing import Dict, Any, List, Optional, Union
import curses

from ui.rendering.text import safe_addnstr
from ui.rendering.colors import GENERAL_UI_COLOR
from config.ui_labels import SEPARATOR
from ui.labels.core import StatusLabel
from ui.labels.registry import registry

def render_status_label(stdscr, y: int, x: int, label: StatusLabel,
                      context: Optional[Dict[str, Any]] = None,
                      separator: str = SEPARATOR,
                      separator_color: int = GENERAL_UI_COLOR,
                      show_separator: bool = True) -> int:
    if context is None:
        context = {}

    if show_separator and x > 0:
        sep_text = f' {separator} '
        safe_addnstr(stdscr, y, x, sep_text, separator_color)
        x += len(sep_text)

    safe_addnstr(stdscr, y, x, label.name, label.label_color)
    x += len(label.name)

    value = label.get_value(context)
    if value:
        value_text = f': {value}'
        safe_addnstr(stdscr, y, x, value_text, label.value_color)
        x += len(value_text)

    return x

def render_status_labels(stdscr, y: int, x: int,
                       labels: List[Union[str, StatusLabel]],
                       context: Optional[Dict[str, Any]] = None,
                       separator: str = SEPARATOR,
                       separator_color: int = GENERAL_UI_COLOR) -> int:
    if context is None:
        context = {}

    for i, label_item in enumerate(labels):
        if isinstance(label_item, str):
            label = registry.get(label_item)
            if not label:
                continue
        else:
            label = label_item

        x = render_status_label(
            stdscr, y, x, label, context,
            separator, separator_color,
            show_separator=(i > 0)
        )

    return x

def render_single_label(stdscr, y: int, x: int, label_key: str,
                      context: Optional[Dict[str, Any]] = None,
                      separator: str = SEPARATOR,
                      separator_color: int = GENERAL_UI_COLOR,
                      show_separator: bool = True) -> int:
    label = registry.get(label_key)
    if label:
        return render_status_label(
            stdscr, y, x, label, context,
            separator, separator_color, show_separator
        )
    return x