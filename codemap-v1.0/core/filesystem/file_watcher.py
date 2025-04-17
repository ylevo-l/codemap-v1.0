import os
import threading
from typing import Dict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from core.model.tree_node import TreeNode
from core.operations.tokens import update_node_token_count, token_count_manager
from core.filesystem.file_filter import FileFilter

class _WatchdogHandler(FileSystemEventHandler):
    def __init__(
        self,
        root_path: str,
        file_filter: FileFilter,
        path_to_node: Dict[str, TreeNode],
        tree_changed_flag: threading.Event,
        lock: threading.Lock,
    ) -> None:
        super().__init__()
        self.root_path = root_path
        self.file_filter = file_filter
        self.path_to_node = path_to_node
        self.tree_changed_flag = tree_changed_flag
        self.lock = lock

    def _add_file(self, path: str, is_dir: bool) -> None:
        parent_path = os.path.dirname(path)
        with self.lock:
            parent = self.path_to_node.get(parent_path)
            if not parent or not parent.is_dir:
                return
            node = TreeNode(path, is_dir, parent)
            parent.add_child(node)
            parent.sort_children()
            self.path_to_node[path] = node
        if not is_dir:
            token_count_manager.queue_token_count(path, self._token_cb)

    def _remove_file(self, path: str) -> None:
        with self.lock:
            node = self.path_to_node.pop(path, None)
            if not node:
                return
            if node.parent:
                try:
                    node.parent.children.remove(node)
                except ValueError:
                    pass
                if not node.is_dir and not node.disabled:
                    node.parent.update_token_count(-node.token_count)
        self.tree_changed_flag.set()

    def _token_cb(self, node_path: str, count: int) -> None:
        with self.lock:
            node = self.path_to_node.get(node_path)
            if not node or node.is_dir or node.disabled:
                return
            update_node_token_count(node, count)
            self.tree_changed_flag.set()

    def on_created(self, event: FileSystemEvent):
        if self.file_filter.is_ignored(os.path.basename(event.src_path)):
            return
        self._add_file(event.src_path, event.is_directory)
        self.tree_changed_flag.set()

    def on_deleted(self, event: FileSystemEvent):
        self._remove_file(event.src_path)

    def on_modified(self, event: FileSystemEvent):
        if event.is_directory:
            return
        if self.file_filter.is_ignored(os.path.basename(event.src_path)):
            return
        token_count_manager.queue_token_count(event.src_path, self._token_cb, force_update=True)

    def on_moved(self, event: FileSystemEvent):
        self._remove_file(event.src_path)
        if not self.file_filter.is_ignored(os.path.basename(event.dest_path)):
            self._add_file(event.dest_path, event.is_directory)
        self.tree_changed_flag.set()

def watch_filesystem(
    root_path: str,
    file_filter: FileFilter,
    path_to_node: Dict[str, TreeNode],
    tree_changed_flag: threading.Event,
    stop_event: threading.Event,
    lock: threading.Lock,

) -> None:
    handler = _WatchdogHandler(root_path, file_filter, path_to_node, tree_changed_flag, lock)
    observer = Observer()
    observer.schedule(handler, root_path, recursive=True)
    observer.start()
    try:
        stop_event.wait()
    finally:
        observer.stop()
        observer.join()
