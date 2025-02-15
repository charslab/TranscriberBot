import coloredlogs
import config
import resources
import database
import antiflood
import transcriberbot.bot
import transcriberbot.multiprocessing


def main():
    coloredlogs.install(
        level='INFO',
        fmt='%(asctime)s - %(name)s - %(levelname)s - %(filename)s [%(funcName)s:%(lineno)d] - %(message)s'
    )

    config.init('../config')
    transcriberbot.multiprocessing.init()
    print("VOICE POOL:", transcriberbot.multiprocessing.voice_pool())

    resources.init("../values")
    antiflood.init()
    database.init_schema(config.get_config_prop("app")["database"])

    transcriberbot.bot.run(config.bot_token())


if __name__ == '__main__':
    main()
