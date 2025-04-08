import curses
import time
from typing import List, Tuple, Optional, Dict, Set

from core.model import TreeNode
from config.constants import SUCCESS_MESSAGE_DURATION
from ui.rendering.components import render_tree, draw_line, render_status_bar, render_success_message
from ui.core.state import UIState

class Renderer:
    def __init__(self, stdscr, ui_state: UIState):
        self.stdscr = stdscr
        self.ui_state = ui_state

        self.last_dimensions = (0, 0)
        self.last_flattened_id = None
        self.last_current_index = -1
        self.last_scroll_offset = 0
        self.last_tokens_visible = False

        self.rendered_lines = {}
        self.visible_range = (0, 0)

    def render(self, flattened_nodes: List[Tuple[TreeNode, int, bool]],
               current_node: Optional[TreeNode], total_tokens: int):
        max_y, max_x = self.stdscr.getmaxyx()
        dimensions_changed = (max_y, max_x) != self.last_dimensions

        if dimensions_changed:
            self.stdscr.clear()
            self.last_dimensions = (max_y, max_x)
            self.rendered_lines.clear()

        visible_lines = max_y - 1
        tokens_visible = self._are_tokens_visible(
            flattened_nodes, self.ui_state.scroll_offset, visible_lines
        )

        tree_changed = id(flattened_nodes) != self.last_flattened_id
        scroll_changed = self.ui_state.scroll_offset != self.last_scroll_offset
        selection_moved = self.ui_state.current_index != self.last_current_index
        show_success = self.ui_state.copying_success

        if show_success and time.time() - self.ui_state.success_message_time > SUCCESS_MESSAGE_DURATION:
            self.ui_state.copying_success = False
            show_success = False

        need_full_redraw = dimensions_changed or tree_changed or scroll_changed or self.last_tokens_visible != tokens_visible

        new_visible_range = (self.ui_state.scroll_offset,
                              min(self.ui_state.scroll_offset + visible_lines, len(flattened_nodes)))

        if self.visible_range != new_visible_range:
            keys_to_remove = [k for k in self.rendered_lines.keys()
                               if k < new_visible_range[0] or k >= new_visible_range[1]]
            for k in keys_to_remove:
                del self.rendered_lines[k]

            self.visible_range = new_visible_range

        if need_full_redraw:
            if not dimensions_changed:
                self.stdscr.erase()

            try:
                separator_line = '─' * max_x
                self.stdscr.addnstr(max_y - 2, 0, separator_line, max_x - 1, curses.color_pair(7))
            except:
                pass

            render_tree(
                self.stdscr, flattened_nodes,
                self.ui_state.current_index, self.ui_state.scroll_offset
            )

            for i in range(min(visible_lines, len(flattened_nodes) - self.ui_state.scroll_offset)):
                idx = self.ui_state.scroll_offset + i
                if idx < len(flattened_nodes):
                    node, depth, show_tokens = flattened_nodes[idx]
                    self.rendered_lines[idx] = (self._calculate_node_hash(node, depth, show_tokens, idx == self.ui_state.current_index), '')

        elif selection_moved:
            y_old = self.last_current_index - self.ui_state.scroll_offset
            y_new = self.ui_state.current_index - self.ui_state.scroll_offset

            if 0 <= y_old < visible_lines and self.last_current_index < len(flattened_nodes):
                node_old, depth_old, show_tokens_old = flattened_nodes[self.last_current_index]
                self.rendered_lines[self.last_current_index] = (-1, '')
                draw_line(self.stdscr, node_old, depth_old, show_tokens_old, y_old, False)
                self.rendered_lines[self.last_current_index] = (
                    self._calculate_node_hash(node_old, depth_old, show_tokens_old, False),
                    ''
                )

            if 0 <= y_new < visible_lines:
                node_new, depth_new, show_tokens_new = flattened_nodes[self.ui_state.current_index]
                self.rendered_lines[self.ui_state.current_index] = (-1, '')
                draw_line(self.stdscr, node_new, depth_new, show_tokens_new, y_new, True)
                self.rendered_lines[self.ui_state.current_index] = (
                    self._calculate_node_hash(node_new, depth_new, show_tokens_new, True),
                    ''
                )

        if show_success:
            message = getattr(self.ui_state, 'success_message', 'Operation completed successfully.')
            render_success_message(self.stdscr, message)
        else:
            render_status_bar(
                self.stdscr, current_node,
                self.ui_state.physical_shift_pressed, total_tokens, tokens_visible
            )

        self.stdscr.refresh()

        self.last_flattened_id = id(flattened_nodes)
        self.last_current_index = self.ui_state.current_index
        self.last_scroll_offset = self.ui_state.scroll_offset
        self.last_tokens_visible = tokens_visible

    def _calculate_node_hash(self, node: TreeNode, depth: int, show_tokens: bool, is_selected: bool) -> int:
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

    def _are_tokens_visible(self, flattened_nodes: List[Tuple[TreeNode, int, bool]],
                            scroll_offset: int, visible_lines: int) -> bool:
        if not flattened_nodes or scroll_offset >= len(flattened_nodes):
            return False

        visible_range = flattened_nodes[
            scroll_offset:min(scroll_offset + visible_lines, len(flattened_nodes))
        ]
        return any(show_tokens for _, _, show_tokens in visible_range)