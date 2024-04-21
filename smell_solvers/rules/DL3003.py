from __future__ import annotations

import logging
import re

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy

logger = logging.getLogger(__name__.split('.')[0])
logger.setLevel(logging.DEBUG)


class DL3003(Strategy):
    """
    Rule DL3003 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3003

    Rationale:
        Only use cd in a subshell. Most commands can work with absolute paths and it in most cases not necessary to change
        directories. Docker provides the WORKDIR instruction if you really need to change the current working directory.

    Note:
        The commands composed with && are not fixed by this rule.
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        lines = dockerfile.lines

        position = smell_pos - 1

        prev_workdir = None
        for line in reversed(lines[:position]):
            if line.strip().startswith('WORKDIR'):
                prev_workdir = line.replace('WORKDIR', '').strip()
                break

        line = lines[position]
        if re.match("RUN +CD ", line.strip(), flags=re.IGNORECASE) is not None:
            if "&&" not in line:
                logger.info("Not &&")
                new_workdir = re.sub('RUN +CD', 'WORKDIR', line, count=1, flags=re.IGNORECASE)
                # check if the previous WORKDIR is the same as the new one
                if not new_workdir.replace('WORKDIR', '').strip() == prev_workdir:
                    lines[position] = new_workdir
                else:
                    lines[position] = ''
            else:
                logger.info("Yes &&")
                new_workdir = re.sub("RUN +CD", 'WORKDIR', line.split("&&")[0], count=1, flags=re.IGNORECASE) + "\n"
                # check if the previous WORKDIR is the same as the new one
                if not new_workdir.replace('WORKDIR', '').strip() == prev_workdir:
                    lines[position] = new_workdir
                else:
                    lines[position] = ''
                # check if the RUN command is on the next line
                if line.split("&&", 1)[1].strip().endswith("\\"):
                    lines[position + 1] = "RUN " + lines[position + 1].lstrip()
                else:
                    lines.insert(position + 1, "RUN " + line.split("&&", 1)[1])
                # logger.info(lines)

            dockerfile.update_smells_dict()
        else:
            logger.error("!!! Cannot solve DL3003 rule. The line does not match the format 'RUN cd ...'")
