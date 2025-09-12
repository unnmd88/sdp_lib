import enum
import itertools
import re
import sys
import time
from collections import Counter
from collections.abc import Sequence
from enum import StrEnum
from typing import (
    MutableSequence,
    Pattern
)


MATCHING_OPERATORS = {'|': 'or', '&': 'and', '-': 'or'}
ALLOWED_LEFT_EXTRA_CHARS = {'(': 'left'}
ALLOWED_RIGHT_EXTRA_CHARS = {')': 'right'}
ALLOWED_PARENS = ALLOWED_LEFT_EXTRA_CHARS | ALLOWED_RIGHT_EXTRA_CHARS



def remove_left_right_spaces(string: str, left=True, right=True) -> str:
    """
    Удаляет пробельные символы справа/слева у строки.
    :param string: Строка, в которой необходимо удалить пробельные символы.
    :param left:  True -> удаляет все пробельные символы слева.
    :param right: True -> удаляет все пробельные символы справа.
    :return: Строка с удаленными пробельными символами справа/слева.
    """
    if left:
        string = string.lstrip()
    if right:
        string = string.rstrip()
    return string


def get_main_and_mr_expr(
    cond_string: str,
    sep: str = ','
) -> tuple[None | str, str, str]:
    """
    Делит строку на 2 части по заданному разделителю.
    1-ую часть оставляет без изменений, из 2-й части делает условие
    с функцией "mr" для продления.
    Пример строки: "1|2 & 4, 5"
    ""
    :param cond_string: Строка для обработки и формирования условий.
    :param sep: Разделитель, по которому будет разделена строка.
    :return: Кортеж из 3-х элементов:
             [0] -> Текст ошибки в виде строки, если есть. Иначе None.
             [1] -> 1-ая часть строки до разделителя, без изменений, если нет ошибки.
                    Из примера: "1|2 & 4". Иначе пустая строка "".
             [2] -> 2-ая часть строки после разделителя с условием продления,
                    если разделитель присутствует в строке и после разделителя имеется символ цифры,
                    означающий номер группы. Из примера: "and mr(G5)". Иначе пустая строка "".
            Пример. Из строки "1|2 & 4, 5" вернётся кортеж: (None, "1|2 & 4", "and mr(G5)").
    """
    gr = cond_string.split(sep)
    error = None
    main_expr = mr_expr = ''
    if len(gr) == 2:
        try:
            num_group = int(gr[1])
            main_expr, mr_expr = gr[0], f'and mr(G{num_group})'
        except ValueError:
            error = f'Номер группы после "{sep}" должен быть числом.'
    elif len(gr) == 1:
        main_expr, mr_expr = gr[0], ''
    else:
        error = ErrMessages.invalid_condition
    return error, remove_left_right_spaces(main_expr), remove_left_right_spaces(mr_expr)


class FieldNames(StrEnum):
    """ Содержит имена полей для словаря."""

    errors = 'errors'
    result_condition = 'result_condition'


class ErrMessages(StrEnum):
    """ Содержит текстовое представление ошибок."""

    invalid_condition = 'Некорректное условие'


class Patterns(enum.Enum):
    """ Шаблоны для парса регулярными выражениями. """

    allowed_chars = re.compile('[' + r'\d()\s,' + f'{"".join(MATCHING_OPERATORS)}'  + ']')
    func_range = re.compile(r'\d+' + f'[{"".join(MATCHING_OPERATORS)}]' + r'\d+')
    operators = re.compile(f'[{"".join(MATCHING_OPERATORS)}]')
    func_single = re.compile(r'\d+')


class Token:
    """
    Класс для обработки токенов и формирования из них условия продления/вызова для
    Traffic Lights configurator контроллера "Поток."
    """

    max_range = 255
    patterns: Sequence[Pattern] = tuple(p.value for p in Patterns if p != Patterns.allowed_chars)

    def __init__(self, token: str, func_name: str = 'ddr', strict_validate: bool = False):
        self._raw_token = token.replace(" ", '')
        self._strict_validate = strict_validate
        self._errors = []
        self._func_name = func_name
        self._expr_without_parens = ''
        self._expr_with_parens_if_has = ''
        self._entity = ''
        self._parens_left_side = ''
        self._parens_right_side = ''
        self._range_start: int = 0
        self._range_stop: int = 0
        self._op = ''
        self.is_combining_operator = False
        self._parse_token()

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'errors={self._errors} '
            f'raw_token={self._raw_token} '
            f'strict_validate={self._strict_validate} '
            f'expr="{self._expr_without_parens}" '
            f'entity={self._entity} '
            f'parens_left_side="{self._parens_left_side}" '
            f'parens_right_side="{self._parens_right_side}" '
            f'op="{self._op}" '
            f'is_combining_operator={self.is_combining_operator} '
            f'func_name="{self._func_name}" '
            f'condition="{self._expr_with_parens_if_has}"'
            f')'
        )

    def _validate_parens(self) -> bool:
        """
        Проверяет валидность скобок в токене, добавляет текст ошибки в self._errors при наличии.
        :return: False, если есть ошибки в скобках токена, иначе True.
        """
        parens_errors = []
        bad_chars = [str(c) for c in f'{self._parens_left_side}{self._parens_right_side}' if c not in ALLOWED_PARENS]
        if bad_chars:
            parens_errors.append(
                f'Ошибка в фрагменте "{self._raw_token}": '
                f'Слева и справа от диапазона/объединяющего оператора должны быть скобки: "(" или ")". '
                f'Недопустимые символы: {bad_chars}.'
            )
        if self._strict_validate and not bad_chars:
            for paren in self._parens_left_side:
                if paren != '(':
                    parens_errors.append(
                        f'В левой части фрагмента {self._raw_token} должны быть только открывающие скобки "("'
                    )
                    break # TO DO
            for paren in self._parens_right_side:
                if paren != ')':
                    parens_errors.append(
                        f'В правой части фрагмента {self._raw_token} должны быть только закрывающие скобки ")"'
                    )  # TO DO
                    break
        self._errors += parens_errors
        return True if not parens_errors else False

    def _parse_token(self):
        """
        Основной метод парса токена и формирования соответствующих атрибутов.
        :return:
        """
        # self._expr_without_parens = ''
        # self._entity = ''
        # self._expr_with_parens = ''
        for pattern in self.patterns:
            matches = re.findall(pattern, self._raw_token)
            # print(f'matches: {matches}')
            if len(matches) == 1: # Шаблон токене найден успешно
                self._entity = matches[0]
                self._parens_left_side, self._parens_right_side = re.split(pattern, self._raw_token)
                if self._validate_parens():
                    if self._entity in MATCHING_OPERATORS:
                        self.is_combining_operator = True
                    if not self.is_combining_operator:
                        if self._entity.isdigit():
                            self._range_start = self._range_stop = int(self._entity)
                        else:
                            raw_operator = re.findall(Patterns.operators.value, self._entity)[0]
                            self._range_start, self._range_stop = map(int, self._entity.split(raw_operator))
                            self._op = MATCHING_OPERATORS[raw_operator]
                        self._expr_without_parens = f' {self._op} '.join(
                            f'{self._func_name}(D{num})' for num in range(self._range_start, self._range_stop + 1)
                        )
                        if (self._range_stop - self._range_start) > self.max_range:
                            self._errors.append(
                                f'Ошибка в фрагменте: "{self._raw_token}". '
                                f'Диапазон не должен превышать {self.max_range}. '
                                f'Заданный диапазон={self._range_stop - self._range_start}'
                            )
                        if self._range_start > self._range_stop:
                            self._errors.append(
                                f'Ошибка в фрагменте: "{self._raw_token}". Неверно задан диапазон. '
                                f'Диапазон необходимо задавать от меньшего к большему, а не наоборот.'
                            )
                    else:
                        self._expr_without_parens = MATCHING_OPERATORS[self._entity]
                    if not self._errors:
                        self._expr_with_parens_if_has = f'{self._parens_left_side}{self._expr_without_parens}{self._parens_right_side}'
            elif len(matches) >= 2: # Найдено несколько шаблонов в токене, что является ошибкой токена.
                self._errors.append(f'В фрагменте "{self._raw_token}" ошибка.')
            if self._errors or self._expr_with_parens_if_has:
                return True
        self._errors.append(f'Ошибка в фрагменте {self._raw_token}.')
        return False

    def get_errors(self):
        return self._errors

    def get_raw_token(self):
        return self._raw_token

    def get_func_name(self):
        return self._func_name

    def get_condition(self, wrap_parentheses: bool = False):
        if wrap_parentheses and not self.is_combining_operator:
            return f'({self._expr_with_parens_if_has})'
        return self._expr_with_parens_if_has


class ConditionMaker:
    def __init__(self, raw_string: str, func_name: str = 'ddr', strict_mode = False):
        self._raw_string = re.sub(r' {2,}', ' ', raw_string).rstrip().lstrip()
        self._strict_mode = strict_mode
        self._counter = Counter(self._raw_string)
        self._manual_parents_control = bool(self._counter[')'] or self._counter['('])
        self._func_name = func_name
        self._errors = []
        self._result_condition = ''
        self._main_stmt = self._and_mr_stmt = ''
        self._tokens_to_parse = self._processed_tokens = None

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'raw_string="{self._raw_string}" '
            f'counter="{self._counter}" '
            f'errors={self._errors} '
            f'tokens_to_parse={self._tokens_to_parse} '
            f'parsed_tokens={self._processed_tokens} '
            f'main_stmt="{self._main_stmt}" '
            f'and_mr_stmt="{self._and_mr_stmt}" '
            f'result_condition="{self._result_condition}"'
            f')'
        )

    def _check_valid_chars_in_raw_string(self):
        bad_chars = [str(char) for char in self._raw_string if re.search(Patterns.allowed_chars.value, char) is None]
        if bad_chars:
            self._errors.append(f'Строка содержит недопустимые символы: {bad_chars}')
        return True if not bad_chars else False

    def _check_valid_num_parens(self) -> bool:
        if self._counter[')'] != self._counter['(']:
            self._errors.append(
                f'Ошибка в заданном выражении: количество открывающих и закрывающих скобок не совпадает.'
            )
            return False
        return True

    def _create_tokens(self):
        self._processed_tokens = []
        for raw_token in self._tokens_to_parse:
            token = Token(raw_token, self._func_name)
            self._errors += token.get_errors()
            self._processed_tokens.append(token)
        return self._processed_tokens

    def _check_token_position(self):
        for i, token in enumerate(self._processed_tokens, 1):
            operators = [f'"{op}"' for op in MATCHING_OPERATORS]
            if i % 2 == 0: # Чётный токен всегда должен быть оператором.
                if not token.is_combining_operator:
                    self._errors.append(
                        f'Ошибка в фрагменте {token.get_raw_token()}. Данный фрагмент должен быть '
                        f'выражением, а не объединяющим оператором типа {", ".join(operators)}.'
                    )
            else:
                if token.is_combining_operator:
                    self._errors.append(
                        f'Ошибка в фрагменте {token.get_raw_token()}. Данный фрагмент должен быть '
                        f'объединяющим оператором типа {", ".join(operators)}.'
                    )

    def _create_main_stmt(self):
        if not self._manual_parents_control and (len(self._tokens_to_parse) > 1):
            wrap_parentheses = True
        else:
            wrap_parentheses = False
        return ' '.join(
            token.get_condition(wrap_parentheses=wrap_parentheses) for token in self._processed_tokens
        )

    def _create_result_condition_string(self) -> str:
        if not self._errors:
            if self._and_mr_stmt:
                self._result_condition = f'({self._create_main_stmt()}) {self._and_mr_stmt}'
            else:
                self._result_condition = self._create_main_stmt()
        else:
            self._result_condition = ''
        return self._result_condition

    def get_result_condition(self) -> str:
        return self._result_condition

    def get_result_as_dict(self):
        return {str(FieldNames.errors): self._errors, str(FieldNames.result_condition): self._result_condition}

    def build(self):
        self._errors = []
        self._check_valid_chars_in_raw_string()
        self._check_valid_num_parens()
        if self._errors:
            self._create_result_condition_string()
            return self.get_result_as_dict()

        err, self._main_stmt, self._and_mr_stmt = get_main_and_mr_expr(self._raw_string)
        if err is not None:
            self._errors.append(err)
        else:
            self._tokens_to_parse = self._main_stmt.split()
            self._processed_tokens: MutableSequence[Token] = []
            if len(self._tokens_to_parse) % 2 == 0 or self._tokens_to_parse[0] in MATCHING_OPERATORS:
                self._errors.append(ErrMessages.invalid_condition)
            else:
                self._create_tokens()
                self._check_token_position()
        self._create_result_condition_string()
        return self.get_result_as_dict()


def debug():
    while True:
        try:
            print()
            user_data = input('Ввод выражения: ')
            start_time = time.perf_counter()
            _maker = ConditionMaker(user_data)
            print(_maker.build())
            print(_maker)
            print(_maker.get_result_as_dict())
            print(f'result_condition: {_maker.get_result_condition()}')
            print(f'time: {time.perf_counter() - start_time}')
            print('-' * 100)
        except KeyboardInterrupt:
            print(f'\nЗавершаю выполнение...')
            sys.exit()


if __name__ == '__main__':
    # s_str = ' 5&9 | 10|17 | 121|124,12'
    t = Token('22|23')
    # t = Token('|')
    # t = Token('((|)))')
    print(t)

    s_str = ' 1|2 ,14'
    maker = ConditionMaker(s_str, 'ddo')
    print(maker.build())
    print(maker)
    debug()
