"""
Color management for terminal UI.

Initializes color pairs for curses.
"""

import curses


def init_colors():
    """
    Initialize color pairs for curses.
    
    Sets up standard color pairs used throughout the application.
    """
    curses.start_color()
    curses.use_default_colors()
    
    # Define color pairs
    curses.init_pair(1, curses.COLOR_CYAN, -1)        # Files
    curses.init_pair(2, curses.COLOR_GREEN, -1)       # Directories
    curses.init_pair(3, curses.COLOR_RED, -1)         # Disabled files
    curses.init_pair(4, curses.COLOR_YELLOW, -1)      # Highlighted items
    curses.init_pair(5, curses.COLOR_YELLOW, -1)      # Token counts
    curses.init_pair(6, curses.COLOR_WHITE, curses.COLOR_BLUE)  # Selected items
    curses.init_pair(7, curses.COLOR_WHITE, -1)       # Status text