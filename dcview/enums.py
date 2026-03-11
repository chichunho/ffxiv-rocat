from enum import Enum


class ReplyOption(Enum):
    Direct = "DirectMessage"
    Ephemeral = "Ephemeral"
    Public = "Public"
