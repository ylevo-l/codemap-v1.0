import os, threading
from typing import List, Tuple, Dict, Set

from core.model.tree_node import TreeNode
from core.operations.tokens import token_count_manager, update_node_token_count

def collect_visible_files(node: TreeNode, path_mode: str) -> List[Tuple[str, str]]:
    files = []; visited: Set[str] = set()
    def recurse(nd: TreeNode, path_parts: List[str]):
        if nd.path in visited: return
        visited.add(nd.path)
        if path_mode == "relative":
            current_display_path = os.path.join(*(path_parts + [nd.display_name]))
        else:
            current_display_path = nd.display_name
        if nd.is_dir:
            if nd.expanded:
                for child in nd.children:
                    recurse(child, path_parts + [nd.display_name])
        elif not nd.disabled:
            try:
                if os.path.exists(nd.path):
                    with open(nd.path, "r", encoding="utf-8", errors='ignore') as f:
                        content = f.read()
                else:
                    content = "<File not found>"
            except Exception as e:
                content = f"<Could not read file: {e}>"
            files.append((current_display_path, content))
    recurse(node, [])
    return files

def calculate_token_counts(
    root: TreeNode, path_to_node: Dict[str, TreeNode],
    tree_changed_flag: threading.Event, lock: threading.Lock

) -> None:

    if not token_count_manager.is_running:
        token_count_manager.start()
    def token_count_callback(node_path: str, token_count: int) -> None:
        node_updated = False
        with lock:
            node = path_to_node.get(node_path)
            if node and not node.is_dir:
                changed = update_node_token_count(node, token_count)
                if changed: node_updated = True
        if node_updated: tree_changed_flag.set()
    def _schedule(paths: List[str]) -> None:
        for p in paths:
            token_count_manager.queue_token_count(p, token_count_callback, force_update=False)
    visible: List[str] = []
    with lock:
        for n in path_to_node.values():
            if not n.is_dir and not n.disabled and (n.parent is None or n.parent.expanded):
                visible.append(n.path)
    _schedule(visible)
    def _background():
        remaining = []
        with lock:
            for n in path_to_node.values():
                if n.path not in visible and not n.is_dir and not n.disabled:
                    remaining.append(n.path)
        _schedule(remaining)
    threading.Thread(target=_background, daemon=True, name="tok_lazy").start()
