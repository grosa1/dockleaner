from __future__ import annotations

import datetime as Date
import time
from datetime import datetime
import requests
from utils.dockerhub_api import get_latest_tag
from utils.common import request_data
import logging as logger
logger.getLogger('backoff').addHandler(logger.StreamHandler())


class LaunchpadAPIException(Exception):
    def __init__(self, msg='Launchpad API request failed', *args, **kwargs):
        super().__init__(msg, *args, **kwargs)


def get_distro_serie(distro: str, tag: str) -> str:
    """
    Retrieve the serie from the given distribution and tag.
    i.e. get_distro_serie('ubuntu', '20.04') returns 'focal'
    """

    api_url = 'https://api.launchpad.net/1.0/' + distro + '/series'

    try:
        response = request_data(api_url)
        response = response.json()
    except Exception as e:
        raise LaunchpadAPIException() from None

    series = response['entries']

    if series == 0: 
        return None
    
    # Get latest distro release tag
    if tag == 'latest':
        tag = get_latest_tag(distro)

    if '-' in tag:
        tag = tag.split('-')[0]

    for serie_json in series:
        if tag in serie_json['version'] or serie_json['version'] in tag or tag in serie_json['name']:
            return serie_json['name']
        
    return None


def get_package_binary_version(distro: str, distro_series: str, binary_name: str, date: datetime) -> str:
    """
    Retrieve the version of the given package.

    :param distro: the distribution of the package
    :param distro_series: the distro arch series of the given ubuntu distribution (e.g., precise, trusty, xenial, etc.
    :param binary_name: name of the package
    :param date: date of package release
    :return: version of the package
    """

    start_element = 0
    search_size = 100
    
    while True:
        # URL encoding 
        binary_name = requests.utils.quote(binary_name)

        api_url = 'https://api.launchpad.net/1.0/' + distro + '/+archive/primary?ws.start=' + str(start_element) \
                  + '&ws.size=' + str(search_size) \
                  + '&ws.op=getPublishedBinaries' \
                  + '&binary_name=' + binary_name \
                  + '&status=Published' \
                  + '&exact_match=true' \
                  + '&order_by_date=true'

        try:
            response = request_data(api_url)
            response = response.json()
        except Exception as e:
            raise LaunchpadAPIException() from None

        binaries_number = response['total_size']
        binaries = response['entries']

        if binaries_number == 0: 
            return None

        distro_arch_serie = 'https://api.launchpad.net/1.0/' + distro + '/' + distro_series
        for binary_json in binaries:
            if distro_arch_serie not in binary_json['distro_arch_series_link']:
                continue

            date_string = binary_json['date_published'].split('T')[0]
            parsed_date = Date.datetime.strptime(date_string, '%Y-%m-%d')
            pocket = binary_json['pocket']
            valid_pocket = (pocket != 'Proposed' and pocket != 'Backports')

            if date > parsed_date and valid_pocket:
                return binary_json['binary_package_version']

        start_element = start_element + search_size

        if start_element >= binaries_number:
            return None
        
        time.sleep(1)


def pkgs_repo_available(distro: str, distro_series: str) -> bool:
    """
    Check if the given distro is EOL

    :param distro: the name of the distribution (e.g. ubuntu)
    :param distro_series: the distro arch series of the given ubuntu distribution (e.g., precise, trusty, xenial, etc.
    :return: True if the distro is EOL, False otherwise
    """
    api_url = 'https://api.launchpad.net/1.0/{}/{}'.format(distro, distro_series)

    try:
        response = request_data(api_url)
        response = response.json()
    except Exception as e:
        raise LaunchpadAPIException() from None

    return response['active']