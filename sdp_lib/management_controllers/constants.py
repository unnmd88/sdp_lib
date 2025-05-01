from enum import StrEnum


class AllowedControllers(StrEnum):

    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'



class Names(StrEnum):
    http_prefix = 'http://'


ERROR    = 0
RESPONSE = 0