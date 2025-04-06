import curses
from typing import Optional

from ui.controls.events import Event, EventType
from ui.controls.keyboard import ControlManager


class KeyboardInput:
    """
    Processes keyboard input and maps keys to appropriate events.
    
    This component is responsible for handling all keyboard input,
    ensuring consistent behavior across the application.
    """
    
    def __init__(self, control_manager: ControlManager):
        """
        Initialize the keyboard input handler.
        
        Args:
            control_manager: The control manager to send events to
        """
        self.control_manager = control_manager
        
    def process_key(self, key: int) -> bool:
        """
        Process a key press and map it to an event.
        
        Args:
            key: The key code from curses
            
        Returns:
            True if the key was handled, False otherwise
        """
        if key == -1:  # No key pressed
            return False
            
        # Get the event corresponding to the key
        event = self.control_manager.get_event_from_key(key)
            
        # If we have an event, process it through the control manager
        if event:
            return self.control_manager.handle_event(event)
            
        return False