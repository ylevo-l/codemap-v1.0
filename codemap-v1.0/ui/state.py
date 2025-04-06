import threading
from config import SCROLL_SPEED

class UIState:
    def __init__(self):
        self.current_index = 0
        self.scroll_offset = 0
        
        self.physical_shift_pressed = False
        
        self.copying_success = False
        self.success_message_time = 0.0
        
        self.should_quit = False
        
        self.redraw_needed = threading.Event()
        
        self.step_normal = SCROLL_SPEED["normal"]
        self.step_accel = SCROLL_SPEED["accelerated"]
    
    def update_selected_index(self, direction: int, flattened_nodes_length: int, is_shift_pressed: bool = False) -> None:
        if flattened_nodes_length == 0:
            self.current_index = 0
            return
        
        step = self.step_accel if is_shift_pressed else self.step_normal
        
        if direction < 0:
            self.current_index = max(0, self.current_index - step)
        elif direction > 0:
            self.current_index = min(flattened_nodes_length - 1, self.current_index + step)
        
        self.current_index = max(0, min(self.current_index, flattened_nodes_length - 1))
    
    def ensure_visible(self, visible_lines: int, flattened_nodes_length: int) -> None:
        if flattened_nodes_length == 0:
            self.scroll_offset = 0
            self.current_index = 0
            return
        
        self.current_index = max(0, min(self.current_index, flattened_nodes_length - 1))
        
        if self.current_index < self.scroll_offset:
            self.scroll_offset = self.current_index
        elif self.current_index >= self.scroll_offset + visible_lines:
            self.scroll_offset = self.current_index - visible_lines + 1
        
        self.scroll_offset = max(0, self.scroll_offset)
        self.scroll_offset = min(self.scroll_offset, max(0, flattened_nodes_length - visible_lines))