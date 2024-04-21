from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
import re


class DL3048(Strategy):
    """
    TODO:
    Rule DL3048 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3048

    Rationale:
        Invalid Label Key
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        smelly_cmd = dockerfile.parsed_lines[smell_pos]

        new_labels = list()
        labels = smelly_cmd.value
        for i in range(0, len(labels), 2):
            key = labels[i].strip()

            # Replace all non-`.` and non-`-` characters with `.`
            new_label = list()
            for c in key:
                if len(new_label) > 0:
                    if c.isalnum():
                        if new_label[-1].islower() and c.isupper():
                            new_label.append('-')
                            new_label.append(c)
                        else:
                            new_label.append(c)
                    elif new_label[-1] != c:
                        if c in ['-', '.']:
                            new_label.append(c)
                        else:
                            new_label.append('-')
                else:
                    if c.isalnum():
                        new_label.append(c)

            new_labels.append(f"{''.join(new_label).lower()}={labels[i + 1]}")

        new_labels = "LABEL " + " \\\n    ".join(new_labels)

        for i in range(smelly_cmd.start_line - 1, smelly_cmd.end_line):
            dockerfile.lines[i] = ""

        dockerfile.lines[smelly_cmd.start_line - 1] = new_labels + "\n"

        dockerfile.update_smells_dict()
