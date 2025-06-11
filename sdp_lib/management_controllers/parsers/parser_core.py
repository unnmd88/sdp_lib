import abc
from typing import Any


class Parsers:

    def __init__(self, content: Any = None):
        self.content = content
        self.config = None
        self.parsed_content_as_dict = {}
        self.data_for_response: dict[str, Any] | None = None
        self.extras_data = {}

    @abc.abstractmethod
    def parse(self, *args, **kwargs) -> dict[str, Any]:
        """ Основной метод парса данных для формирования response. """


