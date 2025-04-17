import curses
from typing import Optional
from core.model import TreeNode
from ui.rendering.text import safe_addnstr
from ui.rendering.colors import DIRECTORY_COLOR
from config.ui_labels import SUCCESS_MESSAGE
from ui.rendering.labels import _create_node_labels, render_node_labels, render_token_info

def render_success_message(stdscr, message=SUCCESS_MESSAGE):
    max_y, max_x = stdscr.getmaxyx()
    stdscr.move(max_y - 1, 0)
    stdscr.clrtoeol()
    safe_addnstr(stdscr, max_y - 1, 0, message, DIRECTORY_COLOR, curses.A_BOLD)

def render_status_bar(stdscr, current_node: Optional[TreeNode], shift_mode: bool, total_tokens: int, tokens_visible: bool):
    max_y, max_x = stdscr.getmaxyx()
    stdscr.move(max_y - 1, 0)
    stdscr.clrtoeol()
    x_pos = 0
    node_labels = _create_node_labels(current_node, shift_mode)
    x_pos = render_node_labels(stdscr, max_y - 1, x_pos, node_labels)
    x_pos = render_token_info(stdscr, max_y - 1, x_pos, tokens_visible, total_tokens)
    if x_pos < max_x:
        stdscr.move(max_y - 1, x_pos)
        stdscr.clrtoeol()
