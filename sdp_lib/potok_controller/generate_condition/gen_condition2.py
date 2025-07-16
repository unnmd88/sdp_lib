import enum
import itertools
import re
import sys
from collections import Counter
from collections.abc import MutableMapping, Sequence
from enum import StrEnum
from typing import (
    MutableSequence,
    Any, Pattern
)


MATCHING_OPERATORS = {'|': 'or', '&': 'and', '-': 'or'}
ALLOWED_LEFT_EXTRA_CHARS = {'('}
ALLOWED_RIGHT_EXTRA_CHARS = {')'}
ALLOWED_PARENS = ALLOWED_LEFT_EXTRA_CHARS | ALLOWED_RIGHT_EXTRA_CHARS
STRICT_MODE = False


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


class Patterns(enum.Enum):
    func_range = re.compile(r'\d+' + f'[{"".join(MATCHING_OPERATORS)}]' + r'\d+')
    operators = re.compile(f'[{"".join(MATCHING_OPERATORS)}]')
    func_single = re.compile(r'\d+')


class Token:

    max_range = 255
    patterns: Sequence[Pattern] = tuple(p.value for p in Patterns)
    # range_pattern = re.compile(r'\d+' + f'[{"".join(MATCHING_OPERATORS)}]' + r'\d+')
    # single_pattern = re.compile(r'\d+')
    # operators_pattern = re.compile(f'[{"".join(MATCHING_OPERATORS)}]')

    def __init__(self, token: str, func_name: str = 'ddr', strict_validate: bool = False):
        self._raw_token = token.replace(" ", '')
        self._strict_validate = strict_validate
        self._errors = []
        self._func_name = func_name
        self._expr_without_parens = ''
        self._expr_with_parens = ''
        self._entity = ''
        self._parens_left_side = ''
        self._parens_right_side = ''
        self._range_start: int = 0
        self._range_stop: int = 0
        self._op = ''
        self.is_operator = False
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
            f'is_operator={self.is_operator} '
            f'func_name="{self._func_name}" '
            f'condition="{self._expr_with_parens}"'
            f')'
        )

    def _validate_parens(self):
        parens_errors = []
        bad_chars = [
            c for c in itertools.chain(self._parens_left_side, self._parens_right_side)
            if c not in ALLOWED_PARENS
        ]
        if bad_chars:
            parens_errors.append(
                f'Ошибка в фрагменте "{self._raw_token}": недопустимые символы: {bad_chars}'
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
        self._expr_without_parens = ''
        self._entity = ''
        self._expr_with_parens = ''
        for pattern in self.patterns:
            matches = re.findall(pattern, self._raw_token)
            print(f'matches: {matches}')
            if len(matches) == 1:
                self._entity = matches[0]
                self._parens_left_side, self._parens_right_side = re.split(pattern, self._raw_token)
                if self._validate_parens():
                    if self._entity in MATCHING_OPERATORS:
                        self.is_operator = True
                    if not self.is_operator:
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
                        self._expr_with_parens = f'{self._parens_left_side}{self._expr_without_parens}{self._parens_right_side}'
            elif len(matches) >= 2:
                self._errors.append(
                    f'В фрагменте "{self._raw_token}" ошибка. Диапазон должен быть в единственном экземпляре, '
                    f'предоставлено {len(matches)}: {matches}'
                )
            if self._errors or self._expr_with_parens:
                return True
        self._errors.append(f'Ошибка в фрагменте {self._raw_token}.')
        print(self)
        return False

    def get_errors(self):
        return self._errors

    def get_raw_token(self):
        return self._raw_token

    def get_func_name(self):
        return self._func_name

    def get_condition(self, wrap_parentheses: bool = False):
        if wrap_parentheses and not self.is_operator:
            return f'({self._expr_with_parens})'
        return self._expr_with_parens


class ConditionMaker:
    def __init__(self, raw_string: str, func_name: str = 'ddr'):
        self._raw_string = re.sub(r' {2,}', ' ', raw_string).rstrip().lstrip()
        self._counter = Counter(self._raw_string)
        self._manual_parents_control = bool(self._counter[')'] or self._counter['('])
        self._func_name = func_name
        self._result_condition = ''
        self._errors = []
        self._main_expr = self._and_mr_expr = ''
        self._tokens_to_parse = self._processed_tokens = None

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'raw_string="{self._raw_string}" '
            f'errors={self._errors} '
            f'tokens_to_parse={self._tokens_to_parse} '
            f'parsed_tokens={self._processed_tokens} '
            f'main_expr="{self._main_expr}" '
            f'and_mr_expr="{self._and_mr_expr}" '
            f'result_condition="{self._result_condition}"'
            f')'
        )

    def _create_main_expr(self):
        if not self._manual_parents_control and (len(self._tokens_to_parse) > 1):
            wrap_parentheses = True
        else:
            wrap_parentheses = False
        return ' '.join(
            token.get_condition(wrap_parentheses=wrap_parentheses) for token in self._processed_tokens
        )

    def _process_tokens(self):
        self._processed_tokens = []
        for raw_token in self._tokens_to_parse:
            token = Token(raw_token, self._func_name)
            self._errors += token.get_errors()
            self._processed_tokens.append(token)
        for i, token in enumerate(self._processed_tokens, 1):
            operators = [f'"{op}"' for op in MATCHING_OPERATORS]
            if i % 2 == 0: # Чётный токен всегда должен быть оператором.
                if not token.is_operator:
                    self._errors.append(
                        f'Ошибка в фрагменте {token.get_raw_token()}. Данный фрагмент должен быть '
                        f'выражением, а не объединяющим оператором типа {", ".join(operators)}.'
                    )
            else:
                if token.is_operator:
                    self._errors.append(
                        f'Ошибка в фрагменте {token.get_raw_token()}. Данный фрагмент должен быть '
                        f'объединяющим оператором типа {", ".join(operators)}.'
                    )
        return self._processed_tokens

    def _create_result_condition_string(self) -> str:
        if not self._errors:
            if self._and_mr_expr:
                self._result_condition = f'({self._create_main_expr()}) {self._and_mr_expr}'
            else:
                self._result_condition = self._create_main_expr()
        else:
            self._result_condition = ''
        return self._result_condition

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
            self._processed_tokens: MutableSequence[Token] = []
            if len(self._tokens_to_parse) % 2 == 0 or self._tokens_to_parse[0] in MATCHING_OPERATORS:
                self._errors.append(ErrMessages.invalid_condition)
            else:
                self._process_tokens()
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
    # t = Token('22|22')
    # t = Token('|')
    # t = Token('((|)))')
    # print(t)

    s_str = ' 1|2 ,14'
    maker = ConditionMaker(s_str, 'ddo')
    print(maker.process_data_and_build_result_as_dict())
    print(maker)
    debug()
