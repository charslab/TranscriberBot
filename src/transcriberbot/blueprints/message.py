"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
import resources as R

from wonda import Blueprint, Message
from wonda.bot.rules import Text
from database import TBDB
from transcriberbot.rules import FromPrivate

bp = Blueprint()


@bp.on.message(FromPrivate())
async def private_message(m: Message):
    await m.answer(R.get_string_resource("message_private", TBDB.get_chat_lang(m.chat.id)))

