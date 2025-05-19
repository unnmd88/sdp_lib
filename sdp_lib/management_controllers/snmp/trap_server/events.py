from sdp_lib.management_controllers.snmp import oids


class BaseEvent:
    def __init__(self, varbinds, time_ticks: int):
        self._varbinds = varbinds
        self._time_ticks = time_ticks
        # self._prev_time_ticks = 0

    def __repr__(self):
        return f'varbinds: {self._varbinds}\ntime ticks={self._time_ticks}'

    def get_time_ticks(self):
        try:
            return int(self._varbinds[oids.Oids.time_ticks])
        except KeyError:
            return int(self._varbinds[oids.Oids.time_ticks][:-2])

    def set_previous_time_ticks(self, time_ticks: int):
        self._prev_time_ticks = int(time_ticks)


class StageEvents(BaseEvent):

    def __init__(self, varbinds, num_stage: int, val_stage: str, time_ticks):
        super().__init__(varbinds, time_ticks)
        self._num_stage = num_stage
        self._val_stage = val_stage
        # self._prev_stage_num = 0
        # self._prev_stage_val = ''
        # self._prev_time_ticks_change_stage_point = 0

    def __repr__(self):
        return (
            f'{super().__repr__()}\n'
            f'num_stage={self._num_stage}\nval_stage={self._val_stage}'
        )

    def load_prev_stage_info(self, num_stage: int, oid_val: str):
        self._prev_stage_num = int(num_stage)
        self._prev_stage_val = str(oid_val)

    def load_prev_prev_time_ticks_change_stage_point(self, time_ticks: int):
        self._prev_time_ticks_change_stage_point = int(time_ticks)

    @property
    def prev_stage_number(self):
        return self._prev_stage_num

    @property
    def prev_stage_oid_val(self):
        return self._prev_stage_val

