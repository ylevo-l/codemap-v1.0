import os
from typing import Optional, List, Dict, Set
from functools import lru_cache

class TreeNode:

    _basename_cache: Dict[str, str] = {}
    _dirname_cache: Dict[str, str] = {}

    def __init__(self, path: str, is_dir: bool, parent: Optional['TreeNode'] = None):
        self.path = path
        self.is_dir = is_dir
        self.expanded = False if is_dir else None

        if path in TreeNode._basename_cache:
            self.display_name = TreeNode._basename_cache[path]
        else:
            self.display_name = os.path.basename(path)
            TreeNode._basename_cache[path] = self.display_name

        self.render_name = self.display_name
        self.disabled = False if not is_dir else None
        self.children: List['TreeNode'] = []
        self.token_count: int = 0
        self.parent = parent

    def add_child(self, child: 'TreeNode') -> None:

        self.children.append(child)

    def sort_children(self) -> None:

        self.children.sort(key=lambda x: (not x.is_dir, x.display_name.lower()))

    def calculate_token_count(self) -> int:

        if not self.is_dir:
            return 0 if self.disabled else self.token_count

        self.token_count = sum(
            child.calculate_token_count() for child in self.children
            if (child.is_dir and child.expanded) or (not child.is_dir and not child.disabled)
        )
        return self.token_count

    def update_token_count(self, delta: int) -> None:

        if delta == 0:
            return

        self.token_count += delta

        if self.parent:
            self.parent.update_token_count(delta)

    def update_render_name(self) -> None:

        self.render_name = self.display_name

    @staticmethod
    def clear_caches() -> None:

        TreeNode._basename_cache.clear()
        TreeNode._dirname_cache.clear()

@lru_cache(maxsize=1024)
def get_path_basename(path: str) -> str:

    return os.path.basename(path)

@lru_cache(maxsize=1024)
def get_path_dirname(path: str) -> str:

    return os.path.dirname(path)