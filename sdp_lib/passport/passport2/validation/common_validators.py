import re
from collections import defaultdict
from collections.abc import (
    Iterable,
    Sequence,
    Container
)

from docx import Document
from docx.table import (
    _Rows,
    _Cell
)

from sdp_lib.passport.constants import (
    row0_14_dt,
    row1_14_dt,
    row0_15_dt,
    Patterns,
    AllowedValues,
    timing_matches,
    PatternsDirectionTable
)
from sdp_lib.passport.passport2.base2 import (
    MessageStorage,
    ValidationData,
    CellData,
    DirectionsOrStagesSequenceValidation,
    Comparison,
    NumberValidation,
    CellMapping
)
from sdp_lib.passport.passport2.check_lists import TableGeometryCheckList
from sdp_lib.passport.passport2.utils import (
    repair_string_if_sep_in_illegal_pos,
    remove_left_light_spaces_from_cell_text
)
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import get_stage_or_direction_number_or_none

"""

** Проверка соответствия всех ячеек заданному образцу. **

** Проверка ячейки ** :
1. Текст
2. 

** Проверка дублей в строке(row) **

"""


def check_is_directions_table(rows: _Rows) -> bool:
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


def validate_geometry(
    rows: _Rows,
    allowed_lengths: Container,
    min_rows: int,
) -> TableGeometryCheckList:
    num_cols = len(rows[0].cells)
    num_rows = len(rows)
    return TableGeometryCheckList(
        allowed_lengths,
        min_rows,
        ValidationData(num_cols, num_cols in allowed_lengths),
        ValidationData(num_rows, num_rows >= min_rows),
    )


def gen_cell_mappings_and_lrstrip_in_cell_text(
    i_table: int,
    i_row: int,
    docx_cells: Iterable[_Cell],
):
    return (CellMapping(i_table, i, i_row, remove_left_light_spaces_from_cell_text(c)) for i, c in enumerate(docx_cells))


def create_default_cells(
    i_table: int,
    i_row: int,
    cells: Iterable[_Cell],
):
    for i_col, c in enumerate(cells):
        src_txt = c.text
        txt_without_spaces = remove_left_light_spaces_from_cell_text(c).text
        yield CellData(
            value=src_txt,
            recovered_val=txt_without_spaces if len(src_txt) != len(txt_without_spaces) else None,
            cell_mapping=CellMapping(i_table, i_col, i_row, c),
        )


def create_cells_for_head_row(
    i_table: int,
    i_row: int,
    cells: Iterable[_Cell],
    patterns: Iterable[str | re.Pattern],
    to_recover: Iterable[str] = None,
):
    cells_lr_strip = (remove_left_light_spaces_from_cell_text(c) for c in  cells)
    for i_col, (c, p, r) in enumerate(zip(cells_lr_strip, patterns, to_recover, strict=True)):
        cm = CellMapping(i_table, i_col, i_row, c)
        txt = c.text
        res = bool(re.match(p, txt))
        was_recovered = to_recover if len(txt) != len(r) else None
        yield CellData(
            value=txt,
            text_is_valid=res,
            context_is_valid=res,
            recovered_val=was_recovered,
            cell_mapping=cm,
            messages=MessageStorage([Text.name_error] if was_recovered else [], [])
        ).write_messages_to_table_cell()


def num_validate_and_create_cell(cell: CellMapping) -> CellData:
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


def get_alias(string, patterns_and_aliases: Sequence[tuple[re.Pattern | str, str]]) -> str | None:
    if string:
        for data in patterns_and_aliases:
            if re.match(data[0], string) is not None:
                return data[1]
    return None


def match_cells_one_string_to_many_patterns_and_create_cell(
    cell_mapping: CellMapping,
    patterns_and_aliases: Sequence[tuple[str | re.Pattern, str]],
    duplicate_pattern_result_to_context=False
):
    txt = cell_mapping.cell.text
    alias = get_alias(txt, patterns_and_aliases)
    is_valid = bool(alias)
    recovered_val_by_alias = alias if alias is not None and len(alias) != len(txt) else None
    if alias and len(alias) == len(txt) or not txt:
        err_has_differences_in_src_text_and_alias = []
    elif alias and len(alias) != len(txt):
        err_has_differences_in_src_text_and_alias = [Text.typo_in_name]
    elif txt and alias is None:
        err_has_differences_in_src_text_and_alias = [Text.invalid_name]
    else:
        raise AssertionError('DEBUG. Ошибка логики.')
    return CellData(
        value=txt,
        text_is_valid=is_valid,
        context_is_valid=is_valid if duplicate_pattern_result_to_context else None,
        recovered_val=recovered_val_by_alias,
        converted_val=alias,
        cell_mapping=cell_mapping,
        messages=MessageStorage(err_has_differences_in_src_text_and_alias, [])
    )


def validate_sequence_directions_or_stages_nums_and_create_cell(
    cell_mapping: CellMapping,
    sep=',',
    always_red_pattern: str | re.Pattern = Patterns.always_red.value
) -> CellData:
    nums, bad_nums, = defaultdict(int), []
    ms = MessageStorage([], [])
    src_txt = cell_mapping.cell.text
    repaired_string1 = src_txt.replace(' ', '')
    if len(repaired_string1) == 0:
        is_empty, is_always_red = True, False
    else:
        is_empty, is_always_red = False, bool(re.match(always_red_pattern, repaired_string1))
    seq_validation = DirectionsOrStagesSequenceValidation(is_empty, is_always_red, nums, bad_nums, Comparison())
    repaired_string2 = repair_string_if_sep_in_illegal_pos(repaired_string1)
    if len(repaired_string1) != len(repaired_string2):
        ms.add_errors(Text.illegal_pos_for_char(sep))
    if is_empty:
        ms.add_errors(Text.cell_is_empty)
        return CellData(src_txt, False, False, extra=seq_validation, messages=ms, cell_mapping=cell_mapping)
    split_string = repaired_string2.split(sep)
    for i, n in enumerate(split_string):
        num = get_stage_or_direction_number_or_none(n)
        if num is not None:
            nums[num] += 1
        elif num is None:
            bad_nums.append(n)
    if doubles:= tuple(seq_validation.gen_doubles()):
        ms.add_errors(Text.doubles(doubles))
    if bad_nums:
        ms.add_errors(Text.invalid_nums(bad_nums))
        nums.clear()
        return CellData(src_txt, False, False, extra=seq_validation, messages=ms, cell_mapping=cell_mapping)
    return CellData(src_txt, True, recovered_val=repaired_string2, extra=seq_validation, messages=ms,  cell_mapping=cell_mapping)


def validate_number_and_create_cell(key_for_matches, val_to_validate: str) -> CellData:
    tv = NumberValidation([])
    try:
        val_f = float(val_to_validate.replace(',', '.', 1))
    except ValueError:
        tv.errors.append(Text.is_not_a_number)
        return CellData(val_to_validate, False, False, extra=tv)
    values: AllowedValues = timing_matches[key_for_matches]
    if values.min <= val_f <= values.max: # OK case
        return CellData(val_to_validate, True, True, recovered_txt=int(val_f) if val_f.is_integer() else val_f, extra=tv)

    if val_f < values.min:
        err = Text.val_must_be_gt(values.min)
    elif val_f > values.max:
        err = Text.val_must_be_lt(values.max)
    else:
        raise Exception(f'Debug: val_to_validate not fully validated')
    tv.errors.append(err)
    return CellData(val_to_validate, True, False, recovered_txt=int(val_f) if val_f.is_integer() else val_f, extra=tv)




if __name__ == '__main__':
    print(row0_14_dt)
    print(row0_15_dt)
    print(row1_14_dt)
    print(len(row1_14_dt))
    r2 = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Ткж', 'Пост. красное', 'Красн.', 'Зелен.', '')

    path1 = '/home/auser/Downloads/СО_2120_Северный_б_р_Санникова_ул_Декабристов_ул_'
    path2 = '/home/auser/Downloads/ПД Паспорт шаблон 2025 (Копия)'
    path3 = '/home/auser/py.projects/sdp_lib/sdp_lib/passport/СО_2094_ул_Островитянова_ул_Ак_Волгина_2.docx'
    doc = Document(path3)
