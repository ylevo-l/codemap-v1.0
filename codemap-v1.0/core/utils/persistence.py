import os, shutil, hashlib, tempfile
from core.utils.caching import LRUCache
from config.constants import SNAPSHOT_DIR

class SnapshotManager:
    def __init__(self, base_dir: str):
        self._base_dir = base_dir
        os.makedirs(self._base_dir, exist_ok=True)
        self._exists_cache: LRUCache[str, bool] = LRUCache(2048)

    def _hash(self, path: str) -> str:
        return hashlib.sha1(os.path.abspath(path).encode()).hexdigest()

    def _snap_path(self, path: str) -> str:
        return os.path.join(self._base_dir, self._hash(path))

    def has_snapshot(self, path: str) -> bool:
        cached = self._exists_cache.get(path)
        if cached is not None:
            return cached
        exists = os.path.exists(self._snap_path(path))
        self._exists_cache.put(path, exists)
        return exists

    def save_snapshot(self, path: str) -> bool:
        target = self._snap_path(path)
        tmp = f"{target}.tmp"
        try:
            if os.path.exists(tmp):
                shutil.rmtree(tmp, ignore_errors=True)
            if os.path.isdir(path):
                shutil.copytree(path, tmp)
            else:
                os.makedirs(tmp, exist_ok=True)
                shutil.copy2(path, os.path.join(tmp, os.path.basename(path)))
            os.replace(tmp, target)
            self._exists_cache.put(path, True)
            return True
        except:
            shutil.rmtree(tmp, ignore_errors=True)
            return False

    def _restore_dir(self, src: str, dst: str):
        for root, _, files in os.walk(src):
            rel = os.path.relpath(root, src)
            dest = dst if rel == "." else os.path.join(dst, rel)
            os.makedirs(dest, exist_ok=True)
            for f in files:
                shutil.copy2(os.path.join(root, f), os.path.join(dest, f))

    def load_snapshot(self, path: str) -> bool:
        src = self._snap_path(path)
        if not os.path.exists(src):
            self._exists_cache.put(path, False)
            return False
        try:
            if os.path.isdir(path):
                self._restore_dir(src, path)
            else:
                shutil.copy2(os.path.join(src, os.path.basename(path)), path)
            return True
        except:
            return False

    def delete_snapshot(self, path: str) -> bool:
        try:
            shutil.rmtree(self._snap_path(path), ignore_errors=True)
            self._exists_cache.put(path, False)
            return True
        except:
            return False

snapshot_manager = SnapshotManager(SNAPSHOT_DIR)

def has_snapshot(path: str) -> bool:
    return snapshot_manager.has_snapshot(path)

def save_snapshot(path: str) -> bool:
    return snapshot_manager.save_snapshot(path)

def load_snapshot(path: str) -> bool:
    return snapshot_manager.load_snapshot(path)

def delete_snapshot(path: str) -> bool:
    return snapshot_manager.delete_snapshot(path)
