import re
from enum import Enum


class Patterns(Enum):
    always_red = re.compile(r'кр|-|поко', re.IGNORECASE)