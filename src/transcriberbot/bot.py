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
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
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

      self.active_chats_cache = {}

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

  def register_command_handler(self, fn, bypass_admin_check=False):
    self.command_handlers[fn.__name__] = (fn, bypass_admin_check)

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
    
    admin_filter = tbfilters.FilterIsAdmin(self.mqbot)

    functional.apply_fn(
      self.command_handlers.items(), 
      lambda h: self.__add_handler(ChannelCommandHandler(
        h[0], 
        lambda b, u, **kwargs: self.__pre__hook(h[1][0], b, u, **kwargs),
        filters=admin_filter if h[1][1] is False else None))
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

def command(bypass_admin_check=False):
  def decor(fn):
    TranscriberBot.get().register_command_handler(fn, bypass_admin_check)
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
  TranscriberBot.get().register_command_handler(handler)

# Init
def init():
  functional.apply_fn(get_language_list(), install_language_handlers)

# Message callbacks
@message(Filters.text & Filters.private)
def private_message(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(
    chat_id=chat_id, 
    text=R.get_string_resource("message_private", TBDB.get_chat_lang(chat_id))
  )

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

def transcribe_audio_file(bot, update, path):
  chat_id = get_chat_id(update)
  lang = TBDB.get_chat_lang(chat_id)
  message_id = get_message_id(update)
  is_group = chat_id < 0

  message = bot.send_message(
    chat_id=chat_id, 
    text=R.get_string_resource("transcribing", lang) + "\n",
    reply_to_message_id=message_id,
    parse_mode="html",
    is_group=is_group
  ).result()
  
  TranscriberBot.get().start_thread(message_id)
  logger.debug("Starting thread %d", message_id)

  keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton("Stop", callback_data=message_id)]]
  )

  text = R.get_string_resource("transcription_text", lang) + "\n"
  success = False
  for speech in audiotools.transcribe(path, lang):
    logger.debug("Thread %d running: %r", message_id, TranscriberBot.get().thread_running(message_id))
    if TranscriberBot.get().thread_running(message_id) is False:
      TranscriberBot.get().del_thread(message_id)
      return

    retry = True
    retry_num = 0

    while retry and TranscriberBot.get().thread_running(message_id):
      try:
        if len(text + speech) >= 4080:
          text = R.get_string_resource("transcription_continues", lang) + "\n"
          message = bot.send_message(
            chat_id=chat_id,
            text=text + speech + " <b>[..]</b>",
            reply_to_message_id=message.message_id,
            parse_mode="html",
            is_group=is_group,
            reply_markup=keyboard
          ).result()
        else:
          message = bot.edit_message_text(
            text=text + speech + " <b>[..]</b>", 
            chat_id=chat_id, 
            message_id=message.message_id,
            parse_mode="html",
            is_group=is_group,
            reply_markup=keyboard
          ).result()

        text += speech
        retry = False
        success = True

      except telegram.error.TimedOut as t:
        logger.error("Timeout error %s", traceback.format_exc())
        retry_num += 1
        if retry_num >= 3:
          retry = False
      
      except telegram.error.RetryAfter as r:
        logger.warning("Retrying after %d", r.retry_after)
        time.sleep(r.retry_after)

      except telegram.error.TelegramError as te:
        logger.error("Telegram error %s", traceback.format_exc())
        retry = False

      except Exception as e:
        logger.error("Exception %s", traceback.format_exc())
        retry = False

  retry = True
  retry_num = 0
  while retry and TranscriberBot.get().thread_running(message_id):
    try:
      if success:
        bot.edit_message_text(
          text=text, 
          chat_id=chat_id, 
          message_id=message.message_id,
          parse_mode="html",
          is_group=is_group
        )
      else:
        bot.edit_message_text(
          R.get_string_resource("transcription_failed", lang),
          chat_id=chat_id,
          message_id=message.message_id,
          parse_mode="html",
          is_group=is_group
        )
      retry = False
    except telegram.error.TimedOut as t:
      logger.error("Timeout error %s", traceback.format_exc())
      retry_num += 1
      if retry_num >= 3:
        retry = False
    
    except telegram.error.RetryAfter as r:
      logger.warning("Retrying after %d", r.retry_after)
      time.sleep(r.retry_after)

    except telegram.error.TelegramError as te:
      logger.error("Telegram error %s", traceback.format_exc())
      retry = False

    except Exception as e:
      logger.error("Exception %s", traceback.format_exc())
      retry = False 

  TranscriberBot.get().del_thread(message_id)

def process_media_voice(bot, update, media, name):
  chat_id = get_chat_id(update)
  file_id = media.file_id
  file_path = os.path.join(config.get_config_prop("app")["media_path"], file_id)
  file = bot.get_file(file_id)
  file.download(file_path)
  
  try:
    transcribe_audio_file(bot, update, file_path)
  except Exception as e:
    logger.error("Exception handling %s from %d: %s", name, chat_id, traceback.format_exc())
    
  finally:
    os.remove(file_path)

@message(Filters.voice)
def voice(bot, update):
  chat_id = get_chat_id(update)
  voice_enabled = TBDB.get_chat_voice_enabled(chat_id)
  if voice_enabled == 0:
    return
  
  v = None
  if update.message is not None:
    v = update.message.voice
  elif update.channel_post is not None:
    v = update.channel_post.voice
  file_id = v.file_id 

  if voice_enabled == 2:
    pass
  else:
    TranscriberBot.get().voice_thread_pool.submit(
      process_media_voice, bot, update, v, "voice"
    )

@message(Filters.audio)
def audio(bot, update):
  chat_id = get_chat_id(update)
  voice_enabled = TBDB.get_chat_voice_enabled(chat_id)

  if voice_enabled == 0:
    return

  a = None
  if update.message is not None:
    a = update.message.audio
  elif update.channel_post is not None:
    a = update.channel_post.audio
  
  if voice_enabled == 2:
    pass
  else:
    TranscriberBot.get().voice_thread_pool.submit(
      process_media_voice, bot, update, a, "audio"
    )

@message(Filters.video_note)
def video_note(bot, update):
  chat_id = get_chat_id(update)
  voice_enabled = TBDB.get_chat_voice_enabled(chat_id)

  if voice_enabled == 0:
    return

  vn = None
  if update.message is not None:
    vn = update.message.video_note
  elif update.channel_post is not None:
    vn = update.channel_post.video_note
  
  if voice_enabled == 2:
    pass
  else:
    TranscriberBot.get().voice_thread_pool.submit(
      process_media_voice, bot, update, vn, "video_note"
    )

def process_media_photo(bot, update, photo, chat):
  chat_id = get_chat_id(update)
  message_id = get_message_id(update)
  is_group = chat_id < 0

  message = None

  if chat["photos_enabled"] == 1:
    message = bot.send_message(
      chat_id=chat_id, 
      text=R.get_string_resource("photo_recognizing", chat["lang"]), 
      reply_to_message_id=message_id,
      parse_mode="html",
      is_group=is_group
    ).result()

  file_id = photo[-1].file_id
  file_path = os.path.join(config.get_config_prop("app")["media_path"], file_id)
  bot.get_file(file_id).download(file_path)

  def process(message):
    if chat["qr_enabled"] == 1:
      qr = phototools.read_qr(file_path, chat["lang"])
      if qr is not None:
        qr = R.get_string_resource("qr_result", chat["lang"]) + "\n" + qr

        if message is not None:
          bot.edit_message_text(
            text=qr, 
            chat_id=chat_id, 
            message_id=message.message_id, 
            parse_mode="html", 
            is_group=is_group
          )
          return
        else:
          message = bot.send_message(
            chat_id=chat_id,
            text=qr,
            reply_to_message_id=message_id,
            parse_mode="html",
            is_group=is_group
          ).result()
      """bot.edit_message_text(
          R.get_string_resource("qr_no_text", lang), 
          chat_id, 
          message_id=message.message_id, 
          parse_mode="html", 
          is_group=is_group
      )"""

    if chat["photos_enabled"] == 1:
      text = phototools.image_ocr(file_path, chat["lang"])
      if text is not None:
        text = R.get_string_resource("ocr_result", chat["lang"]) + "\n" + text
        bot.edit_message_text(
          text=text, 
          chat_id=chat_id, 
          message_id=message.message_id, 
          parse_mode="html", 
          is_group=is_group
        )
        return

      bot.edit_message_text(
        text=R.get_string_resource("photo_no_text", lang), 
        chat_id=chat_id, 
        message_id=message.message_id, 
        parse_mode="html", 
        is_group=is_group
      )

  retry = True
  retry_num = 0
  try:
    while retry:
      process(message)
      retry = False

  except telegram.error.TimedOut as t:
    logger.error("Timeout error %s", traceback.format_exc())
    retry_num += 1
    if retry_num >= 3:
      retry = False
  
  except telegram.error.RetryAfter as r:
    logger.warning("Retrying after %d", r.retry_after)
    time.sleep(r.retry_after)

  except telegram.error.TelegramError as te:
    logger.error("Telegram error %s", traceback.format_exc())
    retry = False

  except Exception as e:
    logger.error("Exception %s", traceback.format_exc())
    retry = False 
  
  finally:
    os.remove(file_path)

@message(Filters.photo)
def photo(bot, update):
  chat_id = get_chat_id(update)
  chat = TBDB.get_chat_entry(chat_id)
  if chat["qr_enabled"] == 0 and chat["photos_enabled"] == 0:
    return

  p = None
  if update.message is not None:
    p = update.message.photo
  elif update.channel_post is not None:
    p = update.channel_post.photo

  if p:
    TranscriberBot.get().photos_thread_pool.submit(
      process_media_photo, bot, update, p, chat
    )

# Command callbacks
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

@command(bypass_admin_check=False)
def start(bot, update):
  welcome_message(bot, update)

@command(bypass_admin_check=False)
def help(bot, update):
  welcome_message(bot, update)

@command(bypass_admin_check=False)
def lang(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(chat_id=chat_id, text=TBDB.get_chat_lang(chat_id))

@command(bypass_admin_check=False)
def rate(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("message_rate", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(bypass_admin_check=False)
def disable_voice(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_voice_enabled(chat_id, 0)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("voice_disabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(bypass_admin_check=False)
def enable_voice(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_voice_enabled(chat_id, 1)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("voice_enabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(bypass_admin_check=False)
def voice_ask(bot, update):
  pass

@command(bypass_admin_check=False)
def disable_photos(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_photos_enabled(chat_id, 0)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("photos_disabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(bypass_admin_check=False)
def enable_photos(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_photos_enabled(chat_id, 1)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("photos_enabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(bypass_admin_check=False)
def disable_qr(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_qr_enabled(chat_id, 0)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("qr_disabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(bypass_admin_check=False)
def enable_qr(bot, update):
  chat_id = get_chat_id(update)
  TBDB.set_chat_qr_enabled(chat_id, 1)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("qr_enabled", TBDB.get_chat_lang(chat_id)),
    is_group = chat_id < 0
  )

@command(bypass_admin_check=True)
def translate(bot, update):
  chat_id = get_chat_id(update)
  message = update.message
  if not message:
    message = update.channel_post

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

@command(bypass_admin_check=False)
def stats(bot, update):
  pass

@command(bypass_admin_check=False)
def donate(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("message_donate", TBDB.get_chat_lang(chat_id)), 
    parse_mode="html",
    is_group = chat_id < 0
  )

@command(bypass_admin_check=True)
def privacy(bot, update):
  chat_id = get_chat_id(update)
  bot.send_message(
    chat_id=chat_id,
    text=R.get_string_resource("privacy_policy", TBDB.get_chat_lang(chat_id)),
    parse_mode='html',
    is_group = chat_id < 0
  )
