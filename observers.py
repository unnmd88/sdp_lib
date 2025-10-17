import logging
from datetime import datetime as dt
import time
from collections.abc import MutableSequence
from dataclasses import dataclass
from enum import IntEnum, StrEnum

from excel_logs import ExcelLogger

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
# formatter = logging.Formatter('{name} [{levelname:^11}] {asctime} {message}', style='{')
formatter = logging.Formatter('{asctime} {message}', style='{')
file_handler = logging.FileHandler('observer.log')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)


class States(StrEnum):
    ON = 'Занят'
    OFF = 'Не Занят'
    UNDEFINED = 'Нет данных'


@dataclass
class Period:
    state: States
    start: dt = 0
    end: dt = 0
    duration: float = 0


class BaseSwitchStateObserver:
    def __init__(
            self,
            # comparison_val,
            start_curr_val = None,
            start_prev_val = None,
            name: str = '',
            excel_logger: ExcelLogger = None,
    ):
        # self._timer_online = 0
        # self._timer_offline = 0
        # self._timer_no_response = 0
        # self._gp_timer = 0
        self._gp_timer = time.perf_counter()
        # self._comparison_val = comparison_val
        self._curr_val = start_curr_val
        self._prev_val = start_prev_val
        self._name = name
        # self._offline: MutableSequence[SwitchPointData] = []
        # self._online: MutableSequence[SwitchPointData] = []
        # self._no_connection: MutableSequence[SwitchPointData] = []
        self._curr_period_data = Period(state=States.UNDEFINED, start=dt.now())
        self._current_state = None
        self._prev_state = None
        self._periods: MutableSequence[Period] = []
        self.excel_logger = excel_logger
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

    # def _dump_data(self, container, timer):
    #     self._curr_period_data.end = dt.now()
    #     self._curr_period_data.duration = round(time.perf_counter() - timer, 3)
    #     self._curr_period_data.end = dt.now()
    #     container.append(self._curr_period_data)
    #     self._curr_period_data = Period(start=dt.now())


    # def check(self, curr_val):
    #     is_switched = False
    #     if curr_val != '0' and self._timer_online == 0: # переход из 0 в 1
    #         is_switched = True
    #         self._curr_data_time.end = dt.now()
    #         self._dump_data(self._offline, self._timer_offline)
    #         self._timer_online = time.perf_counter()
    #         self._timer_offline = 0
    #         self._timer_no_response = 0
    #     elif curr_val == '0' and self._timer_offline == 0:
    #         is_switched = True
    #         self._curr_data_time.end = dt.now()
    #         self._dump_data(self._online, self._timer_online)
    #         self._timer_offline = time.perf_counter()
    #         self._timer_online = 0
    #         self._timer_no_response = 0
    #     elif self._timer_no_response == 0: # нет данных от дк
    #         is_switched = True
    #         self._curr_data_time.end = dt.now()
    #         if self._timer_offline > 0:
    #             self._dump_data(self._offline, self._timer_offline)
    #         elif self._timer_online > 0:
    #             self._dump_data(self._online, self._timer_online)
    #         else:
    #             raise ValueError('Something went wrong...')
    #         self._timer_online = 0
    #         self._timer_offline = 0
    #
    #
    #
    #     self._prev_val = curr_val

    def _set_state(self, curr_val):
        if curr_val is None:
            self._state = States.UNDEFINED
        elif curr_val == '0' or curr_val.isdigit() and int(curr_val) == 0:
            self._current_state = States.OFF
        elif curr_val and int(curr_val, 16) > 1:
            self._current_state = States.ON

    def check(self, curr_val):
        self._set_state(curr_val)
        print(f'{self._current_state=} {self._prev_state=}')
        if self._prev_state != self._current_state:
            print(f'self._prev_state != self._prev_state')
            self._curr_period_data.end = dt.now()
            self._curr_period_data.duration = round(time.perf_counter() - self._gp_timer, 3)
            self._periods.append(self._curr_period_data)
            logger.info(f'name: {self._name} {self._curr_period_data.state=} {self._curr_period_data.duration=}')
            self._curr_period_data = Period(state=self._current_state, start=dt.now())
            self._gp_timer = time.perf_counter()
        self._prev_state = self._current_state

    def check_and_write_log(self, curr_val):
        self._set_state(curr_val)
        print(f'{self._current_state=} {self._prev_state=}')
        if self._prev_state != self._current_state:
            self._curr_period_data.end = dt.now()
            self._curr_period_data.duration = round(time.perf_counter() - self._gp_timer, 3)
            self._periods.append(self._curr_period_data)
            self.excel_logger.add_data_next_row(
                [
                    self._curr_period_data.start,
                    self._curr_period_data.end,
                    self._curr_period_data.state,
                    self._name,
                    self._curr_period_data.duration
                ]
            )
            logger.info(f'name: {self._name} {self._curr_period_data.state=} {self._curr_period_data.duration=}')
            self._curr_period_data = Period(state=self._current_state, start=dt.now())
            self._gp_timer = time.perf_counter()
        self._prev_state = self._current_state

