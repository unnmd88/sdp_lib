import re
from collections import deque
from dataclasses import dataclass
from enum import StrEnum
from typing import MutableSequence


class ErrMessages(StrEnum):
    invalid_condition = 'Некорректное условие'


def get_main_and_mr_expr(cond_string: str) -> tuple[None | str, str, str]:
    gr = cond_string.split(',')
    error = None
    main_expr = mr_expr = ''
    if len(gr) == 2:
        main_expr, mr_expr = gr[0], f' and mr(G{gr[1]})'
    elif len(gr) == 1:
        main_expr, mr_expr = gr[0], ''
    else:
        error = ErrMessages.invalid_condition
    print(f'>> {error, main_expr, mr_expr}')
    return error, main_expr, mr_expr





allowed_operators = {'|': 'or', '&': 'and'}


class Cond:

    def __init__(self, expr: str, left_op = '', func_name = 'ddr'):
        self._raw_expr = expr
        self._left_op = left_op
        self._func_name = func_name
        self._errors = []
        self._processed_expr = ''
        for op in allowed_operators:
            success_splited = self._raw_expr.split(op)
            if len(success_splited) == 2:
                try:
                    self._left, self._right = map(int, success_splited)
                except ValueError:
                    self._errors.append(f'Ошибка в выражении: {op}. Номер группы должен быть числом')
                self._op = op.replace(" ", '')
                break
        else:
            self._errors.append(f'Недопустимые символы в выражении {self._raw_expr}')

        if left_op and left_op not in allowed_operators:
            self._errors.append(f'Недопустимый оператор перед условием: {self._raw_expr}')
        if not self._errors:
            op = allowed_operators[self._op]
            self._processed_expr = (
                f' {op} '.join(f'{self._func_name}(D{num})' for num in range(self._left, self._right + 1))
            )

    def get_raw_expression(self):
        return self._raw_expr

    def get_errors(self):
        return self._errors

    def get_left_op(self):
        return self._left_op

    def get_func_name(self):
        return self._func_name

    def get_processed_expression(self):
        return self._processed_expr

    #
    #
    # def __repr__(self):
    #     return (
    #         f'{self.__class__.__name__}('
    #         f'expr={self._expr} '
    #         f'left_op={self._left_op} '
    #         f'func_name={self._func_name} '
    #         f'condition_string=<{self.get_string_condition()}>'
    #         f')'
    #     )
    #
    # def set_func_name(self, name: str):
    #     self._func_name = name
    #
    # def get_string_condition(self):
    #     op = allowed_operators[self._op]
    #     cond = f' {op} '.join(f'{self._func_name}(D{num})' for num in range(self._left, self._right + 1))
    #     # print(f'cond: {cond}')
    #     # print(f'{self._left_op} {cond}')
    #     if self._left_op:
    #         return f' {allowed_operators[self._left_op]} {cond}'
    #     return cond


class ConditionMaker:
    def __init__(self, raw_string: str):
        self._raw_string = re.sub(r' {2,}', ' ', raw_string)
        self._processed_string = ''
        self._errors = []
        self._main_expr = self._and_mr_expr = ''
        self._tokens_to_parse = self._parsed_tokens = None

    def get_result_as_dict(self):
        print(self._parsed_tokens)
        print(self._tokens_to_parse)
        return {'errors': self._errors, 'processed_string': self._processed_string}

    def build_processed_condition_string(self):
        err, self._main_expr, self._and_mr_expr = get_main_and_mr_expr(self._raw_string)
        if err is not None:
            self._errors.append(err)
            return
        self._tokens_to_parse = self._main_expr.split()
        stack_tokens_to_parse = deque(self._tokens_to_parse)
        self._parsed_tokens: MutableSequence[Cond] = []
        self._processed_string = ''
        if len(self._tokens_to_parse) % 2 == 0 or self._tokens_to_parse[0] in allowed_operators:
            self._errors.append(ErrMessages.invalid_condition)
            return
        first = Cond(stack_tokens_to_parse.popleft())
        self._parsed_tokens.append(first)
        while stack_tokens_to_parse:
            left_op, expr = stack_tokens_to_parse.popleft(), stack_tokens_to_parse.popleft()
            self._parsed_tokens.append(Cond(expr, left_op))
        self.build_condition_string()

    def build_condition_string(self) -> str:
        for t in self._parsed_tokens:
            self._processed_string += t.get_processed_condition()
        if self._and_mr_expr:
            self._processed_string = f'({self._processed_string}) {self._and_mr_expr}'
        self._processed_string = re.sub(r' {2,}', ' ', self._processed_string)
        print(f'self._new_condition_string: {self._processed_string}')
        return self._processed_string



def parse_string(string: str):
    processed_condition = ConditionMaker(string)
    processed_condition.build_processed_condition_string()
    print(processed_condition.get_result_as_dict())



# def parse_string(string: str) -> list[str]:
#     string = re.sub(r' {2,}', ' ', string)
#     parsed_tokens = []
#     main_expr, mr_expr = get_main_and_mr_expr(string)
#     print(f'main_expr: {main_expr}')
#     print(f'mr_expr: {mr_expr}')
#     print(f'main_expr.splited: {main_expr.split()}')
#     tokens = deque(main_expr.split())
#     print(f'tokens: {tokens}')
#     if len(tokens) % 2 == 0 or tokens[0] in allowed_operators:
#         raise ValueError
#
#     first = Cond(tokens.popleft())
#     print(first)
#     # first.get_string_condition()
#     parsed_tokens.append(first)
#     while tokens:
#         left_op, expr = tokens.popleft(), tokens.popleft()
#         parsed_tokens.append(Cond(expr, left_op))
#     res = ''
#     for r in parsed_tokens:
#         r.get_string_condition()
#         res += r.get_string_condition()
#     if mr_expr:
#         res = f'({res}) {mr_expr}'
#     res = re.sub(r' {2,}', ' ', res)
#     print(f'rrr: {res}')




if __name__ == '__main__':
    # generate_condition_string('1-3, 2-5,')
    s = '1|3, 2-5,'.replace(" ", '')
    pt = r'\d[\|,\&]{1}\d'
    # print(re.findall(pt, s))
    # print('3|8 & 5&9 | 10|17'.split())
    s_str = '3|8 & 5&9 | 10|17,12'
    print(parse_string(s_str))
    # print()
    # s_str = '1|2'
    # print(parse_string(s_str))