import datetime
import time
from typing import (
    NamedTuple,
    Any
)

from sdp_lib.data_capture.storage import RecordsStorage
from sdp_lib.utils_common.utils_common import format_time


class ExtraDataEvent(NamedTuple):
    expected_value: Any
    pattern: str


class Event:
    def __init__(
        self,
        entity_name: str,
        records_storage: RecordsStorage,
        pattern_if_curr_val_is_none: str = 'Ошибка...',
        expected_val_data: ExtraDataEvent | None = None,
        protocol: str = ''
    ):
        self._records_storage = records_storage
        self._entity_name = entity_name
        self._pattern_if_curr_val_is_none = pattern_if_curr_val_is_none
        self._current_val = None
        self._prev_val = None
        self._current_val_duration: float = 0
        self._expected_val_duration: float = 0
        self._expected_val_data = expected_val_data or ExtraDataEvent(None, '')
        self._protocol = protocol

    def __repr__(self):
        return (
            f'{self.__class__.__name__}('
            f'curr_val={self._current_val} prev_val={self._prev_val} '
            f'filelog_records={self._records_storage.filelog_records} '
            f'excel_records={self._records_storage.excel_records}'
            f')'
        )

    def _restart_current_val_duration(self):
        self._current_val_duration = time.perf_counter()

    def _restart_extra_val_duration(self):
        self._expected_val_duration = time.perf_counter()

    def get_current_val_duration(self) -> float:
        return time.perf_counter() - self._current_val_duration

    def get_expected_val_duration(self) -> float:
        return time.perf_counter() - self._expected_val_duration

    def process(self, err, curr_value):
        if err:
            self._records_storage.put_to_filelog_storage(str(err))
            return None
        if curr_value is None:
            self._records_storage.put_to_filelog_storage(self._pattern_if_curr_val_is_none)
            return None

        timestamp = datetime.datetime.now()
        curr_val_duration = self.get_current_val_duration()
        self._current_val = curr_value
        if self._current_val != self._prev_val:
            msg = (format_time(timestamp),  self._protocol, self._prev_val, f'{curr_val_duration:.3f}')
            self._records_storage.put_to_excel_records_storage(msg)
            self._restart_current_val_duration()
            if self._current_val == self._expected_val_data.expected_value:
                self._records_storage.put_to_filelog_storage(
                    f'{self._expected_val_data.pattern}, Продолжительность: {self.get_expected_val_duration():.3f}c'
                )
                self._restart_extra_val_duration()
        self._prev_val = self._current_val
        self._records_storage.put_to_filelog_storage(
            f'{self._entity_name}={self._prev_val}, Продолжительность: {curr_val_duration:.3f}c'
        )