import os
import threading
import queue
from typing import Callable, Dict
from core.model.tree_node import TreeNode
from config.constants import count_tokens

class TokenCountManager:
    def __init__(self, max_workers: int = 4):
        self.max_workers = max_workers
        self.queue = queue.Queue()
        self.active_tasks = set()
        self.workers = []
        self.is_running = False
        self.lock = threading.Lock()
        self.file_tokens: Dict[str, Dict[str, int]] = {}

    def start(self):
        if self.is_running:
            return
        self.is_running = True
        for _ in range(self.max_workers):
            t = threading.Thread(target=self._worker, daemon=True)
            t.start()
            self.workers.append(t)

    def stop(self):
        self.is_running = False
        for _ in self.workers:
            self.queue.put(None)
        for t in self.workers:
            t.join(timeout=0.5)
        self.workers.clear()

    def _worker(self):
        while self.is_running:
            task = None
            try:
                task = self.queue.get(timeout=0.5)
            except queue.Empty:
                continue
            if task is None:
                break
            path, cb, force_update = task
            with self.lock:
                if path in self.active_tasks:
                    self.queue.task_done()
                    continue
                self.active_tasks.add(path)
            try:
                mtime = os.path.getmtime(path)
                cached = self.file_tokens.get(path)
                if cached and mtime <= cached["mtime"] and not force_update:
                    count = cached["count"]
                else:
                    with open(path, "r", encoding="utf-8") as f:
                        count = count_tokens(f.read())
                    self.file_tokens[path] = {"count": count, "mtime": mtime}
                if cb:
                    cb(path, count)
            except:
                if cb:
                    cb(path, 0)
            finally:
                with self.lock:
                    self.active_tasks.discard(path)
                self.queue.task_done()

    def queue_token_count(self, path: str, cb: Callable[[str, int], None], force_update: bool = False):
        if not self.is_running:
            self.start()
        if not force_update and path in self.file_tokens:
            if cb:
                cb(path, self.file_tokens[path]["count"])
            return
        self.queue.put((path, cb, force_update))

token_count_manager = TokenCountManager()

def update_node_token_count(node: TreeNode, new_count: int) -> None:
    if node.is_dir:
        return
    delta = new_count - node.token_count
    if delta == 0:
        return
    node.token_count = new_count
    parent = node.parent
    while parent and parent.expanded:
        parent.update_token_count(delta)
        parent = parent.parent
