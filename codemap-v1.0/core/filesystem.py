import os
import time
import threading
from typing import Dict, List, Optional

from core.model import TreeNode
from config.constants import count_tokens

class FileFilter:
    def __init__(self, ignored_patterns: List[str], allowed_extensions: List[str]):
        self.ignored_patterns = ignored_patterns
        self.allowed_extensions = allowed_extensions
    
    def is_ignored(self, name: str) -> bool:
        if any(p in name for p in self.ignored_patterns):
            return True
        
        _, ext = os.path.splitext(name)
        return bool(self.allowed_extensions and ext and ext.lower() not in self.allowed_extensions)

def build_tree(root_path: str, file_filter: FileFilter,
              path_to_node: Dict[str, TreeNode], lock: threading.Lock) -> TreeNode:
    root_node = TreeNode(root_path, True)
    root_node.expanded = True
    
    with lock:
        path_to_node[root_path] = root_node
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if not file_filter.is_ignored(d)]
            
            current_dir_node = path_to_node.get(dirpath)
            if not current_dir_node:
                continue
            
            for dirname in dirnames:
                full_path = os.path.join(dirpath, dirname)
                dir_node = TreeNode(full_path, True, current_dir_node)
                current_dir_node.add_child(dir_node)
                path_to_node[full_path] = dir_node
            
            for filename in filenames:
                if file_filter.is_ignored(filename):
                    continue
                
                full_path = os.path.join(dirpath, filename)
                file_node = TreeNode(full_path, False, current_dir_node)
                
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        file_node.token_count = count_tokens(f.read())
                except:
                    file_node.token_count = 0
                
                current_dir_node.add_child(file_node)
                path_to_node[full_path] = file_node
            
            current_dir_node.sort_children()
    
    root_node.calculate_token_count()
    return root_node

def scan_filesystem(root_path: str, file_filter: FileFilter,
                  path_to_node: Dict[str, TreeNode], tree_changed_flag: threading.Event,
                  stop_event: threading.Event, lock: threading.Lock) -> None:
    previous_state = {}
    
    with lock:
        for path, node in path_to_node.items():
            if not node.is_dir:
                try:
                    previous_state[path] = os.path.getmtime(path)
                except:
                    previous_state[path] = None
    
    while not stop_event.is_set():
        current_state = {}
        
        for dirpath, dirnames, filenames in os.walk(root_path):
            dirnames[:] = [d for d in dirnames if not file_filter.is_ignored(d)]
            
            for name in filenames:
                if file_filter.is_ignored(name):
                    continue
                
                full_path = os.path.join(dirpath, name)
                try:
                    current_state[full_path] = os.path.getmtime(full_path)
                except:
                    current_state[full_path] = None
        
        added = set(current_state.keys()) - set(previous_state.keys())
        removed = set(previous_state.keys()) - set(current_state.keys())
        modified = {
            path for path in current_state.keys() & previous_state.keys() 
            if current_state[path] != previous_state[path]
        }
        
        if added or removed or modified:
            with lock:
                for path in added:
                    is_dir = os.path.isdir(path)
                    parent_path = os.path.dirname(path)
                    parent_node = path_to_node.get(parent_path)
                    
                    if parent_node and parent_node.is_dir and parent_node.expanded:
                        new_node = TreeNode(path, is_dir, parent_node)
                        
                        if not is_dir:
                            try:
                                with open(path, "r", encoding="utf-8") as f:
                                    new_node.token_count = count_tokens(f.read())
                            except:
                                new_node.token_count = 0
                                
                            if not new_node.disabled:
                                parent_node.update_token_count(new_node.token_count)
                                
                        parent_node.add_child(new_node)
                        parent_node.sort_children()
                        path_to_node[path] = new_node
                
                for path in removed:
                    node = path_to_node.get(path)
                    if node:
                        parent = node.parent
                        if parent:
                            parent.children.remove(node)
                            
                            if not node.is_dir and not node.disabled:
                                parent.update_token_count(-node.token_count)
                                
                        del path_to_node[path]
                
                for path in modified:
                    node = path_to_node.get(path)
                    if node and not node.is_dir and not node.disabled:
                        try:
                            with open(path, "r", encoding="utf-8") as f:
                                new_count = count_tokens(f.read())
                        except:
                            new_count = 0
                            
                        delta = new_count - node.token_count
                        node.token_count = new_count
                        
                        if node.parent:
                            node.parent.update_token_count(delta)
                
                tree_changed_flag.set()
        
        previous_state = current_state
        time.sleep(1)