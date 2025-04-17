import keyboard
import curses
from typing import Callable
from ui.controls.manager import ControlManager
from ui.controls.events import Event, EventType
from ui.core.state import State

class KeyboardEventHandler:
    def __init__(self, control_manager: ControlManager, ui_state: State):
        self.control_manager = control_manager
        self.ui_state = ui_state
        self._keyboard_hooked = False
        self._callback_fn = None

    def setup(self, callback_fn: Callable = None):
        if not self._keyboard_hooked:
            try:
                self._callback_fn = callback_fn
                keyboard.hook(self._shift_event_handler)
                self._keyboard_hooked = True
                return True
            except:
                return False
        return True

    def cleanup(self):
        if self._keyboard_hooked:
            keyboard.unhook_all()
            self._keyboard_hooked = False

    def handle_key(self, key: int):
        if key == -1:
            return False
        event = self.control_manager.get_event_from_key(key)
        if event:
            return self.control_manager.handle_event(event)
        return False

    def _shift_event_handler(self, event: keyboard.KeyboardEvent):
        is_shift = event.name == 'shift' or event.name == 'left shift' or event.name == 'right shift'
        if is_shift:
            new_shift_state = (event.event_type == keyboard.KEY_DOWN)
            if self.ui_state.physical_shift_pressed != new_shift_state:
                self.ui_state.physical_shift_pressed = new_shift_state
                self.ui_state.redraw_needed.set()
                shift_event = Event(EventType.SHIFT_MODE_CHANGED, source="keyboard", data={"shift": new_shift_state})
                self.control_manager.handle_event(shift_event)
                if self._callback_fn:
                    self._callback_fn()
