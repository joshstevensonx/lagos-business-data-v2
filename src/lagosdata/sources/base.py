from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Iterable

class Source(ABC):
    name: str
    @abstractmethod
    def search(self, term: str, area: str) -> Iterable[dict]: ...
