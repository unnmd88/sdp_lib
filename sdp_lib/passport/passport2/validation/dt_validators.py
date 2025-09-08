import itertools
import re
from collections import Counter, defaultdict
from collections.abc import Sequence, Callable, Generator, Iterable, Container
from enum import IntEnum
from functools import wraps
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from docx.table import _Rows, _Row, Table

from sdp_lib.passport.constants import TableNames, row0_14_dt, patterns_row1_15_dt, row1_14_dt, \
    patterns_row1_14_dt, allowed_column_lengths_dt, allowed_min_num_rows, patterns_row0_14_dt, \
    DirectionEntities, PatternsDirectionTable, HeadRowsDirectionTableData, dt_mapping_from_length, ColNamesDirectionsTable, \
    dt_timing_columns, dt_timing_columns_mapping, matches, AllowedValues
from sdp_lib.passport.passport2.base2 import AbstractRow, DirectionRow, CellData, NumberValidation, CellMapping, \
    MessageStorage
from sdp_lib.passport.passport2.utils import remove_left_light_spaces_from_cell_text, add_text_co_cell
from sdp_lib.passport.passport2.validation.base import  CheckListDirectionRow, \
    BaseCellValidationResult, CheckListTable, BaseValidationResult, Cell
from sdp_lib.passport.passport2.validation.common_validators import validate_geometry, \
    validate_sequence_directions_or_stages_nums_and_create_cell, \
    match_cells_one_string_to_many_patterns_and_create_cell, \
    validate_number_and_create_cell, match_one_to_one_and_load_errors_if_has_and_create_cell, create_cells_for_head_row, \
    create_default_cells
from sdp_lib.passport.text_messages import Text
from sdp_lib.passport.passport2.utils import write_messages_to_cell
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
            remove_left_light_spaces_from_cell_text(row0_cells),
            names_and_patterns.first_row_patterns,
            names_and_patterns.first_row_names
        ),

        (
            remove_left_light_spaces_from_cell_text(row1_cells),
            names_and_patterns.second_row_patterns,
            names_and_patterns.second_row_names
        ),
    )


def num_validate_and_load_errors_if_has_and_create_cell(cell: CellMapping) -> CellData:
    txt = cell.cell.text
    num = get_stage_or_direction_number_or_none(txt)
    is_valid = bool(num)
    return CellData(
        value=txt,
        text_is_valid=is_valid,
        context_is_valid=is_valid,
        converted_val=num if is_valid else None,
        cell_mapping=cell,
        messages=MessageStorage([Text.bad_number] if not is_valid and txt else [], [])
    )


def validate_tlc(direction_entity, val):
    pass


def validate_timings(direction_entity, t_name: str, val: str):
    tv = NumberValidation([])
    text_is_valid = False
    try:
        val_i = int(val)
        text_is_valid = True
        if direction_entity is None:
            return CellData(val, text_is_valid, None, recovered_txt=val_i, extra=tv)
    except ValueError:
        tv.errors.append(Text.is_not_a_number)
        return CellData(val, text_is_valid, text_is_valid, extra=tv)
    values: AllowedValues = matches[(direction_entity, t_name)]

    if values.min <= val_i <= values.max:  # OK case
        return CellData(val, text_is_valid, text_is_valid, recovered_txt=val_i, extra=tv)

    if val_i < values.min:
        err = Text.val_must_be_gt(values.min)
    elif val_i > values.max:
        err = Text.val_must_be_lt(values.max)
    else:
        raise Exception(f'Debug: val_to_validate not fully validated')
    tv.errors.append(err)
    return CellData(val, text_is_valid, False, recovered_txt=val_i, extra=tv)


class DirectionTablePositionMapping(IntEnum):
    num                 = 0
    entity              = 1
    stages              = 2
    tlc                 = 3
    t_green_ext         = 4
    t_green_flashing    = 5
    t_green_yellow      = 6
    t_red               = 7
    t_red_yellow        = 8
    t_z                 = 9
    t_zz                = 10
    always_red          = 11
    toov_red            = 12
    toov_green          = 13
    description         = 14


@timed
def validate_directions_table(i_table: int, table: Table, ) -> CheckListTable:
    rows: _Rows = table.rows
    geometry_check_list = validate_geometry(rows, allowed_column_lengths_dt, allowed_min_num_rows)
    length = len(table.columns)
    names_and_patterns: HeadRowsDirectionTableData = dt_mapping_from_length[length]
    first_row = tuple(create_default_cells(i_table, 0, rows[0].cells))
    second_row = tuple(create_cells_for_head_row(
        i_table, 1, rows[1].cells, names_and_patterns.second_row_patterns, names_and_patterns.second_row_names
    ))

    print(f'length: {length}')
    timing_columns = dt_timing_columns_mapping[length]
    # print(first_row)
    for i in range(2, length):
        cells = rows[i].cells
        num = num_validate_and_load_errors_if_has_and_create_cell(
            CellMapping(i_table, 0, i, remove_left_light_spaces_from_cell_text(cells[0]))
        ).write_messages_to_table_cell()

        # entity = match_cells_one_string_to_many_patterns_and_create_cell(next(cells), entity_patterns_and_aliases, True)
        entity = match_cells_one_string_to_many_patterns_and_create_cell(
            CellMapping(i_table, 1, i, remove_left_light_spaces_from_cell_text(cells[1])),
            entity_patterns_and_aliases,
            True
        ).write_messages_to_table_cell()

        # stages = validate_sequence_directions_or_stages_nums_and_create_cell(next(cells))
        # tlc = CellData(next(cells))
        # timings = (validate_timings(entity.recovered_val, col_name, next(cells)) if entity.recovered_val == DirectionEntities.vehicle else CellData('PLUG') for col_name in timing_columns)

        # tzd = validate_number_and_create_cell((entity.recovered, ColNamesDirectionsTable.t_green_ext), next(cells))
        # res = (num, entity, stages, tlc, tzd) + tuple(CellData('PLUG') for _ in range(9))
        chain = itertools.chain(
            (num, entity, ),
           (CellData('PLUG') for _ in range(12)),

        )
        r =  DirectionRow(tuple(c for c in chain))
        print(r.represent(attr_splitter='\n') if i in (8, length - 100) else r)

    doc.save('abra.docx')


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
    path5 = '/home/auser/py.projects/sdp_lib/sdp_lib/passport/СО_2094_ул_Островитянова_ул_Ак_Волгина_2.docx'


    doc = Document(path5)
    # c = CheckListTable()
    validate_directions_table(0, doc.tables[0])

