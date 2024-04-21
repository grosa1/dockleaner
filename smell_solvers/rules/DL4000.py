from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
from utils.common import dequote
import re

class DL4000(Strategy):
    """
    Rule DL4000 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL4000

    Rationale:
        "MAINTAINER is deprecated since Docker 1.13.0"
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        command_pos = -1
        maintainers = list()
        for line in dockerfile.parsed_lines.values():
            if line.cmd.lower() == 'maintainer':
                if command_pos == -1 or line.start_line - 1 < command_pos:
                    command_pos = line.start_line - 1
                for m in re.split(r'\s{2,}', line.value[0]):
                    maintainers.append(dequote(m.strip()))
                for i in range(line.start_line - 1, line.end_line):
                    dockerfile.lines[i] = ""
                dockerfile.lines[i] = "\n"

        if maintainers:
            dockerfile.lines[command_pos] = f'LABEL maintainer="{", ".join(maintainers)}"\n'
            dockerfile.update_smells_dict()

