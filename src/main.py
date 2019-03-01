import coloredlogs,logging
import config
import resources
import database
import antiflood

from telegram.ext import Filters

import transcriberbot
from transcriberbot import TranscriberBot

coloredlogs.install(
  level='DEBUG',
  fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s [%(funcName)s:%(lineno)d] - %(message)s'
)
logger = logging.getLogger(__name__)

if __name__ == '__main__':
  config.init('../config')
  resources.init("../values")
  antiflood.init()
  transcriberbot.init()
  database.init_schema(config.get_config_prop("app")["database"])

  TranscriberBot.get().start(config.get_config_prop("telegram")["token"])