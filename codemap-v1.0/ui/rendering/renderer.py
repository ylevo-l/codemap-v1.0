import curses,time
from typing import List,Tuple,Optional
from core.model import TreeNode
from config.constants import SUCCESS_MESSAGE_DURATION
from ui.rendering.components import render_status_bar,render_success_message
from ui.core.state import State
from ui.rendering.text import safe_addnstr,clear_line
from ui.rendering.colors import FILE_COLOR,DIRECTORY_COLOR,DISABLED_COLOR,GENERAL_UI_COLOR,STRUCTURE_COLOR
from ui.core.labels import render_single_label
from config.ui_labels import SEPARATOR
from config.symbols import CURSOR_SYMBOL_SELECTED,CURSOR_SYMBOL_UNSELECTED,ARROW_COLLAPSED,ARROW_EXPANDED

class Renderer:
    def __init__(self,screen:any,state:State):
        self.s=screen
        self.u=state
        self.h=self.w=0
        self.pi=self.po=-1
        self.pt=False
        self.pl=None

    def _trunc(self,t:str,w:int)->str:
        return t if w<=3 or len(t)<=w else t[:w-3]+"..."

    def _resize(self):
        y,x=self.s.getmaxyx()
        if (y,x)!=(self.h,self.w):
            self.h,self.w=y,x
            self.s.clear()

    def _tokvis(self,l:List[Tuple[TreeNode,int,bool]])->bool:
        o=self.u.scroll_offset
        return bool(l) and o<len(l) and l[o][2]

    def _succ(self)->bool:
        if not self.u.copying_success:
            return False
        if time.time()-self.u.success_message_time>SUCCESS_MESSAGE_DURATION:
            self.u.copying_success=False
            return False
        return True

    def _line(self,n:TreeNode,d:int,st:bool,row:int,sel:bool):
        _,mx=self.s.getmaxyx()
        x=0
        cur=CURSOR_SYMBOL_SELECTED if sel else CURSOR_SYMBOL_UNSELECTED
        safe_addnstr(self.s,row,x,cur,STRUCTURE_COLOR,curses.A_BOLD if sel else 0)
        x+=len(cur)
        branch="│ "*d
        safe_addnstr(self.s,row,x,branch,STRUCTURE_COLOR)
        x+=len(branch)
        if n.is_dir:
            arr=ARROW_EXPANDED if n.expanded else ARROW_COLLAPSED
            safe_addnstr(self.s,row,x,arr,STRUCTURE_COLOR,curses.A_BOLD if sel else 0)
            x+=len(arr)
        clr=DIRECTORY_COLOR if n.is_dir else DISABLED_COLOR if n.disabled else FILE_COLOR
        name=self._trunc(n.render_name,mx-x-20)
        safe_addnstr(self.s,row,x,name,clr,curses.A_BOLD if sel else 0)
        x+=len(name)
        if st and n.token_count>0 and x+15<mx:
            ctx={"node":n}
            x=render_single_label(self.s,row,x,"tokens",ctx,separator=SEPARATOR,separator_color=GENERAL_UI_COLOR,show_separator=True)
        if x<mx:
            clear_line(self.s,row,x)

    def _view(self,l:List[Tuple[TreeNode,int,bool]],start:int,rows:int):
        end=min(start+rows,len(l))
        for r,idx in enumerate(range(start,end)):
            n,d,st=l[idx]
            self._line(n,d,st,r,idx==self.u.current_index)
        for r in range(end-start,rows):
            clear_line(self.s,r,0)

    def _footer(self,c:Optional[TreeNode],tot:int,tv:bool,succ:bool):
        if succ:
            render_success_message(self.s,getattr(self.u,"success_message",""))
        else:
            render_status_bar(self.s,c,self.u.physical_shift_pressed,tot,tv)

    def render(self,l:List[Tuple[TreeNode,int,bool]],c:Optional[TreeNode],tot:int):
        self._resize()
        rows=self.h-1
        tv=self._tokvis(l)
        succ=self._succ()
        quick=l is self.pl and tv==self.pt and not succ
        if quick and self.u.scroll_offset==self.po and self.u.current_index!=self.pi:
            pr=self.pi-self.u.scroll_offset
            nr=self.u.current_index-self.u.scroll_offset
            if 0<=pr<rows:
                n,d,st=l[self.pi]
                self._line(n,d,st,pr,False)
            if 0<=nr<rows:
                n,d,st=l[self.u.current_index]
                self._line(n,d,st,nr,True)
        else:
            self._view(l,self.u.scroll_offset,rows)
        self._footer(c,tot,tv,succ)
        self.s.noutrefresh()
        curses.doupdate()
        self.pi=self.u.current_index
        self.po=self.u.scroll_offset
        self.pt=tv
        self.pl=l
