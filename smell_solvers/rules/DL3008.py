from __future__ import annotations

import logging
import re
from datetime import datetime

from logic.dockerfile_obj import Dockerfile
from smell_solvers.strategy import Strategy
from utils.docker_utils import get_distro_info, is_valid_dockerfile_command, validate_package
from utils.launchpad_api import get_package_binary_version, pkgs_repo_available

logger = logging.getLogger(__name__.split('.')[0])
logger.setLevel(logging.DEBUG)


class DL3008(Strategy):
    """
    Rule DL3008 solver

    Reference:
        https://github.com/hadolint/hadolint/wiki/DL3008

    Rationale:
        "Version pinning forces the build to retrieve a particular version regardless of what’s in the cache.
        This technique can also reduce failures due to unanticipated changes in required packages."

    Note:
        It actually works only with ubuntu-based images.
        TODO: Can be improved by using the package manager of the image to get package versions (apt-cache madison <package>)
        TODO:/bin/bash -c "apt-get update && apt-cache madison \$(apt-cache search '' | sort -d | awk '{print \$1}')"
    """

    def fix(self, dockerfile: Dockerfile, smell_pos: int) -> None:
        date = dockerfile.last_edit
        lines = dockerfile.lines

        # Get nearest FROM
        for line in reversed(lines[:smell_pos]):
            if line.strip().upper().startswith('FROM'):
                image_info = line.strip().split(" ")[1]

        # Get distro info
        distro_info = get_distro_info(image_info)
        if not distro_info:
            logger.error(f'!!! Cannot solve DL3008 rule. OS not supported "{image_info}"')
            return

        distro = distro_info.split(':')[0]
        serie = distro_info.split(':')[1]

        if not pkgs_repo_available(distro, serie):
            logger.error(f'!!! Cannot solve DL3008 rule. Package repositories not available for "{image_info}"')
            return

        # Find apt-get position
        position = smell_pos - 1
        for line in lines[position:]:
            if "apt-get" in line and " install " in line and not line.strip().startswith("#"):
                break
            position += 1

        # Find apt-get install position
        splitted_line = lines[position].split("apt-get")
        install_position = 0
        for splitted_part in splitted_line:
            if " install " in splitted_part:
                break
            else:
                install_position += 1

        # Get packages after install and remove \n from package name
        words = splitted_line[install_position].split(" install ")[1].strip().split(" ")

        while True:
            word = words.pop(0)

            if word.startswith('"') and word.endswith('"') or word.startswith("'") and word.endswith("'"):
                word = word[1:-1]

            if '\t' in word:  # Remove tab char and get clean packages
                for splitted_word in word.split('\t'):
                    words.insert(0, splitted_word)

            if self.__is_stop_word(word):
                break
            elif word.startswith('`'):  # Consume ` command execution `
                while len(words) > 0 and not word.endswith('`'):
                    word = words.pop(0)

            elif word == '\\':
                position += 1
                # Escape comments
                while len(lines) > position and lines[position].strip().startswith('#'):
                    position += 1

                if len(lines) > position:
                    next_line = lines[position]
                    words = next_line.strip().split(" ")
            elif self.__is_unpinned_package(word):
                # Line cleaning
                # lines[position] = lines[position].replace("\t", "    ")
                lines[position] = lines[position].rstrip() + '\n'
                pinned = self.__pin_package(image_info, distro, serie, word, date)
                lines[position] = lines[position].replace(f"{word}", f"{pinned}", 1)

            if len(words) == 0:
                break

    def __is_unpinned_package(self, package_name: str) -> bool:
        """
        Check if the given package name is unpinned.
        Note: Package names like "dotnet-runtime-6.0" are seen as "pinned"
        """
        return ('=' not in package_name and \
                not package_name.startswith('-') and \
                not is_valid_dockerfile_command(package_name) and \
                bool(re.match(r"[a-z,A-Z,0-9,.,+,-]+\Z", package_name)) and \
                package_name != '')

    def __is_stop_word(self, stop_word: str) -> bool:
        return ';' in stop_word or '&' in stop_word or is_valid_dockerfile_command(stop_word)

    def __pin_package(self, image_info: str, distro: str, serie: str, package_name: str, date: datetime) -> str:
        pinned_package = package_name
        version = get_package_binary_version(distro, serie, package_name, date)

        if version:
            rnum = 2
            while rnum >= 0:
                version = self.__format_version(version, rnum)
                if not version:
                    logger.error(f'!!! Cannot pin version to {package_name}.')
                    return package_name

                pinned_package = package_name + '=' + version
                status = validate_package(image_info, pinned_package)
                if status == 100:
                    rnum -= 1
                else:
                    logger.info(f'Pinned: {pinned_package}')
                    break
        else:
            logger.error(f'!!! Cannot pin version to {package_name}. Package not found.')

        return pinned_package

    def __format_version(self, version: str, rnum: int) -> str:
        """
        Format the given version inserting the '*' char at the given rnum position
        :param version: version to format
        :param rnum: the position to overwrite. If rnum is 2, PATCH release is overwritten, if 1 MINOR release...
        I.e. __format_version('2.13.4', 2) returns '2.13.*' (The PATCH release is overwritten)
        """
        if rnum <= 0:
            # return '*'
            return None

        snum = 0

        # first_symbol = re.findall('[.-:+~]',version)[0]
        for count, char in enumerate(version):
            if snum == rnum:
                return version[:count] + '*'

            if char == '.' or char == '-' or (char == ':' and snum != 0) or char == '+':
                snum += 1

        return version

# todo fix install multipli su singola linea - example11