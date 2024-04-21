from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
from utils.docker_utils import COMMANDS, parse_dockerfile_str


class DL3059(Strategy):
    """
    Rule DL3059 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3059

    Rationale:
        "Multiple consecutive RUN instructions. Consider consolidation."

    Note:
        The RUN instructions are not consolidated if they are separated by comments or other instructions.
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        command_pos = smell_pos - 1

        # find the previous RUN instruction
        prev_run_pos = -1
        for i in reversed(range(command_pos)):
            prev_line = dockerfile.lines[i].strip()
            if prev_line:
                if prev_line.startswith("#") or prev_line.startswith("RUN --"):
                    break
                elif prev_line.split(" ")[0] in COMMANDS:
                    if prev_line.startswith("RUN"):
                        prev_run_pos = i
                    else:
                        break

        # if there is a previous RUN instruction, consolidate the successive RUN instructions until a comment or other instruction is found
        if prev_run_pos > 0:
            i = prev_run_pos + 1
            while i < len(dockerfile.lines):
                line = dockerfile.lines[i].strip()
                # delete intermediate blank lines
                if not line and i+1 < len(dockerfile.lines) \
                        and dockerfile.lines[i + 1].startswith("RUN") and not dockerfile.lines[i + 1].startswith("RUN --"):
                    del dockerfile.lines[i]
                elif not line.startswith("#") and \
                        line.startswith("RUN") and not line.startswith("RUN --"):
                    if not dockerfile.lines[i - 1].endswith(" \\\n"):
                        dockerfile.lines[i - 1] = dockerfile.lines[i - 1].rstrip() + " \\\n"
                    dockerfile.lines[i] = dockerfile.lines[i].lstrip().replace("RUN", "    &&", 1)
                    i += 1
                else:
                    break

            dockerfile.update_smells_dict()
