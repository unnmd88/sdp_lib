import itertools
import re
from collections import Counter, defaultdict
from collections.abc import Sequence, Callable, Generator, Iterable, Container
from functools import wraps
from typing import Any

from docx import Document
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from docx.table import _Rows, _Row

from sdp_lib.passport.constants import TableNames, row0_14_dt, patterns_row1_15_dt, row1_14_dt, \
    patterns_row1_14_dt, allowed_column_lengths_dt, allowed_min_num_rows, patterns_row0_14_dt, \
    DirectionEntities, PatternsDirectionTable, HeadRowsDirectionTableData, dt_mapping, ColNamesDirectionsTable, \
    dt_timing_columns, dt_timing_columns_mapping, matches, AllowedValues
from sdp_lib.passport.passport2.base2 import AbstractRow, DirectionRow, CellData, NumberValidation
from sdp_lib.passport.passport2.utils import remove_left_light_spaces_from_cells
from sdp_lib.passport.passport2.validation.base import  CheckListDirectionRow, \
    BaseCellValidationResult, CheckListTable, BaseValidationResult, Cell
from sdp_lib.passport.passport2.validation.common_validators import validate_geometry, match_cells_one_to_one, \
    validate_sequence_directions_or_stages_nums_and_create_cell, match_cells_one_string_to_many_patterns, \
    validate_number_and_create_cell
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


def validate_tlc(direction_entity, val):
    pass


def validate_timings(direction_entity, t_name: str, val: str):
    tv = NumberValidation([])
    text_is_valid = False
    try:
        val_i = int(val)
        text_is_valid = True
        if direction_entity is None:
            return CellData(val, text_is_valid, None, recovered=val_i, extra=tv)
    except ValueError:
        tv.errors.append(Text.is_not_a_number)
        return CellData(val, text_is_valid, text_is_valid, extra=tv)
    values: AllowedValues = matches[(direction_entity, t_name)]

    if values.min <= val_i <= values.max:  # OK case
        return CellData(val, text_is_valid, text_is_valid, recovered=val_i, extra=tv)

    if val_i < values.min:
        err = Text.val_must_be_gt(values.min)
    elif val_i > values.max:
        err = Text.val_must_be_lt(values.max)
    else:
        raise Exception(f'Debug: val_to_validate not fully validated')
    tv.errors.append(err)
    return CellData(val, text_is_valid, False, recovered=val_i, extra=tv)


@timed
def validate_directions_table(rows: _Rows) -> CheckListTable:
    geometry_check_list = validate_geometry(rows, allowed_column_lengths_dt, allowed_min_num_rows)
    first_row, second_row = get_two_head_rows(rows[0].cells, rows[1].cells)
    length = len(rows[0].cells)
    data_rows = []
    timing_columns = dt_timing_columns_mapping[length]
    print(first_row)
    for i in range(2, length):
        new_line = '\n'
        if i == 5:
            rows[i].cells[2].text += f'{new_line}{new_line.join(t for t in ("abra1", "abra2", "cadanra4"))}'
            rows[i].cells[2].paragraphs[0].paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
            rows[i].cells[2].paragraphs[0].runs[0].font.color.rgb = RGBColor(250, 0 , 0)

            doc.save('abra.docx')
        cells = remove_left_light_spaces_from_cells(rows[i].cells)
        num = validate_num_and_create_cell(next(cells))
        entity = match_cells_one_string_to_many_patterns(next(cells), entity_patterns_and_aliases, True)
        stages = validate_sequence_directions_or_stages_nums_and_create_cell(next(cells))
        tlc = CellData(next(cells))
        timings = (validate_timings(entity.recovered, col_name, next(cells)) if entity.recovered == DirectionEntities.vehicle else CellData('PLUG') for col_name in timing_columns)

        # tzd = validate_number_and_create_cell((entity.recovered, ColNamesDirectionsTable.t_green_ext), next(cells))
        # res = (num, entity, stages, tlc, tzd) + tuple(CellData('PLUG') for _ in range(9))
        chain = itertools.chain(
            (num, entity, stages, tlc, ),
            timings,
           (CellData('PLUG') for _ in range(4)),

        )
        r =  DirectionRow(tuple(c for c in chain))
        print(r.represent(attr_splitter='\n') if i in (8, length - 100) else r)




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

