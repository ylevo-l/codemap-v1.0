import curses
from typing import Dict, Callable, Optional, Set, List
import time

from ui.controls.events import Event, EventType
from ui.core.state import UIState

class ControlManager:
    def __init__(self, ui_state: UIState):
        self.ui_state = ui_state
        self.event_handlers: Dict[EventType, Callable[[Event], bool]] = {}

        self.last_event_times: Dict[EventType, float] = {}
        self.throttle_intervals: Dict[EventType, float] = {

            EventType.NAVIGATION_UP: 0.01,
            EventType.NAVIGATION_DOWN: 0.01,

            EventType.TOGGLE_NODE: 0.05,
            EventType.TOGGLE_SUBTREE: 0.1,
            EventType.TOGGLE_DISABLE: 0.05,

            EventType.COPY_CONTENT: 0.2,
            EventType.REFACTOR_CONTENT: 0.2,

            EventType.QUIT: 0.0,
            EventType.ENTER_KEY: 0.05,
            EventType.SHIFT_MODE_CHANGED: 0.05
        }

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
            EventType.REFACTOR_CONTENT: 30
        }

        self._key_event_map: Dict[int, Event] = {}
        self._last_key_map_update = 0

        self.event_queue: List[Event] = []

    def register_handler(self, event_type: EventType, handler: Callable[[Event], bool]):
        self.event_handlers[event_type] = handler

        self._key_event_map.clear()

    def handle_event(self, event: Event) -> bool:
        if not event or event.event_type not in self.event_handlers:
            return False

        now = time.time()
        throttle_interval = self.throttle_intervals.get(event.event_type, 0.0)
        last_time = self.last_event_times.get(event.event_type, 0.0)

        if throttle_interval > 0 and now - last_time < throttle_interval:

            return False

        self.last_event_times[event.event_type] = now

        try:
            return self.event_handlers[event.event_type](event)
        except Exception:

            return False

    def get_event_from_key(self, key: int) -> Optional[Event]:
        now = time.time()

        if key in self._key_event_map:
            cached_event = self._key_event_map[key]

            if cached_event.event_type in {EventType.NAVIGATION_UP, EventType.NAVIGATION_DOWN}:
                cached_event.data = {"shift": self.ui_state.physical_shift_pressed}

            return cached_event

        if now - self._last_key_map_update > 60.0:
            self._key_event_map.clear()
            self._last_key_map_update = now

        if key in (ord("w"), ord("W"), curses.KEY_UP):
            event = Event(EventType.NAVIGATION_UP, source="keyboard",
                         data={"shift": self.ui_state.physical_shift_pressed})
            self._key_event_map[key] = event
            return event

        if key in (ord("s"), ord("S"), curses.KEY_DOWN):
            event = Event(EventType.NAVIGATION_DOWN, source="keyboard",
                         data={"shift": self.ui_state.physical_shift_pressed})
            self._key_event_map[key] = event
            return event

        if self.ui_state.physical_shift_pressed and key == ord("E"):
            event = Event(EventType.TOGGLE_SUBTREE, source="keyboard")

            return event

        if self.ui_state.physical_shift_pressed and key == ord("R"):
            event = Event(EventType.REFACTOR_CONTENT, source="keyboard",
                         data={"shift": True})

            return event

        if key in (curses.KEY_ENTER, 10, 13):
            event = Event(EventType.ENTER_KEY, source="keyboard")
            self._key_event_map[key] = event
            return event

        if key in (ord("c"), ord("C")):
            event = Event(EventType.COPY_CONTENT, source="keyboard")
            self._key_event_map[key] = event
            return event

        if key in (ord("q"), ord("Q")):
            event = Event(EventType.QUIT, source="keyboard")
            self._key_event_map[key] = event
            return event

        if key in (ord("e"), ord("E")):
            if not self.ui_state.physical_shift_pressed:
                event = Event(EventType.TOGGLE_NODE, source="keyboard")

                return event

        if key in (ord("d"), ord("D")):
            event = Event(EventType.TOGGLE_DISABLE, source="keyboard")
            self._key_event_map[key] = event
            return event

        if key in (ord("r"), ord("R")):
            if not self.ui_state.physical_shift_pressed:
                event = Event(EventType.REFACTOR_CONTENT, source="keyboard",
                             data={"shift": False})

                return event

        return None

    def queue_event(self, event: Event) -> None:
        self.event_queue.append(event)

    def process_queued_events(self) -> bool:
        if not self.event_queue:
            return False

        self.event_queue.sort(
            key=lambda e: self.event_priorities.get(e.event_type, 0),
            reverse=True
        )

        processed = False
        while self.event_queue:
            event = self.event_queue.pop(0)
            if self.handle_event(event):
                processed = True

        return processed