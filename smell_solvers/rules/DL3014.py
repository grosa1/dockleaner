from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy


class DL3014(Strategy):
    """
    Rule DL3014 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3014

    Rationale:
        "Without the --assume-yes option it might be possible that the build breaks without human intervention."
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        lines = dockerfile.lines

        # Find apt-get position
        position = smell_pos - 1
        for line in lines[position:]:
            if "apt-get" in line and " install " in line and not line.strip().startswith("#"):
                break
            position += 1

        # Get apt-get install position
        splitted_line = lines[position].split("apt-get")

        install_position = 0
        for splitted_part in splitted_line:
            if " install " in splitted_part:
                break
            else:
                install_position += 1

                # Adding --no-install-recommends option
        if not '-y' in splitted_line[install_position]:
            option_pos = splitted_line[install_position].find(' install ') + 8  # install chars number + space
            splitted_line[install_position] = splitted_line[install_position][:option_pos] + " -y " + splitted_line[
                                                                                                          install_position][
                                                                                                      option_pos:]

            # Update lines
            lines[position] = "apt-get".join(splitted_line)
