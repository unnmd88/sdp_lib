from enum import StrEnum

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

    @classmethod
    def get_bad_num(
            cls,
            num_stage: str | int = '',
            table_name: ColNamesTimeProgramsTable | ColNamesDirectionsTable = ''
    ) -> str:
        return (
            f'Неверно задан номер "{str(table_name)}": {num_stage}. '
            f'Допускаются номера в виде целых чисел("1", "2", "6" и т.д) или '
            f'числа через точку("1.1", "1.2", "4.1" и т.д.)'
        )
