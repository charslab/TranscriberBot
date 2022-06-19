import config
from telegram.ext import BaseFilter

class FilterIsAdmin(BaseFilter):
  def filter(self, message):
    if message.chat.id >= 0:
      return True

    if message.chat.type == 'channel':
      return True

    if message.from_user.id == 1087968824:
      return True

    sender = message.from_user
    admins = message.chat.get_administrators()

    is_admin = list(filter(lambda cm: cm.user.id == sender.id, admins))
    is_admin = len(is_admin) > 0

    return is_admin

chat_admin = FilterIsAdmin()

class FilterIsOwner(BaseFilter):
  #def __init__(self):
    #self.admins = config.get_config_prop('telegram')['admins']

  def filter(self, message):
    admins = config.get_config_prop('telegram')['admins']
    is_owner = list(filter(lambda admin: admin == str(message.chat.id), admins))
    return len(is_owner) > 0

bot_admin = FilterIsOwner()
