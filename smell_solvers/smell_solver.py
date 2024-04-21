from __future__ import annotations

import sys
from os import listdir
from os.path import isfile, join
from typing import List

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy

RULES_PATH = sys.path[0] + '/smell_solvers/rules'


class SmellSolver:
    """
    SmellSolver class offers the function to solve smells with Strategy design pattern
    """

    def __init__(self) -> None:
        self._strategy = None
        self._available_strategies = self.__load_strategies()

    @property
    def strategy(self) -> Strategy:
        return self._strategy

    @strategy.setter
    def strategy(self, strategy: Strategy) -> None:
        """
        Define the strategy of the smell to solve
        """
        self._strategy = strategy

    def fix_smell(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        """
        Fix the smell (previously set) in a specific line position of the given Dockerfile
        :param dockerfile: Dockerfile to fix
        :param smell_pos: position of the line containing the smell 
        :return: None
        """
        if self._strategy:
            self._strategy.fix(dockerfile, smell_pos)

    def strategy_exists(self, name: str) -> bool:
        """
        Check if the given strategy name is available
        :param name: name of the strategy to check
        :return: True/False
        """
        return name in self._available_strategies

    def __load_strategies(self) -> List[str]:
        """
        Search all the available strategies in the 'rules' folder
        :return: list of strings representing the existing strategies
        """
        return [f.split('.')[0] for f in listdir(RULES_PATH) if isfile(join(RULES_PATH, f))]
