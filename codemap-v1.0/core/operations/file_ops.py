import os
import time
import threading
from typing import List, Tuple, Dict
from core.model.tree_node import TreeNode
from core.operations.tokens import token_count_manager, update_node_token_count

def collect_visible_files(node: TreeNode, path_mode: str) -> List[Tuple[str, str]]:
    files = []
    visited = set()
    def recurse(nd: TreeNode, path: List[str]):
        if nd.path in visited:
            return
        visited.add(nd.path)
        current_path = path + [nd.display_name]
        if nd.is_dir and nd.expanded:
            for child in nd.children:
                recurse(child, current_path)
        elif not nd.is_dir and not nd.disabled:
            if path_mode == "relative":
                display_path = os.path.join(*current_path)
            else:
                display_path = nd.display_name
            try:
                with open(nd.path, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                content = "<Could not read file>"
            files.append((display_path, content))
    recurse(node, [])
    return files

def calculate_token_counts(root: TreeNode, path_to_node: Dict[str, TreeNode],
                          tree_changed_flag: threading.Event, lock: threading.Lock) -> None:
    token_count_manager.start()
    def token_count_callback(node_path: str, token_count: int) -> None:
        with lock:
            node = path_to_node.get(node_path)
            if node and not node.is_dir:
                previous_count = node.token_count
                update_node_token_count(node, token_count)
                if previous_count != token_count and not node.disabled:
                    tree_changed_flag.set()
    try:
        batch_size = 10
        last_check_time = 0
        scanning_enabled = True
        scan_throttle_time = 1.0
        while True:
            current_time = time.time()
            if current_time - last_check_time >= scan_throttle_time:
                last_check_time = current_time
                scanning_enabled = True
            if scanning_enabled:
                nodes_to_process = []
                with lock:
                    for node in path_to_node.values():
                        if (not node.is_dir and
                            node.token_count == 0 and
                            not node.disabled and
                            node.path not in token_count_manager.active_tasks):
                            nodes_to_process.append(node)
                            if len(nodes_to_process) >= batch_size:
                                break
                if nodes_to_process:
                    for node in nodes_to_process:
                        token_count_manager.queue_token_count(node.path, token_count_callback, force_update=False)
                    scanning_enabled = False
            time.sleep(0.1)
    except:
        token_count_manager.stop()
