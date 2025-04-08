import os
from typing import Dict, List

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