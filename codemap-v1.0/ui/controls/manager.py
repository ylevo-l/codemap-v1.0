import time, curses
from typing import Dict, Callable, Optional
from config import CLI_REFRESH_INTERVAL
from ui.controls.events import Event, EventType
from ui.core.state import State

class ControlManager:
    def __init__(self, ui_state: State):
        self.ui_state = ui_state
        self.event_handlers: Dict[EventType, Callable[[Event], bool]] = {}
        base = CLI_REFRESH_INTERVAL
        self.throttle: Dict[EventType, float] = {
            EventType.COPY_CONTENT:     base * 4,
            EventType.PASTE_CONTENT:    base * 4,
            EventType.REFACTOR_CONTENT: base * 4,
            EventType.SAVE_CONTENT:     base * 4,
            EventType.LOAD_CONTENT:     base * 4,
        }
        self.last: Dict[EventType, float] = {}
        self._key_map = self._build_key_map()

    def _build_key_map(self) -> Dict[int, Event]:
        m: Dict[int, Event] = {}
        def add(k, e): m[k] = e
        nav_up   = [ord("w"), ord("W"), curses.KEY_UP]
        nav_down = [ord("s"), ord("S"), curses.KEY_DOWN]
        for k in nav_up:   add(k, Event(EventType.NAVIGATION_UP,   "keyboard"))
        for k in nav_down: add(k, Event(EventType.NAVIGATION_DOWN, "keyboard"))
        add(ord("c"), Event(EventType.COPY_CONTENT,  "keyboard"))
        add(ord("C"), Event(EventType.COPY_CONTENT,  "keyboard"))
        add(ord("p"), Event(EventType.PASTE_CONTENT, "keyboard"))
        add(ord("P"), Event(EventType.PASTE_CONTENT, "keyboard"))
        add(ord("b"), Event(EventType.SAVE_CONTENT,  "keyboard"))
        add(ord("B"), Event(EventType.SAVE_CONTENT,  "keyboard"))
        add(ord("v"), Event(EventType.LOAD_CONTENT,  "keyboard"))
        add(ord("V"), Event(EventType.LOAD_CONTENT,  "keyboard"))
        add(ord("q"), Event(EventType.QUIT,          "keyboard"))
        add(ord("Q"), Event(EventType.QUIT,          "keyboard"))
        add(ord("e"), Event(EventType.TOGGLE_NODE,   "keyboard"))
        add(ord("E"), Event(EventType.TOGGLE_NODE,   "keyboard"))
        add(ord("d"), Event(EventType.TOGGLE_DISABLE,"keyboard"))
        add(ord("D"), Event(EventType.TOGGLE_DISABLE,"keyboard"))
        add(ord("r"), Event(EventType.REFACTOR_CONTENT,"keyboard"))
        add(ord("R"), Event(EventType.REFACTOR_CONTENT,"keyboard"))
        add(ord('/'), Event(EventType.SEARCH,        "keyboard"))
        add(curses.KEY_ENTER, Event(EventType.ENTER_KEY, "keyboard"))
        add(10, Event(EventType.ENTER_KEY, "keyboard"))
        add(13, Event(EventType.ENTER_KEY, "keyboard"))
        if hasattr(curses, "KEY_SR"): add(getattr(curses, "KEY_SR"), Event(EventType.NAVIGATION_UP,   "keyboard"))
        if hasattr(curses, "KEY_SF"): add(getattr(curses, "KEY_SF"), Event(EventType.NAVIGATION_DOWN, "keyboard"))
        return m

    def register_handler(self, et: EventType, handler: Callable[[Event], bool]):
        self.event_handlers[et] = handler

    def _throttled(self, et: EventType) -> bool:
        interval = self.throttle.get(et)
        if interval is None or interval == 0.0:
            return False
        now = time.perf_counter()
        last = self.last.get(et, 0.0)
        if now - last < interval:
            return True
        self.last[et] = now
        return False

    def handle_event(self, e: Event) -> bool:
        handler = self.event_handlers.get(e.event_type)
        if handler is None:
            return False
        if self._throttled(e.event_type):
            return False
        try:
            return handler(e)
        except:
            return False

    def get_event_from_key(self, k: int) -> Optional[Event]:
        base_event = self._key_map.get(k)
        if base_event is None:
            return None
        shift = self.ui_state.physical_shift_pressed
        if base_event.event_type in (EventType.NAVIGATION_UP, EventType.NAVIGATION_DOWN):
            return Event(base_event.event_type, "keyboard", {"shift": shift})
        if base_event.event_type == EventType.TOGGLE_NODE:
            return Event(EventType.TOGGLE_SUBTREE if shift else EventType.TOGGLE_NODE, "keyboard")
        if base_event.event_type == EventType.TOGGLE_DISABLE:
            return Event(EventType.SHIFT_DISABLE_ALL if shift else EventType.TOGGLE_DISABLE, "keyboard")
        if base_event.event_type == EventType.REFACTOR_CONTENT:
            return Event(EventType.REFACTOR_CONTENT, "keyboard", {"shift": shift})
        return base_event
