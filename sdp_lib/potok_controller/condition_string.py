from typing import List, Dict


from .lexer import LexerOriginalConditionString


lexer = LexerOriginalConditionString.get_lexer().build()


class ConditionStringPotokTlc:
    """
    Класс - обрабчик в строки условия перехода/продления
    Traffic lights configurator контроллера Поток
    """

    def __init__(self, condition_string: str):
        """
        :param condition_string: Строка с условием перехода/продления
                                 Traffic lights configurator контроллера Поток
        """

        self.condition_string = condition_string
        self.tokens = None

    def create_tokens(self) -> List:
        """
        Формирует список токенов(функций) из self.condition_string
        :return: Список токенов(функций) из self.condition_string
        """

        all_tokens = {token.value.strip() for token in lexer.lex(self.condition_string)}
        self.tokens = sorted([token for token in all_tokens])
        print(self.tokens)
        return self.tokens

    @classmethod
    def replace_operators(cls, string: str) -> str:
        """
        Заменяет "or" и "and" в строке на "+" и "*" соответственно.
        :param string: строка, в которой требуется заменить символы.
        :return: строка с заменёнными символами.
        """

        return cls.replace_chars(replace_data={'and': '*', 'or': '+'}, string=string)

    @classmethod
    def replace_chars(cls, replace_data: Dict[str, str], string: str):
        """
        Заменяет символы в строке.
        :param string: строка, в которой требуется заменить символы.
        :param replace_data: k: символы, которые требуется заемить, v: символы, на которые требуется заемить
        :return: строка с заменёнными символами. если kwargs пустой, возвращает переданную строку
        """

        for pattern, replacement in replace_data.items():
            string = string.replace(pattern, replacement)
        return string
