from typing import List, Tuple
from core.model.tree_node import TreeNode
from ui.core.state import State

class NavigationHandler:
    def __init__(self, ui_state: State):
        self.ui_state = ui_state

    def navigate(self, direction: int, nodes: List[Tuple[TreeNode, int, bool]], shift: bool) -> int:
        if not nodes:
            return 0
        idx = self.ui_state.current_index
        step = self.ui_state.step_accel if shift else self.ui_state.step_normal
        if direction < 0:
            dest = max(0, idx - step)
        else:
            dest = min(len(nodes) - 1, idx + step)
        if idx == dest:
            return idx
        scan = range(idx - 1, dest - 1, -1) if direction < 0 else range(idx + 1, dest + 1)
        for i in scan:
            if nodes[i][0].is_dir:
                return i
        return dest
