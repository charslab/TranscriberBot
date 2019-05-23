import config
import database
import resources as R
import metaclass
import functional 
import audiotools
import phototools
import pprint
import logging
import os
import traceback
import telegram
import time
import antiflood
import translator

from datetime import datetime

from database import TBDB
from telegram.ext import Updater, CommandHandler, MessageHandler, CallbackQueryHandler, Filters
from telegram.ext import messagequeue as mq
from telegram.utils.request import Request
from telegram.error import Unauthorized

from concurrent.futures import ThreadPoolExecutor

from transcriberbot import tbfilters
from transcriberbot.channel_command_handler import ChannelCommandHandler

logger = logging.getLogger(__name__)

# Utils
def get_language_list():
  return config.get_config_prop("app")["languages"].keys()

def get_chat_id(update):
  chat_id = None
  if update.message is not None:
    chat_id = update.message.chat.id
  elif update.channel_post is not None:
    chat_id = update.channel_post.chat.id
  return chat_id

def get_message_id(update):
  if update.message is not None:
    return update.message.message_id
  elif update.channel_post is not None:
    return update.channel_post.message_id

  return None

class TranscriberBot(metaclass=metaclass.Singleton):
  class MQBot(telegram.bot.Bot):
    def __init__(self, *args, is_queued_def=True, mqueue=None, **kwargs):
      super().__init__(*args, **kwargs)
      self._is_messages_queued_default = is_queued_def
      self._msg_queue = mqueue or mq.MessageQueue()

      chats = TBDB.get_chats()
      self.active_chats_cache = dict(zip(
        [c['chat_id'] for c in chats], 
        [c['active'] for c in chats]
      ))

    def __del__(self):
      try:
        self._msg_queue.stop()
      except:
        pass
      super().__del__()

    def active_check(self, fn, *args, **kwargs):
      err = None
      res = None

      try:
        res = fn(*args, **kwargs)
      except Unauthorized as e:
        pprint.pprint(e)
        logger.error(e)
        err = e

      if err is not None:
        chat_id = kwargs['chat_id']
        if chat_id not in self.active_chats_cache or self.active_chats_cache[chat_id] == 1:
          logger.debug("Marking chat {} as inactive".format(chat_id))
          self.active_chats_cache[chat_id] = 0
          TBDB.set_chat_active(chat_id, self.active_chats_cache[chat_id])
        raise err

      return res

    @mq.queuedmessage
    def send_message(self, *args, **kwargs):
      return self.active_check(super().send_message, *args, **kwargs)

    @mq.queuedmessage
    def edit_message_text(self, *args, **kwargs):
      return self.active_check(super().edit_message_text, *args, **kwargs)

  def __init__(self):
    self.error_handler = None
    self.message_handlers = {}
    self.command_handlers = {}
    self.callback_handlers = {}
    self.floods = {}
    self.workers = {}

    antiflood.register_flood_warning_callback( 
      lambda chat_id: TranscriberBot.get().bot().send_message(
        chat_id=chat_id,
        text=R.get_string_resource("flood_warning", TBDB.get_chat_lang(chat_id)),
        parse_mode = "html",
        is_group = chat_id < 0
      )
    )

    def flood_started(chat_id):
      logger.info("Flood detected in %d, ignoring messages", chat_id)
      self.floods[chat_id] = True

    def flood_ended(chat_id):
      logger.info("Flood ended for %d", chat_id)
      self.floods[chat_id] = False

    antiflood.register_flood_started_callback(flood_started)
    antiflood.register_flood_ended_callback(flood_ended)
  
  @staticmethod
  def get():
    return TranscriberBot()  

  def bot(self):
    return self.mqbot

  def start(self, token):
    self.voice_thread_pool = ThreadPoolExecutor(
      max_workers=config.get_config_prop("app")["voice_max_threads"]
    )
    self.photos_thread_pool = ThreadPoolExecutor(
      max_workers=config.get_config_prop("app")["photos_max_threads"]
    )

    self.misc_thread_pool = ThreadPoolExecutor(
      max_workers=2
    )

    self.queue = mq.MessageQueue()
    self.request = Request(con_pool_size=10)
    self.mqbot = self.MQBot(token, request=self.request, mqueue=self.queue)
    self.updater = Updater(bot=self.mqbot)
    self.dispatcher = self.updater.dispatcher
    self.__register_handlers()
    self.updater.start_polling(clean=True)
    self.updater.idle()

  def register_message_handler(self, filter, fn):
    self.message_handlers[filter] = fn

  def register_command_handler(self, fn, filters=None):
    self.command_handlers[fn.__name__] = (fn, filters)

  def register_callback_handler(self, fn):
    self.callback_handlers[fn.__name__] = fn

  def start_thread(self, id):
    self.workers[str(id)] = True

  def stop_thread(self, id):
    self.workers[str(id)] = False

  def thread_running(self, id):
    return self.workers[str(id)]

  def del_thread(self, id):
    del self.workers[str(id)]

  def __add_handler(self, handler):
    self.dispatcher.add_handler(handler)

  def __add_error_handler(self, handler):
    self.dispatcher.add_error_handler(handler)

  def __pre__hook(self, fn, b, u, **kwargs):
    m = u.message or u.channel_post
    if not m:
      return

    age = (datetime.now() - m.date).total_seconds() 
    if age > config.get_config_prop("app")["antiflood"]["age_threshold"]:
      return

    chat_id = get_chat_id(u)
    antiflood.on_chat_msg_received(chat_id)

    if chat_id in self.floods and self.floods[chat_id] is True:
      return

    if not TBDB.get_chat_entry(chat_id):
      # happens when welcome/joined message is not received
      TBDB.create_default_chat_entry(chat_id, 'en-US')
      
    if chat_id in self.mqbot.active_chats_cache and self.mqbot.active_chats_cache[chat_id] == 0:
      logger.debug("Marking chat {} as active".format(chat_id))
      self.mqbot.active_chats_cache[chat_id] = 1
      TBDB.set_chat_active(chat_id, self.mqbot.active_chats_cache[chat_id])

    return fn(b, u, **kwargs)

  def __register_handlers(self):
    functional.apply_fn(
      self.message_handlers.items(), 
      lambda h: self.__add_handler(MessageHandler(
        h[0], 
        lambda b, u, **kwargs: self.__pre__hook(h[1], b, u, **kwargs)))
    )

    functional.apply_fn(
      self.command_handlers.items(), 
      lambda h: self.__add_handler(ChannelCommandHandler(
        h[0], 
        lambda b, u, **kwargs: self.__pre__hook(h[1][0], b, u, **kwargs),
        filters=h[1][1]))
    )

    functional.apply_fn(
      self.callback_handlers.items(),
      lambda h: self.__add_handler(CallbackQueryHandler(h[1]))
    )

# Decorators for adding callbacks
def message(filter):
  def decor(fn):
    TranscriberBot.get().register_message_handler(filter, fn)
  return decor

def command(filters=None):
  def decor(fn):
    TranscriberBot.get().register_command_handler(fn, filters)
  return decor

def callback_query(fn):
  TranscriberBot.get().register_callback_handler(fn)

# Install language command callbacks
def language_handler(bot, update, language):
  chat_id = get_chat_id(update)
  lang = config.get_config_prop("app")["languages"][language] #ISO 639-1 code for language
  TBDB.set_chat_lang(chat_id, lang)
  message = R.get_string_resource("language_set", lang).replace("{lang}", language)
  reply = update.message or update.channel_post
  reply.reply_text(message)

def install_language_handlers(language):
  handler = lambda b, u: language_handler(b, u, language)
  handler.__name__ = language
  TranscriberBot.get().register_command_handler(handler, filters=tbfilters.chat_admin)

# Init
def init():
  functional.apply_fn(get_language_list(), install_language_handlers)

def welcome_message(bot, update):
  chat_id = get_chat_id(update)
  message_id = get_message_id(update)
  chat_record = TBDB.get_chat_entry(chat_id)

  language = None
  if chat_record is not None:
    language = chat_record["lang"]
  elif update.message is not None and update.message.from_user.language_code is not None:
    # Channel posts do not have a language_code attribute
    logger.debug("Language_code: %s", update.message.from_user.language_code)
    language = update.message.from_user.language_code
  
  message = R.get_string_resource("message_welcome", language)
  message = message.replace("{languages}", "/" + "\n/".join(get_language_list())) #Format them to be a list of commands
  bot.send_message(
    chat_id=chat_id, 
    text=message, 
    reply_to_message_id = message_id, 
    parse_mode = "html",
    is_group = chat_id < 0
  )

  if chat_record is None:
    if language is None:
      language = "en-US"

    if len(language) < 5:
      language = R.iso639_2_to_639_1(language)
    
    logger.debug("No record found for chat {}, creating one with lang {}".format(chat_id, language))
    TBDB.create_default_chat_entry(chat_id, language)