from typing import Self, TypeVar, Type

import aiohttp

from sdp_lib.management_controllers.parsers.parsers_peek_http import ParserBase
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb


P = TypeVar('P', bound=ParserBase, covariant=True)


class GetData(PeekWeb):

    parser_class: Type[P]

    def __init__(self, ipv4: str, session: aiohttp.ClientSession):
        super().__init__(ipv4=ipv4, session=session)
        self.method = self.fetch

    @classmethod
    def get_parser_obj(cls, content: str) -> P:
        """
        Возвращает объект класса парсера.
        :param content: Контент веб страницы, который будет
                        передан конструктору класса cls.parser_class.
        :return: Экземпляр класса парсера.
        """
        return cls.parser_class(content)

    def __repr__(self):
        return (
            f'cls.parser_class: {self.parser_class}\n'
            f'self.parser: {self.parser}\n'
            f'self.response: {self.response}\n'
            f'self.method: {self.method.__name__}'
        )

    # async def get_and_parse(self) -> Self:
    #     """
    #     Получает контент, парсит его для вычленения данных.
    #     :return: Self.
    #     """
    #     error, content_data = await self.http_request_to_host()
    #     if error is None:
    #         self.parser = self.get_parser_obj(content_data)
    #         self.parser.parse()
    #     else:
    #         self.parser = None
    #
    #     self.add_data_to_data_response_attrs(error, self.parser.data_for_response)
    #     return self

    async def get_and_parse(self) -> Self:
        """
        Получает контент, парсит его для вычленения данных.
        :return: Self.
        """
        error, content_data = await self.http_request_to_host()
        if error is None:
            self.parser = self.get_parser_obj(content_data)
            self.parser.parse()
        else:
            self.parser = None

        self.add_data_to_data_response_attrs(
            error=error,
            data=None if self.parser is None else self.parser.data_for_response
        )
        return self

