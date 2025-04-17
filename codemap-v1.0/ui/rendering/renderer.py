import curses, time
from typing import List, Tuple, Optional
from core.model import TreeNode
from config.constants import SUCCESS_MESSAGE_DURATION
from ui.rendering.components import render_status_bar, render_success_message
from ui.core.state import State
from ui.rendering.text import safe_addnstr, clear_line
from ui.rendering.colors import FILE_COLOR, DIRECTORY_COLOR, DISABLED_COLOR, GENERAL_UI_COLOR, STRUCTURE_COLOR, SELECTED_COLOR
from ui.core.labels import render_single_label
from config.ui_labels import SEPARATOR
from config.symbols import CURSOR_SYMBOL_SELECTED, CURSOR_SYMBOL_UNSELECTED, ARROW_COLLAPSED, ARROW_EXPANDED

def _truncate_node_name(name: str, max_width: int) -> str:
    if max_width <= 3:
        return name
    if len(name) > max_width:
        return name[: max_width - 3] + "..."
    return name

class Renderer:
    def __init__(self, stdscr: any, ui_state: State):
        self.stdscr = stdscr
        self.ui_state = ui_state
        self.width = 0
        self.height = 0
        self.last_current_index = -1
        self.last_scroll_offset = 0
        self.last_tokens_visible = False
        self.last_flattened_nodes = None

    def _clear_screen_if_resized(self) -> None:
        max_y, max_x = self.stdscr.getmaxyx()
        if max_y != self.height or max_x != self.width:
            self.stdscr.clear()
            self.height = max_y
            self.width = max_x

    def _top_node_shows_tokens(self, flattened_nodes: List[Tuple[TreeNode, int, bool]], offset: int) -> bool:
        if not flattened_nodes:
            return False
        if offset < len(flattened_nodes):
            return flattened_nodes[offset][2]
        return False

    def _should_render_success_message(self) -> bool:
        if not self.ui_state.copying_success:
            return False
        if time.time() - self.ui_state.success_message_time > SUCCESS_MESSAGE_DURATION:
            self.ui_state.copying_success = False
            return False
        return True

    def _clear_viewport(self, visible_lines: int) -> None:
        for row in range(visible_lines):
            self.stdscr.move(row, 0)
            self.stdscr.clrtoeol()
    def _render_node_line(
        self,
        stdscr: any,
        node: TreeNode,
        depth: int,
        show_tokens: bool,
        y: int,
        is_selected: bool,
    ) -> None:
        max_y, max_x = stdscr.getmaxyx()
        x = 0
        arrow = CURSOR_SYMBOL_SELECTED if is_selected else CURSOR_SYMBOL_UNSELECTED
        safe_addnstr(stdscr, y, x, arrow, STRUCTURE_COLOR, curses.A_BOLD if is_selected else 0)
        x += len(arrow)
        prefix = "│ " * depth
        safe_addnstr(stdscr, y, x, prefix, STRUCTURE_COLOR)
        x += len(prefix)
        if node.is_dir:
            symbol = ARROW_EXPANDED if node.expanded else ARROW_COLLAPSED
            safe_addnstr(
                stdscr,
                y,
                x,
                symbol,
                STRUCTURE_COLOR,
                curses.A_BOLD if is_selected else 0,
            )
            x += len(symbol)
        color = DIRECTORY_COLOR if node.is_dir else (DISABLED_COLOR if node.disabled else FILE_COLOR)
        attr = curses.A_BOLD if is_selected else 0
        node_name = _truncate_node_name(node.render_name, max_x - x - 20)
        safe_addnstr(stdscr, y, x, node_name, color, attr)
        x += len(node_name)
        if show_tokens and node.token_count > 0 and x + 15 < max_x:
            context = {"node": node}
            x = render_single_label(
                stdscr,
                y,
                x,
                "tokens",
                context,
                separator=SEPARATOR,
                separator_color=GENERAL_UI_COLOR,
                show_separator=True,
            )
        if x < max_x:
            clear_line(stdscr, y, x)
    def _render_node_list(
        self, flattened_nodes: List[Tuple[TreeNode, int, bool]], start_idx: int, end_idx: int
    ) -> None:
        for i in range(start_idx, end_idx):
            node, depth, show_tokens = flattened_nodes[i]
            row = i - start_idx
            is_selected = i == self.ui_state.current_index
            self._render_node_line(self.stdscr, node, depth, show_tokens, row, is_selected)
    def _render_footer_bar(
        self, current_node: Optional[TreeNode], total_tokens: int, tokens_visible: bool, show_success: bool
    ) -> None:
        if show_success:
            msg = getattr(self.ui_state, "success_message", "")
            render_success_message(self.stdscr, msg)
        else:
            render_status_bar(
                self.stdscr,
                current_node,
                self.ui_state.physical_shift_pressed,
                total_tokens,
                tokens_visible,
            )
    def render(
        self,
        flattened_nodes: List[Tuple[TreeNode, int, bool]],
        current_node: Optional[TreeNode],
        total_tokens: int,
    ) -> None:
        self._clear_screen_if_resized()
        max_y, _ = self.stdscr.getmaxyx()
        visible_lines = max_y - 1
        tokens_visible = self._top_node_shows_tokens(flattened_nodes, self.ui_state.scroll_offset)
        show_success = self._should_render_success_message()
        same_list = flattened_nodes is self.last_flattened_nodes
        selection_changed = self.ui_state.current_index != self.last_current_index
        scroll_changed = self.ui_state.scroll_offset != self.last_scroll_offset
        incremental = (
            same_list
            and not scroll_changed
            and selection_changed
            and not show_success
            and tokens_visible == self.last_tokens_visible
        )
        if incremental:
            row_prev = self.last_current_index - self.ui_state.scroll_offset
            row_new = self.ui_state.current_index - self.ui_state.scroll_offset
            if 0 <= row_prev < visible_lines:
                node_prev, depth_prev, show_tokens_prev = flattened_nodes[self.last_current_index]
                self._render_node_line(self.stdscr, node_prev, depth_prev, show_tokens_prev, row_prev, False)
            if 0 <= row_new < visible_lines:
                node_new, depth_new, show_tokens_new = flattened_nodes[self.ui_state.current_index]
                self._render_node_line(self.stdscr, node_new, depth_new, show_tokens_new, row_new, True)
            self._render_footer_bar(current_node, total_tokens, tokens_visible, show_success)
        else:
            self._clear_viewport(visible_lines)
            start_idx = self.ui_state.scroll_offset
            end_idx = min(start_idx + visible_lines, len(flattened_nodes))
            self._render_node_list(flattened_nodes, start_idx, end_idx)
            self._render_footer_bar(current_node, total_tokens, tokens_visible, show_success)
        self.stdscr.noutrefresh()
        curses.doupdate()
        self.last_current_index = self.ui_state.current_index
        self.last_scroll_offset = self.ui_state.scroll_offset
        self.last_tokens_visible = tokens_visible
        self.last_flattened_nodes = flattened_nodes
