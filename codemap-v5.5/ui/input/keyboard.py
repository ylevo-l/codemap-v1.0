import curses
from typing import Optional

from ui.controls.events import Event, EventType
from ui.controls.keyboard import ControlManager

class KeyboardInput:

    def __init__(self, control_manager: ControlManager):

        self.control_manager = control_manager

    def process_key(self, key: int) -> bool:

        if key == -1:
            return False

        event = self.control_manager.get_event_from_key(key)

        if event:
            return self.control_manager.handle_event(event)

        return False