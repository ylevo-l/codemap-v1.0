from typing import Dict, Any, List, Optional, Callable, Union

class StatusLabel:
    def __init__(self, key: str, name: str,
                value_getter: Callable[[Dict[str, Any]], Any] = None,
                label_color: int = None,
                value_color: int = None):
        self.key = key
        self.name = name
        self.value_getter = value_getter
        self.label_color = label_color
        self.value_color = value_color

    def get_value(self, context: Optional[Dict[str, Any]] = None) -> str:
        if self.value_getter is None:
            return ""

        if context is None:
            context = {}

        try:
            value = self.value_getter(context)
            return str(value) if value is not None else ""
        except:
            return ""

class StatusLabelRegistry:
    def __init__(self):
        self.labels: Dict[str, StatusLabel] = {}

    def register(self, label: StatusLabel) -> None:
        self.labels[label.key] = label

    def get(self, key: str) -> Optional[StatusLabel]:
        return self.labels.get(key)

    def get_all(self) -> List[StatusLabel]:
        return list(self.labels.values())