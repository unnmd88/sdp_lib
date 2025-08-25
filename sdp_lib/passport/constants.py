import pprint
from enum import (
    Enum,
    StrEnum,
    IntEnum,
    auto,

)
from itertools import zip_longest, combinations_with_replacement
from typing import NamedTuple


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


class DirectionTypes(StrEnum):
    common = 'Направление'
    vehicle = 'Транспортное'
    pedestrian = 'Пешеходное'
    arrow = 'Поворотное'
    always_red = 'Пост. красн'

    @classmethod
    def get_standard_types(cls):
        return ', '.join(str(d) for d in cls if d not in {cls.common})


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
    t_zz = 'Тз'

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
    stage_type = 'Тип фазы'


class ModeNames(StrEnum):
    va = 'va'
    ft = 'ft'
    man = 'man'
    central = 'central'


class StageTypes(StrEnum):
    main = 'Основная фаза'
    calling = 'Вызывная фаза'


# class AllowedComparisonCells(StrEnum):
#     table_directions_cell_stages = f'{TableNames.directions_table}, ячейка {ColNamesDirectionsTable.stages}'
#     table_time_program_cell_directions = f'{TableNames.time_program}, ячейка {ColNamesTimeProgramsTable.directions}'


class ComparisonDescriptions(StrEnum):
    directions_table_to_time_table = 'Сравнение направлений и фаз из Таблицы направлений с временной программой'
    two_directions_table = 'Сравнение двух таблиц направлений'
    two_time_program_tables = 'Сравнение двух временных программ'


class Fields(StrEnum):
    number = 'number'
    is_valid = 'is_valid'
    direction = 'direction'
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
    category_description = 'category_description'
    category = 'category'
    time_program = 'time_program'
    missing_in_src = 'missing_in_src'
    missing_in_dst = 'missing_in_dst'
    # keys_in_missing_container = 'keys_in_missing_container'
    # values_in_missing_container = 'values_in_missing_container'
    # src_meta = 'src_meta'
    # dst_meta = 'dst_meta'
    table_name = 'table_name'
    cell_name = 'cell_name'
    comparison_results = 'comparison_results'
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
    t_always_red = 't_always_red'
    toov_green = 'toov_green'
    toov_red = 'toov_red'



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


default_values = {
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_green_ext): 0,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_flashing_green): 3,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_yellow): 3,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_red): 0,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_red_yellow): 1,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_z): 0,
    (DirectionTypes.vehicle, ColNamesDirectionsTable.t_zz): 0,

    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_green_ext): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_flashing_green): 3,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_yellow): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_red): 3,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_red_yellow): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_z): 0,
    (DirectionTypes.pedestrian, ColNamesDirectionsTable.t_zz): 0,

    (DirectionTypes.arrow, ColNamesDirectionsTable.t_green_ext): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_flashing_green): 3,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_yellow): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_red): 3,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_red_yellow): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_z): 0,
    (DirectionTypes.arrow, ColNamesDirectionsTable.t_zz): 0,
}


if __name__ == '__main__':

    print(WEEKDAYS)
