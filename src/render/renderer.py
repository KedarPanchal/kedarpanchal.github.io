from abc import ABC, abstractmethod
from types import SimpleNamespace


class Renderer(ABC):
    @abstractmethod
    def render(self, src: SimpleNamespace) -> None:
        pass


