import curses, time
from core.model import TreeNode
from core.operations import toggle_node, toggle_subtree, collect_visible_files
from core.utils.clipboard import copy_files_subloop, copy_text_to_clipboard
from core.state import gather_state, save_state
from ui.core.state import UIState
from config.constants import STATE_FILE

def handle_regular_key(key: int, node: TreeNode, ui_state: UIState, tree_changed_flag: any) -> None:
    if key in (ord('e'), ord('E')) and node.is_dir:
        toggle_node(node)
        node.calculate_token_count()
        if node.parent:
            node.parent.calculate_token_count()
        tree_changed_flag.set()
    elif key in (ord('d'), ord('D')) and not node.is_dir:
        previous_tokens = node.token_count if not node.disabled else 0
        node.disabled = not node.disabled
        node.update_render_name()
        new_tokens = node.token_count if not node.disabled else 0
        delta = new_tokens - previous_tokens
        if node.parent:
            node.parent.update_token_count(delta)
        tree_changed_flag.set()

def handle_shift_key(key: int, node: TreeNode, ui_state: UIState, tree_changed_flag: any) -> None:
    if node.is_dir and key == ord('E'):
        toggle_subtree(node)
        node.calculate_token_count()
        if node.parent:
            node.parent.calculate_token_count()
        tree_changed_flag.set()

def handle_copy_action(stdscr: any, node: TreeNode, fmt: str, path_mode: str, ui_state: UIState) -> None:
    files_to_copy = collect_visible_files(node, path_mode)
    if files_to_copy:
        copied_text = copy_files_subloop(stdscr, files_to_copy, fmt)
        copy_text_to_clipboard(copied_text)
        ui_state.copying_success = True
        ui_state.success_message_time = time.time()

def handle_enter_key(node: TreeNode, tree_changed_flag: any) -> None:
    if node.is_dir:
        toggle_node(node)
        node.calculate_token_count()
        if node.parent:
            node.parent.calculate_token_count()
        tree_changed_flag.set()

def handle_quit(root_node: TreeNode) -> bool:
    state = {}
    gather_state(root_node, state, base_path=root_node.path, is_root=True)
    save_state(STATE_FILE, state)
    return True