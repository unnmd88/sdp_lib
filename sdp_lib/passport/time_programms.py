import re
from collections.abc import MutableMapping
from typing import Any

from sdp_lib.passport.base import AbstractEntity, AbstractTable, ColumnData, get_stage_or_direction_data, get_number
from sdp_lib.passport.constants import ColNamesTimeProgramsTable, WEEKDAYS, ModeNames
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.storages import Message, Actions
from sdp_lib.passport.text_messages import Text
from sdp_lib.passport.utils import get_int_or_float, make_int_or_float_collection
from sdp_lib.utils_common.utils_common import remove_chars


class StageRow(AbstractEntity, ReprMixin):

    REST_STAGE = re.compile(r'покоя|крас|-', re.IGNORECASE)

    def __init__(
            self,
            index: int,
            num_pp: int | str,
            num_stage: int | str,
            directions: str,
            num: str = '',
            t_cyc: str = '',
            weekdays: str = '',
            t_osn: str = '',
            t_sdvig: str = '',
            t_min_man: str = '',
            t_min_va: str = '',
            t_max1_va: str = '',
            t_max2_va: str = '',
            req_condition: str = '',
            ext_condition: str = '',
            term_condition: str = ''

    ):
        super().__init__()
        self._actions = Actions()
        self.index = index
        self.num_pp = get_number(num_pp, ColNamesTimeProgramsTable.num_pp)
        if not self.num_pp.is_valid:
            self._err_and_warn.add_warnings(Message(Text.bad_num_pp))
        self.num_stage = get_number(num_stage, ColNamesTimeProgramsTable.num_stage)
        if not self.num_stage.is_valid:
            self._err_and_warn.add_errors(Text.get_bad_num(num_stage, ColNamesTimeProgramsTable.num_stage))
            self._actions.set_val_compare_stages(False)
        self.directions = get_stage_or_direction_data(
            directions, self.REST_STAGE, ColNamesTimeProgramsTable.directions
        )
        print(self.directions)
        self.num = num
        self.t_cyc = t_cyc
        self.weekdays = weekdays
        self.t_osn = t_osn
        self.t_sdvig = t_sdvig
        self.t_min_man = t_min_man
        self.t_min_va = t_min_va
        self.t_max1_va = t_max1_va
        self.t_max2_va = t_max2_va
        self.req_condition = req_condition
        self.ext_condition = ext_condition
        self.term_condition = term_condition

    @property
    def allow_compare_stages(self) -> bool:
        return self._actions.allow_compare_stages


class HeadData(AbstractEntity, ReprMixin):
    def __init__(
            self, number: int | str,
            weekdays: str,

    ):
        super().__init__()
        self._number = self._get_number(number)
        self._weekdays = self._get_number(number)

    def _get_number(self, init_val: str):
        default_val = None
        try:
            val = int(init_val)
        except ValueError:
            self._err_and_warn.add_errors(Message(f'Номер программы не является числом: {init_val!r}.'))
            val = init_val
        return ColumnData(ColNamesTimeProgramsTable.number, init_val, default_val, val)

    def _get_weekdays(self, init_val: str):
        default_val = None
        weekdays = init_val.replace(' ', '').replace(':', '').split(',') # Ожидается строка типа "пн,вт,ср,чт,пт,сб,вс"
        for day in weekdays:
            try:
                WEEKDAYS[day.lower()]
            except KeyError:
                self._err_and_warn.add_errors(
                    Message(f'Дни недели заданы некорректно: {init_val!r}. Пример: <пн,вт,ср,чт,пт,сб,вс>')
                )
                break

            val = init_val
        return ColumnData(ColNamesTimeProgramsTable.number, init_val, default_val, val)

    def _extra_init_and_check_data(self):
        pass


class TimeProgramTable(AbstractTable, ReprMixin):
    def __init__(self, income_data: str, mode: ModeNames):
        super().__init__(income_data)
        self._all_programs: MutableMapping[int, HeadData] = {}

if __name__ == '__main__':
    r = re.compile('\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}')
    print(re.findall(r, '07:00:00-11:00:00'))
    tp1 = StageRow(0,'1', '1', '1,2,4,5')
    print(tp1)
    print(tp1.num_stage)
    print(tp1.directions)
    print(tp1.get_message_storage())
