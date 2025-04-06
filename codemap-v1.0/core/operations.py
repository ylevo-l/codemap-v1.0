import os
import time
import threading
from typing import Generator, Tuple, List, Dict

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

def flatten_tree(node: TreeNode, depth: int = 0, ancestor_has_tokens: bool = False) -> Generator[Tuple[TreeNode, int, bool], None, None]:
    show_tokens = False
    if not ancestor_has_tokens and node.token_count > 0 and node.is_dir:
        show_tokens = True
        ancestor_has_tokens = True
    
    yield (node, depth, show_tokens)
    
    if node.is_dir and node.expanded:
        for child in node.children:
            yield from flatten_tree(child, depth + 1, ancestor_has_tokens)

def collect_visible_files(node: TreeNode, path_mode: str) -> List[Tuple[str, str]]:
    files = []
    
    def recurse(nd: TreeNode, path: List[str]):
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

def calculate_token_counts(root: TreeNode, path_to_node: Dict[str, TreeNode],
                          tree_changed_flag: threading.Event, lock: threading.Lock) -> None:
    while True:
        with lock:
            for node in path_to_node.values():
                if not node.is_dir and node.token_count == 0 and not node.disabled:
                    try:
                        with open(node.path, "r", encoding="utf-8") as f:
                            node.token_count = count_tokens(f.read())
                    except:
                        node.token_count = 0
                    
                    if node.parent:
                        node.parent.update_token_count(node.token_count)
                
                tree_changed_flag.set()
        
        time.sleep(5)