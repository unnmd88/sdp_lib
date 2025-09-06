import itertools
import re
from collections import Counter, defaultdict
from collections.abc import Sequence, Callable, Generator, Iterable, Container
from functools import wraps
from typing import Any

from docx import Document
from docx.table import _Rows, _Row

from sdp_lib.passport.constants import TableNames, row0_14_dt, patterns_row1_15_dt, row1_14_dt, DirectionTablePatterns, \
    patterns_row1_14_dt, allowed_column_lengths_dt, allowed_min_num_rows, patterns_row0_14_dt, dt_patterns_row0, \
    dt_patterns_row1, DirectionEntities, PatternsDt
from sdp_lib.passport.passport2.base2 import AbstractRow, DirectionRow, CellData
from sdp_lib.passport.passport2.utils import remove_left_light_spaces_from_cells
from sdp_lib.passport.passport2.validation.base import  CheckListDirectionRow, \
    BaseCellValidationResult, CheckListTable, BaseValidationResult, Cell
from sdp_lib.passport.passport2.validation.common_validators import validate_geometry, match_cells, \
    validate_sequence_directions_or_stages_nums_and_create_cell
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import to_json, timed, remove_left_light_spaces, \
    get_stage_or_direction_number_or_none


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


def check_num_direction_or_stage(value) -> str:
    if get_stage_or_direction_number_or_none(value) is None:
        return f'Недопустимый номер: {value}' if value else f'Номер не задан'
    return ''


# dt_struct_validation_functions: Sequence[Callable] = (check_columns_length, check_min_num_rows)
def get_two_head_rows(row0_cells, row1_cells) -> tuple[DirectionRow, DirectionRow]:
    rows_length = len(row0_cells)
    return (
        DirectionRow(tuple(match_cells(remove_left_light_spaces_from_cells(row0_cells), dt_patterns_row0[rows_length], True))),
        DirectionRow(tuple(match_cells(remove_left_light_spaces_from_cells(row1_cells), dt_patterns_row1[rows_length], True))),
    )

def validate_num_and_create_cell(val) -> CellData:
    num = get_stage_or_direction_number_or_none(val)
    is_valid = bool(num)
    return CellData(val, is_valid, is_valid, recovered=num)


def validate_direction_entity_and_create_cell(val) -> CellData:
    entity =  None
    if re.search(PatternsDt.vehicle.value, val):
        entity = DirectionEntities.vehicle
    elif re.search(PatternsDt.arrow.value, val):
        entity = DirectionEntities.arrow
    elif re.search(PatternsDt.pedestrian.value, val):
        entity = DirectionEntities.pedestrian
    elif re.search(PatternsDt.public.value, val):
        entity = DirectionEntities.public
    elif re.search(PatternsDt.tram.value, val):
        entity = DirectionEntities.tram
    elif re.search(PatternsDt.always_red.value, val):
        entity = DirectionEntities.always_red
    is_valid = bool(entity)
    return CellData(val, is_valid, is_valid, recovered=entity != val)


@timed
def validate_directions_table(rows: _Rows) -> CheckListTable:
    geometry_check_list = validate_geometry(rows, allowed_column_lengths_dt, allowed_min_num_rows)
    first_row, second_row = get_two_head_rows(rows[0].cells, rows[1].cells)
    length = len(rows[0].cells)
    data_rows = []
    print(first_row)
    for i in range(2, length):
        cells = remove_left_light_spaces_from_cells(rows[i].cells)
        num = validate_num_and_create_cell(next(cells))
        entity = validate_direction_entity_and_create_cell(next(cells))
        stages = validate_sequence_directions_or_stages_nums_and_create_cell(next(cells))
        res = (num, entity, stages) + tuple(CellData() for _ in range(11))
        r=  DirectionRow(res)
        print(r)




# @timed
# def validate_directions_table(rows_cells: _Rows) -> CheckListTable:
#     length_columns, min_num_rows = validate_geometry(
#         (check_columns_length, len(rows_cells[0].cells), allowed_column_lengths_dt),
#         (check_min_num_rows, len(rows_cells), allowed_column_lengths_dt)
#     )
#     check_list = CheckListTable(length_columns, min_num_rows)
#     print(check_list)
#     for i in range(2, len(rows_cells)):
#         check_list.data_rows.append(validate_data_row_dt(rows_cells[i].cells))
#     print(to_json(check_list.dump(), 'ff'))
#     return check_list


if __name__ == '__main__':
    # strings = ('1,2,2,4', '1.1,1.4,5,7,10', '', '     ', '1e,2dqd')
    # for s in strings:
    #     rr = check_directions_or_stages_string(s)
    #
    # # path = 'C://Programms//py.projects//sdp_lib//sdp_lib//passport//СО_2094_ул_Островитянова_ул_Ак_Волгина (2)'
    path1 = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    path2 = '/home/auser/Downloads/ПД Паспорт шаблон 2025 (Копия)'
    path3 = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_ (1)'
    path4 = "C:\Programms\py.projects\sdp_lib\sdp_lib\passport\СО_2094_ул_Островитянова_ул_Ак_Волгина (2).docx"

    doc = Document(f'{path4}')
    # c = CheckListTable()
    validate_directions_table(doc.tables[0].rows)

