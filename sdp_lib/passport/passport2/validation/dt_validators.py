import re
from collections.abc import Sequence, Callable, Generator
from typing import Any

from docx import Document
from docx.table import _Rows

from sdp_lib.passport.constants import TableNames
from sdp_lib.passport.passport2.patterns import DirectionTablePatterns
from sdp_lib.passport.passport2.validation.base import get_int_or_float, CheckListDirectionRow, \
    BaseCellValidationResult, check_directions_or_stages_string, CheckListTable
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import to_json, timed


def _check_is_directions_table(rows: _Rows) -> bool:
    # return bool(
    #     14 <= len(rows[0].cells) <= 15
    #     and re.search(DirectionTablePatterns.row1_cell0.value, rows[1].cells[0].text) is not None
    #     and re.search(DirectionTablePatterns.row1_cell1.value, rows[1].cells[1].text) is not None
    # )
    first_and_second_rows_is_head = all(
        re.search(p, s) is not None for p, s in zip(
            (DirectionTablePatterns.row1_cell0.value, DirectionTablePatterns.row1_cell1.value),
            (rows[1].cells[0].text, rows[1].cells[1].text),
            strict=True
        )
    )
    try:
        assert first_and_second_rows_is_head
        # Проверка, что третья строка(индекс=2) это строка с первой группой
        cell_num_group = int(rows[2].cells[0].text)
        cell_t_green_ext = (int(rows[2].cells[5].text) - 3)
        assert cell_num_group - 1  >= 0
        assert cell_t_green_ext >= 0
    except (AssertionError, ValueError):
        return False
    return True


def check_length_cols_direction_table(row_length: int) -> str:
    if not row_length in (14, 15):
        return Text.bad_length(TableNames.directions_table, row_length)
    return ''
    # if not len(t_rows[0].cells) in (14, 15):
    #     return Text.bad_length(TableNames.directions_table, len(t_rows[1]))
    # return ''


def check_min_num_rows(num_rows: int) -> str:
    if num_rows >= 3:
        return ''
    return Text.bad_num_rows(str(TableNames.directions_table), num_rows, 'мин=3')


def check_num_direction_or_stage(value) -> str:
    if get_int_or_float(value) is None:
        return f'Недопустимый номер: {value}' if value else f'Номер не задан'
    return ''


dt_struct_validation_functions: Sequence[Callable] = (check_length_cols_direction_table, check_min_num_rows)


def validate_data_row_dt(cells) -> CheckListDirectionRow:
    is_empty = all(not v.text for v in cells)
    num_from_cell = cells[0].text
    num_validation = BaseCellValidationResult(num_from_cell)
    num_validation.set_is_checked(True)
    err_num_msg = check_num_direction_or_stage(num_from_cell)
    num_validation.add_errors(err_num_msg)
    num_validation.set_ok(not bool(err_num_msg))
    stages = cells[2].text
    stages_validation = check_directions_or_stages_string(stages)
    stages_validation.set_is_checked(True)
    return CheckListDirectionRow(num_validation, check_directions_or_stages_string(stages), is_empty)


def validate_geometry_dt(rows_cells) -> Generator[BaseCellValidationResult, Any, None]:
    for func, arg in zip(dt_struct_validation_functions, (len(rows_cells[0].cells), len(rows_cells))):
        instance = BaseCellValidationResult(arg)
        instance.set_is_checked(True)
        err_msg = func(arg)
        instance.set_ok(not bool(err_msg))
        instance.add_errors(err_msg)
        yield instance


@timed
def validate_directions_table(rows_cells: _Rows) -> CheckListTable:
    length_columns, min_num_rows = validate_geometry_dt(rows_cells)
    check_list = CheckListTable(length_columns, min_num_rows)
    for i in range(2, len(rows_cells)):
        check_list.data_rows.append(validate_data_row_dt(rows_cells[i].cells))
    print(to_json(check_list.dump(), 'ff'))
    return check_list


if __name__ == '__main__':
    strings = ('1,2,2,4', '1.1,1.4,5,7,10', '', '     ', '1e,2dqd')
    for s in strings:
        rr = check_directions_or_stages_string(s)

    # path = 'C://Programms//py.projects//sdp_lib//sdp_lib//passport//СО_2094_ул_Островитянова_ул_Ак_Волгина (2)'
    path = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    doc = Document(f'{path}.docx')
    c = CheckListTable()
    validate_directions_table(doc.tables[0].rows)