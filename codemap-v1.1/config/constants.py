import sys
import tiktoken

STATE_FILE = "__tree_state__"
SUCCESS_MESSAGE_DURATION = 1.0
IGNORED_PATTERNS = [
    "__pycache__", "node_modules", "dist", "build", "venv", ".git", ".svn", ".hg",
    ".idea", ".vscode", ".env", ".DS_Store", "Thumbs.db", ".bak", ".tmp",
    "desktop.ini", ".log", ".db", ".key", ".pyc", ".exe", ".dll", ".so", ".dylib",
    "__tree_state__"
]
ALLOWED_EXTENSIONS = [
    ".py", ".pyi", ".pyc", ".pyo", ".pyd", ".txt", ".md", ".rst", ".docx", ".pdf",
    ".odt", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".sh", ".bash", ".zsh", ".csh",
    ".ksh", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".ts", ".tsx", ".jsx", ".mjs",
    ".cjs", ".pl", ".php", ".tcl", ".lua", ".java", ".cpp", ".c", ".h", ".hpp", ".cs",
    ".go", ".rs", ".swift", ".vb", ".fs", ".sql", ".html", ".htm", ".css", ".scss",
    ".sass", ".less", ".xml"
]

COPY_FORMAT_PRESETS = {
    "blocks": "{path}:\n\"\"\"\n{content}\n\"\"\"\n",
    "lines": "{path}: {content}\n",
    "raw": "{content}\n"
}

SCROLL_SPEED = {"normal": 1, "accelerated": 5}
MAX_TREE_DEPTH = 10
INPUT_TIMEOUT = 0.02

CLEANUP_PATTERNS = [
    "__pycache__",
    "*.pyc",
    "*.pyo",
    "*.pyd",
    ".coverage",
    ".pytest_cache",
    ".hypothesis",
    "*.so",
    "*.c",
    "*.o"
]

CLEANUP_OPTIONS = {
    "enabled": True,
    "recursive": True,
    "follow_symlinks": False,
    "delete_empty_dirs": False
}

try:
    ENCODING = tiktoken.encoding_for_model("gpt-4o")
except KeyError:
    print("Error: Model encoding not found.")
    sys.exit(1)

def count_tokens(content: str) -> int:
    return len(ENCODING.encode(content))