import threading,curses
from typing import Optional,Dict,List,Tuple
from core.model import TreeNode
from core.operations import toggle_node,toggle_subtree,collect_visible_files
from core.operations.tree_ops import are_all_files_enabled,toggle_folder_enable_state
from core.utils.clipboard import copy_files_subloop,copy_text_to_clipboard
from core.refactor.ops import refactor_file
from core.refactor.bulk import refactor_files
from core.utils.state import gather_state,save_state
from core.utils.persistence import save_snapshot,load_snapshot,delete_snapshot,has_snapshot
from core.utils.terminal import reset_terminal
from config import STATE_FILE
from config.ui_labels import REFACTOR_SUCCESS_MESSAGE,REFACTOR_ALL_SUCCESS_MESSAGE,SUCCESS_MESSAGE
from ui.controls.events import Event,EventType
from ui.controls.navigation import NavigationHandler
from ui.core.state import State

class ActionHandler:
    def __init__(self,stdscr,ui_state:State,root_node:TreeNode,path_to_node:Dict[str,TreeNode],fmt:str,path_mode:str,tree_changed_flag:threading.Event,lock:threading.Lock):
        self.stdscr=stdscr
        self.ui_state=ui_state
        self.root_node=root_node
        self.path_to_node=path_to_node
        self.fmt=fmt
        self.path_mode=path_mode
        self.tree_changed_flag=tree_changed_flag
        self.lock=lock
        self.current_node=None
        self.flattened_cache:List[Tuple[TreeNode,int,bool]]=[]
        self.selected_node_path=None
        self.navigation_handler=NavigationHandler(ui_state)

    def update_context(self,current_node:Optional[TreeNode],flattened_cache:List[Tuple[TreeNode,int,bool]]):
        self.current_node=current_node
        self.flattened_cache=flattened_cache
        if current_node:
            self.selected_node_path=current_node.path

    def handle_navigation_up(self,event:Event):
        shift=self.ui_state.physical_shift_pressed
        new_index=self.navigation_handler.navigate(-1,self.flattened_cache,shift)
        self.ui_state.current_index=new_index
        return True

    def handle_navigation_down(self,event:Event):
        shift=self.ui_state.physical_shift_pressed
        new_index=self.navigation_handler.navigate(1,self.flattened_cache,shift)
        self.ui_state.current_index=new_index
        return True

    def handle_toggle_node(self,event:Event):
        if not self.current_node or not self.current_node.is_dir:
            return False
        with self.lock:
            toggle_node(self.current_node)
            self.root_node.calculate_token_count()
            self.tree_changed_flag.set()
        return True

    def handle_toggle_subtree(self,event:Event):
        if not self.current_node or not self.current_node.is_dir:
            return False
        with self.lock:
            toggle_subtree(self.current_node)
            self.root_node.calculate_token_count()
            self.tree_changed_flag.set()
        return True

    def handle_toggle_disable(self,event:Event):
        if not self.current_node or self.current_node.is_dir:
            return False
        with self.lock:
            self.current_node.disabled=not self.current_node.disabled
            self.current_node.update_render_name()
            self.root_node.calculate_token_count()
            self.tree_changed_flag.set()
        return True

    def handle_copy_content(self,event:Event):
        if not self.current_node:
            return False
        files_to_copy=collect_visible_files(self.current_node,self.path_mode)
        if not files_to_copy:
            return False
        copied_text=copy_files_subloop(self.stdscr,files_to_copy,self.fmt)
        copy_text_to_clipboard(copied_text)
        self.ui_state.set_success(SUCCESS_MESSAGE)
        return True

    def handle_refactor_content(self,event:Event):
        if not self.current_node:
            return False
        if self.current_node.is_dir:
            if not (event.data and event.data.get("shift",False) and self.current_node.expanded):
                return False
            visible:List[str]=[]
            visited=set()

            def collect(node:TreeNode):
                if node.path in visited:
                    return
                visited.add(node.path)
                if node.is_dir and node.expanded:
                    for child in node.children:
                        collect(child)
                elif not node.is_dir and not node.disabled:
                    visible.append(node.path)
            collect(self.current_node)
            if not visible:
                return False
            refactor_files(visible)
            self.ui_state.set_success(REFACTOR_ALL_SUCCESS_MESSAGE)
            return True
        if refactor_file(self.current_node.path):
            self.ui_state.set_success(REFACTOR_SUCCESS_MESSAGE)
            return True
        return False

    def handle_save_content(self,event:Event):
        if not self.current_node or has_snapshot(self.current_node.path):
            return False
        if save_snapshot(self.current_node.path):
            self.ui_state.set_success("Snapshot saved")
            return True
        return False

    def handle_load_content(self,event:Event):
        if not self.current_node or not has_snapshot(self.current_node.path):
            return False
        if self.ui_state.physical_delete_pressed:
            if delete_snapshot(self.current_node.path):
                self.ui_state.set_success("Snapshot deleted")
                return True
            return False
        if load_snapshot(self.current_node.path):
            self.ui_state.set_success("Snapshot loaded")
            self.tree_changed_flag.set()
            return True
        return False

    def handle_enter_key(self,event:Event):
        return self.handle_toggle_node(event)

    def handle_quit(self,event:Event):
        with self.lock:
            state={}
            gather_state(self.root_node,state,base_path=self.root_node.path,is_root=True)
            save_state(STATE_FILE,state)
        reset_terminal(self.stdscr)
        self.ui_state.should_quit=True
        return True

    def handle_shift_mode_changed(self,event:Event):
        return True

    def handle_shift_disable_all(self,event:Event):
        if not self.current_node or not self.current_node.is_dir:
            return False
        with self.lock:
            all_enabled=are_all_files_enabled(self.current_node)
            toggle_folder_enable_state(self.current_node,not all_enabled)
            self.root_node.calculate_token_count()
            self.tree_changed_flag.set()
        return True

    def register_handlers(self,control_manager):
        control_manager.register_handler(EventType.NAVIGATION_UP,self.handle_navigation_up)
        control_manager.register_handler(EventType.NAVIGATION_DOWN,self.handle_navigation_down)
        control_manager.register_handler(EventType.TOGGLE_NODE,self.handle_toggle_node)
        control_manager.register_handler(EventType.TOGGLE_SUBTREE,self.handle_toggle_subtree)
        control_manager.register_handler(EventType.TOGGLE_DISABLE,self.handle_toggle_disable)
        control_manager.register_handler(EventType.COPY_CONTENT,self.handle_copy_content)
        control_manager.register_handler(EventType.REFACTOR_CONTENT,self.handle_refactor_content)
        control_manager.register_handler(EventType.SAVE_CONTENT,self.handle_save_content)
        control_manager.register_handler(EventType.LOAD_CONTENT,self.handle_load_content)
        control_manager.register_handler(EventType.ENTER_KEY,self.handle_enter_key)
        control_manager.register_handler(EventType.QUIT,self.handle_quit)
        control_manager.register_handler(EventType.SHIFT_MODE_CHANGED,self.handle_shift_mode_changed)
        control_manager.register_handler(EventType.SHIFT_DISABLE_ALL,self.handle_shift_disable_all)
