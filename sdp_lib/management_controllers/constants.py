from enum import StrEnum


class AllowedControllers(StrEnum):

    SWARCO = 'Swarco'
    POTOK_P = 'Поток (P)'
    POTOK_S = 'Поток (S)'
    PEEK = 'Peek'

    @classmethod
    def get_all_controllers(cls):
        return {c for c in AllowedControllers}



class Names(StrEnum):
    http_prefix = 'http://'


ERROR    = 0
RESPONSE = 0