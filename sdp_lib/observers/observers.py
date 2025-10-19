import logging
from datetime import datetime as dt
import time
from collections.abc import MutableSequence
from dataclasses import dataclass
from enum import StrEnum
from functools import cached_property

from sdp_lib.loggers.excel import ExcelLogger


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


class BaseStateObserver:
    def __init__(
            self,
            position: int,
            start_curr_val = None,
            start_prev_val = None,
            name: str = '',
            excel_logger: ExcelLogger = None,
    ):
        self._position = position
        self._name = name
        self._gp_timer = time.perf_counter()
        self._curr_val = start_curr_val
        self._prev_val = start_prev_val
        self._curr_period_data = Period(state=States.UNDEFINED, start=dt.now())
        self._current_state = None
        self._prev_state = None
        self._periods: MutableSequence[Period] = []
        self.excel_logger = excel_logger

    def __repr__(self):
        return f'{self.__class__.__name__}(pos={self._position}, name={self._name})'

    @cached_property
    def position(self) -> int:
        return self._position

    def _set_state(self, curr_val):
        if curr_val is None:
            self._current_state = States.UNDEFINED
        elif curr_val == '0' or curr_val.isdigit() and int(curr_val) == 0:
            self._current_state = States.OFF
        elif curr_val and int(curr_val, 16) >= 1:
            self._current_state = States.ON

    def check(self, curr_val):
        self._set_state(curr_val)
        print(f'{self._current_state=} {self._prev_state=}')
        if self._prev_state != self._current_state:
            print(f'self._prev_state != self._prev_state')
            self._curr_period_data.end = dt.now()
            self._curr_period_data.duration = round(time.perf_counter() - self._gp_timer, 3)
            self._periods.append(self._curr_period_data)
            self._curr_period_data = Period(state=self._current_state, start=dt.now())
            self._gp_timer = time.perf_counter()
        self._prev_state = self._current_state

    def check_is_switched_and_write_log(self, curr_val):
        is_switched = False
        self._set_state(curr_val)
        print(f'{self._name=} {self._current_state=} {self._prev_state=}')
        if self._prev_state != self._current_state:
            self._curr_period_data.end = dt.now()
            self._curr_period_data.duration = round(time.perf_counter() - self._gp_timer, 3)
            self._periods.append(self._curr_period_data)
            self.excel_logger.append_to_next_row(
                [
                    self._curr_period_data.start,
                    self._curr_period_data.end,
                    self._curr_period_data.state,
                    self._name,
                    self._curr_period_data.duration
                ]
            )
            self._curr_period_data = Period(state=self._current_state, start=dt.now())
            self._gp_timer = time.perf_counter()
            is_switched = True
        self._prev_state = self._current_state
        return is_switched


