from collections import OrderedDict
from typing import TypeVar, Optional, List, Tuple, Generic

K = TypeVar('K')

V = TypeVar('V')

class LRUCache(Generic[K, V]):
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self._cache: OrderedDict[K, V] = OrderedDict()

    def get(self, key: K, default: Optional[V] = None) -> Optional[V]:
        if key in self._cache:
            value = self._cache.pop(key)
            self._cache[key] = value
            return value
        return default

    def put(self, key: K, value: V) -> None:
        if key in self._cache:
            self._cache.pop(key)
        elif len(self._cache) >= self.max_size:
            self._cache.popitem(last=False)
        self._cache[key] = value

    def remove(self, key: K) -> None:
        if key in self._cache:
            self._cache.pop(key)

    def clear(self) -> None:
        self._cache.clear()

    def __contains__(self, key: K) -> bool:
        return key in self._cache

    def __len__(self) -> int:
        return len(self._cache)

    def items(self) -> List[Tuple[K, V]]:
        return list(self._cache.items())

    def keys(self) -> List[K]:
        return list(self._cache.keys())

    def values(self) -> List[V]:
        return list(self._cache.values())
