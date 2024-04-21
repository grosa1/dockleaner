from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
from utils.docker_utils import is_valid_dockerfile_command, parse_dockerfile_str
from utils.common import parse_line_indent
import re
import logging
logger = logging.getLogger(__name__.split('.')[0])
logger.setLevel(logging.DEBUG)


class DL3009(Strategy):
    """
    Rule DL3009 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3009

    Rationale:
        "Cleaning up the apt cache and removing /var/lib/apt/lists helps keep the image size down.
        Since the RUN statement starts with apt-get update, the package cache will always be refreshed prior to apt-get
        install."

    Note:
        Only the last RUN command with apt-get install will be fixed. This avoids to run again apt update if there are
        subsequent instructions.
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        # Find latest "RUN apt-get install" position
        smelly_command = None
        command_end_pos = -1
        for line in dockerfile.parsed_lines.values():
            cmd = line.cmd
            value = line.value[0]
            if cmd == 'RUN' and \
                    "apt-get" in value and " install " in value:
                smelly_command = line
                command_end_pos = line.end_line - 1

        if not smelly_command or command_end_pos == -1:
            logger.error(f'!!! Cannot solve DL3009 rule. No fixable RUN command with apt-get install detected.')
            return

        # Check if apt-get clean and rm -rf /var/lib/apt/lists/* are already present
        is_apt_clean_present = False
        if 'apt-get clean' in smelly_command.value[0]:
            is_apt_clean_present = True

        is_rm_lists_present = False
        if re.search(r'rm -[a-zA-Z]+ /var/lib/apt/lists', smelly_command.value[0]):
            is_rm_lists_present = True

        if is_apt_clean_present and is_rm_lists_present:
            logger.info(f'!!! DL3009 rule already solved. No fix needed.')
            return

        line_indent = parse_line_indent(dockerfile.lines[command_end_pos])

        # determine if we need to add && at the end or beginning for concatenation
        if not dockerfile.lines[command_end_pos].startswith('RUN') and not dockerfile.lines[command_end_pos].lstrip().startswith('&&'):
            line_end = ' && \\' + '\n'
            clean_command = line_indent + 'apt-get clean && \\' + '\n'
            rm_command = line_indent + 'rm -rf /var/lib/apt/lists/*' + '\n'
        else:
            line_end = ' \\' + '\n'
            clean_command = line_indent + '&& apt-get clean \\' + '\n'
            rm_command = line_indent + '&& rm -rf /var/lib/apt/lists/*' + '\n'

        # Adding line end at the last RUN command
        if dockerfile.lines[command_end_pos].strip().endswith(';'):
            dockerfile.lines[command_end_pos] = dockerfile.lines[command_end_pos].rstrip()[:-1] + line_end
        else:
            dockerfile.lines[command_end_pos] = dockerfile.lines[command_end_pos].rstrip() + line_end

        insert_pos = command_end_pos + 1
        if not is_apt_clean_present:
            dockerfile.lines.insert(insert_pos, clean_command)
            insert_pos += 1

        if not is_rm_lists_present:
            dockerfile.lines.insert(insert_pos, rm_command)

        dockerfile.update_smells_dict()
