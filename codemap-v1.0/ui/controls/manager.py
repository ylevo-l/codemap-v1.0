import time, curses
from typing import Dict, Callable, Optional, List
from ui.controls.events import Event, EventType
from ui.core.state import State

class ControlManager:
    def __init__(self, ui_state: State):
        self.ui_state = ui_state
        self.event_handlers: Dict[EventType, Callable[[Event], bool]] = {}
        nav_throttle = 0.0
        self.throttle_intervals: Dict[EventType, float] = {
            EventType.NAVIGATION_UP: nav_throttle,
            EventType.NAVIGATION_DOWN: nav_throttle,
            EventType.TOGGLE_NODE: 0.02,
            EventType.TOGGLE_SUBTREE: 0.05,
            EventType.TOGGLE_DISABLE: 0.02,
            EventType.COPY_CONTENT: 0.1,
            EventType.REFACTOR_CONTENT: 0.1,
            EventType.SAVE_CONTENT: 0.1,
            EventType.LOAD_CONTENT: 0.1,
            EventType.QUIT: 0.0,
            EventType.ENTER_KEY: 0.02,
            EventType.SHIFT_MODE_CHANGED: 0.0,
            EventType.SHIFT_DISABLE_ALL: 0.1,
        }
        self.last_event_times: Dict[EventType, float] = {}
        self.event_priorities: Dict[EventType, int] = {
            EventType.QUIT: 100,
            EventType.SHIFT_MODE_CHANGED: 90,
            EventType.NAVIGATION_UP: 80,
            EventType.NAVIGATION_DOWN: 80,
            EventType.ENTER_KEY: 70,
            EventType.TOGGLE_NODE: 60,
            EventType.TOGGLE_SUBTREE: 50,
            EventType.TOGGLE_DISABLE: 40,
            EventType.COPY_CONTENT: 30,
            EventType.REFACTOR_CONTENT: 30,
            EventType.SAVE_CONTENT: 30,
            EventType.LOAD_CONTENT: 30,
            EventType.SHIFT_DISABLE_ALL: 20,
        }
        self._key_event_cache: Dict[int, Event] = {}
        self._cache_expire = 60.0
        self._last_cache_flush = time.time()
        self.event_queue: List[Event] = []

    def register_handler(self, event_type: EventType, handler: Callable[[Event], bool]):
        self.event_handlers[event_type] = handler
        self._key_event_cache.clear()

    def _is_throttled(self, event_type: EventType) -> bool:
        interval = self.throttle_intervals.get(event_type, 0.0)
        if interval == 0.0:
            return False
        now = time.time()
        last = self.last_event_times.get(event_type, 0.0)
        if now - last < interval:
            return True
        self.last_event_times[event_type] = now
        return False

    def handle_event(self, event: Event) -> bool:
        if event.event_type not in self.event_handlers:
            return False
        if self._is_throttled(event.event_type):
            return False
        try:
            return self.event_handlers[event.event_type](event)
        except:
            return False

    def _flush_cache_if_needed(self):
        now = time.time()
        if now - self._last_cache_flush > self._cache_expire:
            self._key_event_cache.clear()
            self._last_cache_flush = now

    def get_event_from_key(self, key: int) -> Optional[Event]:
        self._flush_cache_if_needed()
        if key in self._key_event_cache:
            evt = self._key_event_cache[key]
            if evt.event_type in (EventType.NAVIGATION_UP, EventType.NAVIGATION_DOWN):
                evt.data = {"shift": self.ui_state.physical_shift_pressed}
            return evt
        shift = self.ui_state.physical_shift_pressed
        mapping = {
            ord("w"): Event(EventType.NAVIGATION_UP, "keyboard", {"shift": shift}),
            ord("W"): Event(EventType.NAVIGATION_UP, "keyboard", {"shift": shift}),
            curses.KEY_UP: Event(EventType.NAVIGATION_UP, "keyboard", {"shift": shift}),
            ord("s"): Event(EventType.NAVIGATION_DOWN, "keyboard", {"shift": shift}),
            ord("S"): Event(EventType.NAVIGATION_DOWN, "keyboard", {"shift": shift}),
            curses.KEY_DOWN: Event(EventType.NAVIGATION_DOWN, "keyboard", {"shift": shift}),
            curses.KEY_ENTER: Event(EventType.ENTER_KEY, "keyboard"),
            10: Event(EventType.ENTER_KEY, "keyboard"),
            13: Event(EventType.ENTER_KEY, "keyboard"),
            ord("c"): Event(EventType.COPY_CONTENT, "keyboard"),
            ord("C"): Event(EventType.COPY_CONTENT, "keyboard"),
            ord("b"): Event(EventType.SAVE_CONTENT, "keyboard"),
            ord("B"): Event(EventType.SAVE_CONTENT, "keyboard"),
            ord("v"): Event(EventType.LOAD_CONTENT, "keyboard"),
            ord("V"): Event(EventType.LOAD_CONTENT, "keyboard"),
            ord("q"): Event(EventType.QUIT, "keyboard"),
            ord("Q"): Event(EventType.QUIT, "keyboard"),
            ord("e"): Event(EventType.TOGGLE_NODE, "keyboard") if not shift else Event(EventType.TOGGLE_SUBTREE, "keyboard"),
            ord("E"): Event(EventType.TOGGLE_NODE, "keyboard") if not shift else Event(EventType.TOGGLE_SUBTREE, "keyboard"),
            ord("d"): Event(EventType.TOGGLE_DISABLE, "keyboard") if not shift else Event(EventType.SHIFT_DISABLE_ALL, "keyboard"),
            ord("D"): Event(EventType.TOGGLE_DISABLE, "keyboard") if not shift else Event(EventType.SHIFT_DISABLE_ALL, "keyboard"),
            ord("r"): Event(EventType.REFACTOR_CONTENT, "keyboard", {"shift": shift}),
            ord("R"): Event(EventType.REFACTOR_CONTENT, "keyboard", {"shift": shift}),
        }
        if hasattr(curses, "KEY_SR"):
            mapping[getattr(curses, "KEY_SR")] = Event(EventType.NAVIGATION_UP, "keyboard", {"shift": True})
        if hasattr(curses, "KEY_SF"):
            mapping[getattr(curses, "KEY_SF")] = Event(EventType.NAVIGATION_DOWN, "keyboard", {"shift": True})
        if key in mapping:
            self._key_event_cache[key] = mapping[key]
            return mapping[key]
        return None

    def queue_event(self, event: Event):
        self.event_queue.append(event)

    def process_queued_events(self) -> bool:
        if not self.event_queue:
            return False
        self.event_queue.sort(key=lambda e: self.event_priorities.get(e.event_type, 0), reverse=True)
        processed = False
        while self.event_queue:
            if self.handle_event(self.event_queue.pop(0)):
                processed = True
        return processed
