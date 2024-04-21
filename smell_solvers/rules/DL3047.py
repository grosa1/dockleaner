from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy


class DL3047(Strategy):
    """
    Rule DL3047 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3047

    Rationale:
        "wget without flag --progress will result in excessively bloated build logs when downloading larger files.
        That's because it outputs a line for each fraction of a percentage point while downloading a big file.
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        lines = dockerfile.lines

        # Find wget line position
        position = smell_pos - 1
        for line in lines[position:]:
            if 'wget' in line and not line.strip().startswith('#'):
                break
            position += 1

        # Get wget position in the found line
        wget_position = lines[position].find('wget')

        # Adding --progress=dot:giga option
        if not '--progress' in lines[position]:
            option_pos = wget_position + 4  # wget chars number
            lines[position] = lines[position][:option_pos] + ' --progress=dot:giga ' + lines[position][option_pos:]
