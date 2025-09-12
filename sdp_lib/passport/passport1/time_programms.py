import logging
import re
from dataclasses import dataclass

from sdp_lib.passport.passport1.base import (
    AbstractTableWithStages,
    Cell,
    get_cell_with_value_as_number_,

    Message,
    StageOrDirectionCell,
    AbstractRow,
    get_cell
)
from sdp_lib.passport.constants import (
    ColNamesTimeProgramsTable,
    WEEKDAYS,
    TableNames,
    RowNames,
    ModeNames,
    MessageCategories,
    Fields
)
from sdp_lib.passport.mixins import ReprMixin

from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import read_file_as_string, to_json, timed

DEBUG = True

logger = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class StageRowCells:
    num_pp: Cell
    number: Cell
    directions: StageOrDirectionCell
    weekdays: Cell
    t_osn: Cell
    t_sdvig: Cell
    t_min_ft: Cell
    stage_type: Cell
    t_min_va: Cell
    t_max1_va: Cell
    t_max2_va: Cell
    req_condition: Cell
    ext_condition: Cell
    term_condition: Cell


class StageRow(AbstractRow, ReprMixin):

    name = RowNames.stage

    REST_STAGE = re.compile(r'покоя|крас|-', re.IGNORECASE)

    def __init__(
            self,
            index: int,
            num_pp: int | str,
            num_stage: int | str,
            directions: str,
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
        super().__init__(index)
        self._cells = StageRowCells(
            get_cell_with_value_as_number_(num_pp, ColNamesTimeProgramsTable.num_pp),
            get_cell_with_value_as_number_(num_stage, ColNamesTimeProgramsTable.num_stage),
            StageOrDirectionCell(directions),
            get_cell(ColNamesTimeProgramsTable.weekdays, weekdays),
            get_cell(ColNamesTimeProgramsTable.t_osn, t_osn),
            get_cell(ColNamesTimeProgramsTable.t_sdvig, t_sdvig),
            get_cell(ColNamesTimeProgramsTable.t_min, t_min_ft),
            get_cell(ColNamesTimeProgramsTable.stage_type, stage_type),
            get_cell(ColNamesTimeProgramsTable.t_min, t_min_va),
            get_cell(ColNamesTimeProgramsTable.t_max1, t_max1_va),
            get_cell(ColNamesTimeProgramsTable.t_max2, t_max2_va),
            get_cell(ColNamesTimeProgramsTable.req_condition, req_condition),
            get_cell(ColNamesTimeProgramsTable.ext_condition, ext_condition),
            get_cell(ColNamesTimeProgramsTable.term_condition, term_condition),
        )
        if not self._cells.num_pp.is_valid:
            self._extra_data.add_warnings(Message(Text.bad_num_pp, MessageCategories.validation))
        if not self._cells.number.is_valid:
            self._extra_data.add_errors(Message(Text.get_bad_num(num_stage, ColNamesTimeProgramsTable.num_stage), MessageCategories.validation))
            self._extra_data.permissions.set_val_for_compare_stages(False)
        if not self._cells.directions.is_valid:
            self._extra_data.err_and_warn.add_errors(Message(Text.get_bad_val(directions, ColNamesTimeProgramsTable.directions), MessageCategories.validation))
            self._extra_data.permissions.set_val_for_compare_stages(False)


class HeadTimeProgramRow(AbstractRow, ReprMixin):

    name = RowNames.head_time_table

    def __init__(
            self,
            number: int | str,
            weekdays: str = '',
    ):
        super().__init__(-1)
        self._number = self._get_number(number)
        self._weekdays = self._get_weekdays(weekdays)

    def _get_number(self, init_val: str):
        default_val = None
        try:
            val = int(init_val)
        except ValueError:
            self._extra_data.err_and_warn.add_errors(Message(f'Номер программы не является числом: {init_val!r}.'))
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
                    self._extra_data.err_and_warn.add_errors(
                        Message(f'Дни недели заданы некорректно: {init_val!r}. Пример: <пн,вт,ср,чт,пт,сб,вс>')
                    )
                    break
                val = init_val
        return Cell(ColNamesTimeProgramsTable.number, init_val, default_val, val, is_valid)

    def _extra_init_and_check_data(self):
        pass

    def get_table_number(self) -> int | None:
        return self._number.value


class TimeProgramTable(AbstractTableWithStages, ReprMixin):

    name = TableNames.time_program
    allowed_cnt_row_props = {1, 2, 3}
    row_class = StageRow
    key_name = Fields.stages

    def __init__(
            self,
            income_data: str,
            head_data: HeadTimeProgramRow = HeadTimeProgramRow(1),
            mode: ModeNames = None
    ):
        super().__init__(income_data)
        self._head_data = head_data
        self._mode = mode

    def get_number(self) -> int | None:
        return self._head_data.get_table_number()


@timed
def display_time_programs(raw_data: str = None):
    if raw_data is None:
        data_as_string = read_file_as_string('../_mock_data/time_program_example1')
    else:
        data_as_string = raw_data

    tp_table = TimeProgramTable(data_as_string, HeadTimeProgramRow(1))

    print(tp_table.dump_to_dict())
    print(to_json(tp_table.dump_to_dict()))

    return tp_table



if __name__ == '__main__':
    r = re.compile('\d{2}:\d{2}:\d{2}-\d{2}:\d{2}:\d{2}')
    print(re.findall(r, '07:00:00-11:00:00'))
    row1 = StageRow(0,'1', '1', '1,2,4,5')
    display_time_programs()

