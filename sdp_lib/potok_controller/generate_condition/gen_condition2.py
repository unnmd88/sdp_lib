import re
from enum import StrEnum
from typing import MutableSequence


class ErrMessages(StrEnum):
    invalid_condition = 'Некорректное условие'


def get_main_and_mr_expr(cond_string: str) -> tuple[None | str, str, str]:
    gr = cond_string.split(',')
    error = None
    main_expr = mr_expr = ''
    if len(gr) == 2:
        main_expr, mr_expr = gr[0], f'and mr(G{gr[1]})'
    elif len(gr) == 1:
        main_expr, mr_expr = gr[0], ''
    else:
        error = ErrMessages.invalid_condition
    print(f'>> {error, main_expr, mr_expr}')
    return error, main_expr, mr_expr


allowed_operators = {'|': 'or', '&': 'and'}


class Tokens:
    def __init__(self, token: str, func_name = 'ddr'):
        self._raw_token = token.replace(" ", '')
        self._func_name = func_name
        self._errors = []
        self._left = ''
        self._right = ''
        self._op = ''
        self._processed_expr = None
        self._check_token_and_add_err_if_has()

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'errors={self._errors} '
            f'raw_token={self._raw_token} '
            f'func_name={self._func_name} '
            f'processed_expr=<{self._processed_expr}>'
            f')'
        )

    def _check_token_and_add_err_if_has(self):
        self._processed_expr = allowed_operators.get(self._raw_token, '')
        if self._processed_expr:
            return self._processed_expr

        for op in allowed_operators:
            success_splited = self._raw_token.split(op)
            if len(success_splited) == 2:
                self._left, self._right = success_splited
                self._op = allowed_operators[op]
                break
        else:
            self._errors.append(
                f'Отсутствует допустимый оператор в выражении {self._raw_token}. '
                f'Используйте один из: {[f"<{op}>" for op in allowed_operators]}'
            )
            return False
        try:
            self._left, self._right = map(int, success_splited)
        except ValueError:
            self._errors.append(f'Ошибка в выражении: <{self._raw_token}>. Номер группы должен быть числом')
            return False

        self._op = allowed_operators[op]
        self._processed_expr = (
            f' {self._op} '.join(f'{self._func_name}(D{num})' for num in range(self._left, self._right + 1))
        )
        return True

    def _validate_token(self):
        self._processed_expr = allowed_operators.get(self._raw_token, '')
        if not self._processed_expr:
            for op in allowed_operators:
                success_splited = self._raw_token.split(op)
                if len(success_splited) == 2:
                    try:
                        self._left, self._right = map(int, success_splited)
                        self._op = allowed_operators[op]
                        self._processed_expr = (
                            f' {self._op} '.join(
                                f'{self._func_name}(D{num})' for num in range(self._left, self._right + 1))
                        )
                    except ValueError:
                        self._processed_expr = ''
                        self._errors.append(f'Ошибка в выражении: <{self._raw_token}>. Номер группы должен быть числом')
                    break
            else:
                self._errors.append(f'Недопустимые символы в выражении {self._raw_token}')

    def get_errors(self):
        return self._errors

    def get_raw_token(self):
        return self._raw_token

    def get_func_name(self):
        return self._func_name

    def get_processed_condition(self):
        return self._processed_expr


class ConditionMaker:
    def __init__(self, raw_string: str):
        self._raw_string = re.sub(r' {2,}', ' ', raw_string)
        self._processed_expr = ''
        self._errors = []
        self._main_expr = self._and_mr_expr = ''
        self._tokens_to_parse = self._parsed_tokens = None

    def _create_parsed_tokens(self):
        self._parsed_tokens = []
        for raw_token in self._tokens_to_parse:
            token = Tokens(raw_token)
            self._errors += token.get_errors()
            self._parsed_tokens.append(token)
        return self._parsed_tokens

    def _create_main_expr(self):
        return ' '.join(token.get_processed_condition() for token in self._parsed_tokens)

    def _create_condition_string(self) -> str:
        if not self._errors:
            if self._and_mr_expr:
                self._processed_expr = f'({self._create_main_expr()}) {self._and_mr_expr}'
            else:
                self._processed_expr = self._create_main_expr()
        else:
            self._processed_expr = ''
        return self._processed_expr

    def process_data_and_build_result_as_dict(self):
        err, self._main_expr, self._and_mr_expr = get_main_and_mr_expr(self._raw_string)
        if err is not None:
            self._errors.append(err)
            return
        self._tokens_to_parse = self._main_expr.split()
        self._parsed_tokens: MutableSequence[Tokens] = []

        if len(self._tokens_to_parse) % 2 == 0 or self._tokens_to_parse[0] in allowed_operators:
            self._errors.append(ErrMessages.invalid_condition)
            return
        self._create_parsed_tokens()
        return {'errors': self._errors, 'processed_string': self._create_condition_string()}


if __name__ == '__main__':
    # generate_condition_string('1-3, 2-5,')
    s = '1|3, 2-5,'.replace(" ", '')
    pt = r'\d[\|,\&]{1}\d'
    # print(re.findall(pt, s))
    # print('3|8 & 5&9 | 10|17'.split())
    # s_str = '3|r & 5&9 | 10|17,12'
    s_str = '& 5&9 | 10|17,12'
    processed_condition = ConditionMaker(s_str)
    print(processed_condition.process_data_and_build_result_as_dict())


    # print()
    # s_str = '1|2'
    # print(parse_string(s_str))