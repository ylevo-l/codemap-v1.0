import curses

def safe_addnstr(stdscr, y, x, text, color, attr=0):
    try:
        max_y, max_x = stdscr.getmaxyx()
        if y < 0 or y >= max_y or x < 0 or x >= max_x:
            return
        max_chars = max_x - x - 1
        if max_chars <= 0:
            return
        display_text = text[:max_chars] if len(text) > max_chars else text
        stdscr.addstr(y, x, display_text, curses.color_pair(color) | attr)
    except:
        pass

def clear_line(stdscr, y, x):
    try:
        max_y, max_x = stdscr.getmaxyx()
        if 0 <= y < max_y and 0 <= x < max_x:
            stdscr.move(y, x)
            stdscr.clrtoeol()
    except:
        try:
            max_y, max_x = stdscr.getmaxyx()
            if 0 <= y < max_y and 0 <= x < max_x:
                space_str = " " * (max_x - x)
                stdscr.addstr(y, x, space_str[:max_x - x - 1])
        except:
            pass
