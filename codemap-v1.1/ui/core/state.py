import threading
import time
from typing import Tuple, Dict, Any, Optional, Set

from config import SCROLL_SPEED
from config.ui_labels import SUCCESS_MESSAGE

class UIState:
    def __init__(self):

        self.current_index = 0
        self.scroll_offset = 0
        self._prev_current_index = 0
        self._prev_scroll_offset = 0

        self.physical_shift_pressed = False

        self.copying_success = False
        self.success_message_time = 0.0
        self.success_message = SUCCESS_MESSAGE

        self.should_quit = False

        self.redraw_needed = threading.Event()

        self.step_normal = SCROLL_SPEED["normal"]
        self.step_accel = SCROLL_SPEED["accelerated"]

        self._last_update_time = time.time()
        self._changed_properties = set()

        self._lock = threading.RLock()

    def update_selected_index(self, direction: int, flattened_nodes_length: int,
                             is_shift_pressed: bool = False) -> None:
        with self._lock:

            self._prev_current_index = self.current_index

            if flattened_nodes_length == 0:
                self.current_index = 0
                return

            step = self.step_accel if is_shift_pressed else self.step_normal

            if direction < 0:
                self.current_index = max(0, self.current_index - step)
            elif direction > 0:
                self.current_index = min(flattened_nodes_length - 1, self.current_index + step)

            self.current_index = max(0, min(self.current_index, flattened_nodes_length - 1))

            if self._prev_current_index != self.current_index:
                self._changed_properties.add('current_index')
                self._last_update_time = time.time()

    def ensure_visible(self, visible_lines: int, flattened_nodes_length: int) -> bool:
        with self._lock:

            self._prev_scroll_offset = self.scroll_offset

            if flattened_nodes_length == 0:
                self.scroll_offset = 0
                self.current_index = 0
                return False

            self.current_index = max(0, min(self.current_index, flattened_nodes_length - 1))

            if self.current_index < self.scroll_offset:
                self.scroll_offset = self.current_index
            elif self.current_index >= self.scroll_offset + visible_lines:
                self.scroll_offset = self.current_index - visible_lines + 1

            self.scroll_offset = max(0, self.scroll_offset)
            self.scroll_offset = min(self.scroll_offset, max(0, flattened_nodes_length - visible_lines))

            scroll_changed = self._prev_scroll_offset != self.scroll_offset
            if scroll_changed:
                self._changed_properties.add('scroll_offset')
                self._last_update_time = time.time()
            return scroll_changed

    def set_success_message(self, message=SUCCESS_MESSAGE, show: bool = True) -> None:
        with self._lock:
            self.copying_success = show
            if show:
                self.success_message_time = time.time()
                self.success_message = message
            self._changed_properties.add('copying_success')

    def set_shift_pressed(self, pressed: bool) -> None:
        with self._lock:
            if self.physical_shift_pressed != pressed:
                self.physical_shift_pressed = pressed
                self._changed_properties.add('physical_shift_pressed')
                self.redraw_needed.set()

    def request_redraw(self) -> None:
        self.redraw_needed.set()

    def has_changes(self) -> bool:
        return len(self._changed_properties) > 0

    def get_changed_properties(self) -> Set[str]:
        return self._changed_properties.copy()

    def reset_change_tracking(self) -> None:
        with self._lock:
            self._changed_properties.clear()

    def get_navigation_state(self) -> Dict[str, Any]:
        with self._lock:
            return {
                'current_index': self.current_index,
                'scroll_offset': self.scroll_offset,
                'shift_pressed': self.physical_shift_pressed
            }

    def get_update_time(self) -> float:
        return self._last_update_time