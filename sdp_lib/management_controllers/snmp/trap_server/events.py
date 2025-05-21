import abc
import pickle
from collections.abc import Sequence
from typing import Any

from sdp_lib.management_controllers.snmp import oids, snmp_utils


class BaseEvent:
    def __init__(
            self,
            *,
            varbinds: dict[str, Any],
            time_ticks: int,
    ):
        self._varbinds = varbinds
        self._time_ticks = time_ticks


    def __repr__(self):
        return (
            f'{self.__class__.__name__}'
            f'('
            f'time_ticks={self._time_ticks}, '
            f'varbinds={self._varbinds}'
            f')'
        )

    @property
    def time_ticks(self):
        return self._time_ticks

    @property
    def varbinds(self):
        return self._varbinds

    def _get_time_ticks(self):
        try:
            return int(self._varbinds[oids.Oids.time_ticks])
        except KeyError:
            return int(self._varbinds[oids.Oids.time_ticks][:-2])

    def set_previous_time_ticks(self, time_ticks: int):
        self._prev_time_ticks = int(time_ticks)


class StageEvents(BaseEvent):

    def __init__(
            self,
            *,
            varbinds,
            time_ticks: int,
            num_stage: int,
            val_stage: str,
            is_restart_cycle_stage_point: int
    ):
        super().__init__(varbinds=varbinds, time_ticks=time_ticks)
        self._num_stage = num_stage
        self._val_stage = val_stage
        self._is_restart_cycle_stage_point = is_restart_cycle_stage_point

        # self._prev_stage_num = 0
        # self._prev_stage_val = ''
        # self._prev_time_ticks_change_stage_point = 0

    def __repr__(self):
        return (f'{self.__class__.__name__}'
                f'('
                f'num_stage={self._num_stage}, '
                f'val_stage={self._val_stage}, '
                f'time_ticks={self._time_ticks}, '
                f'is_restart_cycle_stage_point={self._is_restart_cycle_stage_point}, '
                f'varbinds={self._varbinds}'
                f')'
        )

    def __sub__(self, other) -> float:
        if  isinstance(other, StageEvents):
            return (self._time_ticks - other.time_ticks) / 100
        return NotImplemented

    @property
    def num_stage(self):
        return self._num_stage

    @property
    def val_stage(self):
        return self._val_stage

    @property
    def is_restart_cycle_stage_point(self):
        return self._is_restart_cycle_stage_point


class Cycles:

    allowed_type_stages = StageEvents

    def __init__(self, cyc_stages: Sequence[StageEvents]):
        self._cyc_stages = cyc_stages

    def __iter__(self):
        return (s for s in self._cyc_stages)

    def _check_cyc_stages(self):
        if not self._cyc_stages:
            raise TypeError('cyc_stages пуст. должен содержать минимум одну фазу')
        if not all(isinstance(s, StageEvents) for s in self._cyc_stages):
            raise AttributeError(f'В cyc_stages должны содержаться экземпляры класса {self.allowed_type_stages!r}')

    def get_all_stage_events(self):
        return self._cyc_stages

    def get_num_stages(self):
        return len(self._cyc_stages)

    def get_first_stage_event(self):
        return self._cyc_stages[0]

    def get_last_stage_event(self):
        return self._cyc_stages[-1]

    def get_time_cyc(self):
        return self._cyc_stages[-1] - self._cyc_stages[0]

    @property
    def first_stage(self):
        return self._cyc_stages[0].num_stage

    @property
    def last_stage(self):
        return self._cyc_stages[-1].num_stage


if __name__ == '__main__':
    with open(f'vb.pkl', 'rb') as f:
        vb = snmp_utils.parse_varbinds_to_dict(pickle.load(f))
    ob = StageEvents(varbinds=vb, time_ticks=3398636, num_stage=1, val_stage='2', is_restart_cycle_stage_point=False)
    ob1 = StageEvents(varbinds=vb, time_ticks=4398636, num_stage=1, val_stage='2', is_restart_cycle_stage_point=False)
    print(ob1 - ob)

    cyc = Cycles([ob, ob1])
    print(cyc.get_time_cyc())
    print(cyc.get_all_stage_events())
    print(cyc.get_first_stage_event())
    print(cyc.get_last_stage_event())
    print('*' * 100)
    for obj in cyc:
        print(obj)






