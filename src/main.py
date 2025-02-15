import coloredlogs
import config
import resources
import database
import antiflood
import transcriberbot.bot


def main():
    coloredlogs.install(
        level='DEBUG',
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s [%(funcName)s:%(lineno)d] - %(message)s'
    )

    config.init('../config')
    resources.init("../values")
    antiflood.init()
    database.init_schema(config.get_config_prop("app")["database"])

    transcriberbot.bot.run(config.bot_token())


if __name__ == '__main__':
    main()
