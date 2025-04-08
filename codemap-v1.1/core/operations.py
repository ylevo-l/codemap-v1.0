import os
import time
import threading
import queue
from typing import Generator, Tuple, List, Dict, Set, Optional, Callable

from core.model import TreeNode
from config.constants import count_tokens

def toggle_node(node: TreeNode) -> None:

    if node.is_dir:
        node.expanded = not node.expanded
        node.update_render_name()

def set_subtree_expanded(node: TreeNode, expanded: bool) -> None:

    if node.is_dir:
        node.expanded = expanded
        node.update_render_name()

        for child in node.children:
            set_subtree_expanded(child, expanded)

def toggle_subtree(node: TreeNode) -> None:

    if node.is_dir:
        set_subtree_expanded(node, not node.expanded)

def flatten_tree(node: TreeNode, depth: int = 0, ancestor_has_tokens: bool = False,
                visited: Optional[Set[str]] = None) -> Generator[Tuple[TreeNode, int, bool], None, None]:

    if visited is None:
        visited = set()

    if node.path in visited:
        return

    visited.add(node.path)

    show_tokens = False
    if not ancestor_has_tokens and node.token_count > 0 and node.is_dir:
        show_tokens = True
        ancestor_has_tokens = True

    yield (node, depth, show_tokens)

    if node.is_dir and node.expanded:
        for child in node.children:
            yield from flatten_tree(child, depth + 1, ancestor_has_tokens, visited)

class TokenCountManager:

    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue = queue.Queue()
        self.active_tasks = set()
        self.workers = []
        self.is_running = False
        self.lock = threading.Lock()

    def start(self):

        if self.is_running:
            return

        self.is_running = True
        for _ in range(self.max_workers):
            worker = threading.Thread(target=self._worker_loop, daemon=True)
            worker.start()
            self.workers.append(worker)

    def stop(self):

        self.is_running = False
        for _ in range(len(self.workers)):
            self.queue.put(None)

        for worker in self.workers:
            worker.join(timeout=0.5)

        self.workers = []

    def _worker_loop(self):

        while self.is_running:
            try:
                task = self.queue.get(timeout=0.5)
                if task is None or not self.is_running:
                    break

                node_path, callback = task
                with self.lock:
                    if node_path in self.active_tasks:
                        self.queue.task_done()
                        continue
                    self.active_tasks.add(node_path)

                try:

                    with open(node_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    token_count = count_tokens(content)

                    if callback:
                        callback(node_path, token_count)
                except Exception as e:

                    if callback:
                        callback(node_path, 0)

                with self.lock:
                    self.active_tasks.discard(node_path)

                self.queue.task_done()
            except queue.Empty:

                continue
            except Exception:

                try:
                    self.queue.task_done()
                except:
                    pass

    def queue_token_count(self, node_path: str, callback: Callable[[str, int], None]) -> None:

        if not self.is_running:
            self.start()

        self.queue.put((node_path, callback))

token_count_manager = TokenCountManager()

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

def update_node_token_count(node: TreeNode, new_count: int) -> None:

    if node.is_dir:
        return

    delta = 0
    if not node.disabled:
        delta = new_count - node.token_count

    node.token_count = new_count

    if delta != 0 and node.parent:
        node.parent.update_token_count(delta)

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

        while True:
            current_time = time.time()

            if current_time - last_check_time >= 5.0:
                last_check_time = current_time

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

                for node in nodes_to_process:
                    token_count_manager.queue_token_count(node.path, token_count_callback)

            time.sleep(0.1)
    except:

        token_count_manager.stop()