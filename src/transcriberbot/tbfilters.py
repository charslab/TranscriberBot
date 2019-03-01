from telegram.ext import BaseFilter

class FilterIsAdmin(BaseFilter):
	def __init__(self, bot):
		self.bot = bot

	def filter(self, message):
		if message.chat.id >= 0:
			return True

		if message.chat.type == 'channel':
			return True

		sender = message.from_user
		admins = message.chat.get_administrators()

		is_admin = list(filter(lambda cm: cm.user.id == sender.id, admins))
		is_admin = len(is_admin) > 0

		return is_admin