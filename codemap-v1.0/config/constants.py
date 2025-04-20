import os,sys,tiktoken,fnmatch,shutil,tempfile,stat,queue,threading,time,subprocess,curses,json,gc,signal,argparse
from pathlib import Path

STATE_FILE=os.path.join(os.getenv("APPDATA") or os.path.expanduser("~") if sys.platform.startswith("win") else os.getenv("XDG_STATE_HOME") or os.path.expanduser("~/.codemap"),"CodeMap","__tree_state__" if sys.platform.startswith("win") else "__tree_state__")

SNAPSHOT_DIR=os.path.join(os.getenv("APPDATA") or os.path.expanduser("~") if sys.platform.startswith("win") else os.getenv("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"),"CodeMap","snapshots")

os.makedirs(SNAPSHOT_DIR,exist_ok=True)

SUCCESS_MESSAGE_DURATION=1.0

IGNORED_PATTERNS=["__pycache__","node_modules","dist","build","venv",".git",".svn",".hg",".idea",".vscode",".env",".DS_Store","Thumbs.db",".bak",".tmp","desktop.ini",".log",".db",".key",".pyc",".exe",".dll",".so",".dylib","__tree_state__"]

ALLOWED_EXTENSIONS=[".py",".pyi",".pyc",".pyo",".pyd",".txt",".md",".rst",".docx",".pdf",".odt",".yaml",".yml",".toml",".ini",".cfg",".sh",".bash",".zsh",".csh",".ksh",".bat",".cmd",".ps1",".vbs",".js",".ts",".tsx",".jsx",".mjs",".cjs",".pl",".php",".tcl",".lua",".java",".cpp",".c",".h",".hpp",".cs",".go",".rs",".swift",".vb",".fs",".sql",".html",".htm",".css",".scss",".sass",".less",".xml"]

COPY_FORMAT_PRESETS={"blocks":"{path}:\n\"\"\"\n{content}\n\"\"\"\n","lines":"{path}: {content}\n","raw":"{content}\n","optimized":"{path}\n```{language}\n{content}\n```\n","compact":"```{language} {path}\n{content}\n```"}

SCROLL_SPEED={"normal":1,"accelerated":5}

MAX_TREE_DEPTH=10

INPUT_TIMEOUT=0.0

CLEANUP_PATTERNS=["__pycache__","*.pyc","*.pyo","*.pyd",".coverage",".pytest_cache",".hypothesis","*.so","*.c","*.o"]

CLEANUP_OPTIONS={"enabled":True,"recursive":True,"follow_symlinks":False,"delete_empty_dirs":False}

ENCODING=tiktoken.encoding_for_model("gpt-4o")

def count_tokens(content:str)->int:
    return len(ENCODING.encode(content))

__all__=["STATE_FILE","SNAPSHOT_DIR","SUCCESS_MESSAGE_DURATION","IGNORED_PATTERNS","ALLOWED_EXTENSIONS","COPY_FORMAT_PRESETS","SCROLL_SPEED","MAX_TREE_DEPTH","INPUT_TIMEOUT","count_tokens","CLEANUP_PATTERNS","CLEANUP_OPTIONS"]
