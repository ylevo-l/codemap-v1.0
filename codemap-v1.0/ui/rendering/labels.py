import curses
import re
from typing import Optional, List
from core.model import TreeNode
from ui.rendering.text import safe_addnstr
from ui.rendering.colors import GENERAL_UI_COLOR, UI_BRACKET_COLOR
from ui.core.labels import render_single_label
from config.ui_labels import (
    COPY_LABEL, TOGGLE_LABEL, TOGGLE_ALL_LABEL, ENABLE_LABEL, DISABLE_LABEL,
    NO_FILES_LABEL, NO_TOKENS_LABEL, SEPARATOR, REFACTOR_LABEL, REFACTOR_ALL_LABEL

)
from core.operations.tree_ops import are_all_files_enabled

_BRACKET_PATTERN = re.compile(r'(\[[^\]]+\])(.*)')

def _split_label(label_text):
    match = _BRACKET_PATTERN.match(label_text)
    if match:
        return match.group(1), match.group(2)
    return None, label_text

def _create_node_labels(current_node: Optional[TreeNode], shift_mode: bool) -> List[str]:
    node_labels = []
    if current_node:
        if current_node.is_dir:
            node_labels.append(TOGGLE_ALL_LABEL if shift_mode else TOGGLE_LABEL)
            if shift_mode and current_node.expanded:
                node_labels.append(REFACTOR_ALL_LABEL)
            if shift_mode:
                if are_all_files_enabled(current_node):
                    node_labels.append("[D] Disable All")
                else:
                    node_labels.append("[D] Enable All")
            if current_node.expanded:
                node_labels.append(COPY_LABEL)
        else:
            node_labels.append(ENABLE_LABEL if current_node.disabled else DISABLE_LABEL)
            node_labels.append(REFACTOR_LABEL)
            if not current_node.disabled:
                node_labels.append(COPY_LABEL)
    else:
        node_labels.append(NO_FILES_LABEL)
    return node_labels

def render_node_labels(stdscr, y: int, x: int, node_labels: List[str]) -> int:
    for i, label_text in enumerate(node_labels):
        bracket_part, text_part = _split_label(label_text)
        if bracket_part:
            safe_addnstr(stdscr, y, x, bracket_part, UI_BRACKET_COLOR)
            x += len(bracket_part)
            safe_addnstr(stdscr, y, x, text_part, GENERAL_UI_COLOR)
            x += len(text_part)
        else:
            safe_addnstr(stdscr, y, x, label_text, GENERAL_UI_COLOR)
            x += len(label_text)
        if i < len(node_labels) - 1:
            safe_addnstr(stdscr, y, x, ' ', GENERAL_UI_COLOR)
            x += 1
    return x

def render_token_info(stdscr, y: int, x: int, tokens_visible: bool, total_tokens: int) -> int:
    if not tokens_visible and total_tokens > 0:
        context = {"total_tokens": total_tokens}
        x = render_single_label(stdscr, y, x, "tokens", context, separator=SEPARATOR, separator_color=GENERAL_UI_COLOR, show_separator=True)
    elif not tokens_visible and total_tokens == 0:
        sep_text = f' {SEPARATOR} '
        safe_addnstr(stdscr, y, x, sep_text, GENERAL_UI_COLOR)
        x += len(sep_text)
        no_tokens = f'{NO_TOKENS_LABEL}'
        safe_addnstr(stdscr, y, x, no_tokens, GENERAL_UI_COLOR)
        x += len(no_tokens)
    return x
