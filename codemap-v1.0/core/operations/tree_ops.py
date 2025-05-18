from typing import Generator, Tuple, Set, Optional, List

from core.model.tree_node import TreeNode
from config.symbols import BRANCH_VERTICAL, BRANCH_JUNCTION, BRANCH_LAST

def _build_prefix(stack: List[bool]) -> str:
    if not stack:
        return ""
    parts = []
    for last in stack[:-1]:
        parts.append("  " if last else BRANCH_VERTICAL)
    parts.append(BRANCH_LAST if stack[-1] else BRANCH_JUNCTION)
    return "".join(parts)

def flatten_tree(
    node: TreeNode,
    stack: Optional[List[bool]] = None,
    visited: Optional[Set[str]] = None,
    is_root: bool = True,

) -> Generator[Tuple[TreeNode, str, bool], None, None]:
    if visited is None:
        visited = set()
    if stack is None:
        stack = []
    if node.path in visited:
        return
    visited.add(node.path)
    show_tokens = is_root and node.token_count > 0
    prefix = _build_prefix(stack)
    yield (node, prefix, show_tokens)
    if node.is_dir and node.expanded:
        total = len(node.children)
        for idx, child in enumerate(node.children):
            last = idx == total - 1
            yield from flatten_tree(child, stack + [last], visited, False)

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

def are_all_files_enabled(node: TreeNode) -> bool:
    if not node.is_dir:
        return not node.disabled
    for child in node.children:
        if child.is_dir:
            if not are_all_files_enabled(child):
                return False
        else:
            if child.disabled:
                return False
    return True

def toggle_folder_enable_state(node: TreeNode, enable: bool) -> None:
    if not node.is_dir:
        return
    for child in node.children:
        if child.is_dir:
            toggle_folder_enable_state(child, enable)
        else:
            child.disabled = not enable
            child.update_render_name()
