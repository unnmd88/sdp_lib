import abc
import pickle
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

    @property
    def num_stage(self):
        return self._num_stage

    @property
    def val_stage(self):
        return self._val_stage

    @property
    def is_restart_cycle_stage_point(self):
        return self._is_restart_cycle_stage_point



if __name__ == '__main__':
    with open(f'vb.pkl', 'rb') as f:
        vb = snmp_utils.parse_varbinds_to_dict(pickle.load(f))
    ob = StageEvents(varbinds=vb, time_ticks=3398636,num_stage=1, val_stage='2', is_restart_cycle_stage_point=False)
    print(ob)
    print(ob.dggdasbd())





