import pickle
from collections.abc import Sequence
from typing import Any

from sdp_lib.management_controllers.snmp import (
    oids,
    snmp_utils
)


class BaseEvent:
    def __init__(
            self,
            *,
            source: str,
            varbinds: dict[str, Any],
            time_ticks: int,
    ):
        self._source = source
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
    def source(self):
        return self._source

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


class StageEvents(BaseEvent):

    def __init__(
            self,
            *,
            source: str,
            varbinds: dict[str, Any],
            time_ticks: int,
            num_stage: int,
            val_stage: str,
            is_restart_cycle_stage_point: int,
            prev_event
    ):
        super().__init__(source=source, varbinds=varbinds, time_ticks=time_ticks)
        self._num_stage = num_stage
        self._val_stage = val_stage
        self._is_restart_cycle_stage_point = is_restart_cycle_stage_point
        self._prev_event = prev_event

    def __repr__(self):
        return (f'{self.__class__.__name__}'
                f'('
                f'num_stage={self._num_stage}, '
                f'val_stage={self._val_stage}, '
                f'time_ticks={self._time_ticks}, '
                f'is_restart_cycle_stage_point={self._is_restart_cycle_stage_point}, '
                f'varbinds={self._varbinds}'
                # f'prev_event num_stage: {self._prev_event if self._prev_event is not None else "None"}'
                f')'
        )

    def __sub__(self, other) -> float:
        if  isinstance(other, StageEvents):
            return (self._time_ticks - other.time_ticks) / 100
        return NotImplemented

    def __setattr__(self, key, value):
        if key == '_prev_event_stage' and (not isinstance(value, StageEvents) or value is not None):
            raise AttributeError('Аттрибут "prev_event_stage" экземпляром данного класса или None')
        super().__setattr__(key, value)

    def get_data_from_last_to_curr_event(self, last_event) -> str:
        return (
            f'Время от начала фазы {last_event.num_stage} до начала {self._num_stage}: '
            f'{self - last_event} секунд'
        )

    def get_time_delta_from_prev_to_curr_event(self) -> float:
        return self - self._prev_event

    def create_log_message(self):
        return  (
            f'Хост: {self._source} | '
            f'Номер фазы={self._num_stage} | '
            f'Значение фазы в oid={self._val_stage} | '
            f'time_ticks={self._time_ticks}'
        )

    @property
    def prev_event(self):
        return self._prev_event

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
    msg_header_pattern = f'\n** Данные цикла **'

    def __init__(self, cyc_stages: Sequence[StageEvents]):
        self._cyc_stages = tuple(cyc_stages)

    def __getitem__(self, item):
        return self._cyc_stages[item]

    def __iter__(self):
        return (stage for stage in self._cyc_stages)

    def _check_cyc_stages(self):
        if not self._cyc_stages:
            raise TypeError('cyc_stages пуст. должен содержать минимум одну фазу')
        if not all(isinstance(s, StageEvents) for s in self._cyc_stages):
            raise AttributeError(f'В cyc_stages должны содержаться экземпляры класса {self.allowed_type_stages!r}')

    @property
    def first_stage(self):
        return self._cyc_stages[0].num_stage

    @property
    def last_stage(self):
        return self._cyc_stages[-1].num_stage

    def get_all_stage_events(self):
        return self._cyc_stages

    def get_num_stages(self):
        return len(self._cyc_stages)

    def get_first_stage_event(self):
        return self._cyc_stages[0]

    def get_last_stage_event(self):
        return self._cyc_stages[-1]

    def get_cyc_time(self):
        return self._cyc_stages[-1] - self._cyc_stages[0]

    def get_stage_sequence(self):
        return "->".join(str(stg.num_stage) for stg in self)

    def get_stages_data_for_log_as_string(self):
        data = ''
        for i, event in enumerate(self[1:]):
            try:
                data += (
                    f'\nВремя в секундах от старта фазы {self[i].num_stage}'
                    f' до старта фазы {event.num_stage} = {event - self[i]}'
                )
            except AttributeError:
                data += f'\ntime-delta: has not info for stage {event.num_stage}...'
        return data

    def get_cycle_data_for_log_as_string(self):
        return (
            f'{self.msg_header_pattern}\n'
            f'Время цикла в секундах={self.get_cyc_time()}, '
            f'Чередование фаз в цикле={self.get_stage_sequence()}'
        )

    def create_log_message(self, extra_msg: str = ''):

        return (
                self.get_cycle_data_for_log_as_string()
                + self.get_stages_data_for_log_as_string()
                + '\n'
                + extra_msg
                + (f'-' * 120)
        )


def tsts():
    with open(f'vb.pkl', 'rb') as f:
        vb = snmp_utils.parse_varbinds_to_dict(pickle.load(f))
    ob = StageEvents(varbinds=vb, time_ticks=3398636, num_stage=1, val_stage='2', is_restart_cycle_stage_point=True, prev_event=None)
    ob1 = StageEvents(varbinds=vb, time_ticks=3498636, num_stage=2, val_stage='3', is_restart_cycle_stage_point=False, prev_event=ob)
    ob2 = StageEvents(varbinds=vb, time_ticks=3598636, num_stage=3, val_stage='4', is_restart_cycle_stage_point=False, prev_event=ob1)
    ob3 = StageEvents(varbinds=vb, time_ticks=3598736, num_stage=4, val_stage='4', is_restart_cycle_stage_point=True, prev_event=ob2)
    print(ob1 - ob)

    cyc = Cycles([ob, ob1, ob2, ob3])
    print(cyc.get_cyc_time())
    print(cyc.get_all_stage_events())
    print(cyc.get_first_stage_event())
    print(cyc.get_last_stage_event())
    print('*' * 100)
    for obj in cyc:
        print(obj)
    print('*' * 100)
    print(ob1.get_data_from_last_to_curr_event(ob))

    print(cyc.create_log_message())


if __name__ == '__main__':
    tsts()







