from ui.labels.core import StatusLabel, StatusLabelRegistry
from ui.rendering.colors import TOKEN_LABEL_COLOR, GENERAL_UI_COLOR
from config.ui_labels import TOKEN_LABEL
from typing import Dict, Any

registry = StatusLabelRegistry()

def token_value_getter(context: Dict[str, Any]) -> str:
    if "node" in context and hasattr(context["node"], "token_count"):
        return context["node"].token_count

    if "node_tokens" in context:
        return context["node_tokens"]

    if "total_tokens" in context:
        return context["total_tokens"]

    return ""

def register_default_labels():
    token_label = StatusLabel(
        key="tokens",
        name=TOKEN_LABEL,
        value_getter=token_value_getter,
        label_color=TOKEN_LABEL_COLOR,
        value_color=GENERAL_UI_COLOR
    )
    registry.register(token_label)