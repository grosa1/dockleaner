from __future__ import annotations

import re

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy


class DL3020(Strategy):
    """
    Rule DL3020 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3020

    Rationale:
        "For other items (files, directories) that do not require ADD’s tar auto-extraction capability,
        you should always use COPY."
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        lines = dockerfile.lines

        position = smell_pos - 1
        line = lines[position]

        if line.strip().upper().startswith('ADD'):
            # Handle sensitive case replace
            lines[position] = re.sub(re.escape('ADD'), 'COPY', line, count=1, flags=re.IGNORECASE)
