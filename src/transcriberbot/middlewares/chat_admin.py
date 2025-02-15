"""
Author: Carlo Alberto Barbano <carlo.alberto.barbano@outlook.com>
Date: 15/02/25
"""
from wonda import ABCMiddleware, Bot, Message, Token, ChatMemberUpdate
from wonda.bot.rules import Command
from wonda.types import ChatType
from wonda.types.objects import User

class ChatAdminMiddleware(ABCMiddleware[Message]):
    pass