from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
import shlex
import re


class DL3025(Strategy):
    """
    Rule DL3025 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3025

    Rationale:
        Use arguments JSON notation for CMD and ENTRYPOINT arguments

    Note:
        The CMD or ENTRYPOINT instruction is formatted when fixing the smell by adding \n where && or ; are present
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        smelly_cmd = dockerfile.parsed_lines[smell_pos]

        new_cmd = list()
        for stmt in smelly_cmd.value:
            if stmt.startswith("[") and stmt.endswith("]"):
                stmt = " ".join(stmt[1:-1].split(","))
            lexer = shlex.shlex(stmt, posix=True)
            lexer.whitespace_split = True
            for t in lexer:
                t = re.sub(r'\s+', ' ', t.strip())
                t = t.replace('"', '\\"')
                new_cmd.append('"' + t + '"')

        line_indent = '    '
        new_cmd_str = f"{smelly_cmd.cmd} [{', '.join(new_cmd)}]"
        args = list()
        for c in new_cmd_str.split():
            args.append(c)
            if c == ';' or c == '&&' or c.endswith(';",') or c.endswith('&&",'):
                args.append('\\\n' + line_indent)

        new_cmd = ' '.join(args)

        # replace old command
        for i in range(smelly_cmd.end_line - smelly_cmd.start_line + 1):
            del dockerfile.lines[smelly_cmd.start_line - 1]

        dockerfile.lines.insert(smelly_cmd.start_line - 1, new_cmd + "\n")

        dockerfile.update_smells_dict()
