"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import logging
import config
from concurrent.futures import ThreadPoolExecutor

voice_thread_pool, photos_thread_pool, misc_thread_pool = None, None, None


def init():
    global voice_thread_pool
    global photos_thread_pool
    global misc_thread_pool

    voice_thread_pool = ThreadPoolExecutor(
        max_workers=config.get_config_prop("app")["voice_max_threads"]
    )
    photos_thread_pool = ThreadPoolExecutor(
        max_workers=config.get_config_prop("app")["photos_max_threads"]
    )

    misc_thread_pool = ThreadPoolExecutor(
        max_workers=2
    )

    print("POOLS INITIALIZED:", voice_thread_pool, photos_thread_pool, misc_thread_pool)
    logging.info("Thread pools initialized")


def voice_pool():
    global voice_thread_pool
    return voice_thread_pool
