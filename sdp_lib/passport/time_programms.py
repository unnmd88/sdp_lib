import pprint
import re
import time
from collections.abc import MutableMapping

from sdp_lib.passport.base import AbstractTable, Cell, get_stage_or_direction_data, get_number_data, AbstractRow
from sdp_lib.passport.constants import ColNamesTimeProgramsTable, WEEKDAYS, TableNames, RowNames, ModeNames
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.storages import Message, Actions, StagesData
from sdp_lib.passport.text_messages import Text



class StageRow(AbstractRow, ReprMixin):

    row_name = RowNames.stage

    REST_STAGE = re.compile(r'покоя|крас|-', re.IGNORECASE)

    def __init__(
            self,
            index: int,
            num_pp: int | str,
            num_stage: int | str,
            directions: str,
            t_cyc: str = '',
            weekdays: str = '',
            t_osn: str = '',
            t_sdvig: str = '',
            t_min_ft: str = '',
            stage_type: str = '',
            t_min_va: str = '',
            t_max1_va: str = '',
            t_max2_va: str = '',
            req_condition: str = '',
            ext_condition: str = '',
            term_condition: str = ''

    ):
        super().__init__()
        self.index = index
        self.num_pp = get_number_data(num_pp, ColNamesTimeProgramsTable.num_pp)
        if not self.num_pp.is_valid:
            self._err_and_warn.add_warnings(Message(Text.bad_num_pp))
        self.number = get_number_data(num_stage, ColNamesTimeProgramsTable.num_stage)
        if not self.number.is_valid:
            self._err_and_warn.add_errors(Text.get_bad_num(num_stage, ColNamesTimeProgramsTable.num_stage))
            self._actions.set_val_for_compare_stages(False)
        self.directions = get_stage_or_direction_data(
            directions, self.REST_STAGE, ColNamesTimeProgramsTable.directions
        )
        if self.directions.column_data.is_valid is False:
            self._actions.set_val_for_compare_stages(False)
        print(f'DD: {self.directions}')
        self.t_cyc = t_cyc
        self.weekdays = weekdays
        self.t_osn = t_osn
        self.t_sdvig = t_sdvig
        self.t_min_ft = t_min_ft
        self.stage_type = stage_type
        self.t_min_va = t_min_va
        self.t_max1_va = t_max1_va
        self.t_max2_va = t_max2_va
        self.req_condition = req_condition
        self.ext_condition = ext_condition
        self.term_condition = term_condition

    @property
    def allow_compare_stages(self) -> bool:
        return self._actions.allow_compare_stages


class HeadDataRow(AbstractRow, ReprMixin):

    row_name = RowNames.head_time_table

    def __init__(
            self,
            number: int | str,
            weekdays: str = '',

    ):
        super().__init__()
        self._number = self._get_number(number)
        self._weekdays = self._get_weekdays(weekdays)

    def _get_number(self, init_val: str):
        default_val = None
        try:
            val = int(init_val)
        except ValueError:
            self._err_and_warn.add_errors(Message(f'Номер программы не является числом: {init_val!r}.'))
            val = None
        return Cell(ColNamesTimeProgramsTable.number, init_val, default_val, val)

    def _get_weekdays(self, init_val: str):
        default_val = None
        is_valid = True
        val = init_val
        if init_val == '':
            is_valid = False
        else:
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
        return Cell(ColNamesTimeProgramsTable.number, init_val, default_val, val, is_valid)

    def _extra_init_and_check_data(self):
        pass

    def get_table_number(self) -> int | None:
        return self._number.value


class TimeProgramTable(AbstractTable, ReprMixin):

    table_name = TableNames.time_program
    allowed_cnt_row_props = {1, 2, 3}
    row_class = StageRow

    def __init__(self, income_data: str, head_data: HeadDataRow, mode: ModeNames = None):
        super().__init__(income_data)
        self._head_data = head_data
        self._mode = mode

    def get_number(self) -> int | None:
        return self._head_data.get_table_number()


class TimeProgramTables:
    def __init__(self, *tables: TimeProgramTable):
        self._tables = {table.get_number(): table for table in tables}
        print(f'self._tables: {self._tables}')

    def __getitem__(self, item: int | float):
        return self._tables[item]

    def __iter__(self):
        return (table for table in self._tables.values())

    def as_dict(self) -> MutableMapping[int | float, TimeProgramTable]:
        return self._tables




def display_time_programs(raw_data: str = None) -> TimeProgramTable:
    if raw_data is None:
        raw_data = (
            '1\t1\t1, 2, 8, 10, 11, 14, 21, 22\n'
            '2\t2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n'
            '3\t3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n'
            '4\t4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n'
            '5\t5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n'
            '6\t6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n'
            '7\t7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n'
            '8\t8\t1, 5, 7, 10, 11, 16, 19, 22\n'
            '9\t9\t1, 5, 7, 10, 11, 16, 19, 22\n'
            '10\t10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()
        )
    start_time = time.perf_counter()
    # grp = DirectionRow(0, '12s', direction_type='Пост красн.', stages='1,3,4,43')
    # print(grp)
    # print('-*-' * 100)

    time_program_table = TimeProgramTable(raw_data, HeadDataRow(1))
    tables = TimeProgramTables(time_program_table)
    for t in tables:
        print(f't: {t}')
    print(tables[1])
    print(f'tables: {tables}')
    print()
    print(time_program_table)
    pprint.pprint(time_program_table.get_all_rows())
    print(f'Время составило: {time.perf_counter() - start_time}')
    # for k, v in grp.__dict__.items():
    #     print(f'k:{k}={v}')
    pprint.pprint(time_program_table.get_stages_data().get_direction_to_stages_mapping())
    pprint.pprint(time_program_table.get_stages_data().get_stage_to_direction_mapping())
    return time_program_table



if __name__ == '__main__':
    r = re.compile('\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}')
    print(re.findall(r, '07:00:00-11:00:00'))
    tp1 = StageRow(0,'1', '1', '1,2,4,5')
    print(tp1)
    print(tp1.number)
    print(tp1.directions)
    print(tp1.get_message_storage())
    _data2 = '1\t1, 2, 8, 10, 11, 14, 21, 22\n2\t2, 4, 8, 9, 11, 12, 17, 22, 25\n3\t4, 5, 8, 9, 11, 12, 17, 19, 20, 21, 22\n4\t3, 4, 7, 8, 11, 12, 17, 19, 21, 22\n5\t6, 7, 10, 11, 12, 15, 16, 19, 22\n6\t5, 6, 10, 11, 12, 13, 15, 16, 23, 25\n7\t5, 6, 10, 12, 13, 15, 16, 18, 23, 25\n8\t1, 5, 7, 10, 11, 16, 19, 22\n9\t1, 5, 7, 10, 11, 16, 19, 22\n10\t5, 6, 10, 12, 13, 15, 16, 18, 19\n'.rstrip()

    display_time_programs(_data2)
