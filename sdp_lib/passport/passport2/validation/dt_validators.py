import itertools
import re
from collections import Counter, defaultdict
from collections.abc import Sequence, Callable, Generator, Iterable, Container
from functools import wraps
from typing import Any

from docx import Document
from docx.table import _Rows, _Row

from sdp_lib.passport.constants import TableNames, row0_14_dt, patterns_row1_15_dt, row1_14_dt, \
    patterns_row1_14_dt, allowed_column_lengths_dt, allowed_min_num_rows, patterns_row0_14_dt, dt_patterns_row0, \
    dt_patterns_row1, DirectionEntities, PatternsDirectionTable, HeadRowsDirectionTableData, dt_mapping
from sdp_lib.passport.passport2.base2 import AbstractRow, DirectionRow, CellData
from sdp_lib.passport.passport2.utils import remove_left_light_spaces_from_cells
from sdp_lib.passport.passport2.validation.base import  CheckListDirectionRow, \
    BaseCellValidationResult, CheckListTable, BaseValidationResult, Cell
from sdp_lib.passport.passport2.validation.common_validators import validate_geometry, match_cells_one_to_one, \
    validate_sequence_directions_or_stages_nums_and_create_cell, match_cells_one_string_to_many_patterns
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import to_json, timed, remove_left_light_spaces, \
    get_stage_or_direction_number_or_none


entity_patterns_and_aliases = (
    (PatternsDirectionTable.vehicle.value, DirectionEntities.vehicle,),
    (PatternsDirectionTable.arrow.value, DirectionEntities.arrow,),
    (PatternsDirectionTable.pedestrian.value, DirectionEntities.pedestrian,),
    (PatternsDirectionTable.always_red.value, DirectionEntities.always_red,),
    (PatternsDirectionTable.public.value, DirectionEntities.public,),
    (PatternsDirectionTable.tram.value, DirectionEntities.tram,),
)


def _check_is_directions_table(rows: _Rows) -> bool:
    first_and_second_rows_is_head = all(
        re.match(p, s) is not None for p, s in zip(
            (PatternsDirectionTable.num_direction.value, PatternsDirectionTable.entity_direction.value),
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


def _get_head_rows_iter(row0_cells, row1_cells, names_and_patterns):
    return (
        (
            remove_left_light_spaces_from_cells(row0_cells),
            names_and_patterns.first_row_patterns,
            names_and_patterns.first_row_names
        ),

        (
            remove_left_light_spaces_from_cells(row1_cells),
            names_and_patterns.second_row_patterns,
            names_and_patterns.second_row_names
        ),
    )


def get_two_head_rows(row0_cells, row1_cells) -> Iterable[DirectionRow, DirectionRow]:
    rows_length = len(row0_cells)
    names_and_patterns: HeadRowsDirectionTableData = dt_mapping[rows_length]
    for row, patterns, recover in (_get_head_rows_iter(row0_cells, row1_cells, names_and_patterns)):
        yield DirectionRow(tuple(match_cells_one_to_one(row, patterns, recover, True)))


def validate_num_and_create_cell(val) -> CellData:
    num = get_stage_or_direction_number_or_none(val)
    is_valid = bool(num)
    return CellData(val, is_valid, is_valid, recovered=num)


def validate_direction_entity_and_create_cell(val) -> CellData:
    entity =  None
    if re.search(PatternsDirectionTable.vehicle.value, val):
        entity = DirectionEntities.vehicle
    elif re.search(PatternsDirectionTable.arrow.value, val):
        entity = DirectionEntities.arrow
    elif re.search(PatternsDirectionTable.pedestrian.value, val):
        entity = DirectionEntities.pedestrian
    elif re.search(PatternsDirectionTable.public.value, val):
        entity = DirectionEntities.public
    elif re.search(PatternsDirectionTable.tram.value, val):
        entity = DirectionEntities.tram
    elif re.search(PatternsDirectionTable.always_red.value, val):
        entity = DirectionEntities.always_red
    is_valid = bool(entity)
    return CellData(val, is_valid, is_valid, recovered=entity)


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
        entity = match_cells_one_string_to_many_patterns(next(cells), entity_patterns_and_aliases, True)
        stages = validate_sequence_directions_or_stages_nums_and_create_cell(next(cells))
        res = (num, entity, stages) + tuple(CellData() for _ in range(11))
        r =  DirectionRow(res)
        print(r if i == 8 else 'skipped')




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

