from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy


class DL3015(Strategy):
    """
    Rule DL3015 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3015

    Rationale:
        "Avoid installing additional packages that you did not explicitly want."

    Note:
        The DL3015 smell is fixed by adding the --no-install-recommends option to the apt-get install command.
        hadolint does not raise the smell when "apt" is used instead of "apt-get"
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        lines = dockerfile.lines

        # Find apt-get position and adding --no-install-recommends option
        position = smell_pos - 1
        for line in lines[position:]:
            if "apt-get" in line and " install " in line and "--no-install-recommends" not in line and not line.strip().startswith("#"):
                lines[position] = lines[position].replace(" install ", " install --no-install-recommends ")
            if "\\" in line:
                position += 1

