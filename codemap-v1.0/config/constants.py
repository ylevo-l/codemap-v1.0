import os
import sys
import functools
import tiktoken
import subprocess
import re
from pathlib import Path
import logging

@functools.lru_cache(maxsize=1)
def _detect_refresh_rate() -> float:
    try:
        if sys.platform.startswith("win"):
            import ctypes
            user32 = ctypes.windll.user32
            gdi32 = ctypes.windll.gdi32
            hdc = user32.GetDC(0)
            hz = gdi32.GetDeviceCaps(hdc, 116)
            user32.ReleaseDC(0, hdc)
            return float(hz)
        if sys.platform.startswith("darwin"):
            out = subprocess.check_output(["system_profiler", "SPDisplaysDataType"], timeout=2, text=True, errors='ignore')
            m = re.search(r"Refresh Rate:\s*(\d+)", out)
            return float(m.group(1)) if m else 0.0
        out = subprocess.check_output(["xrandr", "--current"], timeout=1, text=True, errors='ignore')
        current_mode_line = re.search(r"^\s*.*?\s*\d+x\d+.*?\*.*$", out, re.MULTILINE)
        if current_mode_line:
            m = re.search(r"(\d+(?:\.\d+)?)\s*\*?\+", current_mode_line.group(0))
            if m:
                return float(m.group(1))
        m = re.search(r"\s(\d+(?:\.\d+)?)\s*Hz", out)
        return float(m.group(1)) if m else 0.0
    except (ImportError, subprocess.CalledProcessError, FileNotFoundError, ValueError, AttributeError, subprocess.TimeoutExpired) as e:
        logging.warning(f"Could not auto-detect refresh rate: {e}. Falling back.")
        return 0.0
    except Exception as e:
        logging.error(f"Unexpected error detecting refresh rate: {e}", exc_info=True)
        return 0.0

def _env_rate() -> float:
    try:
        v = float(os.getenv("CM_REFRESH_HZ", "0"))
        return v if v >= 30 else 0.0
    except ValueError:
        logging.warning("Invalid value for CM_REFRESH_HZ environment variable. Must be a float.")
        return 0.0

@functools.lru_cache(maxsize=1)
def get_refresh_rate() -> float:
    env_val = _env_rate()
    if env_val > 0:
        return env_val
    detected_val = _detect_refresh_rate()
    if detected_val > 0:
        return detected_val
    return 144.0

def get_cli_refresh_interval() -> float:
    rate = get_refresh_rate()
    effective_rate = min(120.0, max(1.0, rate))
    return 1.0 / effective_rate

if sys.platform.startswith("win"):
    _config_base = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "CodeMap"
    _data_base = _config_base
    _state_base = _config_base

else:
    _config_base = Path(os.getenv("XDG_CONFIG_HOME", Path.home() / ".config")) / "CodeMap"
    _data_base = Path(os.getenv("XDG_DATA_HOME", Path.home() / ".local" / "share")) / "CodeMap"
    _state_base = Path(os.getenv("XDG_STATE_HOME", Path.home() / ".local" / "state")) / "CodeMap"

os.makedirs(_config_base, exist_ok=True)

os.makedirs(_data_base, exist_ok=True)

os.makedirs(_state_base, exist_ok=True)

STATE_FILE = str(_state_base / "__tree_state__")

SNAPSHOT_DIR = str(_data_base / "snapshots")

os.makedirs(SNAPSHOT_DIR, exist_ok=True)

SUCCESS_MESSAGE_DURATION = 1.0

CLI_REFRESH_INTERVAL = get_cli_refresh_interval()

IGNORED_PATTERNS = [
    "__pycache__", "node_modules", "dist", "build", "venv", ".git", ".svn", ".hg",
    ".idea", ".vscode", ".env*", ".DS_Store", "Thumbs.db", "*.bak", "*.tmp",
    "desktop.ini", "*.log", "*.db", "*.key", "*.pyc", "*.exe", "*.dll", "*.so",
    "*.dylib", "__tree_state__", "target", "*.o", "*.obj", "*.class", "*.jar",
    "*.war", "*.ear", ".cache", ".pytest_cache", ".mypy_cache", ".tox",
    "*.swp", "*.swo", "buildlog.txt", ".terraform", "*.lock", "poetry.lock", "package-lock.json",
    "yarn.lock", "Pipfile.lock", "composer.lock",

]

ALLOWED_EXTENSIONS = [
    ".py", ".pyi", ".pyw", ".txt", ".md", ".rst", ".json", ".xml", ".html", ".htm", ".css",
    ".scss", ".sass", ".less", ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf", ".properties",
    ".sh", ".bash", ".zsh", ".csh", ".ksh", ".bat", ".cmd", ".ps1", ".vbs", ".js", ".ts",
    ".jsx", ".tsx", ".mjs", ".cjs", ".c", ".cpp", ".h", ".hpp", ".cc", ".hh", ".cs", ".go",
    ".rs", ".swift", ".java", ".kt", ".kts", ".scala", ".sc", ".groovy", ".gradle", ".rb",
    ".php", ".pl", ".pm", ".sql", "Dockerfile", ".dockerignore", ".json5", ".hjson", ".tf",
    ".tfvars", ".hcl",

]

COPY_FORMAT_PRESETS = {
    "blocks": "{path}:\n\"\"\"\n{content}\n\"\"\"\n",
    "lines": "{path}: {content}\n",
    "raw": "{content}\n",
    "optimized": "{path}\n```{language}\n{content}\n```\n",
    "compact": "```{language} {path}\n{content}\n```",
    "dash": "{path}\n---\n{language}\n{content}\n---\n",

}

SCROLL_SPEED = {"normal": 1, "accelerated": 5}

MAX_TREE_DEPTH = 15

INPUT_TIMEOUT = max(0.01, CLI_REFRESH_INTERVAL)

CLEANUP_PATTERNS = [
    "__pycache__", "*.pyc", "*.pyo", "*.pyd", ".coverage", ".pytest_cache",
    ".hypothesis", "*.so", "*.o", "*.obj", "*.class", "target/", "build/", "dist/",
    "*.log", "*.tmp", "*.bak",

]

CLEANUP_OPTIONS = {"enabled": True, "recursive": True, "follow_symlinks": False, "delete_empty_dirs": True}

ENCODING = tiktoken.encoding_for_model("gpt-4o")

def count_tokens(content: str) -> int:
    try:
        return len(ENCODING.encode(content))
    except Exception as e:
        logging.error(f"Error during token counting: {e}", exc_info=True)
        return len(content) // 4

__all__ = [
    "STATE_FILE", "SNAPSHOT_DIR", "SUCCESS_MESSAGE_DURATION", "CLI_REFRESH_INTERVAL",
    "IGNORED_PATTERNS", "ALLOWED_EXTENSIONS", "COPY_FORMAT_PRESETS", "SCROLL_SPEED",
    "MAX_TREE_DEPTH", "INPUT_TIMEOUT", "count_tokens", "CLEANUP_PATTERNS",
    "CLEANUP_OPTIONS", "get_refresh_rate", "get_cli_refresh_interval", "ENCODING"

]
