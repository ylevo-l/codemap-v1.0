import curses
import time
from typing import List, Tuple, Optional

from core.model import TreeNode
from config.constants import SUCCESS_MESSAGE_DURATION
from ui.rendering.components import render_tree, draw_line, render_status_bar, render_success_message
from ui.state import UIState

class Renderer:
    def __init__(self, stdscr, ui_state: UIState):
        self.stdscr = stdscr
        self.ui_state = ui_state
        
        self.last_dimensions = (0, 0)
        self.last_flattened_id = None
        self.last_current_index = -1
        self.last_scroll_offset = 0
        self.last_tokens_visible = False
    
    def render(self, flattened_nodes: List[Tuple[TreeNode, int, bool]],
              current_node: Optional[TreeNode], total_tokens: int):
        max_y, max_x = self.stdscr.getmaxyx()
        dimensions_changed = (max_y, max_x) != self.last_dimensions
        
        if dimensions_changed:
            self.stdscr.clear()
            self.last_dimensions = (max_y, max_x)
        
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
        
        if need_full_redraw:
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
        elif selection_moved:
            y_old = self.last_current_index - self.ui_state.scroll_offset
            y_new = self.ui_state.current_index - self.ui_state.scroll_offset
            
            if 0 <= y_old < visible_lines:
                node_old, depth_old, show_tokens_old = flattened_nodes[self.last_current_index]
                draw_line(self.stdscr, node_old, depth_old, show_tokens_old, y_old, False)
            
            if 0 <= y_new < visible_lines:
                node_new, depth_new, show_tokens_new = flattened_nodes[self.ui_state.current_index]
                draw_line(self.stdscr, node_new, depth_new, show_tokens_new, y_new, True)
        
        if show_success:
            render_success_message(self.stdscr)
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
    
    def _are_tokens_visible(self, flattened_nodes: List[Tuple[TreeNode, int, bool]],
                           scroll_offset: int, visible_lines: int):
        if not flattened_nodes or scroll_offset >= len(flattened_nodes):
            return False
        
        visible_range = flattened_nodes[
            scroll_offset:min(scroll_offset + visible_lines, len(flattened_nodes))
        ]
        return any(show_tokens for _, _, show_tokens in visible_range)