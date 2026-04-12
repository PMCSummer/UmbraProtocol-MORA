from __future__ import annotations

import queue
import threading
from dataclasses import dataclass
from typing import Generic, TypeVar


T = TypeVar("T")


@dataclass(frozen=True, slots=True)
class QueueStats:
    pending: int
    in_flight: int
    completed: int


class CaseWorkQueue(Generic[T]):
    def __init__(self, items: list[T], *, id_getter) -> None:
        self._queue: queue.Queue[T] = queue.Queue()
        self._id_getter = id_getter
        self._lock = threading.Lock()
        self._in_flight: set[str] = set()
        self._completed: set[str] = set()
        for item in items:
            self._queue.put(item)

    def get(self, timeout: float = 0.1) -> T | None:
        try:
            item = self._queue.get(timeout=timeout)
        except queue.Empty:
            return None
        item_id = str(self._id_getter(item))
        with self._lock:
            if item_id in self._completed or item_id in self._in_flight:
                self._queue.task_done()
                return None
            self._in_flight.add(item_id)
        return item

    def mark_done(self, item: T) -> None:
        item_id = str(self._id_getter(item))
        with self._lock:
            self._in_flight.discard(item_id)
            self._completed.add(item_id)
        self._queue.task_done()

    def empty(self) -> bool:
        return self._queue.empty()

    def stats(self) -> QueueStats:
        with self._lock:
            return QueueStats(
                pending=self._queue.qsize(),
                in_flight=len(self._in_flight),
                completed=len(self._completed),
            )

