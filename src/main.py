import logging

import config
import resources
import database
import antiflood
import transcriberbot.bot


def main():
    config.init('../config')

    logging.addLevelName(config.APP_LOG, "APP")

    log_level = config.get_config_prop("app")["logging"]["level"]
    logging.basicConfig(
        format='%(asctime)s - %(name)s - %(levelname)s - %(filename)s [%(funcName)s:%(lineno)d] - %(message)s',
        level=log_level
    )
    logging.log(config.APP_LOG, "Setting log level to %s", log_level)

    resources.init("../values")
    antiflood.init()
    database.init_schema(config.get_config_prop("app")["database"])

    transcriberbot.bot.run(config.bot_token())


if __name__ == '__main__':
    main()
