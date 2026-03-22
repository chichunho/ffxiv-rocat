from enum import Enum


class Status(Enum):
    IDLE = "IDLE"
    SAIL = "SAIL"
    RETURNED = "RETURNED"


class Sea(Enum):
    DEEP_SEA = "DEEP"
    SEA_OF_ASH = "ASH"
    SEA_OF_JADE = "JADE"
    SIRENSONG_SEA = "SIRENSONG"
    LILAC_SEA = "LILAC"
