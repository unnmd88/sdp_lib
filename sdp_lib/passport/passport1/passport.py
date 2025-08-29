from collections.abc import (
    MutableSequence,
    Sequence
)
from dataclasses import (
    dataclass,
    asdict
)
from typing import Any

from sdp_lib.passport.passport1.base import (
    ComparisonDirectionsAndStages,
    SourceComparisonMeta,
    ComparisonMeta
)
from sdp_lib.passport.constants import (
    Fields,
    TableNames,
    ColNamesDirectionsTable,
    ColNamesTimeProgramsTable,
    ComparisonDescriptions
)
from sdp_lib.passport.passport1.directions import DirectionsTable
from sdp_lib.passport.passport1.time_programms import (
    TimeProgramTable,
    HeadTimeProgramRow
)
from sdp_lib.utils_common.utils_common import read_file_as_string, to_json, timed


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


@dataclass(frozen=True, slots=True)
class PassportData:
    numCO: str
    address: str
    direction_table: DirectionsTable
    time_program_tables: Sequence[TimeProgramTable]


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
        self._state = {}

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

    def compare_direction_table_to_all_time_programs_and_get_result(self) -> ComparisonResults:
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
            [obj.dump() for _, obj in self.compare_direction_table_and_time_programs()]
        )

    def dump_to_dict(self) -> dict[str, Any]:
        return {
            str(Fields.numCO): self._name,
            str(Fields.address): self._address,
            str(Fields.direction_table):
                self._directions_table.dump_to_dict() if self._directions_table is not None else None,
            str(Fields.time_program_tables):
                {obj.get_number(): obj.dump_to_dict() for obj in self._time_program_tables}
        }


@timed
def display():
    dt = DirectionsTable(read_file_as_string('../_mock_data/directions_example1'))
    tp1 = TimeProgramTable(read_file_as_string('../_mock_data/time_program_example1'), HeadTimeProgramRow(1))
    tp2 = TimeProgramTable(read_file_as_string('../_mock_data/time_program_example2'), HeadTimeProgramRow(2))

    passport = Passport(directions_table=dt, time_program_tables_data=[tp1, tp2])

    try:
        print(passport.compare_direction_table_to_all_time_programs_and_get_result())
        print(to_json(asdict(passport.compare_direction_table_to_all_time_programs_and_get_result()),
                      'compare_result.json'))
    except ValueError:
        print('!! ValueError !!')

    to_json(passport.get_directions_table().dump_to_dict (), 'directions_table.json')
    to_json(passport.dump_to_dict(), 'passport_example')

if __name__ == '__main__':
    display()









