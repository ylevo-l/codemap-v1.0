import curses
import re
from typing import Optional, List, Tuple, Dict, Any, Set
import weakref

from core.model import TreeNode
from ui.rendering.text import safe_addnstr, clear_line
from ui.rendering.colors import (
    FILE_COLOR, DIRECTORY_COLOR, DISABLED_COLOR, UI_LABEL_COLOR,
    TOKEN_LABEL_COLOR, SELECTED_COLOR, GENERAL_UI_COLOR, STRUCTURE_COLOR,
    UI_BRACKET_COLOR
)
from config.ui_labels import (
    COPY_LABEL, TOGGLE_LABEL, TOGGLE_ALL_LABEL, ENABLE_LABEL, DISABLE_LABEL,
    NO_FILES_LABEL, NO_TOKENS_LABEL, SUCCESS_MESSAGE, SEPARATOR, TOKEN_LABEL,
    REFACTOR_LABEL, REFACTOR_ALL_LABEL
)
from ui.core.labels import registry, render_single_label

_ARROW_COLLAPSED = '▸ '
_ARROW_EXPANDED = '▾ '
_INDENT_CACHE = {}
_BRACKET_PATTERN = re.compile(r'(\[[^\]]+\])(.*)')

def _get_indent(depth: int, unit: str) -> str:
    cache_key = (depth, unit)
    if cache_key not in _INDENT_CACHE:
        _INDENT_CACHE[cache_key] = unit * depth
    return _INDENT_CACHE[cache_key]

def _draw_line(stdscr, node: TreeNode, depth: int, show_tokens: bool, y: int, is_selected: bool):
    max_y, max_x = stdscr.getmaxyx()

    indent_unit = '│ ' if max_x < 100 else '│  '

    x = 0

    arrow = '> ' if is_selected else '  '
    safe_addnstr(stdscr, y, x, arrow, GENERAL_UI_COLOR,
                curses.A_BOLD if is_selected else 0)
    x += len(arrow)

    prefix = _get_indent(depth, indent_unit)
    safe_addnstr(stdscr, y, x, prefix, STRUCTURE_COLOR)
    x += len(prefix)

    if node.is_dir:
        symbol = _ARROW_EXPANDED if node.expanded else _ARROW_COLLAPSED
        safe_addnstr(stdscr, y, x, symbol, STRUCTURE_COLOR)
        x += len(symbol)

    color = DIRECTORY_COLOR if node.is_dir else (DISABLED_COLOR if node.disabled else FILE_COLOR)

    attr = curses.A_BOLD if is_selected else 0

    node_name = node.render_name
    max_name_width = max_x - x - 20

    if len(node_name) > max_name_width and max_name_width > 3:
        node_name = node_name[:max_name_width - 3] + '...'

    safe_addnstr(stdscr, y, x, node_name, color, attr)
    x += len(node_name)

    if show_tokens and node.token_count > 0 and x + 15 < max_x:
        context = {"node": node}
        x = render_single_label(
            stdscr, y, x, "tokens", context,
            separator=SEPARATOR,
            separator_color=GENERAL_UI_COLOR,
            show_separator=True
        )

    if x < max_x:
        clear_line(stdscr, y, x)

class TreeRenderer:
    def __init__(self, stdscr):
        self.stdscr = stdscr
        self.line_cache = {}
        self.last_visible_range = (0, 0)

    def render(self, flattened_nodes: List[Tuple[TreeNode, int, bool]],
               current_index: int, scroll_offset: int):
        if not flattened_nodes:
            return

        max_y, _ = self.stdscr.getmaxyx()
        visible_lines = max_y - 1

        for y in range(visible_lines):
            self.stdscr.move(y, 0)
            self.stdscr.clrtoeol()

        visible_range = (scroll_offset, min(scroll_offset + visible_lines, len(flattened_nodes)))

        if self.last_visible_range != visible_range:
            keys_to_remove = [k for k in self.line_cache.keys()
                               if k < visible_range[0] or k >= visible_range[1]]
            for k in keys_to_remove:
                del self.line_cache[k]
            self.last_visible_range = visible_range

        for i in range(min(visible_lines, len(flattened_nodes) - scroll_offset)):
            idx = scroll_offset + i
            if idx >= len(flattened_nodes):
                break

            node, depth, show_tokens = flattened_nodes[idx]
            _draw_line(self.stdscr, node, depth, show_tokens, i, idx == current_index)

            self.line_cache[idx] = self._calculate_line_hash(
                node, depth, show_tokens, idx == current_index
            )

    def _calculate_line_hash(self, node: TreeNode, depth: int,
                            show_tokens: bool, is_selected: bool) -> int:
        return hash((
            node.path,
            node.is_dir,
            node.expanded,
            node.disabled,
            node.token_count,
            node.render_name,
            depth,
            show_tokens,
            is_selected
        ))

_tree_renderer = None

def render_tree(stdscr, flattened_nodes: List[Tuple[TreeNode, int, bool]],
                current_index: int, scroll_offset: int):
    global _tree_renderer

    if _tree_renderer is None:
        _tree_renderer = TreeRenderer(stdscr)

    _tree_renderer.render(flattened_nodes, current_index, scroll_offset)

def render_success_message(stdscr, message=SUCCESS_MESSAGE):
    max_y, max_x = stdscr.getmaxyx()
    stdscr.move(max_y - 1, 0)
    stdscr.clrtoeol()
    safe_addnstr(stdscr, max_y - 1, 0, message, DIRECTORY_COLOR, curses.A_BOLD)

def _split_label(label_text):
    match = _BRACKET_PATTERN.match(label_text)
    if match:
        return match.group(1), match.group(2)
    return None, label_text

def render_status_bar(stdscr, current_node: Optional[TreeNode],
                      shift_mode: bool, total_tokens: int, tokens_visible: bool):
    max_y, max_x = stdscr.getmaxyx()
    stdscr.move(max_y - 1, 0)
    stdscr.clrtoeol()

    x_pos = 0
    node_labels = []

    if current_node:
        if current_node.is_dir:
            node_labels.append(TOGGLE_ALL_LABEL if shift_mode else TOGGLE_LABEL)

            if shift_mode and current_node.expanded:
                node_labels.append(REFACTOR_ALL_LABEL)
        else:
            node_labels.append(ENABLE_LABEL if current_node.disabled else DISABLE_LABEL)

            node_labels.append(REFACTOR_LABEL)

        node_labels.append(COPY_LABEL)
    else:
        node_labels.append(NO_FILES_LABEL)

    for i, label_text in enumerate(node_labels):
        bracket_part, text_part = _split_label(label_text)

        if bracket_part:
            safe_addnstr(stdscr, max_y - 1, x_pos, bracket_part, UI_BRACKET_COLOR)
            x_pos += len(bracket_part)

            safe_addnstr(stdscr, max_y - 1, x_pos, text_part, GENERAL_UI_COLOR)
            x_pos += len(text_part)
        else:
            safe_addnstr(stdscr, max_y - 1, x_pos, label_text, GENERAL_UI_COLOR)
            x_pos += len(label_text)

        if i < len(node_labels) - 1:
            safe_addnstr(stdscr, max_y - 1, x_pos, ' ', GENERAL_UI_COLOR)
            x_pos += 1

    if not tokens_visible:
        if total_tokens > 0:
            context = {"total_tokens": total_tokens}
            x_pos = render_single_label(
                stdscr, max_y - 1, x_pos, "tokens", context,
                separator=SEPARATOR,
                separator_color=GENERAL_UI_COLOR,
                show_separator=True
            )
        else:
            separator = f' {SEPARATOR} '
            safe_addnstr(stdscr, max_y - 1, x_pos, separator, GENERAL_UI_COLOR)
            x_pos += len(separator)

            no_tokens = f'{NO_TOKENS_LABEL}'
            safe_addnstr(stdscr, max_y - 1, x_pos, no_tokens, GENERAL_UI_COLOR)
            x_pos += len(no_tokens)

    if x_pos < max_x:
        clear_line(stdscr, max_y - 1, x_pos)

draw_line = _draw_line