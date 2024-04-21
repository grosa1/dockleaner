from __future__ import annotations

import subprocess

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
from utils.docker_utils import validate_shell
import logging as logger


class DL4006(Strategy):
    """
    Rule DL4006 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL4006

    Rationale:
        "If you want the command to fail due to an error at any stage in the pipe, prepend set -o pipefail &&
        to ensure that an unexpected error prevents the build from inadvertently succeeding."
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        command_pos = smell_pos - 1
        lines = dockerfile.lines

        # Get nearest FROM
        for line in reversed(lines[:smell_pos]):
            if line.strip().upper().startswith('FROM'):
                near_from = line.strip().split(" ")[1]

        # set default shell and option
        path = '/bin/bash'
        option = '-o'

        # set ash if alpine or busybox
        if 'alpine' in near_from or 'busybox' in near_from:
            path = '/bin/ash'
            option = '-eo'

        logger.info("Validate shell {} for {}".format(path, near_from))
        if not validate_shell(near_from, path):
            # shell not found, fallback to default sh
            path = '/bin/sh'
            option = '-o'
            logger.warning("Validate fallback shell {}".format(path))
            has_basic_shell = validate_shell(near_from, path)
            if not has_basic_shell:
                logger.error("!!! Cannot fix DL4006. No valid shell found.")
                return

        new_line = f'SHELL ["{path}", "{option}", "pipefail", "-c"]' + '\n'
        lines.insert(command_pos, new_line)

        dockerfile.update_smells_dict(ignore=['DL4006'])

        # TODO: handle multi-stage Dockerfiles
