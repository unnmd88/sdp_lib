import abc
from typing import Any


class Parsers:

    def __init__(self, data_to_parse: Any = None):
        self.data_to_parse = data_to_parse
        self.config = None
        self.parsed_content_as_dict = {}
        # self.data_for_response: dict[str, Any] | None = None
        self.extras_data = {}

    @abc.abstractmethod
    def parse(self, *args, **kwargs) -> dict[str, Any]:
        """ Основной метод парса данных для формирования response. """
        ...

    def load_config_parser(self, config):
        self.config = config

    def load_data_to_parse(self, data):
        self.data_to_parse = data

    def load_varbinds_and_configparser(
            self,
            varbinds,
            configparser
    ):
        self.load_data_to_parse(varbinds)
        self.load_config_parser(configparser)