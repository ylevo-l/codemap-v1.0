import os, threading, time
from typing import List, Tuple, Dict, Set

from core.model.tree_node import TreeNode
from core.operations.tokens import token_count_manager, update_node_token_count

def collect_visible_files(node: TreeNode, path_mode: str) -> List[Tuple[str, str]]:
    files = []
    visited: Set[str] = set()
    def recurse(nd: TreeNode, parts: List[str]):
        if nd.path in visited:
            return
        visited.add(nd.path)
        display = os.path.join(*(parts + [nd.display_name])) if path_mode == "relative" else nd.display_name
        if nd.is_dir:
            if nd.expanded:
                for child in nd.children:
                    recurse(child, parts + [nd.display_name])
        elif not nd.disabled:
            try:
                if os.path.exists(nd.path):
                    with open(nd.path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                else:
                    content = "<File not found>"
            except Exception as e:
                content = f"<Could not read file: {e}>"
            files.append((display, content))
    recurse(node, [])
    return files

def calculate_token_counts(
    root: TreeNode, path_to_node: Dict[str, TreeNode],
    tree_changed_flag: threading.Event, lock: threading.Lock

) -> None:
    if not token_count_manager.is_running:
        token_count_manager.start()
    def token_cb(node_path: str, cnt: int):
        update = False
        with lock:
            n = path_to_node.get(node_path)
            if n and not n.is_dir:
                if update_node_token_count(n, cnt):
                    update = True
        if update:
            tree_changed_flag.set()
    def _schedule(paths: List[str]):
        for p in paths:
            token_count_manager.queue_token_count(p, token_cb, force_update=False)
    visible = []
    with lock:
        for n in path_to_node.values():
            if not n.is_dir and not n.disabled and (n.parent is None or n.parent.expanded):
                visible.append(n.path)
    _schedule(visible)
    def _later():
        time.sleep(3)
        remaining = []
        with lock:
            for n in path_to_node.values():
                if n.path not in visible and not n.is_dir and not n.disabled:
                    remaining.append(n.path)
        _schedule(remaining)
    threading.Thread(target=_later, daemon=True, name="tok_lazy").start()
