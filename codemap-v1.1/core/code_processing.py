import os
import re
from pygments import lex
from pygments.lexers import get_lexer_by_name, guess_lexer
from pygments.token import Token
from typing import Dict, Any, Optional, List, Tuple

from config.constants import CLEANUP_PATTERNS, CLEANUP_OPTIONS
from core.cleanup import cleanup_directory, get_cleanup_statistics

def get_lexer(language: str, source: str):
    try:
        return get_lexer_by_name(language)
    except Exception:
        return guess_lexer(source)

def filter_tokens(source: str, lexer) -> str:
    return ''.join(token_value for token_type, token_value in lex(source, lexer)
                   if token_type not in Token.Comment and token_type not in Token.Literal.String.Doc)

def remove_extra_whitespace(code: str) -> str:
    code = re.sub(r'\n\s*\n+', '\n\n', code)
    code = re.sub(r'[ \t]+$', '', code, flags=re.M)
    return code.strip()

def determine_language(file_path: str) -> str:
    _, ext = os.path.splitext(file_path)
    ext = ext.lower()

    extension_to_language = {
        '.py': 'python',
        '.js': 'javascript',
        '.html': 'html',
        '.css': 'css',
        '.java': 'java',
        '.c': 'c',
        '.cpp': 'cpp',
        '.h': 'c',
        '.hpp': 'cpp',
        '.cs': 'csharp',
        '.php': 'php',
        '.rb': 'ruby',
        '.go': 'go',
        '.rs': 'rust',
        '.ts': 'typescript',
        '.tsx': 'typescript',
        '.jsx': 'jsx',
        '.sql': 'sql',
        '.sh': 'bash',
        '.json': 'json',
        '.yaml': 'yaml',
        '.yml': 'yaml',
    }

    return extension_to_language.get(ext, 'text')

def strip_comments_and_docstrings(source: str, language: str = 'python') -> str:
    lexer = get_lexer(language, source)
    filtered = filter_tokens(source, lexer)
    return remove_extra_whitespace(filtered)

def cleanup_after_refactor(directory_path: str, custom_patterns: Optional[List[str]] = None,
                          custom_options: Optional[Dict[str, Any]] = None) -> bool:
    patterns = custom_patterns if custom_patterns is not None else CLEANUP_PATTERNS
    options = CLEANUP_OPTIONS.copy()

    if custom_options:
        options.update(custom_options)

    return cleanup_directory(directory_path, patterns, options)

def get_cleanup_preview(directory_path: str, custom_patterns: Optional[List[str]] = None,
                       custom_options: Optional[Dict[str, Any]] = None) -> Tuple[int, int, List[str]]:
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