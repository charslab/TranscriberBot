import logging

import config
import resources
import database
import antiflood
import transcriberbot.bot
import sentry_sdk
from sentry_sdk.integrations.asyncio import AsyncioIntegration

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

    sentry_sdk.init(
        dsn=config.get_config_prop("sentry")["dsn"],
        # Add data like request headers and IP for users, if applicable;
        # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
        send_default_pii=True,
        # Set traces_sample_rate to 1.0 to capture 100%
        # of transactions for tracing.
        traces_sample_rate=1.0,
        # Set profiles_sample_rate to 1.0 to profile 100%
        # of sampled transactions.
        # We recommend adjusting this value in production.
        profiles_sample_rate=1.0,
        integrations=[
            AsyncioIntegration(),
        ],
    )

    sentry_sdk.profiler.start_profiler()
    transcriberbot.bot.run(config.bot_token())


if __name__ == '__main__':
    main()
