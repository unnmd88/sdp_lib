import json
import pprint
import time
from collections.abc import MutableSequence, Sequence, MutableMapping, Iterable
from dataclasses import dataclass, asdict

from sdp_lib.passport.base import StagesData, compare, compare_stages_data_for_directions_and_time_programs, \
    ComparisonDirectionsAndStages, DirectionBaseProperties, DataSourceComparison, ComparisonMeta
from sdp_lib.passport.constants import DirectionTypes, Fields, TableNames, \
    ColNamesDirectionsTable, ColNamesTimeProgramsTable
from sdp_lib.passport.directions import DirectionsTable
from sdp_lib.passport.time_programms import TimeProgramTable, HeadDataRow
from sdp_lib.utils_common.utils_common import read_file_as_string, stages_as_string


class Passport:
    def __init__(
            self,
            *,
            directions_table: DirectionsTable = None,
            time_program_tables_data: MutableSequence[TimeProgramTable] | None = None,
    ):
        self._directions_table = directions_table
        self._time_program_tables = time_program_tables_data


    def __repr__(self):
        return (
            f'table_directions={self._directions_table}\n'
            f'table_stages={self._time_program_tables}'
        )

    def get_directions_table(self) -> DirectionsTable:
        return self._directions_table

    def get_time_program_tables(self) -> Sequence[TimeProgramTable]:
        return self._time_program_tables

    def load_directions_table(self, directions_table: DirectionsTable):
        if not isinstance(directions_table, DirectionsTable):
            raise TypeError(f"program_table must be instance of {DirectionsTable.__name__}")
        self._directions_table = directions_table

    def load_time_program_table(self, program_table: TimeProgramTable):
        if not isinstance(program_table, TimeProgramTable):
            raise TypeError(f"program_table must be instance of {TimeProgramTable.__name__}")
        self._time_program_tables.append(program_table)

    def compare_direction_table_and_time_programs(self, cnt: int = None):
        result = {}
        if not self._directions_table.allow_compare_stages or not self._time_program_tables:
            return result
        if cnt is None:
            cnt = len(self._time_program_tables)
        dir_table_mapping = self._directions_table.get_stages_data().get_direction_to_stages_mapping()
        for n in range(cnt):
            tp = self._time_program_tables[n]
            if tp.allow_compare_stages:
                meta = ComparisonMeta(
                    'Test',
                    DataSourceComparison(TableNames.directions_table, ColNamesDirectionsTable.stages, ''),
                    DataSourceComparison(TableNames.time_program, ColNamesTimeProgramsTable.directions, f'Программа {tp.get_number()}')
                )
                payload = ComparisonDirectionsAndStages(
                    dir_table_mapping,
                    tp.get_stages_data().get_direction_to_stages_mapping(),
                    meta
                )
            else:
                payload = None
            result[tp.get_number()] = payload
        return result

    def compare_direction_table_and_first_time_program(self) -> ComparisonDirectionsAndStages | None:
        try:
            return list(self.compare_direction_table_and_time_programs(1).values())[0]
        except IndexError:
            return None




if __name__ == '__main__':
    start_time = time.perf_counter()
    directions_table = DirectionsTable(read_file_as_string('directions_example').rstrip())
    time_program_table = TimeProgramTable(read_file_as_string('time_program_example').rstrip())
    passport = Passport(
        directions_table=directions_table,
        time_program_tables_data=[time_program_table],
    )
    res1 = passport.compare_direction_table_and_first_time_program()
    s = f'Направления, отсутствующие во временной программе():'
    direct = (
        "\n".join(
            f'Направление={inst.number}; Фазы={stages_as_string(inst.missing_numbers)}'
            for inst in res1.get_missing_in_second()
        )
    )
    print(direct)
    print(passport.compare_direction_table_and_first_time_program())
    print(passport.compare_direction_table_and_first_time_program().dump())
    print(json.dumps(passport.compare_direction_table_and_first_time_program().dump(), indent=4, ensure_ascii=False))
    print(f'Время составило: {time.perf_counter() - start_time}')






