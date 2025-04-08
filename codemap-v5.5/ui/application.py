import curses
import time
import threading
from typing import Dict, List, Tuple, Optional
import cProfile
import gc

from core.model import TreeNode
from core.operations import flatten_tree
from config import INPUT_TIMEOUT
from ui.rendering import init_colors, Renderer
from ui.core.state import UIState
from ui.controls.manager import ControlManager
from ui.controls.keyboard import KeyboardEventHandler
from ui.controls.actions import ActionHandler

class Application:
    def __init__(self, stdscr, root_node: TreeNode, path_to_node: Dict[str, TreeNode],
                fmt: str, path_mode: str, tree_changed_flag: threading.Event,
                lock: threading.Lock):
        self.stdscr = stdscr
        self.root_node = root_node
        self.path_to_node = path_to_node
        self.fmt = fmt
        self.path_mode = path_mode
        self.tree_changed_flag = tree_changed_flag
        self.lock = lock
        self.resized = False

        self._init_components()

    def _init_components(self):
        self._setup_curses()

        self.ui_state = UIState()
        self.flattened_cache = []
        self.total_tokens = 0
        self.selected_node_path = None
        self.action_caused_tree_change = False
        self.last_tree_change_time = 0
        self.last_input_time = time.time()
        self.needs_full_rebuild = True

        self.renderer = Renderer(self.stdscr, self.ui_state)

        self._setup_controls()

        self._cache_tree()

    def _setup_curses(self):
        curses.curs_set(0)
        curses.noecho()
        curses.cbreak()

        if hasattr(curses, "set_escdelay"):
            try:
                curses.set_escdelay(25)
            except:
                pass

        self.stdscr.nodelay(True)
        self.stdscr.keypad(True)
        self.stdscr.timeout(int(INPUT_TIMEOUT * 1000))
        self.stdscr.clear()
        self.stdscr.refresh()

        init_colors()

    def _setup_controls(self):
        self.control_manager = ControlManager(self.ui_state)
        self.keyboard_handler = KeyboardEventHandler(self.control_manager, self.ui_state)

        self.action_handler = ActionHandler(
            self.stdscr,
            self.ui_state,
            self.root_node,
            self.path_to_node,
            self.fmt,
            self.path_mode,
            self.tree_changed_flag,
            self.lock
        )

        self.action_handler.register_handlers(self.control_manager)
        self.keyboard_handler.setup(callback_fn=self._redraw_on_shift_change)

    def _cache_tree(self):

        if not self.needs_full_rebuild and not self.tree_changed_flag.is_set():
            return False

        with self.lock:

            if self.needs_full_rebuild:

                self.flattened_cache = list(flatten_tree(self.root_node))
                self.total_tokens = self.root_node.token_count
                self.needs_full_rebuild = False

                if self.flattened_cache:
                    self.selected_node_path = self.flattened_cache[self.ui_state.current_index][0].path
                return True

        return False

    def _redraw_on_shift_change(self):
        self._update_screen()

    def run(self):
        try:
            needs_redraw = True
            last_gc_time = time.time()

            while not self.ui_state.should_quit:
                current_time = time.time()

                if current_time - last_gc_time > 5.0:
                    gc.collect()
                    last_gc_time = current_time

                if self.resized:
                    curses.endwin()
                    self.stdscr.refresh()
                    self.resized = False
                    needs_redraw = True

                needs_redraw = self._process_events() or needs_redraw

                if needs_redraw:
                    self._update_screen()
                    needs_redraw = False

                input_result = self._handle_input()
                needs_redraw = needs_redraw or input_result

                if not needs_redraw and not self.tree_changed_flag.is_set():
                    time.sleep(INPUT_TIMEOUT)
        finally:
            self.keyboard_handler.cleanup()
            self._cleanup_terminal()

    def _cleanup_terminal(self):
        try:
            self.stdscr.keypad(False)
            curses.echo()
            curses.nocbreak()
            curses.endwin()
        except:
            pass

    def _process_events(self):
        needs_redraw = False
        now = time.time()

        if self.ui_state.copying_success and now - self.ui_state.success_message_time > 1.0:
            self.ui_state.copying_success = False
            needs_redraw = True

        if self.ui_state.redraw_needed.is_set():
            self.ui_state.redraw_needed.clear()
            needs_redraw = True

        if self.tree_changed_flag.is_set():

            if self.action_caused_tree_change or now - self.last_tree_change_time > 0.1:
                self._handle_tree_change()
                self.last_tree_change_time = now
                needs_redraw = True

        return needs_redraw

    def _handle_input(self):
        current_time = time.time()
        key = self.stdscr.getch()

        if key == curses.KEY_RESIZE:
            self.resized = True
            return True

        elif key != -1:
            self.last_input_time = current_time

            if self.keyboard_handler.handle_key(key):
                if self.tree_changed_flag.is_set():
                    self.action_caused_tree_change = True
                return True

        return False

    def _handle_tree_change(self):

        self.needs_full_rebuild = True
        self._cache_tree()

        with self.lock:

            found_index = -1
            if self.action_caused_tree_change and self.selected_node_path:
                for i, (node, _, _) in enumerate(self.flattened_cache):
                    if node.path == self.selected_node_path:
                        found_index = i
                        break

            if found_index != -1:
                self.ui_state.current_index = found_index
            else:
                self.ui_state.update_selected_index(0, len(self.flattened_cache))

            self.tree_changed_flag.clear()

        self.action_caused_tree_change = False
        self.selected_node_path = None

    def _update_screen(self):

        max_y, max_x = self.stdscr.getmaxyx()
        visible_lines = max_y - 1

        with self.lock:
            self.ui_state.ensure_visible(visible_lines, len(self.flattened_cache))

            current_node = None
            if self.flattened_cache and 0 <= self.ui_state.current_index < len(self.flattened_cache):
                current_node = self.flattened_cache[self.ui_state.current_index][0]

                if not self.action_caused_tree_change:
                    self.selected_node_path = current_node.path

                self.action_handler.update_context(current_node, self.flattened_cache)

            self.renderer.render(self.flattened_cache, current_node, self.total_tokens)

def run_application(stdscr, root_node: TreeNode, path_to_node: Dict[str, TreeNode],
                  fmt: str, path_mode: str, tree_changed_flag: threading.Event,
                  lock: threading.Lock):
    if hasattr(curses, 'update_lines_cols'):
        curses.update_lines_cols()

    app = Application(stdscr, root_node, path_to_node, fmt, path_mode, tree_changed_flag, lock)
    app.run()