import sys,subprocess,curses
from typing import List,Tuple
from config.constants import COPY_FORMAT_PRESETS
from core.refactor.language import determine_language

def copy_text_to_clipboard(text:str):
    try:
        (subprocess.Popen("clip",stdin=subprocess.PIPE,shell=True).communicate(input=text.encode("utf-16")) if sys.platform.startswith("win") else subprocess.Popen("pbcopy",stdin=subprocess.PIPE).communicate(input=text.encode("utf-8")) if sys.platform.startswith("darwin") else subprocess.Popen(["xclip","-selection","clipboard"],stdin=subprocess.PIPE).communicate(input=text.encode("utf-8")))
    except:
        pass

def _build_segment(path:str,content:str,fmt:str)->str:
    template=COPY_FORMAT_PRESETS.get(fmt,COPY_FORMAT_PRESETS["optimized"])
    return template.format(path=path,content=(content or "<Could not read file>").rstrip(),language=determine_language(path))

def copy_files_subloop(stdscr,files:List[Tuple[str,str]],fmt:str)->str:
    copied=[]
    if stdscr is None:
        for p,c in files:
            copied.append(_build_segment(p,c,fmt))
        return "\n".join(copied)
    my,mx=stdscr.getmaxyx()
    total=len(files)
    bar_len=max(10,mx-30)
    for idx,(p,c) in enumerate(files,1):
        copied.append(_build_segment(p,c,fmt))
        prog=int(idx/total*bar_len)
        try:
            stdscr.addstr(my-1,0,f'Copying {idx}/{total} files: [{"#"*prog}{"-"*(bar_len-prog)}]'[:mx-1],curses.color_pair(7))
            stdscr.refresh()
        except:
            pass
    return "\n".join(copied)
