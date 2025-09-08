import itertools
import re
from collections.abc import MutableSequence, Set, Sequence, Iterable
from dataclasses import dataclass, field, asdict
from enum import IntEnum, Enum
from pathlib import Path
from typing import NamedTuple, Any

from docx import Document
from docx.enum.table import WD_TABLE_DIRECTION
from docx.document import Document as DocumentObject
from docx.table import Table, _Row

from sdp_lib.passport.constants import TableNames
from sdp_lib.passport.mixins import ReprMixin
from sdp_lib.passport.passport2.base import InitData, MessageStorage, Message, DirectionRowCells, \
    StageOrDirectionNumsCell, \
    Cell, DirectionTypeCell
from sdp_lib.passport.passport2.directions import DirectionsTable, DirectionRow
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import to_json


class TableCategories(IntEnum):
    directions = 0
    time_program_va = 1
    time_program_ft = 2

    @classmethod
    def get_tp_vals(cls) -> Set:
        return {cls.time_program_ft, cls.time_program_va}


class TableMeta(NamedTuple):
    index: int
    category: TableCategories


class DocTablesMeta(ReprMixin):
    def __init__(self, tables: Sequence[TableMeta]):
        self._tables = tables
        self._directions = None
        self._ft = []
        self._va = []
        self.sort_tables_by_categories()

    def __iter__(self):
        return (k_v for k_v in self._tables)

    def __getitem__(self, item):
        return self._tables[item]

    def __len__(self):
        return len(self._tables)

    @property
    def directions(self) -> int:
        return self._directions

    @property
    def va_tables(self) -> MutableSequence[int]:
        return self._va

    @property
    def num_tables(self) -> int:
        return len(self._tables)

    def sort_tables_by_categories(self):
        for table in (table for table in self._tables if table.category is not None):
            if table.category == TableCategories.directions:
                self._directions = table.index
            elif table.category == TableCategories.time_program_ft:
                self._ft.append(table.index)
            elif table.category == TableCategories.time_program_va:
                self._va.append(table.index)

    def get_tables(self):
        return self._tables


class TableDirectionsAllowedLengths(IntEnum):
    standard_15 = 15
    exclude_tzz_14 = 14


"""
Таблица направлений.
length = 14
row0 = ['№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', '"Запрет"', '"Запрет"', '"Запрет"', '"Запрет"', '"Разрешение"', '"Разрешение"', 'Пост. красное', 'ТООВ ', 'ТООВ ', 'Примечание']
row1 = ['№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Тз', 'Пост. красное', 'Красн.', 'Зелен.', '']
---------------
Временная программа фикс.
length = 10
row0 = ['Программа 1', 'Программа 1', 'Программа 1', 'Тц = 89 с.', 'пн,вт,ср,чт,пт,сб,вс:', 'пн,вт,ср,чт,пт,сб,вс:', '06:00:00-21:00:00', '06:00:00-21:00:00', '06:00:00-21:00:00', '06:00:00-21:00:00']
row1 = ['№ пп', '№ фазы', 'Направления', 'Направления', 'Направления', 'Тосн', 'Тосн', 'Тсдвиг', 'Тмин', 'Тип фазы']

Временная программа адаптива.
length = 11
row0 = ['Программа 1', 'Программа 1', '', '', 'пн,вт,ср,чт,пт,сб,вс:', 'пн,вт,ср,чт,пт,сб,вс:', '', '', '06:00:00-21:00:00', '06:00:00-21:00:00', '06:00:00-21:00:00']
row1 = ['№ фазы', 'Направления', 'Направления', 'Условия вызова', 'Условия продления', 'Условия завершения', 'Условия завершения', 'Тмин', 'Тмин', 'Тмакс1\nТр.', 'Тмакс2\nОТ']

"""


class DirectionTableAllPatterns(Enum):
    num = re.compile('^тип\s*направления', re.IGNORECASE)
    direction_type = re.compile('^фазы.*кот.*направ', re.IGNORECASE)
    stages = re.compile('^светоф', re.IGNORECASE)
    tlc = re.compile('^Тзд', re.IGNORECASE)
    t_green_ext = re.compile('^Тзм', re.IGNORECASE)
    t_green_flashing = re.compile('^Тж', re.IGNORECASE)
    t_yellow = re.compile('^Тк', re.IGNORECASE)
    t_red = re.compile('^Ткж', re.IGNORECASE)
    t_red_yellow = re.compile('^Тз', re.IGNORECASE)
    t_z = re.compile('^Тзз', re.IGNORECASE)
    t_zz = re.compile('.+крас', re.IGNORECASE)
    always_red = re.compile('^Крас', re.IGNORECASE)
    toov_green = re.compile('^Зел', re.IGNORECASE)
    toov_red = re.compile('', re.IGNORECASE)

    prohibition = re.compile('^Запрет', re.IGNORECASE)
    permission = re.compile('^Разрешение', re.IGNORECASE)

    description1 = re.compile('', re.IGNORECASE)
    description2 = re.compile('^примечание', re.IGNORECASE)

    TOOV = re.compile('^ТООВ')



class DirectionTablePatterns(Enum):
    row1_cell0  = re.compile('^№\s*нап', re.IGNORECASE)
    row1_cell1  = re.compile('^тип\s*направления', re.IGNORECASE)
    row1_cell2  = re.compile('^фазы.*кот.*направ', re.IGNORECASE)
    row1_cell3  = re.compile('^светоф', re.IGNORECASE)
    row1_cell4  = re.compile('^Тзд', re.IGNORECASE)
    row1_cell5  = re.compile('^Тзм', re.IGNORECASE)
    row1_cell6  = re.compile('^Тж', re.IGNORECASE)
    row1_cell7  = re.compile('^Тк', re.IGNORECASE)
    row1_cell8  = re.compile('^Ткж', re.IGNORECASE)
    row1_cell9  = re.compile('^Тз', re.IGNORECASE)
    row1_cell10 = re.compile('^Тзз', re.IGNORECASE)
    row1_cell11 = re.compile('.+крас', re.IGNORECASE)
    row1_cell12 = re.compile('^Крас', re.IGNORECASE)
    row1_cell13 = re.compile('^Зел', re.IGNORECASE)
    row1_cell14 = re.compile('', re.IGNORECASE)



    # row1_cell0  = ({0}, re.compile('^№\s*нап', re.IGNORECASE))
    # row1_cell1  = ({1}, re.compile('^тип\s*направления', re.IGNORECASE))
    # row1_cell2  = ({2}, re.compile('^фазы.*кот.*направ', re.IGNORECASE))
    # row1_cell3  = ({3}, re.compile('^светоф', re.IGNORECASE))
    # row1_cell4  = ({4}, re.compile('^Тзд', re.IGNORECASE))
    # row1_cell5  = ({5}, re.compile('^Тзм', re.IGNORECASE))
    # row1_cell6  = ({6}, re.compile('^Тж', re.IGNORECASE))
    # row1_cell7  = ({7}, re.compile('^Тк', re.IGNORECASE))
    # row1_cell8  = ({8}, re.compile('^Ткж', re.IGNORECASE))
    # row1_cell9  = ({9}, re.compile('^Тз', re.IGNORECASE))
    # row1_cell10 = ({10}, re.compile('^Тзз', re.IGNORECASE))
    # row1_cell11 = ({11}, re.compile('.+крас', re.IGNORECASE))
    # row1_cell12 = ({12}, re.compile('^Крас', re.IGNORECASE))
    # row1_cell13 = ({13}, re.compile('^Зел', re.IGNORECASE))
    # row1_cell14 = ({14}, re.compile('', re.IGNORECASE))

    # num = re.compile('^тип\s*направления', re.IGNORECASE)
    # direction_type = re.compile('^фазы.*кот.*направ', re.IGNORECASE)
    # stages = re.compile('^светоф', re.IGNORECASE)
    # tlc = re.compile('^Тзд', re.IGNORECASE)
    # t_green_ext = re.compile('^Тзм', re.IGNORECASE)
    # t_green_flashing = re.compile('^Тж', re.IGNORECASE)
    # t_yellow = re.compile('^Тк', re.IGNORECASE)
    # t_red = re.compile('^Ткж', re.IGNORECASE)
    # t_red_yellow = re.compile('^Тз', re.IGNORECASE)
    # t_z = re.compile('^Тзз', re.IGNORECASE)
    # t_zz = re.compile('.+крас', re.IGNORECASE)
    # always_red = re.compile('^Крас', re.IGNORECASE)
    # toov_green = re.compile('^Зел', re.IGNORECASE)
    # toov_red = re.compile('', re.IGNORECASE)
    # description = re.compile('^примечание', re.IGNORECASE)


    @classmethod
    def get_patterns_len(cls, length: int):
        if length == 15:
            for pattern in cls:
                yield pattern.value
        elif length == 14:
            for i, pattern in enumerate(cls):
                if i != 10:
                    yield pattern.value


class TimeProgramFtPatterns(Enum):
    row1_cell0 = re.compile('№\s*пп',  re.IGNORECASE)
    row1_cell1 = re.compile('№\s*фазы',  re.IGNORECASE)
    row1_cell9 = re.compile('Тип\s*фазы',  re.IGNORECASE)


class TimeProgramVaPatterns(Enum):
    row1_cell0 = re.compile('№\s*фазы',  re.IGNORECASE)
    row1_cell1 = re.compile('направления',  re.IGNORECASE)
    row1_cell10 = re.compile('макс.*2',  re.IGNORECASE)


class InvalidCellName(NamedTuple):
    pos: int
    name: str


def _check_is_directions_table(rows) -> bool:
    # return bool(
    #     14 <= len(rows[0].cells) <= 15
    #     and re.search(DirectionTablePatterns.row1_cell0.value, rows[1].cells[0].text) is not None
    #     and re.search(DirectionTablePatterns.row1_cell1.value, rows[1].cells[1].text) is not None
    # )
    first_and_second_rows_is_head = all(
        re.search(p, s) is not None for p, s in zip(
            (DirectionTablePatterns.row1_cell0.value, DirectionTablePatterns.row1_cell1.value),
            (rows[1].cells[0].text_is_valid, rows[1].cells[1].text_is_valid),
            strict=True
        )
    )
    try:
        assert first_and_second_rows_is_head
        # Проверка, что третья строка(индекс=2) это строка с первой группой
        cell_num_group = int(rows[2].cells[0].text_is_valid)
        cell_t_green_ext = (int(rows[2].cells[5].text_is_valid) - 3)
        assert cell_num_group - 1  >= 0
        assert cell_t_green_ext >= 0
    except (AssertionError, ValueError):
        return False
    return True


# individual_cells_dt = {
#     DirectionTablePatterns.
# }


def _check_length_and_col_names_dt(row_cells):
    pass



def _check_bad_col_names_directions_table(row) -> tuple[int | None, MutableSequence[InvalidCellName]]:
    for i, data in enumerate(zip(DirectionTablePatterns.get_patterns_len(len(row.cells)), row.cells)):
        pattern, cell = data
        if re.search(pattern, cell.text_is_valid) is None:
            yield InvalidCellName(i, cell.text_is_valid)


def _check_is_time_program_table_ft(rows) -> bool:
    return bool(
        len(rows[0].cells) == 10
        and re.search(TimeProgramFtPatterns.row1_cell0.value, rows[1].cells[0].text_is_valid) is not None
        and re.search(TimeProgramFtPatterns.row1_cell1.value, rows[1].cells[1].text_is_valid) is not None
        and re.search(TimeProgramFtPatterns.row1_cell9.value, rows[1].cells[9].text_is_valid) is not None
    )


def _check_is_time_program_table_va(rows) -> bool:
    return bool(
        len(rows[0].cells) == 11
        and re.search(TimeProgramVaPatterns.row1_cell0.value, rows[1].cells[0].text_is_valid) is not None
        and re.search(TimeProgramVaPatterns.row1_cell1.value, rows[1].cells[1].text_is_valid) is not None
        and re.search(TimeProgramVaPatterns.row1_cell10.value, rows[1].cells[10].text_is_valid) is not None
    )


def sort(tables: MutableSequence[Table]) -> DocTablesMeta:
    tables_meta = []
    for i, table in enumerate(tables):
        t_rows = table.rows
        entity = None
        if _check_is_directions_table(t_rows):
            entity = TableCategories.directions
        elif _check_is_time_program_table_ft(t_rows):
            entity = TableCategories.time_program_ft
        elif _check_is_time_program_table_va(t_rows):
            entity = TableCategories.time_program_va
        tables_meta.append(TableMeta(i, entity))
    return DocTablesMeta(tables_meta)


class Cells(Enum):
    dt_data_row_length14 = (Cell, ) + (DirectionTypeCell, StageOrDirectionNumsCell) + tuple(Cell for _ in range(14 - 3))
    dt_data_row_length15 = (Cell, ) + (DirectionTypeCell, StageOrDirectionNumsCell) + tuple(Cell for _ in range(15 - 3))
    dt_head_row_length14 = tuple(Cell for _ in range(14))
    dt_head_row_length15 = tuple(Cell for _ in range(15))


class RowMatches(NamedTuple):
    head: Sequence
    data: Sequence


dt_row_matches14 = RowMatches(Cells.dt_head_row_length14.value, Cells.dt_data_row_length14.value)
dt_row_matches15 = RowMatches(Cells.dt_head_row_length15.value, Cells.dt_data_row_length15.value)


def _get_values_for_direction_table_row(
    docx_row,
    val_tzz_if_has_not_in_docx_row='',
    head_row=False
):
    if head_row:
        for i, data in enumerate(docx_row):
            if i == 10 and len(docx_row) == TableDirectionsAllowedLengths.exclude_tzz_14:
                yield Cell(None, val_tzz_if_has_not_in_docx_row, '')
            yield Cell(i, data.text_is_valid, '')
    else:
        for i, data in enumerate(docx_row):
            if i == 10 and len(docx_row) == TableDirectionsAllowedLengths.exclude_tzz_14:
                yield Cell(None, val_tzz_if_has_not_in_docx_row, '')

            if i >= 2 or i == 0:
                yield Cell(i, data.text_is_valid, '')
            elif i == 2:
                yield StageOrDirectionNumsCell(i, data.text_is_valid)
            elif i == 1:
                yield DirectionTypeCell(i, data.text_is_valid)
            else:
                raise ValueError


def _get_values_for_direction_table_row(
    docx_row,
    val_tzz_if_has_not_in_docx_row='',
    head_row=False
):
    if head_row:
        for i, data in enumerate(docx_row):
            if i == 10 and len(docx_row) == TableDirectionsAllowedLengths.exclude_tzz_14:
                yield Cell(None, val_tzz_if_has_not_in_docx_row, '')
            yield Cell(i, data.text_is_valid, '')
    else:
        for i, data in enumerate(docx_row):
            if i == 10 and len(docx_row) == TableDirectionsAllowedLengths.exclude_tzz_14:
                yield Cell(None, val_tzz_if_has_not_in_docx_row, '')

            if i >= 2 or i == 0:
                yield Cell(i, data.text_is_valid, '')
            elif i == 2:
                yield StageOrDirectionNumsCell(i, data.text_is_valid)
            elif i == 1:
                yield DirectionTypeCell(i, data.text_is_valid)
            else:
                raise ValueError


def build_directions_table(index, table: Table):
    rows = table.rows
    dt = DirectionsTable(index, table, [], [])
    if len(rows) == 14:
        matches_data_row = Cells.dt_data_row_length14
    for i, row in enumerate(rows):
        if i <= 1:
            v = '"Разрешение"' if i == 1 else 'Тзз'
            r = DirectionRow(
                    i,
                    row,
                    False,
                    True,
                    DirectionRowCells(*(data for data in _get_values_for_direction_table_row(row.cells, v, True)))
            )
            dt.load_head_rows(r)
        else:
            values_cells15 = [data for data in _get_values_for_direction_table_row(row.cells)]
            r =  DirectionRow(
                    i,
                    row,
                    all(not cell.value for cell in values_cells15),
                    False,
                    DirectionRowCells(*values_cells15)
                )
            dt.load_data_rows(r)
        print(r)



        # values_cells15 = [data for data in _get_values_for_direction_table_row(row.cells)]
        # create_direction_row_length15(row.cells)


def build_tables(tables: MutableSequence[Table]):
    directions = None
    tp = []

    for i, table in enumerate(tables):
        t_rows = table.rows
        entity = None
        if _check_is_directions_table(t_rows):
            bad_names = list(_check_bad_col_names_directions_table(t_rows[1]))
            print(f'bad_names: {bad_names}')
            build_directions_table(i, table)
            entity = TableCategories.directions
        elif _check_is_time_program_table_ft(t_rows):
            entity = TableCategories.time_program_ft
        elif _check_is_time_program_table_va(t_rows):
            entity = TableCategories.time_program_va
    return



def _display_all_tables(doc_x):
    """ Выводит на экран данные всех таблиц doc(x) файла. """
    for table in doc_x.tables:
        print(f'-- Start Table --')
        print(f'table.rows: {list(table.rows)}')
        print(f'table.row: {table.rows}')
        print(f'len(rows): {len(table.rows)}')
        print(f'len(cells): {len(table.rows[0].cells)}')
        for i, row in enumerate(table.rows):
            print(f'{i}: {[cell.text_is_valid for cell in row.cells]}')
        print(f'*' * 100)


class ValidationCheck:
    __slots__ = ('is_checked', 'ok', 'message')
    def __init__(self):
        self.is_checked = False
        self.ok = None
        self.message = ''

    def __repr__(self):
        attrs = ' '.join(f'{attr}={getattr(self, attr)!r}' for attr in self.__slots__)
        return f'{self.__class__.__name__}({attrs})'

    def dump(self):
        return {attr: getattr(self, attr) for attr in self.__slots__}



@dataclass
class CheckListBaseValidation:
    length_direction_table: ValidationCheck = field(default_factory=ValidationCheck)
    min_num_rows: ValidationCheck = field(default_factory=ValidationCheck)
    col_names_direction_table: ValidationCheck = field(default_factory=ValidationCheck)


@dataclass
class CheckListDirectionRow:
    num: ValidationCheck = field(default_factory=ValidationCheck)
    stages: ValidationCheck = field(default_factory=ValidationCheck)


class Passport:
    def __init__(self, docx: str):
        self._path = docx
        self._doc = Document(self._path)
        self._table_directions = None
        self._validation = MessageStorage()
        self._tables_va = []
        self._tables_ft = []
        self._check_list: CheckListBaseValidation = ...

    def create_passport_from_docx(self):
        self._validation.clear_all()
        self._check_list = CheckListBaseValidation()
        for i, table in enumerate(self._doc.tables):
            t_rows = table.rows
            if _check_is_directions_table(table.rows):
                # Секция валидации структуры таблицы направлений
                self._check_length_cols_direction_table(t_rows)
                self._check_min_num_rows_direction_table(t_rows)
                self._check_col_names_direction_table(t_rows)

                build_directions_table(i, table)
                entity = TableCategories.directions
            elif _check_is_time_program_table_ft(t_rows):
                entity = TableCategories.time_program_ft
            elif _check_is_time_program_table_va(t_rows):
                entity = TableCategories.time_program_va

    def _check_length_cols_direction_table(self, t_rows) -> bool:
        self._check_list.length_direction_table.is_checked = True
        try:
            self._check_list.length_direction_table.ok = bool(TableDirectionsAllowedLengths(len(t_rows[0].cells)))
        except ValueError:
            self._check_list.length_direction_table.ok = False
            self._check_list.length_direction_table.message = Text.bad_length(
                TableNames.directions_table, len(t_rows[1])
            )
        return self._check_list.length_direction_table.ok

    def _check_min_num_rows_direction_table(self, t_rows):
        self._check_list.min_num_rows.is_checked = True
        min_rows_is_valid = len(t_rows) >= 3
        if not min_rows_is_valid:
            self._check_list.min_num_rows.message = Text.bad_num_rows(
                str(TableNames.directions_table), len(t_rows), 'мин=3'
            )
        self._check_list.min_num_rows.ok = min_rows_is_valid
        return self._check_list.min_num_rows.ok

    def _check_col_names_direction_table(self, t_rows):
        self._check_list.col_names_direction_table.is_checked = True
        bad_names = list(_check_bad_col_names_directions_table(t_rows[1]))
        if bad_names:
            self._check_list.col_names_direction_table.message = Text.invalid_col_names(
                str(TableNames.directions_table), bad_names
            )
        self._check_list.col_names_direction_table.ok = False if bad_names else True
        return self._check_list.col_names_direction_table.ok



if __name__ == '__main__':
    path = 'C://Programms//py.projects//sdp_lib//sdp_lib//passport//СО_2094_ул_Островитянова_ул_Ак_Волгина (2)'
    doc = Document(f'{path}.docx')
    # print(doc.tables)
    _display_all_tables(doc)
    # build_tables(doc.tables)
    # print(sort(doc.tables))
    # ps = Passport(f'{path}.docx')
    # ps.create_passport_from_docx()
    # doc.tables[0].table_direction = WD_TABLE_DIRECTION.LTR
    # doc.tables[0].add_row()
    # doc.save(f'{path}_22.docx')
