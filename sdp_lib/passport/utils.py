from collections.abc import MutableSequence, Sequence, MutableMapping
from dataclasses import dataclass, field
from typing import TypeAlias

from sdp_lib.passport.constants import StagesMapping


def add_record(container: MutableSequence[str], records: Sequence[str]) -> int:
    cnt = 0
    for record in records:
        cnt += 1
        container.append(record)
    return cnt


stages_content_type: TypeAlias = MutableMapping[float, set[float]]


@dataclass
class StagesData:
    mapping_type: StagesMapping
    _direction_to_stages_mapping: stages_content_type = field(default_factory=dict)
    _stage_to_direction_mapping: stages_content_type = field(default_factory=dict)

    def refresh(self, data: dict[float, set]):
        if self.mapping_type == StagesMapping.direction_to_stages:
            self._direction_to_stages_mapping = {k: v for k, v in data.items()}
            self._stage_to_direction_mapping.clear()
            for direction, stages in self._direction_to_stages_mapping.items():
                for stage in stages:
                    try:
                        self._stage_to_direction_mapping[stage].add(direction)
                    except KeyError:
                        self._stage_to_direction_mapping[stage] = {direction}
        elif self.mapping_type == StagesMapping.stage_to_direction:
            self._stage_to_direction_mapping = {k: v for k, v in data.items()}

    def get_direction_to_stages_mapping(self):
        return self._direction_to_stages_mapping

    def get_stage_to_direction_mapping(self):
        return self._stage_to_direction_mapping