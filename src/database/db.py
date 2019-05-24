import sqlite3
import metaclass
import logging
import config
import traceback

logger = logging.getLogger(__name__)

class Database():
  __instance = None

  def __init__(self, database):
    self.database = database

  def __connect(self):
    self.__connection = sqlite3.connect(self.database)
    self.__cursor = self.__connection.cursor()

  def __close(self):
    self.__connection.commit()
    self.__connection.close()

  def __enter__(self):
    logger.debug("__enter__")
    self.__connect()
    return self

  def assoc(self):
    self.__connection.row_factory = sqlite3.Row
    self.__cursor = self.__connection.cursor()


  def __exit__(self, exc_type, exc_value, exc_traceback):
    logger.debug("__exit__")
    self.__close()

    if exc_type:
      logger.error("exc_type: {}".format(exc_type))
      logger.error("exc_value: {}".format(exc_value))
      logger.error("exc_traceback: {}".format(exc_traceback))
      logger.error(traceback.format_exc())

    return True

  def execute(self, query, *args):
    res = self.__cursor.execute(query, *args)
    return self.__cursor

class TBDB():
  @staticmethod
  def _get_db():
    return Database(config.get_config_prop("app")["database"])


  @staticmethod
  def create_default_chat_entry(chat_id, lang):
    with TBDB._get_db() as db:
      db.execute(
        "INSERT INTO chats(chat_id, lang, voice_enabled, photos_enabled, qr_enabled, active, ban) VALUES(?,?,?,?,?,?,?)", 
        (chat_id, lang, 1, 0, 0, 1, 0)
      )

  @staticmethod
  def get_chat_entry(chat_id):
    with TBDB._get_db() as db:
      db.assoc()
      cursor = db.execute("SELECT * FROM chats WHERE chat_id='{0}'".format(chat_id))
      return cursor.fetchone()

  @staticmethod
  def get_chats():
    with TBDB._get_db() as db:
      db.assoc()
      cursor = db.execute("SELECT * FROM chats")
      return [dict(x) for x in cursor.fetchall()]

  @staticmethod
  def get_chat_lang(chat_id):
    chat_record = TBDB.get_chat_entry(chat_id)
    if not chat_record:
      logger.debug("Record for chat {} not found, creating one.".format(chat_id))
      TBDB.create_default_chat_entry(chat_id, "en-US")
      
    with TBDB._get_db() as db:
      cursor = db.execute("SELECT lang FROM chats WHERE chat_id='{0}'".format(chat_id))
      return cursor.fetchone()[0]

  @staticmethod
  def set_chat_lang(chat_id, lang):
    with TBDB._get_db() as db:
      db.execute("UPDATE chats SET lang='{0}' WHERE chat_id='{1}'".format(lang, chat_id))

  
  @staticmethod
  def get_chat_voice_enabled(chat_id):
    with TBDB._get_db() as db:
      c = db.execute("SELECT voice_enabled FROM chats WHERE chat_id='{0}'".format(chat_id))
      return c.fetchone()[0]

  @staticmethod
  def set_chat_voice_enabled(chat_id, voice_enabled):
    with TBDB._get_db() as db:
      db.execute("UPDATE chats SET voice_enabled='{0}' WHERE chat_id='{1}'".format(voice_enabled, chat_id))

  
  @staticmethod
  def get_chat_photos_enabled(chat_id):
    with TBDB._get_db() as db:
      c = db.execute("SELECT photos_enabled FROM chats WHERE chat_id='{0}'".format(chat_id))
      return c.fetchone()[0]

  @staticmethod
  def set_chat_photos_enabled(chat_id, photos_enabled):
    with TBDB._get_db() as db:
      db.execute("UPDATE chats SET photos_enabled='{0}' WHERE chat_id='{1}'".format(photos_enabled, chat_id))


  @staticmethod
  def get_chat_qr_enabled(chat_id):
    with TBDB._get_db() as db:
      c = db.execute("SELECT qr_enabled FROM chats WHERE chat_id='{0}'".format(chat_id))
      return c.fetchone()[0]

  @staticmethod
  def set_chat_qr_enabled(chat_id, qr_enabled):
    with TBDB._get_db() as db:
      db.execute("UPDATE chats SET qr_enabled='{0}' WHERE chat_id='{1}'".format(qr_enabled, chat_id))

  @staticmethod
  def get_chat_active(chat_id):
    with TBDB._get_db() as db:
      c = db.execute("SELECT active FROM chats WHERE chat_id='{0}'".format(chat_id))
      return c.fetchone()[0]
  
  @staticmethod
  def set_chat_active(chat_id, active):
    with TBDB._get_db() as db:
      db.execute("UPDATE chats SET active='{0}' WHERE chat_id='{1}'".format(active, chat_id))

  @staticmethod
  def get_chat_ban(chat_id):
    with TBDB._get_db() as db:
      c = db.execute("SELECT ban FROM chats WHERE chat_id='{0}'".format(chat_id))
      return c.fetchone()[0]

  @staticmethod
  def set_chat_ban(chat_id, ban):
    with TBDB._get_db() as db:
      db.execute("UPDATE chats SET ban='{0}' WHERE chat_id='{1}'".format(ban, chat_id))
  

  @staticmethod
  def get_chats_num():
    with TBDB._get_db() as db:
      c = db.execute("SELECT count(*) FROM chats")
      return int(c.fetchone()[0])
  
  @staticmethod
  def get_active_chats_num():
    with TBDB._get_db() as db:
      c = db.execute("SELECT count(*) FROM chats where active=1")
      return int(c.fetchone()[0])

