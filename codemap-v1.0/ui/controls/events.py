from enum import Enum, auto
from typing import Dict, Any, Optional

class EventType(Enum):
    NAVIGATION_UP = auto()
    NAVIGATION_DOWN = auto()
    TOGGLE_NODE = auto()
    TOGGLE_SUBTREE = auto()
    TOGGLE_DISABLE = auto()
    COPY_CONTENT = auto()
    REFACTOR_CONTENT = auto()
    QUIT = auto()
    ENTER_KEY = auto()
    SHIFT_MODE_CHANGED = auto()
    SHIFT_DISABLE_ALL = auto()

class Event:
    def __init__(self, event_type: EventType, source: Optional[str] = None, data: Optional[Dict[str, Any]] = None):
        self.event_type = event_type
        self.source = source
        self.data = data
