import re
from typing import (
    Sequence,
    Pattern
)

from sdp_lib.potok_controller.generate_condition.constants import MATCHING_OPERATORS, Patterns, ALLOWED_PARENS


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