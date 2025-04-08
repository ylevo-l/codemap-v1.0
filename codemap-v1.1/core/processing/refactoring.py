import os
from typing import Dict, Any, Optional, List, Tuple

from core.processing.language import determine_language, strip_comments_and_docstrings
from config.constants import CLEANUP_PATTERNS, CLEANUP_OPTIONS

def cleanup_after_refactor(directory_path: str, custom_patterns: Optional[List[str]] = None,
                          custom_options: Optional[Dict[str, Any]] = None) -> bool:
    from core.processing.cleanup import cleanup_directory

    patterns = custom_patterns if custom_patterns is not None else CLEANUP_PATTERNS
    options = CLEANUP_OPTIONS.copy()

    if custom_options:
        options.update(custom_options)

    return cleanup_directory(directory_path, patterns, options)

def get_cleanup_preview(directory_path: str, custom_patterns: Optional[List[str]] = None,
                       custom_options: Optional[Dict[str, Any]] = None) -> Tuple[int, int, List[str]]:
    from core.processing.cleanup import get_cleanup_statistics

    patterns = custom_patterns if custom_patterns is not None else CLEANUP_PATTERNS
    options = CLEANUP_OPTIONS.copy()

    if custom_options:
        options.update(custom_options)

    return get_cleanup_statistics(directory_path, patterns, options)

def refactor_file(file_path: str) -> bool:
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()

        language = determine_language(file_path)
        refactored_content = strip_comments_and_docstrings(content, language)

        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(refactored_content)

        dir_path = os.path.dirname(file_path)
        if dir_path:
            cleanup_after_refactor(dir_path)

        return True
    except Exception:
        return False

def refactor_directory(directory_path: str, custom_cleanup_patterns: Optional[List[str]] = None,
                      custom_cleanup_options: Optional[Dict[str, Any]] = None) -> bool:
    return cleanup_after_refactor(directory_path, custom_cleanup_patterns, custom_cleanup_options)