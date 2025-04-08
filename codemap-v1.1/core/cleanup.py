import os
import shutil
import fnmatch
from typing import List, Dict, Any, Optional, Union, Tuple

def cleanup_directory(directory_path: str, patterns: List[str], options: Dict[str, Any]) -> bool:
    try:
        if not os.path.isdir(directory_path):
            return False

        if not options.get("enabled", True):
            return True

        recursive = options.get("recursive", True)
        follow_symlinks = options.get("follow_symlinks", False)

        items_to_delete = []

        for root, dirs, files in os.walk(directory_path, topdown=True, followlinks=follow_symlinks):
            for dirname in list(dirs):
                for pattern in patterns:
                    if fnmatch.fnmatch(dirname, pattern):
                        full_path = os.path.join(root, dirname)
                        items_to_delete.append(full_path)
                        dirs.remove(dirname)
                        break

            for filename in files:
                for pattern in patterns:
                    if fnmatch.fnmatch(filename, pattern):
                        full_path = os.path.join(root, filename)
                        items_to_delete.append(full_path)
                        break

            if not recursive:
                break

        for item_path in items_to_delete:
            if os.path.isdir(item_path):
                shutil.rmtree(item_path)
            elif os.path.isfile(item_path):
                os.remove(item_path)

        if options.get("delete_empty_dirs", False):
            delete_empty_directories(directory_path, recursive, follow_symlinks)

        return True

    except Exception:
        return False

def delete_empty_directories(directory_path: str, recursive: bool = True, follow_symlinks: bool = False) -> None:
    if not os.path.isdir(directory_path):
        return

    for root, dirs, files in os.walk(directory_path, topdown=False, followlinks=follow_symlinks):
        if root == directory_path:
            continue

        if not files and not dirs:
            try:
                os.rmdir(root)
            except:
                pass

        if not recursive and root != directory_path:
            break

def get_cleanup_statistics(directory_path: str, patterns: List[str], options: Dict[str, Any]) -> Tuple[int, int, List[str]]:
    try:
        if not os.path.isdir(directory_path):
            return 0, 0, []

        if not options.get("enabled", True):
            return 0, 0, []

        recursive = options.get("recursive", True)
        follow_symlinks = options.get("follow_symlinks", False)

        items_to_delete = []
        dir_count = 0
        file_count = 0

        for root, dirs, files in os.walk(directory_path, topdown=True, followlinks=follow_symlinks):
            for dirname in list(dirs):
                for pattern in patterns:
                    if fnmatch.fnmatch(dirname, pattern):
                        full_path = os.path.join(root, dirname)
                        items_to_delete.append(full_path)
                        dir_count += 1
                        dirs.remove(dirname)
                        break

            for filename in files:
                for pattern in patterns:
                    if fnmatch.fnmatch(filename, pattern):
                        full_path = os.path.join(root, filename)
                        items_to_delete.append(full_path)
                        file_count += 1
                        break

            if not recursive:
                break

        return dir_count, file_count, items_to_delete

    except Exception:
        return 0, 0, []