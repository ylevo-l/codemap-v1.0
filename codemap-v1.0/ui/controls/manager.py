import curses
from typing import Dict, Callable, Optional

from ui.controls.events import Event, EventType
from ui.state import UIState

class ControlManager:
    def __init__(self, ui_state: UIState):
        self.ui_state = ui_state
        self.event_handlers: Dict[EventType, Callable[[Event], bool]] = {}
    
    def register_handler(self, event_type: EventType, handler: Callable[[Event], bool]):
        self.event_handlers[event_type] = handler
    
    def handle_event(self, event: Event):
        if event and event.event_type in self.event_handlers:
            return self.event_handlers[event.event_type](event)
        return False
    
    def get_event_from_key(self, key: int) -> Optional[Event]:
        if key in (ord("w"), ord("W"), curses.KEY_UP):
            return Event(EventType.NAVIGATION_UP, source="keyboard",
                        data={"shift": self.ui_state.physical_shift_pressed})
        
        if key in (ord("s"), ord("S"), curses.KEY_DOWN):
            return Event(EventType.NAVIGATION_DOWN, source="keyboard",
                        data={"shift": self.ui_state.physical_shift_pressed})
        
        if self.ui_state.physical_shift_pressed and key == ord("E"):
            return Event(EventType.TOGGLE_SUBTREE, source="keyboard")
        
        if key in (curses.KEY_ENTER, 10, 13):
            return Event(EventType.ENTER_KEY, source="keyboard")
        
        if key == ord("c"):
            return Event(EventType.COPY_CONTENT, source="keyboard")
        
        if key in (ord("q"), ord("Q")):
            return Event(EventType.QUIT, source="keyboard")
        
        if key == ord("e"):
            return Event(EventType.TOGGLE_NODE, source="keyboard")
        
        if key == ord("d"):
            return Event(EventType.TOGGLE_DISABLE, source="keyboard")
        
        return None