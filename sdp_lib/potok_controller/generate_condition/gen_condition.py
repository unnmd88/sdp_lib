import re
import sys
import time
from collections import Counter
from typing import MutableSequence

from sdp_lib.potok_controller.generate_condition.constants import (
    Patterns,
    MATCHING_OPERATORS,
    FieldNames,
    ErrMessages
)
from sdp_lib.potok_controller.generate_condition.tokens import Token
from sdp_lib.potok_controller.generate_condition.utils import get_main_and_mr_stmt


class ConditionMaker:
    def __init__(self, raw_string: str, func_name: str = 'ddr', strict_mode = False):
        self._raw_string = re.sub(r' {2,}', ' ', raw_string).rstrip().lstrip()
        self._strict_mode = strict_mode
        self._chars_counter = Counter(self._raw_string)
        self._manual_parents_control = bool(self._chars_counter[')'] or self._chars_counter['('])
        self._func_name = func_name
        self._errors = []
        self._result_condition = ''
        self._main_stmt = self._and_mr_stmt = ''
        self._tokens_to_parse = self._processed_tokens = None

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'raw_string="{self._raw_string}" '
            f'counter="{self._chars_counter}" '
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
        if self._chars_counter[')'] != self._chars_counter['(']:
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

    def _create_full_condition_string(self) -> str:
        if not self._errors:
            if self._and_mr_stmt:
                self._result_condition = f'({self._create_main_stmt()}) {self._and_mr_stmt}'
            else:
                self._result_condition = self._create_main_stmt()
        else:
            self._result_condition = ''
        return self._result_condition

    def get_errors(self) -> MutableSequence[str]:
        return self._errors

    def get_created_condition(self) -> str:
        return self._result_condition

    def get_result_data_as_dict(self):
        return {str(FieldNames.errors): self._errors, str(FieldNames.result_condition): self._result_condition}

    def make(self):
        self._errors = []
        self._check_valid_chars_in_raw_string()
        self._check_valid_num_parens()
        if self._errors:
            self._create_full_condition_string()
            return self.get_result_data_as_dict()

        err, self._main_stmt, self._and_mr_stmt = get_main_and_mr_stmt(self._raw_string)
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
        self._create_full_condition_string()
        return self.get_result_data_as_dict()


def debug():
    while True:
        try:
            print()
            user_data = input('Ввод выражения: ')
            start_time = time.perf_counter()
            _maker = ConditionMaker(user_data)
            print(_maker.make())
            print(_maker)
            print(_maker.get_result_data_as_dict())
            print(f'result_condition: {_maker.get_created_condition()}')
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
    print(maker.make())
    print(maker)
    debug()
