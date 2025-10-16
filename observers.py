from datetime import datetime as dt
import time
from collections.abc import MutableSequence
from dataclasses import dataclass


@dataclass
class SwitchPointData:
    start: dt = 0
    end: dt = 0
    duration: float = 0


class BaseSwitchStateObserver:
    def __init__(
            self,
            comparison_val,
            start_curr_val = None,
            start_prev_val = None,
            name: str = '',
    ):
        self._gp_timer_online = 0
        self._gp_timer_offline = 0
        self._comparison_val = comparison_val
        self._curr_val = start_curr_val
        self._prev_val = start_prev_val
        self._name = name
        self._offline: MutableSequence[SwitchPointData] = []
        self._online: MutableSequence[SwitchPointData] = []
        self._no_connection: MutableSequence[SwitchPointData] = []
        self._curr_data_time = SwitchPointData(start=dt.now())
    # def check_on(self, curr_val):
    #     if curr_val == '0' and self._prev_val != curr_val:
    #         self._switch_points.append(
    #             SwitchPointData(round(time.perf_counter() - self._gp_timer, 3))
    #         )
    #         self._gp_timer = time.perf_counter()
    #     self._prev_val = curr_val
    #
    # def check_off(self, curr_val):
    #     if curr_val and self._prev_val != curr_val:
    #         self._switch_points.append(
    #             SwitchPointData(time.perf_counter() - self._gp_timer)
    #         )
    #         self._gp_timer = time.perf_counter()
    #         self._prev_val = curr_val

    def _dump_data(self, container, timer):
        self._curr_data_time.end = dt.now()
        self._curr_data_time.duration = round(time.perf_counter() - timer, 3)
        self._curr_data_time.end = dt.now()
        container.append(self._curr_data_time)
        self._curr_data_time = SwitchPointData(start=dt.now())


    def check(self, curr_val):
        is_switched = False
        if curr_val != '0' and self._gp_timer_online == 0: # переход из 0 в 1
            is_switched = True
            self._curr_data_time.end = dt.now()
            self._dump_data(self._offline, self._gp_timer_offline)
            self._gp_timer_online = time.perf_counter()
            self._gp_timer_offline = 0
        elif curr_val == '0' and self._gp_timer_offline == 0:
            is_switched = True
            self._curr_data_time.end = dt.now()
            self._dump_data(self._online, self._gp_timer_online)
            self._gp_timer_offline = time.perf_counter()
            self._gp_timer_online = 0
        else: # нет данных от дк
            is_switched = True


        self._prev_val = curr_val


    # def check(self, curr_val):
    #     if curr_val != '0' and self._gp_timer_online == 0: # переход из 0 в 1
    #         self._offline.append(
    #             SwitchPointData(
    #                 duration=round(time.perf_counter() - self._gp_timer_offline, 3),
    #                 end=dt.now(),
    #             )
    #         )
    #         self._gp_timer_online = time.perf_counter()
    #         self._gp_timer_offline = 0
    #
    #     if curr_val == '0' and self._gp_timer_offline == 0:
    #         self._online.append(
    #             SwitchPointData(round(time.perf_counter() - self._gp_timer_online, 3))
    #         )
    #         self._gp_timer_offline = time.perf_counter()
    #         self._gp_timer_online = 0
    #     self._prev_val = curr_val

