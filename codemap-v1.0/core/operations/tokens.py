import os, threading, concurrent.futures, time
from functools import lru_cache
from typing import Callable, Dict

from config.constants import count_tokens
from core.utils.debug import log

_MAX_CACHE       = 100_000

_FAST_THRESHOLD  = 200_000

_APPROX_DIVISOR  = 4

_MAX_WORKERS_CAP = 8

class TokenCountManager:
    def __init__(self, max_workers: int | None = None):
        self._max = max(2, min(_MAX_WORKERS_CAP, (os.cpu_count() or 4) // 2)) if max_workers is None else max_workers
        self._pool: concurrent.futures.ThreadPoolExecutor | None = None
        self._cache: Dict[str, Dict[str, int | float]] = {}
        self._lock = threading.Lock()
        self._started = False
    @property
    def is_running(self) -> bool:
        return self._started

    def _create_pool(self):
        if self._pool is None:
            self._pool = concurrent.futures.ThreadPoolExecutor(
                self._max, thread_name_prefix="tok"
            )

    def start(self):
        with self._lock:
            if self._started:
                return
            self._create_pool()
            self._started = True
            log("TokenCountManager started")

    def stop(self):
        with self._lock:
            if self._pool:
                self._pool.shutdown(wait=False)
                self._pool = None
            self._started = False
            log("TokenCountManager stopped")
    @lru_cache(65536)
    def _should_read(self, path: str, mtime: float, force: bool) -> bool:
        return force or path not in self._cache or mtime > self._cache[path]["mtime"]

    def _trim_cache(self):
        if len(self._cache) <= _MAX_CACHE:
            return
        for k in list(self._cache.keys())[: len(self._cache) - _MAX_CACHE]:
            self._cache.pop(k, None)

    def trim_cache(self):
        with self._lock:
            self._trim_cache()

    def _estimate_tokens(self, size: int) -> int:
        return max(1, size // _APPROX_DIVISOR)

    def _process(self, path: str, cb: Callable[[str, int], None], force: bool):
        try:
            st = os.stat(path)
            mtime = st.st_mtime
            if not self._should_read(path, mtime, force):
                cb(path, self._cache[path]["count"])
                return
            size = st.st_size
            if size > _FAST_THRESHOLD:
                cnt = self._estimate_tokens(size)
            else:
                with open(path, "r", encoding="utf-8", errors="ignore", newline="") as f:
                    cnt = count_tokens(f.read())
            with self._lock:
                self._cache[path] = {"count": cnt, "mtime": mtime}
                self._trim_cache()
            cb(path, cnt)
        except FileNotFoundError:
            with self._lock:
                self._cache.pop(path, None)
            cb(path, 0)
        except Exception as e:
            log("TOKEN_READ_FAIL", path, e, level=40)
            cb(path, 0)

    def queue_token_count(self, path: str, cb: Callable[[str, int], None], force_update: bool = False):
        if not self._started:
            self.start()
        if self._pool:
            self._pool.submit(self._process, path, cb, force_update)

token_count_manager = TokenCountManager()

def update_node_token_count(node, new: int) -> bool:
    if node.is_dir or node.token_count == new:
        return False
    delta = new - node.token_count
    if delta == 0:
        return False
    node.token_count = new
    if node.disabled:
        return True
    p = node.parent
    while p and p.expanded:
        p.token_count += delta
        p = p.parent
    return True
