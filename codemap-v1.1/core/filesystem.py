import os
import time
import threading
from typing import Dict, List, Set, Optional, Deque
from collections import deque

from core.model import TreeNode
from core.operations import token_count_manager, update_node_token_count
from config.constants import count_tokens

class FileFilter:
    def __init__(self, ignored_patterns: List[str], allowed_extensions: List[str]):
        self.ignored_patterns = ignored_patterns
        self.allowed_extensions = allowed_extensions
        self._ignored_paths_cache: Dict[str, bool] = {}

    def is_ignored(self, name: str) -> bool:

        if name in self._ignored_paths_cache:
            return self._ignored_paths_cache[name]

        for pattern in self.ignored_patterns:
            if pattern in name:
                self._ignored_paths_cache[name] = True
                return True

        _, ext = os.path.splitext(name)
        result = bool(self.allowed_extensions and ext and ext.lower() not in self.allowed_extensions)

        self._ignored_paths_cache[name] = result
        return result

    def clear_cache(self):

        self._ignored_paths_cache.clear()

def build_tree(root_path: str, file_filter: FileFilter,
              path_to_node: Dict[str, TreeNode], lock: threading.Lock) -> TreeNode:

    root_node = TreeNode(root_path, True)
    root_node.expanded = True

    with lock:
        path_to_node[root_path] = root_node

    queue: Deque[TreeNode] = deque([root_node])
    processed_dirs: Set[str] = set([root_path])

    token_count_tasks = 0

    while queue:
        current_dir_node = queue.popleft()
        dir_path = current_dir_node.path

        try:

            contents = os.listdir(dir_path)

            dirs = []
            files = []

            for name in contents:
                if file_filter.is_ignored(name):
                    continue

                full_path = os.path.join(dir_path, name)

                if os.path.isdir(full_path):
                    dirs.append(name)
                else:
                    files.append(name)

            for dirname in sorted(dirs, key=str.lower):
                full_path = os.path.join(dir_path, dirname)

                if full_path in processed_dirs:
                    continue

                processed_dirs.add(full_path)

                with lock:
                    dir_node = TreeNode(full_path, True, current_dir_node)
                    current_dir_node.add_child(dir_node)
                    path_to_node[full_path] = dir_node

                queue.append(dir_node)

            for filename in sorted(files, key=str.lower):
                full_path = os.path.join(dir_path, filename)

                with lock:
                    file_node = TreeNode(full_path, False, current_dir_node)

                    def token_count_callback(node_path: str, token_count: int) -> None:
                        with lock:
                            node = path_to_node.get(node_path)
                            if node and not node.is_dir:
                                update_node_token_count(node, token_count)

                    if token_count_tasks < 50:
                        token_count_manager.queue_token_count(full_path, token_count_callback)
                        token_count_tasks += 1

                    current_dir_node.add_child(file_node)
                    path_to_node[full_path] = file_node

        except (PermissionError, FileNotFoundError, OSError):

            continue

    file_filter.clear_cache()

    root_node.calculate_token_count()
    return root_node

class FileSystemWatcher:

    def __init__(self, root_path: str, file_filter: FileFilter,
                path_to_node: Dict[str, TreeNode], tree_changed_flag: threading.Event,
                stop_event: threading.Event, lock: threading.Lock):
        self.root_path = root_path
        self.file_filter = file_filter
        self.path_to_node = path_to_node
        self.tree_changed_flag = tree_changed_flag
        self.stop_event = stop_event
        self.lock = lock

        self.previous_state: Dict[str, Optional[float]] = {}
        self.scan_queue: Deque[str] = deque()
        self.last_full_scan = 0
        self.last_dir_scan_time: Dict[str, float] = {}

        self.poll_interval = 2.0

        self.recently_modified_dirs: List[str] = []

    def _scan_directory(self, dir_path: str) -> Dict[str, Optional[float]]:

        result = {}

        try:
            for name in os.listdir(dir_path):
                if self.file_filter.is_ignored(name):
                    continue

                full_path = os.path.join(dir_path, name)

                if os.path.isdir(full_path):

                    if (full_path not in self.last_dir_scan_time or
                        time.time() - self.last_dir_scan_time.get(full_path, 0) > 10.0):
                        self.scan_queue.append(full_path)
                elif os.path.isfile(full_path):
                    try:
                        result[full_path] = os.path.getmtime(full_path)
                    except:
                        result[full_path] = None

            self.last_dir_scan_time[dir_path] = time.time()

        except (PermissionError, FileNotFoundError, OSError):
            pass

        return result

    def _handle_file_changes(self, current_state: Dict[str, Optional[float]]) -> None:

        with self.lock:
            existing_paths = set(self.previous_state.keys())
            current_paths = set(current_state.keys())

            added = current_paths - existing_paths
            removed = existing_paths - current_paths

            modified = set()
            for path in existing_paths & current_paths:
                if current_state[path] != self.previous_state[path]:
                    modified.add(path)

            if not (added or removed or modified):
                return

            for path in added:
                is_dir = os.path.isdir(path)
                parent_path = os.path.dirname(path)
                parent_node = self.path_to_node.get(parent_path)

                if parent_node and parent_node.is_dir:

                    if parent_path not in self.recently_modified_dirs:
                        self.recently_modified_dirs.append(parent_path)
                        if len(self.recently_modified_dirs) > 10:
                            self.recently_modified_dirs.pop(0)

                    new_node = TreeNode(path, is_dir, parent_node)

                    if not is_dir:

                        def token_count_callback(node_path: str, token_count: int) -> None:
                            with self.lock:
                                node = self.path_to_node.get(node_path)
                                if node and not node.is_dir and not node.disabled:
                                    update_node_token_count(node, token_count)
                                    parent = node.parent
                                    if parent:
                                        parent.update_token_count(node.token_count)
                                    self.tree_changed_flag.set()

                        token_count_manager.queue_token_count(path, token_count_callback)

                    parent_node.add_child(new_node)
                    parent_node.sort_children()
                    self.path_to_node[path] = new_node

            for path in removed:
                node = self.path_to_node.get(path)
                if node:
                    parent = node.parent
                    if parent:
                        parent_path = parent.path

                        if parent_path not in self.recently_modified_dirs:
                            self.recently_modified_dirs.append(parent_path)
                            if len(self.recently_modified_dirs) > 10:
                                self.recently_modified_dirs.pop(0)

                        parent.children.remove(node)

                        if not node.is_dir and not node.disabled:
                            parent.update_token_count(-node.token_count)

                    del self.path_to_node[path]

            for path in modified:
                node = self.path_to_node.get(path)
                if node and not node.is_dir and not node.disabled:

                    def token_count_callback(node_path: str, token_count: int) -> None:
                        with self.lock:
                            node = self.path_to_node.get(node_path)
                            if node and not node.is_dir and not node.disabled:
                                previous_count = node.token_count
                                delta = token_count - previous_count

                                if delta != 0:
                                    node.token_count = token_count

                                    if node.parent:
                                        node.parent.update_token_count(delta)

                                    self.tree_changed_flag.set()

                    token_count_manager.queue_token_count(path, token_count_callback)

            if added or removed or modified:
                self.tree_changed_flag.set()

    def watch(self) -> None:

        self.scan_queue.append(self.root_path)

        self.previous_state = {}

        while not self.stop_event.is_set():
            current_time = time.time()
            current_state = {}

            for dir_path in self.recently_modified_dirs:
                if os.path.isdir(dir_path) and dir_path not in self.scan_queue:
                    self.scan_queue.appendleft(dir_path)

            scanned_dirs = 0
            while self.scan_queue and scanned_dirs < 5:
                dir_path = self.scan_queue.popleft()

                if (dir_path != self.root_path and
                    dir_path not in self.recently_modified_dirs and
                    dir_path in self.last_dir_scan_time and
                    current_time - self.last_dir_scan_time[dir_path] < 10.0):
                    continue

                dir_state = self._scan_directory(dir_path)
                current_state.update(dir_state)
                scanned_dirs += 1

            if current_time - self.last_full_scan > 30.0:
                self.last_full_scan = current_time

                if self.root_path not in self.scan_queue:
                    self.scan_queue.append(self.root_path)

                old_time = current_time - 60.0
                self.last_dir_scan_time = {
                    k: v for k, v in self.last_dir_scan_time.items()
                    if v > old_time
                }

            self._handle_file_changes(current_state)

            self.previous_state = current_state

            time.sleep(self.poll_interval)

def scan_filesystem(root_path: str, file_filter: FileFilter,
                  path_to_node: Dict[str, TreeNode], tree_changed_flag: threading.Event,
                  stop_event: threading.Event, lock: threading.Lock) -> None:

    watcher = FileSystemWatcher(
        root_path, file_filter, path_to_node,
        tree_changed_flag, stop_event, lock
    )
    watcher.watch()