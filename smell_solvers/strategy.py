from __future__ import annotations

from abc import ABC, abstractmethod

from logic.dockerfile_obj import Dockerfile


class Strategy(ABC):
    """
    Abstract Class of the strategy adopted to solve a smell
    """

    @abstractmethod
    def fix(self, dockerfile: Dockerfile, smell_pos: int):
        pass
