import curses, re
from typing import Optional, List
from core.model import TreeNode
from ui.rendering.text import safe_addnstr
from ui.rendering.colors import GENERAL_UI_COLOR, UI_BRACKET_COLOR
from ui.core.labels import render_single_label
from config.ui_labels import COPY_LABEL, TOGGLE_LABEL, TOGGLE_ALL_LABEL, ENABLE_LABEL, DISABLE_LABEL, NO_FILES_LABEL, NO_TOKENS_LABEL, SEPARATOR, REFACTOR_LABEL, REFACTOR_ALL_LABEL
from core.operations.tree_ops import are_all_files_enabled

_BRACKET_PATTERN = re.compile(r'(\[[^\]]+\])(.*)')

def _split_label(label_text):
    m = _BRACKET_PATTERN.match(label_text)
    if m:
        return m.group(1), m.group(2)
    return None, label_text

def _compact(label_text, shift_mode):
    if shift_mode and label_text.endswith(' All'):
        return label_text[:-4]
    return label_text

def _create_node_labels(current_node: Optional[TreeNode], shift_mode: bool) -> List[str]:
    labels = []
    if current_node:
        if current_node.is_dir:
            labels.append(_compact(TOGGLE_ALL_LABEL if shift_mode else TOGGLE_LABEL, shift_mode))
            if shift_mode and current_node.expanded:
                labels.append(_compact(REFACTOR_ALL_LABEL, shift_mode))
            if shift_mode:
                labels.append('[D] Disable' if are_all_files_enabled(current_node) else '[D] Enable')
            if current_node.expanded:
                labels.append(COPY_LABEL)
        else:
            labels.append(ENABLE_LABEL if current_node.disabled else DISABLE_LABEL)
            labels.append(REFACTOR_LABEL)
            if not current_node.disabled:
                labels.append(COPY_LABEL)
    else:
        labels.append(NO_FILES_LABEL)
    return labels

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
            sep = f' {SEPARATOR} '
            safe_addnstr(stdscr, y, x, sep, GENERAL_UI_COLOR)
            x += len(sep)
    return x

def render_token_info(stdscr, y: int, x: int, tokens_visible: bool, total_tokens: int, copy_visible: bool) -> int:
    if not tokens_visible and total_tokens > 0:
        context = {'total_tokens': total_tokens}
        x = render_single_label(stdscr, y, x, 'tokens', context, separator=SEPARATOR, separator_color=GENERAL_UI_COLOR, show_separator=True)
    elif not tokens_visible and total_tokens == 0 and copy_visible:
        sep = f' {SEPARATOR} '
        safe_addnstr(stdscr, y, x, sep, GENERAL_UI_COLOR)
        x += len(sep)
        safe_addnstr(stdscr, y, x, NO_TOKENS_LABEL, GENERAL_UI_COLOR)
        x += len(NO_TOKENS_LABEL)
    return x
