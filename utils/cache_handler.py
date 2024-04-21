from __future__ import annotations

import os
import pickle
import sys

IMAGES_CACHE_PATH = sys.path[0] + '/.cache/images-version.cache'

def retrieve_distro(image: str) -> str:
    """
    Retrieve, if exists, the distribution info from the given image from the cache

    :param image_info: name and tag of the image. Expected format <image_name>:<image_tag>
    :return: the distribution info in the format <distro_name>:<distro_version>
             i.e. retrieve_distro(myimage:mytag) return 'ubuntu:14.04'
    """

    if not os.path.exists(IMAGES_CACHE_PATH):
        with open(IMAGES_CACHE_PATH, 'wb') as init_file:
            pickle.dump({}, init_file)  # init an empty cache
            pass
        return None
    
    with open(IMAGES_CACHE_PATH, 'rb') as file:
        data = file.read()
    
    cache = pickle.loads(data)

    if image in cache:
        return cache[image]


def update_images_cache(image: str, distro_info: str) -> None:
    """
    Update the cache of the pulled images with the given one

    :param image: name and tag of the image. Expected format <image_name>:<image_tag>
    :param distro_info: name and tag of the related distribution. Expected format <distro_name>:<distro_version>
    """

    with open(IMAGES_CACHE_PATH, 'rb') as f:
        data = f.read()
    
    cache = pickle.loads(data)
    cache[image] = distro_info
    
    with open(IMAGES_CACHE_PATH, 'wb') as f:
        pickle.dump(cache, f)


def clear_cache() -> None:
    """
    Clear the cache of the pulled images
    """
    with open(IMAGES_CACHE_PATH, 'wb') as init_file:
        pickle.dump({}, init_file)  # init an empty cache
