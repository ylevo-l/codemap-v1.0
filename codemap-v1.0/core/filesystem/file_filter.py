import os
import fnmatch
from typing import Dict, List, Optional, Set
from collections import OrderedDict

class FileFilter:
    MAX_IGNORED_PATHS_CACHE_SIZE = 10000
    MAX_EXTENSION_CACHE_SIZE = 1000

    def __init__(self, ignored_patterns: List[str], allowed_extensions: List[str]):
        self.ignored_patterns = ignored_patterns
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions] if allowed_extensions else []
        self._ignored_paths_cache = OrderedDict()
        self._extension_cache = OrderedDict()
        self._compiled_patterns = [(pattern, self._compile_pattern(pattern)) for pattern in ignored_patterns]

    def _compile_pattern(self, pattern: str):
        if '*' not in pattern and '?' not in pattern and '[' not in pattern:
            return None
        return pattern

    def _manage_cache_size(self) -> None:
        while len(self._ignored_paths_cache) > self.MAX_IGNORED_PATHS_CACHE_SIZE:
            self._ignored_paths_cache.popitem(last=False)
        while len(self._extension_cache) > self.MAX_EXTENSION_CACHE_SIZE:
            self._extension_cache.popitem(last=False)

    def is_ignored(self, name: str) -> bool:
        if name in self._ignored_paths_cache:
            result = self._ignored_paths_cache.pop(name)
            self._ignored_paths_cache[name] = result
            return result
        for pattern, compiled in self._compiled_patterns:
            if compiled is None:
                if pattern in name:
                    self._ignored_paths_cache[name] = True
                    self._manage_cache_size()
                    return True
            elif fnmatch.fnmatch(name, pattern):
                self._ignored_paths_cache[name] = True
                self._manage_cache_size()
                return True
        _, ext = os.path.splitext(name)
        if ext:
            ext = ext.lower()
            if ext in self._extension_cache:
                result = self._extension_cache.pop(ext)
                self._extension_cache[ext] = result
                self._ignored_paths_cache[name] = result
                self._manage_cache_size()
                return result
            else:
                result = bool(self.allowed_extensions and ext not in self.allowed_extensions)
                self._extension_cache[ext] = result
                self._ignored_paths_cache[name] = result
                self._manage_cache_size()
                return result
        self._ignored_paths_cache[name] = False
        self._manage_cache_size()
        return False

    def clear_cache(self) -> None:
        self._ignored_paths_cache.clear()
        self._extension_cache.clear()
