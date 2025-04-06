from ui.controls.actions import ActionHandler

# Re-export legacy functions for backward compatibility
# These are empty implementations that will be deprecated in future versions
def handle_regular_key(*args, **kwargs):
    pass

def handle_shift_key(*args, **kwargs):
    pass

def handle_copy_action(*args, **kwargs):
    pass

def handle_enter_key(*args, **kwargs):
    pass

def handle_quit(*args, **kwargs):
    pass

__all__ = [
    'handle_regular_key', 'handle_shift_key', 'handle_copy_action',
    'handle_enter_key', 'handle_quit', 'ActionHandler'
]