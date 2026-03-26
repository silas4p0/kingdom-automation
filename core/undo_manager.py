import copy
from typing import Any


class UndoManager:
    def __init__(self, max_history: int = 100) -> None:
        self._history: list[Any] = []
        self._redo_stack: list[Any] = []
        self._max = max_history

    def push(self, state: Any) -> None:
        self._history.append(copy.deepcopy(state))
        if len(self._history) > self._max:
            self._history.pop(0)
        self._redo_stack.clear()

    def undo(self) -> Any | None:
        if len(self._history) < 2:
            return None
        current = self._history.pop()
        self._redo_stack.append(current)
        return copy.deepcopy(self._history[-1])

    def redo(self) -> Any | None:
        if not self._redo_stack:
            return None
        state = self._redo_stack.pop()
        self._history.append(state)
        return copy.deepcopy(state)

    def can_undo(self) -> bool:
        return len(self._history) >= 2

    def can_redo(self) -> bool:
        return len(self._redo_stack) > 0
