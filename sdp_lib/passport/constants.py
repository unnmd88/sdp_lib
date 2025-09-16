import re
from collections.abc import Sequence
from enum import (
    StrEnum,
    IntEnum,
    Enum, unique,
)
from typing import NamedTuple

from sdp_lib.utils_common.utils_common import gen_seq, get_vector_from_enum


class Patterns(Enum):
    s_char = re.compile('\s')
    always_red = re.compile(r'кр|-|поко', re.IGNORECASE)
    comma_is_start_end_or_end = re.compile('^,*|,*$')
    several_commas = re.compile(',{2,}')
    on = re.compile('^Вкл\.?$', re.IGNORECASE)
    off = re.compile('^Выкл\.?$', re.IGNORECASE)
    # on_off = re.compile('^Выкл\.?$|^Вкл\.?$', re.IGNORECASE)
    on_off = re.compile('^Вы?кл\.?$', re.IGNORECASE)
    dash = re.compile('^-$', re.IGNORECASE)


class PatternsDirectionTable(Enum):
    allowed_entities = re.compile('Транспортное|Поворотное|Пешеходное|общ.*тр|пос.*крас', re.IGNORECASE)
    vehicle = re.compile('^Транспортное', re.IGNORECASE)
    arrow = re.compile('^Поворотное', re.IGNORECASE)
    pedestrian = re.compile('^Пешеходное', re.IGNORECASE)
    public = re.compile('^общ.*тр', re.IGNORECASE)
    tram = re.compile('^трамвайное', re.IGNORECASE)
    velo = re.compile('^вело', re.IGNORECASE)
    always_red = re.compile('^пост.+крас', re.IGNORECASE)
    always_red_text_yes = re.compile('^да', re.IGNORECASE)
    num_direction  = re.compile('^№\s*нап', re.IGNORECASE)
    entity_direction  = re.compile('^тип\s*направления', re.IGNORECASE)
    stages  = re.compile('^фазы.*кот.*направ', re.IGNORECASE)
    traffic_lights  = re.compile('^светофоры', re.IGNORECASE)

    prohibition  = re.compile('"?Запрет"?.', re.IGNORECASE)
    permission  = re.compile('"?Разрешение"?', re.IGNORECASE)

    t_green_extension  = re.compile('^Тзд', re.IGNORECASE)
    t_green_flashing  = re.compile('^Тзм', re.IGNORECASE)
    t_yellow  = re.compile('^Тж', re.IGNORECASE)
    t_red  = re.compile('^Тк', re.IGNORECASE)
    t_red_yellow  = re.compile('^Ткж', re.IGNORECASE)
    t_z  = re.compile('^Тз', re.IGNORECASE)
    t_zz = re.compile('^Тзз', re.IGNORECASE)

    toov = re.compile('^ТООВ')

    toov_red_green_dash = (
        Patterns.on.value,
        Patterns.off.value,
        Patterns.dash.value,
    )

    toov_green = re.compile('^Зел', re.IGNORECASE)
    toov_red = re.compile('^Красн', re.IGNORECASE)

    description = re.compile('^примечание', re.IGNORECASE)
    empty = re.compile('', re.IGNORECASE)


class ColNamesDirectionsTable(StrEnum):
    t_green_ext = 'Тзд'
    t_flashing_green = 'Тзм'
    t_yellow = 'Тж'
    t_red = 'Тк'
    t_red_yellow = 'Ткж'
    t_z = 'Тз'
    t_zz = 'Тзз'

    number = '№ нап.'
    direction_entity = 'Тип направления'
    traffic_lights = 'Светофоры'
    stages = 'Фазы, в кот. участ. направ.'
    prohibition = '"Запрет"'
    permission = '"Разрешение"'
    toov = 'ТООВ'
    always_red = 'Пост. красное'
    toov_green = 'Зелен.'
    toov_red = 'Красн.'
    description = 'Примечание'
    empty = ''


# row0_15_dt = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', '"Запрет"', '"Запрет"', '"Запрет"', '"Запрет"', '"Разрешение"', '"Разрешение"', '"Разрешение"', 'Пост. красное', 'ТООВ ', 'ТООВ ', 'Примечание')
row0_dt_names = (
    ColNamesDirectionsTable.number,
    ColNamesDirectionsTable.direction_entity,
    ColNamesDirectionsTable.stages,
    ColNamesDirectionsTable.traffic_lights,
    ColNamesDirectionsTable.prohibition,
    ColNamesDirectionsTable.prohibition,
    ColNamesDirectionsTable.prohibition,
    ColNamesDirectionsTable.prohibition,
    ColNamesDirectionsTable.permission,
    ColNamesDirectionsTable.permission,
    ColNamesDirectionsTable.permission,
    ColNamesDirectionsTable.always_red,
    ColNamesDirectionsTable.toov,
    ColNamesDirectionsTable.toov,
    ColNamesDirectionsTable.description,
)
# row1_15_dt = ('№ нап.', 'Тип направления', 'Фазы, в кот. участ. направ.', 'Светофоры', 'Тзд', 'Тзм', 'Тж', 'Тк', 'Ткж', 'Тз', 'Тзз', 'Пост. красное', 'Красн.', 'Зелен.', '')
row1_dt_names = (
    ColNamesDirectionsTable.number,
    ColNamesDirectionsTable.direction_entity,
    ColNamesDirectionsTable.stages,
    ColNamesDirectionsTable.traffic_lights,
    ColNamesDirectionsTable.t_green_ext,
    ColNamesDirectionsTable.t_flashing_green,
    ColNamesDirectionsTable.t_yellow,
    ColNamesDirectionsTable.t_red,
    ColNamesDirectionsTable.t_red_yellow,
    ColNamesDirectionsTable.t_z,
    ColNamesDirectionsTable.t_zz,
    ColNamesDirectionsTable.always_red,
    ColNamesDirectionsTable.toov_red,
    ColNamesDirectionsTable.toov_green,
    ColNamesDirectionsTable.empty,
)

row0_dt_patterns = (
    PatternsDirectionTable.num_direction.value,
    PatternsDirectionTable.entity_direction.value,
    PatternsDirectionTable.stages.value,
    PatternsDirectionTable.traffic_lights.value,
    PatternsDirectionTable.prohibition.value,
    PatternsDirectionTable.prohibition.value,
    PatternsDirectionTable.prohibition.value,
    PatternsDirectionTable.prohibition.value,
    PatternsDirectionTable.permission.value,
    PatternsDirectionTable.permission.value,
    PatternsDirectionTable.permission.value,
    PatternsDirectionTable.always_red.value,
    PatternsDirectionTable.toov.value,
    PatternsDirectionTable.toov.value,
    PatternsDirectionTable.description.value,
)

row1_dt_patterns = (
    PatternsDirectionTable.num_direction.value,
    PatternsDirectionTable.entity_direction.value,
    PatternsDirectionTable.stages.value,
    PatternsDirectionTable.traffic_lights.value,
    PatternsDirectionTable.t_green_extension.value,
    PatternsDirectionTable.t_green_flashing.value,
    PatternsDirectionTable.t_yellow.value,
    PatternsDirectionTable.t_red.value,
    PatternsDirectionTable.t_red_yellow.value,
    PatternsDirectionTable.t_z.value,
    PatternsDirectionTable.t_zz.value,
    PatternsDirectionTable.always_red.value,
    PatternsDirectionTable.toov_red.value,
    PatternsDirectionTable.toov_green.value,
    PatternsDirectionTable.empty.value,
)


class HeadRowsDirectionTableData(NamedTuple):
    row0_col_names: Sequence[str]
    row1_col_names: Sequence[str]
    row0_col_patterns: Sequence[re.Pattern | str]
    row1_col_patterns: Sequence[re.Pattern | str]


head_rows_data_dt = HeadRowsDirectionTableData(row0_dt_names, row1_dt_names, row0_dt_patterns, row1_dt_patterns)


allowed_column_lengths_dt = {15}
allowed_min_num_rows = 3


class MessageLevels(StrEnum):
    debug = 'DEBUG'
    info = 'INFO'
    warning = 'WARNING'
    error = 'ERROR'
    critical = 'CRITICAL'


class MessageCategories(IntEnum):
    common = 1
    validation = 2
    compare_directions_table_to_time_table = 3


categories_descriptions = {
    MessageCategories.validation: ('validation', 'Валидация данных'),
    MessageCategories.common: ('common', 'Общее'),
    MessageCategories.compare_directions_table_to_time_table: (
        ('compare1', 'Сравнение соответствия фаз таблицы направлений с временной таблицей')
    )
}


class RowNames(StrEnum):
    direction = 'Направление'
    stage = 'Фаза'
    head_time_table = 'Заголовок временной таблицы'


class TableNames(StrEnum):
    directions_table = 'Таблица направлений'
    time_program = 'Временная программа'
    stages_table = 'Таблица фаз'


class StorageNames(StrEnum):
    direction = 'Направление'
    directions_table = 'Таблица направлений'
    income_data = 'Входные данные'
    errors_and_warnings = 'Ошибки и предупреждения'


class DirectionEntities(StrEnum):
    vehicle = 'Транспортное'
    pedestrian = 'Пешеходное'
    arrow = 'Поворотное'
    always_red = 'Пост. красн'
    public = 'Общ. транспорт'
    tram = 'Трамвайное'
    velo = 'Велосипедное'

    @classmethod
    def get_standard_types(cls):
        return {str(d) for d in cls}
        # return ', '.join(str(d) for d in cls if d not in {cls.common, cls.empty})


standard_directions = {el for el in DirectionEntities}


class StagesMapping(IntEnum):
    direction_to_stages = 0
    stage_to_direction  = 1


class ColNamesDirectionsTable(StrEnum):
    t_green_ext = 'Тзд'
    t_flashing_green = 'Тзм'
    t_yellow = 'Тж'
    t_red = 'Тк'
    t_red_yellow = 'Ткж'
    t_z = 'Тз'
    t_zz = 'Тзз'

    number = '№ нап.'
    direction_type = 'Тип направления'
    traffic_lights = 'Светофоры'
    stages = 'Фазы, в кот. участ. направ.'
    always_red = 'Пост. красное'
    toov_green = 'Зелен.'
    toov_red = 'Красн.'
    description = 'Примечание'


class ColNamesTimeProgramsTable(StrEnum):
    number = 'Программа'
    cycle_time = 'Тц'
    weekdays = 'Дни недели'
    time_interval = 'Временной интервал'

    num_pp = '№ пп'
    num_stage = '№ фазы'
    directions = 'Направления'
    t_osn = 'Тосн'
    t_sdvig = 'Тсдвиг'
    t_min = 'Тмин'
    t_max1 = 'Тмакс1'
    t_max2 = 'Тмакс2'
    stage_type = 'Тип фазы'

    req_condition = 'req_condition'
    ext_condition = 'ext_condition'
    term_condition = 'term_condition'


class ModeNames(StrEnum):
    va = 'va'
    ft = 'ft'
    man = 'man'
    central = 'central'


class StageTypes(StrEnum):
    main = 'Основная фаза'
    calling = 'Вызывная фаза'


class ComparisonDescriptions(StrEnum):
    directions_table_to_time_table = 'Сравнение направлений и фаз из Таблицы направлений с временной программой'
    two_directions_table = 'Сравнение двух таблиц направлений'
    two_time_program_tables = 'Сравнение двух временных программ'


@unique
class Fields(StrEnum):
    geometry = 'geometry'
    col_length = 'col_length'
    num_rows = 'num_rows'
    head_rows = 'head_rows'
    data_rows = 'data_rows'
    empty_rows = 'empty_rows'
    ok = 'ok'

    income_data = 'income_data'
    number = 'number'
    numCO = 'numCO'
    address = 'address'
    direction_table = 'direction_table'
    time_program_tables = 'time_program_tables'
    is_valid = 'is_valid'
    direction = 'direction'
    directions= 'directions'
    direction_type_is_standard = 'direction_type_is_standard'
    stages = 'stages'
    is_standard = 'is_standard'
    cell_value = 'cell_value'
    description = 'description'
    has_discrepancy = 'has_discrepancy'
    discrepancies_found = 'discrepancies_found'
    mappings = 'mappings'
    common = 'Общие'
    compare_directions_table_to_time_table = 'Сравнение фаз из таблицы направлений с временной таблицей`'
    messages = 'messages'
    errors = 'errors'
    cells_values = 'cells_values'
    category_description = 'category_description'
    category = 'category'
    time_program = 'time_program'
    missing_in_src = 'missing_in_src'
    missing_in_dst = 'missing_in_dst'
    max_stage = 'max_stage'
    max_direction = 'max_direction'
    directions_by_type = 'directions_by_type'
    table_name = 'table_name'
    cell_name = 'cell_name'
    comparison_results = 'comparison_results'
    comparison_is_done = 'comparison_is_done'
    index = 'index'
    src_num = 'src_num'
    dst_num = 'dst_num'
    bad_nums =  'bad_nums'
    doubles =  'doubles'
    asc_order =  'asc_order'
    formatted_string = 'formatted_string'
    is_always_red = 'is_always_red'

    traffic_lights = 'traffic_lights'
    t_green_ext = 't_green_ext'
    t_green_flashing = 't_green_flashing'
    t_yellow = 't_yellow'
    t_red = 't_red'
    t_red_yellow = 't_red_yellow'
    t_z = 't_z'
    t_zz = 't_zz'
    always_red = 't_always_red'
    toov_green = 'toov_green'
    toov_red = 'toov_red'

    num_pp = 'num_pp'
    weekdays = 'weekdays'
    t_osn = 't_osn'
    t_sdvig = 't_sdvi'
    t_min_ft = 't_min_ft'
    stage_type = 'stage_type'
    t_min_va = 't_min_va'
    t_max1_va = 't_max1_va'
    t_max2_va = 't_max2_va'
    req_condition = 'req_condition'
    ext_condition = 'ext_condition'
    term_condition = 'term_condition'


WEEKDAYS = {k: None for k in 'пн,вт,ср,чт,пт,сб,вс'.split(',')}

"""
class DefaultTimeValuesDirectionTable(typing.NamedTuple):
    t_green_ext: int
    t_flashing_green: int
    t_yellow: int
    t_red: int
    t_red_yellow: int
    t_z: int
    t_zz: int


vehicle_direction_default_times = DefaultTimeValuesDirectionTable(0, 3, 3, 0, 1, 0, 0)
pedestrian_direction_default_times = DefaultTimeValuesDirectionTable(0, 3, 0, 3, 0, 0, 0)
arrow_direction_default_times = DefaultTimeValuesDirectionTable(0, 3, 0, 3, 0, 0, 0)
common_direction_default_times = DefaultTimeValuesDirectionTable(0, 0, 0, 0, 0, 0, 0)
"""

class AllowedValues(NamedTuple):
    min: float
    max: float
    default: float


min0_max10_default0 = AllowedValues(0, 10, 0)
min3_max3_default3  = AllowedValues(3, 3, 3)
min0_max10_default3  = AllowedValues(3, 10, 3)
min1_max3_default1  = AllowedValues(1, 3, 1)
min0_max0_default0  = AllowedValues(0, 0, 0)
min3_max10_default3  = AllowedValues(3, 10, 3)


class DirectionDataContainer(NamedTuple):
    entity: DirectionEntities
    tl_patterns: Sequence[str | re.Pattern]
    t_green_extension: AllowedValues
    t_green_flashing: AllowedValues
    t_yellow: AllowedValues
    t_red: AllowedValues
    t_red_yellow: AllowedValues
    t_z: AllowedValues
    t_zz: AllowedValues
    can_be_always_red: bool
    toov_patterns: Sequence[str | re.Pattern]

    def get_timings(self):
        return (self[i] for i in range(2, 9))


vehicle_data = DirectionDataContainer(
    entity=DirectionEntities.vehicle,
    tl_patterns=(re.compile(DirectionEntities.vehicle[:2], re.IGNORECASE), ),
    t_green_extension=min0_max10_default0,
    t_green_flashing=min3_max3_default3,
    t_yellow=min3_max3_default3,
    t_red=min0_max10_default0,
    t_red_yellow=min1_max3_default1,
    t_z=min0_max10_default0,
    t_zz=min0_max10_default0,
    can_be_always_red=True,
    toov_patterns=(Patterns.on_off.value, ),
)


pedestrian_data = DirectionDataContainer(
    entity=DirectionEntities.pedestrian,
    tl_patterns=(re.compile('пеш', re.IGNORECASE), ),
    t_green_extension=min0_max10_default0,
    t_green_flashing=min3_max3_default3,
    t_yellow=min0_max0_default0,
    t_red=min0_max10_default0,
    t_red_yellow=min0_max0_default0,
    t_z=min0_max10_default0,
    t_zz=min0_max10_default0,
    can_be_always_red=False,
    toov_patterns=(Patterns.on_off.value, ),
)


arrow_data = DirectionDataContainer(
    entity=DirectionEntities.arrow,
    tl_patterns=(re.compile('д/[c,с]', re.IGNORECASE), ),
    t_green_extension=min0_max10_default0,
    t_green_flashing=min3_max3_default3,
    t_yellow=min0_max0_default0,
    t_red=min0_max10_default0,
    t_red_yellow=min0_max0_default0,
    t_z=min0_max10_default0,
    t_zz=min0_max10_default0,
    can_be_always_red=False,
    toov_patterns=(Patterns.dash.value, ),
)

velo_data = DirectionDataContainer(
    entity=DirectionEntities.velo,
    tl_patterns=(re.compile('^Вел[.\s]', re.IGNORECASE), ),
    t_green_extension=min0_max10_default0,
    t_green_flashing=min3_max3_default3,
    t_yellow=min3_max3_default3,
    t_red=min0_max10_default0,
    t_red_yellow=min1_max3_default1,
    t_z=min0_max10_default0,
    t_zz=min0_max10_default0,
    can_be_always_red=False,
    toov_patterns=(Patterns.on_off.value, ),
)

mapping_direction_data = {
    DirectionEntities.vehicle: vehicle_data,
    DirectionEntities.pedestrian: pedestrian_data,
    DirectionEntities.arrow: arrow_data,
    DirectionEntities.velo: velo_data,
}


if __name__ == '__main__':
    pass
    # print(dt_timing_columns)
    # print(dt_timing_columns_exclude_tzz)
    # print(PatternsDirectionTable.row1_cells.value)
    # print(tuple(PatternsDirectionTable.get_patterns_row1(14)))