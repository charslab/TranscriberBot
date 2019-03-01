import telegram

class ChannelCommandHandler(telegram.ext.CommandHandler):
  def check_update(self, update):
    is_channel = False

    if update.channel_post:
      update.message = update.channel_post
      is_channel = True

    res = super().check_update(update)

    if is_channel:
      update.message = None

    return res