from database.db import Database
from database.db import TBDB

"""
SCHEMA 

TABLE CHATS
| chat_id (int) | lang (str) | 
  voice_enabled (int) | photos_enabled (bool) | 
  qr_enabled (bool) | active(bool) | ban (bool) |

TABLE STATS
| month_year (str) | audio_num (int) | 
  min_tot_audio (int) | min_transcribed_audio (int) | 
  num_pictures (int) |

"""

def init_schema(database):
  with Database(database) as db:
    db.execute("""CREATE TABLE IF NOT EXISTS chats (
      chat_id INTEGER PRIMARY KEY, 
      lang VARCHAR(5) NOT NULL, 
      voice_enabled INTEGER,
      photos_enabled INTEGER,
      qr_enabled INTEGER,
      active INTEGER,
      ban INTEGER)
    """)

    db.execute("""CREATE TABLE IF NOT EXISTS stats (
      month_year INTEGER PRIMARY KEY, 
      audio_num INTEGER, 
      min_tot_audio INTEGER,
      min_transcribed_audio INTEGER,
      num_pictures INTEGER)
    """)