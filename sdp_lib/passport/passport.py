import json
import pprint
import time
from collections.abc import MutableSequence, Sequence, MutableMapping, Iterable
from dataclasses import dataclass, asdict
from functools import cached_property
from typing import Any

from sdp_lib.passport.base import StagesData, compare, compare_stages_data_for_directions_and_time_programs, \
    ComparisonDirectionsAndStages, DirectionBaseProperties, SourceComparisonMeta, ComparisonMeta
from sdp_lib.passport.constants import DirectionTypes, Fields, TableNames, \
    ColNamesDirectionsTable, ColNamesTimeProgramsTable, ComparisonDescriptions
from sdp_lib.passport.directions import DirectionsTable
from sdp_lib.passport.time_programms import TimeProgramTable, HeadTimeProgramRow
from sdp_lib.utils_common.utils_common import read_file_as_string, stages_as_string, write_data_to_file


@dataclass
class ComparisonResults:
    description: str
    keys_missing_in_src: str
    values_missing_in_src: str
    keys_missing_in_dst: str
    values_missing_in_dst: str
    src_meta: dict
    dst_meta: dict
    comparison_results: Sequence[dict]

    @cached_property
    def as_dict(self):
        return asdict(self)

    @cached_property
    def as_json(self):
        return json.dumps(asdict(self), indent=4, ensure_ascii=False)

class Passport:
    def __init__(
            self,
            *,
            name: str = '',
            address = '',
            directions_table: DirectionsTable = None,
            time_program_tables_data: MutableSequence[TimeProgramTable] | None = None,
    ):
        self._name = name
        self._address = address
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

    def compare_direction_table_and_time_programs(self, time_programs_range: range = None):
        if not self._directions_table.allow_compare_stages:
            raise ValueError(
                f'Compare not allowed. Reason: cell <{str(ColNamesDirectionsTable.stages)}> '
                f'in table <{str(TableNames.directions_table)}> is not valid.'
            )
        directions_to_stages = self._directions_table.get_stages_data().get_direction_to_stages_mapping()
        for n in range(len(self._time_program_tables)) if time_programs_range is None else time_programs_range:
            tp = self._time_program_tables[n]
            num_program = tp.get_number()
            if tp.allow_compare_stages:
                meta = ComparisonMeta(
                    'Test',
                    SourceComparisonMeta(
                        TableNames.directions_table,
                        ColNamesDirectionsTable.stages,
                        # ''
                    ),
                    SourceComparisonMeta(
                        TableNames.time_program,
                        ColNamesTimeProgramsTable.directions,
                        f'Программа {num_program}',
                        num_program
                    )
                )
                payload = ComparisonDirectionsAndStages(
                    directions_to_stages,
                    tp.get_stages_data().get_direction_to_stages_mapping(),
                    meta
                )
                comparison = num_program, payload
            else:
                comparison = num_program, None
            yield comparison

    def compare_direction_table_and_first_time_program(self) -> tuple[Any, ComparisonDirectionsAndStages | None]:
        return next(self.compare_direction_table_and_time_programs(range(0, 1)))

    def result_compare_direction_table_and_time_programs(self) -> ComparisonResults:
        results = []
        for num_program, comp_res in self.compare_direction_table_and_time_programs():
            curr = {
                str(Fields.has_discrepancy): comp_res.has_discrepancy,
                # str(Fields.time_program): num_program,
                'src_num': comp_res.get_meta().src.number,
                'dst_num': comp_res.get_meta().dst.number,
                str(Fields.missing_in_src): {obj.number: sorted(obj.missing_numbers) for obj in comp_res.get_missing_in_first()},
                str(Fields.missing_in_dst): {obj.number: sorted(obj.missing_numbers) for obj in comp_res.get_missing_in_second()}
            }
            results.append(curr)

        return ComparisonResults(
            str(ComparisonDescriptions.directions_table_to_time_table),
            'Направление',
            "Фазы",
            'Направление',
            "Фазы",
            {
                str(Fields.table_name): str(TableNames.directions_table),
                str(Fields.cell_name): str(ColNamesDirectionsTable.stages)
            },
            {
                str(Fields.table_name): str(TableNames.time_program),
                str(Fields.cell_name): str(ColNamesTimeProgramsTable.directions)
            },
            results
        )

        # return {
        #     str(Fields.description): "Сравнение направлений и фаз из Таблицы направлений с временной программой",
        #     str(Fields.missing_keys): "Направления",
        #     str(Fields.missing_values): "Фазы",
        #     str(Fields.src_meta): {
        #         str(Fields.table_name): str(TableNames.directions_table),
        #         str(Fields.cell_name): str(ColNamesDirectionsTable.stages)
        #     },
        #     str(Fields.dst_meta): {
        #         str(Fields.table_name): str(TableNames.time_program),
        #         str(Fields.cell_name): str(ColNamesTimeProgramsTable.directions)
        #     },
        #     str(Fields.comparison_results): results
        # }

    def dump_to_dict(self):
        return {
            'numCO': self._name,
            'address': self._address,
            'direction_table': self._directions_table.dump_to_dict(),
            'time_program_tables': [],
            'services':
                {
                    'comparisons': {
                        'mappings': {
                            '1': str(ComparisonDescriptions.directions_table_to_time_table),
                            '2': None,
                            '3': None
                        },
                        "1": self.result_compare_direction_table_and_time_programs().as_dict
                    }
                }
        }


if __name__ == '__main__':
    start_time = time.perf_counter()
    directions_table = DirectionsTable(read_file_as_string('_mock_data/directions_example1').rstrip())
    time_program_table1 = TimeProgramTable(read_file_as_string('_mock_data/time_program_example1').rstrip(), HeadTimeProgramRow(1))
    time_program_table2 = TimeProgramTable(read_file_as_string('_mock_data/time_program_example2').rstrip(), HeadTimeProgramRow(2))
    passport = Passport(
        directions_table=directions_table,
        time_program_tables_data=[time_program_table1, time_program_table2],
    )

    try:
        print(passport.result_compare_direction_table_and_time_programs())
        # print(passport.result_compare_direction_table_and_time_programs().as_json)
        with open('compare_result.json', 'w', encoding='utf-8') as f:
            f.write(passport.result_compare_direction_table_and_time_programs().as_json)
    except ValueError:
        pass

    with open('directions_table.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(passport.get_directions_table().dump_to_dict(), ensure_ascii=False, indent=4))

    with open('passport_example.json', 'w', encoding='utf-8') as f:
        f.write(json.dumps(passport.dump_to_dict(), ensure_ascii=False, indent=4))

    print(f'Время составило: {time.perf_counter() - start_time}')






