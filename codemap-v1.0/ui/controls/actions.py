import time
import threading
import curses
from typing import Optional, Dict, List, Tuple

from core.model import TreeNode
from core.operations import toggle_node, toggle_subtree, collect_visible_files
from core.clipboard import copy_files_subloop, copy_text_to_clipboard
from core.state import gather_state, save_state
from config import STATE_FILE
from ui.controls.events import Event, EventType
from ui.state import UIState

class ActionHandler:
    def __init__(self, stdscr, ui_state: UIState, root_node: TreeNode,
                path_to_node: Dict[str, TreeNode], fmt: str, path_mode: str,
                tree_changed_flag: threading.Event, lock: threading.Lock):
        self.stdscr = stdscr
        self.ui_state = ui_state
        self.root_node = root_node
        self.path_to_node = path_to_node
        self.fmt = fmt
        self.path_mode = path_mode
        self.tree_changed_flag = tree_changed_flag
        self.lock = lock
        self.current_node = None
        self.flattened_cache = []
        self.selected_node_path = None
    
    def update_context(self, current_node: Optional[TreeNode],
                      flattened_cache: List[Tuple[TreeNode, int, bool]]):
        self.current_node = current_node
        self.flattened_cache = flattened_cache
        
        if current_node:
            self.selected_node_path = current_node.path
    
    def handle_navigation_up(self, event: Event):
        with self.lock:
            shift = event.data.get('shift', False) if event.data else False
            self.ui_state.update_selected_index(-1, len(self.flattened_cache), shift)
            return True
    
    def handle_navigation_down(self, event: Event):
        with self.lock:
            shift = event.data.get('shift', False) if event.data else False
            self.ui_state.update_selected_index(1, len(self.flattened_cache), shift)
            return True
    
    def handle_toggle_node(self, event: Event):
        if not self.current_node or not self.current_node.is_dir:
            return False
        
        with self.lock:
            toggle_node(self.current_node)
            self.current_node.calculate_token_count()
            
            if self.current_node.parent:
                self.current_node.parent.calculate_token_count()
            
            self.tree_changed_flag.set()
            return True
    
    def handle_toggle_subtree(self, event: Event):
        if not self.current_node or not self.current_node.is_dir:
            return False
        
        with self.lock:
            toggle_subtree(self.current_node)
            self.current_node.calculate_token_count()
            
            if self.current_node.parent:
                self.current_node.parent.calculate_token_count()
            
            self.tree_changed_flag.set()
            return True
    
    def handle_toggle_disable(self, event: Event):
        if not self.current_node or self.current_node.is_dir:
            return False
        
        with self.lock:
            previous_tokens = self.current_node.token_count if not self.current_node.disabled else 0
            self.current_node.disabled = not self.current_node.disabled
            self.current_node.update_render_name()
            
            new_tokens = self.current_node.token_count if not self.current_node.disabled else 0
            delta = new_tokens - previous_tokens
            
            if self.current_node.parent:
                self.current_node.parent.update_token_count(delta)
            
            self.tree_changed_flag.set()
            return True
    
    def handle_copy_content(self, event: Event):
        if not self.current_node:
            return False
        
        files_to_copy = collect_visible_files(self.current_node, self.path_mode)
        
        if files_to_copy:
            copied_text = copy_files_subloop(self.stdscr, files_to_copy, self.fmt)
            copy_text_to_clipboard(copied_text)
            
            self.ui_state.copying_success = True
            self.ui_state.success_message_time = time.time()
            return True
        
        return False
    
    def handle_enter_key(self, event: Event):
        return self.handle_toggle_node(event)
    
    def handle_quit(self, event: Event):
        with self.lock:
            state = {}
            gather_state(self.root_node, state, base_path=self.root_node.path, is_root=True)
            save_state(STATE_FILE, state)
            
            try:
                self.stdscr.clear()
                self.stdscr.refresh()
                curses.nocbreak()
                self.stdscr.keypad(False)
                curses.echo()
                curses.endwin()
            except:
                pass
            
            self.ui_state.should_quit = True
            return True
    
    def handle_shift_mode_changed(self, event: Event):
        return True
    
    def register_handlers(self, control_manager):
        control_manager.register_handler(
            EventType.NAVIGATION_UP, lambda e: self.handle_navigation_up(e))
        control_manager.register_handler(
            EventType.NAVIGATION_DOWN, lambda e: self.handle_navigation_down(e))
        control_manager.register_handler(
            EventType.TOGGLE_NODE, lambda e: self.handle_toggle_node(e))
        control_manager.register_handler(
            EventType.TOGGLE_SUBTREE, lambda e: self.handle_toggle_subtree(e))
        control_manager.register_handler(
            EventType.TOGGLE_DISABLE, lambda e: self.handle_toggle_disable(e))
        control_manager.register_handler(
            EventType.COPY_CONTENT, lambda e: self.handle_copy_content(e))
        control_manager.register_handler(
            EventType.ENTER_KEY, lambda e: self.handle_enter_key(e))
        control_manager.register_handler(
            EventType.QUIT, lambda e: self.handle_quit(e))
        control_manager.register_handler(
            EventType.SHIFT_MODE_CHANGED, lambda e: self.handle_shift_mode_changed(e))