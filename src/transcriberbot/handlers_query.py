import config
from database import TBDB
import resources as R

from transcriberbot import tbfilters
from transcriberbot.bot import TranscriberBot
from transcriberbot.bot import get_chat_id, get_message_id, get_language_list, callback_query

from telegram.ext import Filters
from transcriberbot import tbfilters

import logging
logger = logging.getLogger(__name__)

@callback_query
def stop(bot, update):
  query = update.callback_query

  TranscriberBot.get().stop_thread(query.data)
  logger.debug("Stopping thread %s", query.data)
  logger.debug("Thread %s running: %r", query.data, TranscriberBot.get().thread_running(query.data))

  string_stopped = R.get_string_resource(
    "transcription_stopped", 
    TBDB.get_chat_lang(query.message.chat_id)
  )

  bot.edit_message_text(
    text=query.message.text + " " + string_stopped,
    chat_id=query.message.chat_id,
    message_id=query.message.message_id,
    parse_mode="html",
    is_group=query.message.chat_id < 0
  )