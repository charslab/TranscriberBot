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


@bp.on.message(Text("bye", "cheers", ignore_case=True))
async def bye_handler(m: Message) -> None:
    await m.answer("See you soon!")


@bp.on.message(Text("take care", "have a good day", ignore_case=True))
async def goodbye_handler(m: Message) -> None:
    await m.answer("You too, bye!")


@bp.on.message(FromPrivate())
async def private_message(m: Message):
    await m.answer(R.get_string_resource("message_private", TBDB.get_chat_lang(m.chat.id)))