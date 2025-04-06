import curses
from typing import Optional, List, Tuple

from core.model import TreeNode
from ui.rendering.text import safe_addnstr, clear_line
from config.ui_labels import (
    COPY_LABEL, TOGGLE_LABEL, TOGGLE_ALL_LABEL, ENABLE_LABEL, DISABLE_LABEL,
    NO_FILES_LABEL, NO_TOKENS_LABEL, SUCCESS_MESSAGE, SEPARATOR, TOKEN_LABEL
)

_ARROW_COLLAPSED = '▸ '
_ARROW_EXPANDED = '▾ '

def _indent(depth: int, unit: str):
    return unit * depth

def _draw_line(stdscr, node: TreeNode, depth: int, show_tokens: bool, y: int, is_selected: bool):
    max_y, max_x = stdscr.getmaxyx()
    indent_unit = '│ ' if max_x < 100 else '│  '
    
    x = 0
    
    arrow = '> ' if is_selected else '  '
    safe_addnstr(stdscr, y, x, arrow, 0)
    x += len(arrow)
    
    prefix = _indent(depth, indent_unit)
    safe_addnstr(stdscr, y, x, prefix, 0)
    x += len(prefix)
    
    if node.is_dir:
        symbol = _ARROW_EXPANDED if node.expanded else _ARROW_COLLAPSED
        safe_addnstr(stdscr, y, x, symbol, 7)
        x += len(symbol)
    
    color = 2 if node.is_dir else (3 if node.disabled else 1)
    node_name = node.render_name
    max_name_width = max_x - x - 20
    
    if len(node_name) > max_name_width and max_name_width > 3:
        node_name = node_name[:max_name_width - 3] + '...'
    
    attr = curses.A_DIM if (is_selected and not node.is_dir) else 0
    safe_addnstr(stdscr, y, x, node_name, color, attr)
    x += len(node_name)
    
    if show_tokens and node.token_count > 0 and x + 15 < max_x:
        safe_addnstr(stdscr, y, x, f' {SEPARATOR} ', 7)
        x += len(f' {SEPARATOR} ')
        
        safe_addnstr(stdscr, y, x, TOKEN_LABEL, 4)
        x += len(TOKEN_LABEL)
        
        safe_addnstr(stdscr, y, x, ':', 7)
        x += 1
        
        safe_addnstr(stdscr, y, x, f' {node.token_count}', 7)
        x += len(str(node.token_count)) + 1
    
    if x < max_x:
        clear_line(stdscr, y, x)

def render_tree(stdscr, flattened_nodes: List[Tuple[TreeNode, int, bool]],
               current_index: int, scroll_offset: int):
    if not flattened_nodes:
        return
    
    max_y, _ = stdscr.getmaxyx()
    visible_lines = max_y - 1
    
    for y in range(visible_lines):
        stdscr.move(y, 0)
        stdscr.clrtoeol()
    
    for i in range(min(visible_lines, len(flattened_nodes) - scroll_offset)):
        idx = scroll_offset + i
        if idx >= len(flattened_nodes):
            break
        
        node, depth, show_tokens = flattened_nodes[idx]
        _draw_line(stdscr, node, depth, show_tokens, i, idx == current_index)

def render_success_message(stdscr):
    max_y, max_x = stdscr.getmaxyx()
    stdscr.move(max_y - 1, 0)
    stdscr.clrtoeol()
    safe_addnstr(stdscr, max_y - 1, 0, SUCCESS_MESSAGE, 6)

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
        else:
            node_labels.append(ENABLE_LABEL if current_node.disabled else DISABLE_LABEL)
        
        node_labels.append(COPY_LABEL)
    else:
        node_labels.append(NO_FILES_LABEL)
    
    for i, label_text in enumerate(node_labels):
        safe_addnstr(stdscr, max_y - 1, x_pos, label_text, 7)
        x_pos += len(label_text)
        
        if i < len(node_labels) - 1:
            safe_addnstr(stdscr, max_y - 1, x_pos, ' ', 7)
            x_pos += 1
        else:
            safe_addnstr(stdscr, max_y - 1, x_pos, ' ', 7)
            x_pos += 1
    
    if not tokens_visible:
        if total_tokens > 0:
            segment = f'{SEPARATOR} '
            safe_addnstr(stdscr, max_y - 1, x_pos, segment, 7)
            x_pos += len(segment)
            
            safe_addnstr(stdscr, max_y - 1, x_pos, TOKEN_LABEL, 4)
            x_pos += len(TOKEN_LABEL)
            
            safe_addnstr(stdscr, max_y - 1, x_pos, ':', 7)
            x_pos += 1
            
            safe_addnstr(stdscr, max_y - 1, x_pos, f' {total_tokens}', 7)
            x_pos += len(str(total_tokens)) + 1
        else:
            segment = f'{SEPARATOR} {NO_TOKENS_LABEL}'
            safe_addnstr(stdscr, max_y - 1, x_pos, segment, 7)
            x_pos += len(segment)
    
    if x_pos < max_x:
        clear_line(stdscr, max_y - 1, x_pos)

draw_line = _draw_line