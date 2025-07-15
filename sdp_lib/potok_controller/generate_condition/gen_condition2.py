import itertools
import re
import sys
from collections import Counter
from collections.abc import MutableMapping
from enum import StrEnum
from typing import (
    MutableSequence,
    Any
)


MATCHING_OPERATORS = {'|': 'or', '&': 'and', '-': 'or'}
ALLOWED_LEFT_EXTRA_CHARS = {'('}
ALLOWED_RIGHT_EXTRA_CHARS = {')'}


def remove_spaces(string: str, left=True, right=True):
    if left:
        string = string.lstrip()
    if right:
        string = string.rstrip()
    return string


def get_main_and_mr_expr(
    cond_string: str,
    sep: str = ','
) -> tuple[None | str, str, str]:
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
    return error, remove_spaces(main_expr), remove_spaces(mr_expr)


class FieldNames(StrEnum):
    errors = 'errors'
    result_condition = 'result_condition'


class ErrMessages(StrEnum):
    invalid_condition = 'Некорректное условие'

class Token:

    max_range = 255
    range_pattern = re.compile(r'\d+' + f'[{"".join(MATCHING_OPERATORS)}]' + r'\d+')
    single_pattern = re.compile(r'\d+')

    def __init__(self, token: str, func_name = 'ddr'):
        self._raw_token = token.replace(" ", '')
        self._errors = []
        self._func_name = func_name
        self._expr = ''
        self._left_parens = ''
        self._right_parens = ''
        self._range_start: int = 0
        self._range_stop: int = 0
        self._op = ''
        self._is_operator = False
        self._is_single = False
        self._condition = None
        self._processing()

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'errors={self._errors} '
            f'raw_token={self._raw_token} '
            f'expr={self._expr} '
            f'left_extra={self._left_parens} '
            f'right_extra={self._right_parens} '
            f'func_name="{self._func_name}" '
            f'processed_expr="{self._condition}"'
            f')'
        )

    def _parse_token(self):

        # for pattern in (self.range_pattern, self.single_pattern):
        #     found = re.findall(pattern, self._raw_token)
        #     if len(found) == 1:
        #         self._expr = found[0]
        #         self._left_parens, self._right_parens =


        self._expr = re.findall(self.range_pattern, self._raw_token)
        if not self._expr:
            self._expr = re.findall(self.single_pattern, self._raw_token)

        print(f'self._expr: {self._expr}')
        # self._expr = ''
        # for s in self._raw_token:
        #     if s in ALLOWED_LEFT_EXTRA_CHARS:
        #         self._left_parens += s
        #     elif s in ALLOWED_RIGHT_EXTRA_CHARS:
        #         self._right_parens += s
        #     else:
        #         self._expr += s

    def _processing(self):

        self._parse_token()
        if not self._expr:
            self._errors.append(f'Некорректное выражение "{self._raw_token}".')
            return False
        if ')' in self._left_parens:
            self._errors.append(
                f'В левой части выражения {self._raw_token} не должны содержаться левые и правые скобки одновременно.'
            )
        if '(' in self._right_parens:
            self._errors.append(
                f'В правой части выражения {self._raw_token} не должны содержаться левые и правые скобки одновременно.'
            )
        if self._errors:
            return False

        matched_operator = MATCHING_OPERATORS.get(self._raw_token, '')
        if matched_operator:
            self._is_operator = True
            self._condition = matched_operator
            return True
        elif self._expr.isdigit():
            self._is_single = True
            self._condition = f'{self._func_name}(D{int(self._expr)})'
            return True

        for op in MATCHING_OPERATORS:
            success_splited = self._expr.split(op)
            if len(success_splited) == 2:
                self._range_start, self._range_stop = success_splited
                self._op = MATCHING_OPERATORS[op]
                break
        else:
            self._errors.append(
                f'Ошибка в выражении "{self._expr}". '
                f'Для диапазона функций используйте один из операторов: {set(f"{op}" for op in MATCHING_OPERATORS)},'
                f'например: "1|4", "125&130". '
                f'Для выражения с одной функцией, используйте число. Например: "5", "20"'
            )
            return False
        try:
            self._range_start, self._range_stop = map(int, success_splited)
            self._create_condition_for_range()
        except ValueError:
            self._errors.append(
                f'Ошибка в выражении: "{self._raw_token}". Номер группы должен быть целым положительным числом.'
            )
            return False
        if (self._range_stop - self._range_start) > self.max_range:
            self._errors.append(
                f'Ошибка в выражении: "{self._raw_token}". Диапазон не должен превышать {self.max_range}. '
                f'Заданный диапазон={self._range_stop - self._range_start}'
            )
            return False
        return True


    def _create_condition_for_range(self):
        self._expr = (
            f' {self._op} '.join(f'{self._func_name}(D{num})' for num in range(self._range_start, self._range_stop + 1))
        )
        self._condition = f'{self._left_parens}{self._expr}{self._right_parens}'
        return self._condition


    def get_errors(self):
        return self._errors

    def get_raw_token(self):
        return self._raw_token

    def get_func_name(self):
        return self._func_name

    def get_condition(self, wrap_parentheses: bool = False):
        if wrap_parentheses and not self._is_operator:
            return f'({self._condition})'
        return self._condition


class ConditionMaker:
    def __init__(self, raw_string: str, func_name: str = 'ddr'):
        self._raw_string = re.sub(r' {2,}', ' ', raw_string).rstrip().lstrip()
        self._counter = Counter(self._raw_string)
        self._manual_parents_control = bool(self._counter[')'] or self._counter['('])
        self._func_name = func_name
        self._result_expr = ''
        self._errors = []
        self._main_expr = self._and_mr_expr = ''
        self._tokens_to_parse = self._parsed_tokens = None

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'raw_string="{self._raw_string}" '
            f'errors={self._errors} '
            f'tokens_to_parse={self._tokens_to_parse} '
            f'parsed_tokens={self._parsed_tokens} '
            f'main_expr="{self._main_expr}" '
            f'and_mr_expr="{self._and_mr_expr}" '
            f'result_expr="{self._result_expr}"'
            f')'
        )

    def _create_main_expr(self):
        if not self._manual_parents_control and (len(self._tokens_to_parse) > 1):
            wrap_parentheses = True
        else:
            wrap_parentheses = False
        return ' '.join(
            token.get_condition(wrap_parentheses=wrap_parentheses) for token in self._parsed_tokens
        )

    def _create_parsed_tokens(self):
        self._parsed_tokens = []
        for raw_token in self._tokens_to_parse:
            token = Token(raw_token, self._func_name)
            self._errors += token.get_errors()
            self._parsed_tokens.append(token)
        return self._parsed_tokens

    def _create_result_condition_string(self) -> str:
        if not self._errors:
            if self._and_mr_expr:
                self._result_expr = f'({self._create_main_expr()}) {self._and_mr_expr}'
            else:
                self._result_expr = self._create_main_expr()
        else:
            self._result_expr = ''
        return self._result_expr

    def build_result_as_dict(self) -> MutableMapping[str, Any]:
        return {FieldNames.errors: self._errors, FieldNames.result_condition: self._create_result_condition_string()}

    def process_data_and_build_result_as_dict(self):

        if self._counter[')'] != self._counter['(']:
            self._errors.append(
                f'Ошибка в заданном выражении: количество открывающих и закрывающих скобок не совпадает.'
            )
            return self.build_result_as_dict()
        err, self._main_expr, self._and_mr_expr = get_main_and_mr_expr(self._raw_string)
        if err is not None:
            self._errors.append(err)
        else:
            self._tokens_to_parse = self._main_expr.split()
            self._parsed_tokens: MutableSequence[Token] = []
            if len(self._tokens_to_parse) % 2 == 0 or self._tokens_to_parse[0] in MATCHING_OPERATORS:
                self._errors.append(ErrMessages.invalid_condition)
            else:
                self._create_parsed_tokens()
        return self.build_result_as_dict()


def debug():
    while True:
        try:
            print()
            user_data = input('Ввод выражения: ')
            _maker = ConditionMaker(user_data)
            print(_maker.process_data_and_build_result_as_dict())
            print(_maker)
        except KeyboardInterrupt:
            print(f'\nЗавершаю выполнение...')
            sys.exit()


if __name__ == '__main__':
    # s_str = ' 5&9 | 10|17 | 121|124,12'

    t = Token('()(1|2)))')

    # s_str = ' 1|2 ,14'
    # maker = ConditionMaker(s_str, 'ddo')
    # print(maker.process_data_and_build_result_as_dict())
    # print(maker)
    # debug()
