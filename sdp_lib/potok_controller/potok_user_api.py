"""
Модуль предоставляет api для взаимодействия со условиями перехода/продления
из Traffic lights configurator контроллера Поток
"""
import abc
from typing import List, Dict

from .lexer import LexerValuesInConditionString
from .parser import pg
from .condition_string import ConditionStringPotokTlc


lexer = LexerValuesInConditionString.get_lexer().build()
parser = pg.build()


class BaseCondition(metaclass=abc.ABCMeta):
    """
    Базовый класс, связанный с обработкой строки условия перехода/продления
    из конфигурации tlc контроллера Поток.
    """

    def __init__(self, condition_string: str):
        """
        :param condition_data: Строка с условием перехода/продления из tlc конфигурации контроллера Поток,
                               с заданными значениями функций(токенов) из tlc конфигурации контроллера Поток.
                               Пример строки: ()
        """

        self.condition_string = condition_string


class ConditionResult(BaseCondition):
    """
    Класс обработки строки условия перехода/продления из tlc конфигурации контроллера Поток
    """

    def __init__(self, condition_string: str):
        """
        :param condition_data: Строка с условием перехода/продления из tlc конфигурации контроллера Поток
               Пример: '(ddr(D33) or ddr(D34)) and mr(G2) and (fctg(G1)<66)'
        :param self.condition_string_for_parse: Строка, в которой функции заменены на требуемые значения и операторы
                                                "and" и "or" заменены на "*" и "+" соответсвенно.
        :param self.current_result: Результат последнего запроса значения всего выражения условия
                                    перехода/продления с заданными значениями
        """

        super().__init__(condition_string)
        self.condition_string_for_parse = None
        self.current_result = None

    def __repr__(self):
        return (f'Последний полученный результат: {self.current_result}\nУсловие: {self.condition_string}\n'
                f'Условие с заменённыыми функциями на значения: {self.condition_string_for_parse}')

    def get_condition_result(self, data: str | Dict) -> bool:
        """
        Возращает результат результат переданного выражения строки условия
        перехода/продления из tlc конфигурации контроллера Поток.
        :param data: словарь с данными, в котором определено соответствие значения для функции(т.е
               в исходную строку условия будут подставлены значения '1' или '0').
               Пример: {'ddr(D33)': '1', 'ddr(D34)': '0', mr(G2): '1', 'fctg(G1)<66: '0'}
        :return: Результат выражения с заданными значениями токенов(функций)
        """

        if isinstance(data, Dict):
            self.func_to_val(data)
        elif isinstance(data, str):
            self.condition_string_for_parse = data
        else:
            raise TypeError(f'Некорректный тип данных: {type(data)}. Допустимый тип "str" или "dict"')

        self.condition_string_for_parse = ConditionStringPotokTlc.replace_operators(
            self.condition_string_for_parse
        )

        result: int = parser.parse(lexer.lex(self.condition_string_for_parse))
        if not isinstance(result, int):
            raise TypeError(f"Ошибка возвращаемого значения: {type(result)}. Должен быть int")  # Для этапа отладки
        self.current_result = bool(result)
        print(f'int result: {result}, bool result: {self.current_result}')
        return self.current_result

    def func_to_val(self, values: Dict):
        """
        Заменяет функции на заданные значения в строке с
        условием перехода/продления из tlc конфигурации контроллера Поток.
        :param values: словарь с данными, в котором определено соответствие значения для функции(т.е
                       в исходную строку условия будут подставлены значения '1' или '0').
                       Пример: {'ddr(D33)': '1', 'ddr(D34)': '0', mr(G2): '1', 'fctg(G1)<66: '0'}
        :return: Возвращает строку с заменёнными функциями(токенами) на значения из values из исходной
                 строки self.condition_string.
                 Пример: self.condition_string -> '(ddr(D33) or ddr(D34)) and mr(G2) and (fctg(G1)<66)'
                         values -> {'ddr(D33)': '1', 'ddr(D34)': '0', mr(G2): '1', 'fctg(G1)<66: '0'}
                         return -> '(1 or 0) and 1 and 0'
        """

        self.condition_string_for_parse = self.condition_string

        for name, val in values.items():
            if not isinstance(val, int) or val not in range(2):
                raise ValueError(f'Передано неверное значение: {val}. Заменяемое значение должно быть 0 или 1')
            self.condition_string_for_parse = self.condition_string_for_parse.replace(name, str(val))
        return self.condition_string_for_parse


class Tokens(BaseCondition):
    """
    Обработка токенов конфигурации tlc контроллера Поток.
    В данном контексте токен эквивалентен функции из строки с условием перехода/продления.
    Примеры токенов: ddr(D1), ddo(D2), fctmg(G1) >= 10, not ddr(D2) и т.д.
    """

    def __init__(self, condition_string: str):
        """
        :param condition_data: Строка с условием перехода/продления из tlc конфигурации контроллера Поток
        """

        super().__init__(condition_string)
        self.current_tokens = None

    def get_tokens(self) -> List:
        """
        Формирмирует токены из строки с условием перехода/продления из tlc конфигурации контроллера Поток
        :return: Список с токенами из входящей строки self.condition_data
        """

        # condition_parser = ConditionParser(self.condition_data)
        self.current_tokens = ConditionStringPotokTlc(self.condition_string).create_tokens()
        return self.current_tokens


class Checker(BaseCondition):
    """
    Содержит различные проверки строки условия/перехода конфигурации tlc
    """

    def check_parens(self) -> List:
        """
        Проверяет корректность расставленных скобок в строке условия вызова/продления на стековой модели LIFO.
        :return: Пустой список, если открывающие и закрывающие скобки расставлены корректно.
                 Если стек пуст и встречается закрывающая скобка - возвращает список с одной закрывающей скобкой [')']
                 Если отсутствуют необходимые закрывающие скобки - возвращает список скобок,
                 которые не были закрыты. Например из строки 'ddr(D1) and (((ddr(D2) or ddr(D3))' вернёт ['(', '(']
        """

        stack = []
        for char in self.condition_string:
            if char == '(':
                stack.append(char)
            elif char == ')':
                if stack and stack[-1] == '(':
                    stack.pop()
                elif not stack:
                    stack.append(char)
                    break
        return stack


if __name__ == '__main__':
    values_ = {
        'ddr(D33)': '0', 'ddr(D34)': '0', 'ddr(D35)': '0', 'ddr(D36)': '0',
        'fctg(G1)<66': '1'
    }
    string_condition = '(ddr(D33) or ddr(D34) or ddr(D35) or ddr(D36)) and (fctg(G1)<66)'

    t = ConditionResult(string_condition)
    print(t)
    t.get_condition_result(values_)

