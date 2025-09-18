import itertools
from collections.abc import (
    MutableSequence,
    Sequence,
    MutableMapping,  Container
)
from typing import (
    NamedTuple,
    Any, TypeVar, Self
)

from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.shared import RGBColor
from docx.table import _Cell, Table

from sdp_lib.passport.constants import MessageCategories, Fields
from sdp_lib.passport.text_messages import Text
from sdp_lib.utils_common.utils_common import (
    create_repr_from_dict_xor_slots,
    add_record
)


class Message(NamedTuple):
    text: str
    category: MessageCategories | int


class MessageStorage(NamedTuple):

    errors: MutableSequence[str]
    warnings: MutableSequence[str]

    def add_errors(self, *errors: str):
        return add_record(self.errors, errors)

    def add_warnings(self, *warnings: str):
        return add_record(self.warnings, warnings)

    def chain(self) -> itertools.chain:
        return itertools.chain(self.errors, self.warnings)

    def clear(self):

        self.errors.clear()
        self.warnings.clear()

    # def get_errors_by_categories(self, message_as_text=True):
    #     res = {}
    #     for msg in self.errors:
    #         m = msg.text if message_as_text else msg
    #         try:
    #             res[int(msg.category)][Fields.messages].append(m)
    #         except KeyError:
    #             cat, description = categories_descriptions.get(int(msg.category), (None, None))
    #             res[cat] = {
    #                 str(Fields.category_description): description,
    #                 str(Fields.messages): [m]
    #             }
    #     return res





class ValidationData(NamedTuple):
    value: Any
    is_valid: bool


class CellMapping(NamedTuple):
    i_table: int
    i_col: int
    i_row: int
    cell: _Cell


class CellData:

    RGB_RED = RGBColor(255, 0, 0)
    RGB_GREEN = RGBColor(0, 255, 0)
    RGB_BLUE = RGBColor(0, 0, 255)

    __slots__ = (
        'value',
        'text_is_valid',
        'context_is_valid',
        'recovered_val',
        'converted_val',
        'extra',
        'cell_mapping',
        'messages'
    )


    def __init__(
            self,
            value: str = None,
            text_is_valid: bool = None,
            context_is_valid: bool = None,
            converted_val=None,
            recovered_val=None,
            extra=None,
            cell_mapping: CellMapping = None,
            messages: MessageStorage = None,
    ):
        self.value = value
        self.text_is_valid = text_is_valid
        self.context_is_valid = context_is_valid
        self.recovered_val = recovered_val
        self.converted_val = converted_val
        self.extra = extra
        self.cell_mapping = cell_mapping
        self.messages = messages or MessageStorage([], [])

    def __repr__(self):
        return create_repr_from_dict_xor_slots(self)

    def write_messages_to_table_cell(
            self,
            sep='\n',
            color: RGBColor = None,
    ):
        new_txt = sep.join(f'*{m}' for m in self.messages.chain())
        if new_txt:
            _cell = self.cell_mapping.cell
            _cell.text = f'{_cell.text}{sep}{new_txt}'
            para = _cell.paragraphs[0]
            para.runs[0].font.color.rgb = color or self.RGB_RED
            para.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER
        return self



class AbstractDataRow:

    def __init__(self, row: Sequence[CellData] | MutableSequence[CellData]):
        self._row = row

    def get_row(self)-> Sequence[CellData] | MutableSequence[CellData]:
        return self._row

    def represent(
            self,
            include_properties=True,
            exclude_startswith='__',
            attr_splitter=' ',
    ):
        return create_repr_from_dict_xor_slots(self, include_properties, exclude_startswith, attr_splitter)

    @property
    def is_valid(self):
        return all(el.context_is_valid for el in self._row)

    @property
    def is_empty(self):
        return all(not el.text_is_valid for el in self._row)

    def dump(self):
        return [
            {
                'value': r.value,
                'text_is_valid': r.text_is_valid,
                'ctx_is_valid': r.context_is_valid,
                'errors': r.messages.errors,
                'warnings': r.messages.warnings,
            }
            for r in self._row
        ]


T_Row = TypeVar('T_Row', bound=AbstractDataRow)


class DirectionDataRow(AbstractDataRow):

    @property
    def num_direction(self) -> CellData:
        return self._row[0]

    @property
    def entity(self) -> CellData:
        return self._row[1]

    @property
    def stages(self) -> CellData:
        return self._row[2]

    @property
    def traffic_lights(self) -> CellData:
        return self._row[3]

    @property
    def t_green_ext(self) -> CellData:
        return self._row[4]

    @property
    def t_green_flashing(self) -> CellData:
        return self._row[5]

    @property
    def t_yellow(self) -> CellData:
        return self._row[6]

    @property
    def t_red(self) -> CellData:
        return self._row[7]

    @property
    def t_red_yellow(self) -> CellData:
        return self._row[8]

    @property
    def t_z(self) -> CellData:
        return self._row[9]

    @property
    def t_zz(self) -> CellData:
        return self._row[10] if len(self._row) == 15 else None

    @property
    def always_red(self) -> CellData:
        return self._row[11 if len(self._row) == 15 else 10]

    @property
    def toov_red(self) -> CellData:
        return self._row[12 if len(self._row) == 15 else 11]

    @property
    def toov_green(self) -> CellData:
        return self._row[13 if len(self._row) == 15 else 12]

    @property
    def description(self) -> CellData:
        return self._row[14 if len(self._row) == 15 else 13]


class TableGeometry(NamedTuple):
    allowed_col_lengths: Container
    allowed_min_num_rows: int
    num_columns: ValidationData
    num_rows: ValidationData
    # messages: MessageStorage

    def get_errors(self):
        if not self.num_columns.is_valid:
            yield Text.bad_cols_num(self.num_columns.value, self.allowed_col_lengths)
        if not self.num_rows.is_valid:
            yield Text.bad_cols_num(self.num_columns.value, self.allowed_min_num_rows)

    @property
    def is_valid(self) -> bool:
        return bool(self.num_columns.is_valid and self.num_rows.is_valid)


class TheTable:
    def __init__(
            self,
            i_table: int,
            table: Table,
            geometry_check_list: TableGeometry,
            head_rows: Sequence[T_Row] = None,
            data_rows: Sequence[T_Row] = None,
            empty_rows: Sequence[T_Row] = None,
            messages: MessageStorage = MessageStorage([], []),
    ):
        self.i_table = i_table
        self.table = table
        self.geometry_check_list = geometry_check_list
        self.head_rows = head_rows
        self.data_rows = data_rows
        self.empty_rows = empty_rows
        self.messages = messages

    def __str__(self):
        return (
            f'i_table: {self.i_table}\n'
            f'geometry_check_list: {self.geometry_check_list}\n'
            f'head_rows: {self.head_rows}\n'
            f'data_rows: {self.data_rows}\n'
            f'empty_rows: {self.empty_rows}\n'
            f'messages: {self.messages}\n'
        )

    def load_head_rows(self, head_rows: Sequence[T_Row] ):
        self.head_rows = head_rows

    def load_data_rows(self, data_rows: Sequence[T_Row]):
        self.data_rows = data_rows

    def load_empty_rows(self, empty_rows: Sequence[T_Row] ):
        self.empty_rows = empty_rows

    def dump(self):
        return {
            Fields.geometry: {
                Fields.col_length: self.geometry_check_list.num_columns.value,
                Fields.num_rows: self.geometry_check_list.num_rows.value,
                Fields.ok: self.geometry_check_list.is_valid,
            },
            Fields.head_rows: [[name.value for name in row_instance.get_row()] for row_instance in self.head_rows],
            Fields.data_rows: [r.dump() for r in self.data_rows]
        }


class Comparison:
    def __init__(self):
        self._va = []
        self._ft = []


class DirectionsOrStagesSequenceValidation(NamedTuple):
    is_always_red: bool
    is_empty: bool
    nums: MutableMapping
    bad_nums: MutableSequence
    compare: Comparison

    def gen_doubles(self):
        return ((n, cnt - 1) for n, cnt in self.nums.items() if cnt > 1)


class NumberValidation(NamedTuple):
    errors: MutableSequence


if __name__ == '__main__':
    inst = CellData()
    print(inst)