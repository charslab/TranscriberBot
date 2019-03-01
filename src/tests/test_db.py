import sys, os
sys.path.append(os.path.abspath(os.path.join('.', 'src')))

import config
import database
from database import TBDB

def setup_function(function):
	config.init(os.path.abspath('config'))
	config.get_config_prop("app")["database"] = "tmp.db"
	database.init_schema(config.get_config_prop("app")["database"])

def teardown_function(function):
	os.remove(config.get_config_prop("app")["database"])

def test_db():
	id = 1234

	TBDB.create_default_chat_entry(id, 'en-US')
	assert TBDB.get_chat_lang(id) == 'en-US'
	assert TBDB.get_chat_active(id) == 1

	TBDB.set_chat_lang(id, 'lang')
	TBDB.set_chat_voice_enabled(id, 2)
	TBDB.set_chat_photos_enabled(id, 1)
	TBDB.set_chat_qr_enabled(id, 1)
	TBDB.set_chat_active(id, 0)
	TBDB.set_chat_ban(id, 1)

	assert TBDB.get_chat_lang(id) == 'lang'
	assert TBDB.get_chat_voice_enabled(id) == 2
	assert TBDB.get_chat_photos_enabled(id) == 1
	assert TBDB.get_chat_qr_enabled(id) == 1
	assert TBDB.get_chat_active(id) == 0
	assert TBDB.get_chat_ban(id) == 1