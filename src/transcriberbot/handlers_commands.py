import config
from database import TBDB
import resources as R

from transcriberbot import tbfilters
from transcriberbot.bot import TranscriberBot
from transcriberbot.bot import get_chat_id, get_message_id, get_language_list, welcome_message, command

from telegram.ext import Filters
from transcriberbot import tbfilters

import translator
import time
import traceback
import logging
logger = logging.getLogger(__name__)

@command(filters=tbfilters.chat_admin)
def start(bot, update):
  welcome_message(bot, update)

@command(filters=tbfilters.chat_admin)
def help(bot, update):
  welcome_message(bot, update)

@command(filters=tbfilters.chat_admin)
def lang(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(chat_id=chat_id, text=TBDB.get_chat_lang(chat_id))

@command(filters=tbfilters.chat_admin)
def rate(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("message_rate", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(tbfilters.chat_admin)
def disable_voice(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_voice_enabled(chat_id, 0)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("voice_disabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(tbfilters.chat_admin)
def enable_voice(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_voice_enabled(chat_id, 1)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("voice_enabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(tbfilters.chat_admin)
def voice_ask(bot, update):
  pass

@command(tbfilters.chat_admin)
def disable_photos(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_photos_enabled(chat_id, 0)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("photos_disabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(tbfilters.chat_admin)
def enable_photos(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_photos_enabled(chat_id, 1)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("photos_enabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(tbfilters.chat_admin)
def disable_qr(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_qr_enabled(chat_id, 0)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("qr_disabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(tbfilters.chat_admin)
def enable_qr(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_qr_enabled(chat_id, 1)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("qr_enabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command()
def translate(bot, update):
  chat_id = get_chat_id(update)
  message = update.message or update.channel_post
  if not message:
    return

  lang = message.text
  lang = lang.replace("/translate", "").strip()
  logger.debug("Language %s", lang)

  if lang not in config.get_config_prop("app")["languages"]:
    bot.send_message(
      chat_id=chat_id,
      text=R.get_string_resource("translate_language_not_found", TBDB.get_chat_lang(chat_id)).format(lang),
      is_group = chat_id < 0
    )
    return

  lang = config.get_config_prop("app")["languages"][lang].split('-')[0]

  if not message.reply_to_message:
    bot.send_message(
      chat_id=chat_id,
      text=R.get_string_resource("translate_reply_to_message", TBDB.get_chat_lang(chat_id)),
      is_group = chat_id < 0
    )
    return

  translation = translator.translate(
    source=TBDB.get_chat_lang(chat_id), 
    target=lang,
    text=message.reply_to_message.text
  )

  message.reply_text(translation)

@command(tbfilters.chat_admin)
def stats(bot, update):
  pass

@command(tbfilters.chat_admin)
def donate(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("message_donate", TBDB.get_chat_lang(chat_id)), 
    parse_mode="html",
    is_group = chat_id < 0
  )

@command(filters=None)
def privacy(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("privacy_policy", TBDB.get_chat_lang(chat_id)),
    parse_mode='html',
    is_group = chat_id < 0
  )

# Admins commands
@command(tbfilters.bot_admin)
def users(bot, update):
  chat_id = get_chat_id(update)
  tot_chats = TBDB.get_chats_num()
  active_chats = TBDB.get_active_chats_num()
  bot.send_message(
    chat_id=chat_id,
    text='Total users: {}\nActive users: {}'.format(tot_chats, active_chats),
    parse_mode='html',
    is_group=chat_id < 0
  )

@command(tbfilters.bot_admin)
def post(bot, update):
  chat_id = get_chat_id(update)
  text = update.message.text[6:]

  def __post():
    chats = TBDB.get_chats()
    sent = 0

    for chat in chats:
      try:
        bot.send_message(
          chat_id=chat['chat_id'],
          text=text,
          parse_mode='html',
          is_group=int(chat['chat_id']) < 0
        )
        sent += 1
        time.sleep(0.1)
      except Exception as e:
        logger.error(
          "Exception sending broadcast to %d: (%s) %s", 
          chat['chat_id'], e, traceback.format_exc())

    bot.send_message(
      chat_id=chat_id,
      text='Broadcast sent to {}/{} chats'.format(sent, len(chats)),
      is_group = chat_id < 0
    )
    TranscriberBot.get().command_handlers['users'](bot, update)
  
  TranscriberBot.get().misc_thread_pool.submit(__post)