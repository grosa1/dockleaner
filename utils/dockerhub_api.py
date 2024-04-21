from __future__ import annotations

import datetime as Date
import time
from datetime import datetime
from utils.common import request_data

API_REQUEST_SLEEP = 2


class DockerHubAPIException(Exception):
    def __init__(self, msg='DockerHub API request failed', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


class ImageNotFoundException(Exception):
    """Raised when no image is found in the registry"""
    def __init__(self, msg="No corresponding image found in the registry.", *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


def parse_image_path(image_name: str) -> str:
    image_path = image_name

    if image_path.startswith("docker.io/"):
        image_path = image_path.replace("docker.io/", "")
    
    if '/' not in image_path:
        image_path = 'library/' + image_path

    image_path = image_path.split("/")[-2] + '/' + image_path.split("/")[-1]

    return image_path


def get_image_version(image_name: str, date: datetime) -> str:
    """
    Retrieve the version of the given image from dockerhub registry.

    :param image_name: name of the image
    :param date: date of image last push in the registry
    :return: version of the image
    """

    start_page = 1
    checked_elements = 0
    search_size = 25

    image_path = parse_image_path(image_name)

    api_url = 'https://hub.docker.com/v2/repositories/' + image_path + \
              '/tags/?page_size=' + str(search_size) + '&page=' + str(start_page) + \
              '&ordering=last_updated'
    while api_url:
        try:
            response = request_data(api_url)
            if response.status_code == 404:
                raise ImageNotFoundException()
            response = response.json()
            api_url = response['next']
        except Exception as e:
            raise DockerHubAPIException(e) from None

        images = response['results']
        images_number = response['count']

        if images_number == 0:
            raise ImageNotFoundException()

        for image_json in images:
            date_string = image_json['tag_last_pushed'].split('T')[0]
            image_date = Date.datetime.strptime(date_string, '%Y-%m-%d')

            if date > image_date:
                return image_json['name']

        start_page += 1
        checked_elements += search_size

        if checked_elements >= images_number:
            return None

        time.sleep(API_REQUEST_SLEEP)


def get_latest_tag(image_name):
    """
    Retrieve the latest tag 'equivalent' of the given image from dockerhub registry.
    i.e. get_latest_tag(ubuntu) return 'focal' [in date 22/04/2021]

    :param image_name: name of the image.
                       If it's an official image, the username 'library/' is not needed.
                       Otherwise, the image_name has to be 'username/image'
    :return: latest tag equivalent of the image
    """

    image_path = parse_image_path(image_name)

    page = 1
    page_size = 25
    latest_found = False
    latest_digests = []

    alt_tag = None
    api_url = f'https://hub.docker.com/v2/repositories/{image_path}/tags/?' \
              f'page_size={str(page_size)}' \
              f'&page={str(page)}' \
              f'&ordering=last_updated'
    while api_url:
        try:
            response = request_data(api_url)
            if response.status_code == 404:
                raise ImageNotFoundException()
            response = response.json()
            api_url = response['next']
        except Exception as e:
            raise DockerHubAPIException(e) from None

        results = response['results']
        images_number = response['count']

        if images_number == 0:
            break

        if not latest_found:
            for result in results:
                # Find the digest of latest image
                if result['name'] == 'latest':
                    latest_found = True
                    for image in result['images']:
                        if image['architecture'] == 'amd64' and image["os"] == "linux":
                            latest_digests.append(image['digest'])
                    break

        for result in results:
            # Find the tag with the previous found digests
            temp_digests = []
            for image in result['images']:
                if image['digest'] in latest_digests and result['name'] != 'latest':
                    if result['name'][0].isdigit():
                        return result['name']
                    else:
                        alt_tag = result['name']  # set versions-less tag if there are no alternatives

        page += 1
        time.sleep(API_REQUEST_SLEEP)

    return alt_tag
