from enum import StrEnum

from sdp_lib.passport.constants import ColNamesTimeProgramsTable


class Text(StrEnum):
    bad_num_pp = (
        f'Не задан "{str(ColNamesTimeProgramsTable.num_pp)}" для фазы. '
        f'Допускаются номера в виде целых чисел("1", "2", "6" и т.д) или '
        f'числа через точку("1.1", "1.2", "4.1" и т.д.)'
    )

    @classmethod
    def get_bad_num_stage(cls, num_stage: str | int = '') -> str:
        return (
            f'Неверно представлен номер фазы: "{str(ColNamesTimeProgramsTable.num_stage)}": {num_stage!r}. '
            f'Допускаются номера в виде целых чисел("1", "2", "6" и т.д) или '
            f'числа через точку("1.1", "1.2", "4.1" и т.д.)'
        )