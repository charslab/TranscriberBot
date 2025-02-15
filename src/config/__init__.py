import os, glob
import json
import functional
import logging
import pprint

logger = logging.getLogger(__name__)

__configs = {}


def parse_file(file):
    logger.info("Loading config file %s", file)

    with open(file) as f:
        data = json.load(f)
    return data


def init(config_folder):
    global __configs
    files = glob.glob(os.path.join(config_folder, "*.json"))

    keys = [x.replace(config_folder, "").replace(".json", "").replace("/", "") for x in files]
    configs = map(parse_file, files)
    __configs = dict(zip(keys, configs))

    base = os.path.join(os.path.dirname(__file__), "../../")

    if not os.path.isabs(__configs['app']['database']):
        __configs['app']['database'] = os.path.join(base, __configs['app']['database'])

    if not os.path.isabs(__configs['app']['media_path']):
        __configs['app']['media_path'] = os.path.join(base, __configs['app']['media_path'])

    if not os.path.isdir(__configs['app']['media_path']):
        os.mkdir(__configs['app']['media_path'])


def get_config_prop(key):
    global __configs
    return __configs[key]


def bot_token():
    return get_config_prop("telegram")["token"]


def get_language_list():
    return get_config_prop("app")["languages"].keys()
