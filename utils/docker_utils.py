from __future__ import annotations

from io import BytesIO
import docker
import dockerfile as dockerfile_parser
from utils.cache_handler import retrieve_distro, update_images_cache
from utils.launchpad_api import get_distro_serie
from typing import Dict
import logging
logger = logging.getLogger(__name__.split('.')[0])
logger.setLevel(logging.DEBUG)

COMMANDS = [c.upper() for c in dockerfile_parser.all_cmds()]
KNOWN_DISTROS = ["ubuntu"]


def get_distro_info(image_info: str) -> str:
    """
    Retrieve, if known, the distribution info from the given image

    :param image_info: name and tag of the image. Expected format <image_name>:<image_tag>
    :return: the distribution info in the format <distro_name>:<distro_series>
             i.e. get_distro_info(ubuntu:20.04) return 'ubuntu:focal'
                  get_distro_info(myimage:mytag) return 'ubuntu:trusty'
    """
    name, tag = image_info, 'latest'

    if ':' in image_info:
        name, tag = image_info.split(":")[0], image_info.split(":")[1]

    distro_info = ''
    if name.lower() not in KNOWN_DISTROS:
        distro_info = get_image_distro(image_info)

        name = distro_info.split(':')[0]
        tag = distro_info.split(':')[1]

        if name.lower() not in KNOWN_DISTROS:
            return None

    distro_serie = get_distro_serie(name, tag)

    return name + ':' + distro_serie if distro_serie else None


def get_image_distro(_image: str) -> str:
    """
    Pull the given image and retrieve the distribution info

    :param _image: name and tag of the image. Expected format <image_name>:<image_tag>
    :return: the distribution info in the format <distro_name>:<distro_version>
             i.e. get_distro_info(myimage:mytag) return 'ubuntu:14.04'
    """
    client = docker.from_env()

    # Check images cache
    # todo: not working, temporary disabled
    # distro_info = retrieve_distro(_image)
    #
    # if distro_info:
    #     return distro_info

    # Check already pulled image
    is_pulled = False
    for local_image in client.images.list():
        if _image in local_image.tags:
            is_pulled = True
            break

    if not is_pulled:
        logger.info('-> Pulling the image: ' + _image + '. This may take some time...')
        client.images.pull(_image)

    result = client.containers.run(_image, command="'cat /etc/os-release'", entrypoint="sh -c", remove=True)
    os_release = parse_os_release(result.decode())

    name = os_release["ID"] if "ID" in os_release else ""
    version = os_release["VERSION_ID"] if "VERSION_ID" in os_release else ""

    if not is_pulled:
        client.images.remove(_image, force=True)

    distro_info = name + ":" + version
    # Update cache
    # update_images_cache(_image, distro_info)  # todo: not working, temporary disabled

    return distro_info


def parse_os_release(os_release: str) -> Dict:
    """
    Parse the given os-release file content and return a dictionary containing the info

    :param os_release: os-release file content
    :return: a dictionary containing the info
    """
    parsed_dict = dict()
    for line in os_release.splitlines():
        if '=' in line:
            key, value = line.split('=', 1)
            key = key.strip()
            value = value.strip()
            if value.startswith('"') and value.endswith('"'):
                value = value[1:-1]
            parsed_dict[key] = value

    return parsed_dict


def get_package_version(container, package) -> str:
    """
    Pull the given image and retrieve the distribution info

    :param _image: name and tag of the image. Expected format <image_name>:<image_tag>
    :return: the distribution info in the format <distro_name>:<distro_version>'
    """
    result = str(container.exec_run(f'apt-cache madison {package}'))
    if result.strip():
        result = result.split('\n')[0].split('|')[1].strip()

    return result


def validate_package(_image: str, package: str) -> int:
    """
    :param _image: name and tag of the image. Expected format <image_name>:<image_tag>
    :return: the distribution info in the format <distro_name>:<distro_version>'
    """
    """
    global container
    print(package)
    result = str(container.exec_run(f'DEBIAN_FRONTEND=newt apt-get install -y {package}'))
    print(result)
    return int(result.split(',')[0].split('exit_code=')[1])
    """
    client = docker.from_env()

    dockerfile_str = 'FROM {}\nRUN apt-get update\nRUN yes | DEBIAN_FRONTEND=noninteractive apt-get install -yqq {}'.format(_image, package)
    try:
        client.images.build(fileobj=BytesIO(dockerfile_str.encode("utf-8")), tag='fix', rm=True, forcerm=True)
        client.images.remove(image='fix', force=True)
        return 0
    except Exception as e:
        logger.error(e)
        return 100


def validate_shell(_image: str, shell_bin_path: str) -> int:
    client = docker.from_env()

    dockerfile_str = 'FROM {}\nRUN which {}'.format(_image, shell_bin_path)
    try:
        client.images.build(fileobj=BytesIO(dockerfile_str.encode("utf-8")), tag='fix', rm=True, forcerm=True)
        client.images.remove(image='fix', force=True)
        return True
    except Exception as e:
        logger.error(e)
        return False


def is_valid_dockerfile_command(command: str) -> bool:
    """
    Check if the given string is a valid Dockerfile command

    :param command: name of the command
    :return: True/False
    """
    return command in COMMANDS


def parse_dockerfile_str(dockerfile_str) -> Dict:
    parsed_dict = dict()
    for cmd in dockerfile_parser.parse_string(dockerfile_str):
        parsed_dict[cmd.start_line] = cmd

    return parsed_dict
