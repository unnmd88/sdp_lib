from enum import StrEnum
from typing import Any

from sdp_lib.passport.constants import ColNamesTimeProgramsTable, ColNamesDirectionsTable, DirectionTypes


class Text(StrEnum):
    bad_num_pp = (
        f'Не задан "{str(ColNamesTimeProgramsTable.num_pp)}" для фазы. '
        f'Допускаются номера в виде целых чисел("1", "2", "6" и т.д) или '
        f'числа через точку("1.1", "1.2", "4.1" и т.д.)'
    )

    always_red_must_be_empty = (
        f'У группы типа "{DirectionTypes.always_red}" не должно быть фаз в '
        f'колонке "{ColNamesDirectionsTable.stages}"'
    )

    income_table_text_rule = (
        f'Некорректные входные данные для обработки. Каждая строка таблицы'
        f'должна начинаться с новой строки("/n"), а каждое значение в'
        f'строке должно быть разделено пробелом или табуляцией.'
    )

    @classmethod
    def get_bad_num(
            cls,
            num_stage: str | int = '',
            cell_name: ColNamesTimeProgramsTable | ColNamesDirectionsTable = ''
    ) -> str:
        return  f'Неверно задан номер в ячейке "{str(cell_name)}": {num_stage}'
        # return (
        #     f'Неверно задан номер "{str(table_name)}": {num_stage}. '
        #     f'Допускаются номера в виде целых чисел("1", "2", "6" и т.д) или '
        #     f'числа через точку("1.1", "1.2", "4.1" и т.д.)'
        # )

    @classmethod
    def get_bad_val(
            cls,
            value: Any = '',
            name: ColNamesTimeProgramsTable | ColNamesDirectionsTable = ''
    ) -> str:
        return f'Неверно задано значение "{name}": {value}'

    @classmethod
    def get_has_doubles(cls, entity: str, column_name: str, doubles: Any):
        return f'У {entity} найдены дубли в "{column_name}": {[el for el in doubles]}'
