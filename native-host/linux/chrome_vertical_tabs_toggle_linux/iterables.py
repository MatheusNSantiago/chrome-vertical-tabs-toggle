from collections.abc import Callable, Iterable
from typing import TypeVar

Item = TypeVar("Item")


def find(items: Iterable[Item], predicate: Callable[[Item], bool]) -> Item | None:
    for item in items:
        if predicate(item):
            return item
