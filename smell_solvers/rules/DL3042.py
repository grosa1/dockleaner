from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
from utils.docker_utils import is_valid_dockerfile_command


class DL3042(Strategy):
    """
    Rule DL3042 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3042

    Rationale:
        "Once a package is installed, it does not be installed and the Docker cache can be leveraged instead.
        Since the pip cache makes the images larger and is not needed, it's better to disable it."
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        lines = dockerfile.lines

        # Find pip install position
        position = smell_pos - 1
        for line in lines[position:]:
            if "pip" in line and " install " in line and not line.strip().startswith("#"):
                # Adding --no-cache-dir option
                if not '--no-cache-dir' in line:
                    option_pos = lines[position].find(' install ') + 8  # install chars number + space
                    lines[position] = lines[position][:option_pos] + " --no-cache-dir " + lines[position][option_pos:]
            elif position != (smell_pos - 1):
                term = line.strip().replace('\t', ' ', 1).split(' ')[0]
                if not line.strip() or is_valid_dockerfile_command(term):
                    break

            position += 1
