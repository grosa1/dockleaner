from __future__ import annotations

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
from utils.dockerhub_api import get_latest_tag
import logging
logger = logging.getLogger(__name__.split('.')[0])
logger.setLevel(logging.DEBUG)


class DL3006(Strategy):
    """
    Rule DL3006 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3006

    Rationale:
        "You can never rely on the latest tags to be a specific version."
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        date = dockerfile.last_edit
        command_pos = smell_pos - 1
        lines = dockerfile.lines

        image_info = lines[command_pos].replace('\t', ' ', 1).split(' ')[1].strip()
        image = image_info.split(':')[0]
        tag = get_latest_tag(image)

        if tag:
            new_image = image + ':' + tag
            lines[command_pos] = lines[command_pos].replace(image_info, new_image, 1)
        else:
            logger.error(f'!!! Cannot solve DL3006 rule. Cannot found an equivalent version tag for "{image_info}"')
