import abc
import collections
import ipaddress
from collections.abc import Callable, Sequence
from functools import cached_property
from typing import Any
import logging
import datetime as dt

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.parsers.snmp_parsers.processing_methods import get_val_as_str
from sdp_lib.management_controllers.snmp import oids, snmp_utils
from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
from sdp_lib.management_controllers.snmp.trap_recv import Fields
from sdp_lib import logging_config


reduce_logger = logging.getLogger('trap info')


class HandlersData:
    def __init__(self):
        self._handlers = {}
        self._max_handlers = 10

    def register_handlers(self, *args: tuple[str, Callable]):
        for ip, handler in args:
            ipaddress.IPv4Address(ip)
            if ip not in self._handlers:
                self._handlers[ip] = collections.deque(maxlen=self._max_handlers)
            self._handlers[ip].append(handler)

    @cached_property
    def registered_handlers(self) -> dict[str, Sequence[Callable]]:
        return self._handlers

    def get_handlers(self, ip_address: str) -> Sequence[Callable]:
        return self._handlers.get(ip_address, [])


class AbstractEvents:
    def __init__(self, type_controller: AllowedControllers, name_source: str = ""):
        self._name_source = name_source
        self._type_controller = type_controller
        self._max_log_messages = 20
        self.time_ticks_current_event = 0
        self.time_ticks_last_event = 0
        self.time_ticks_delta = 0
        self.time_ticks_oid = self._get_time_ticks_oid()
        self._processed_varbinds: dict | None = None
        self._messages_to_write = collections.deque(maxlen=self._max_log_messages)

    def __call__(
            self,
            processed_varbinds: dict[str, Any],
            *args,
            **kwargs
    ):
        if processed_varbinds:
            self.load_processed_varbinds(processed_varbinds)
        if self.check_if_process_need_to_run():
            # print(f'time_ticks_last_event: {self.time_ticks_last_event}')
            # print(f'time_ticks_current_event: {self.time_ticks_current_event}')
            # print(f'time_ticks_delta: {self.time_ticks_delta}')
            self.process_event()

    @abc.abstractmethod
    def check_if_process_need_to_run(self) -> bool:
        """
        Пользовательское определение для подготовки и запуска
        основного метода process_event.
        """

    def _get_time_ticks_oid(self):
        if self._type_controller in (AllowedControllers.POTOK_S, AllowedControllers.SWARCO):
            return '1.3.6.1.2.1.1.3.0'
        else:
            raise NotImplementedError()

    def load_processed_varbinds(self, processed_varbinds):
        self._processed_varbinds = processed_varbinds

    def set_max_messages(self, val: int):
        self._max_log_messages = int(val)

    def process_event(self, *args, **kwargs):
        pass

    def set_delta_time_ticks(self):
        return self.time_ticks_current_event - self.time_ticks_last_event


class StageEvents(AbstractEvents):
    def __init__(self, type_controller, name_source, stages_data: dict[int, tuple[int, int]], reset_cyc_stage_point=1):
        super().__init__(type_controller, name_source)
        self._stages_data = stages_data
        self._stages_times = {}
        self._stage_oid = self._get_stage_oid()
        self._reset_cyc_stage_point = reset_cyc_stage_point
        self._cyc_counter = 0

    def _get_stage_oid(self):
        if self._type_controller in (AllowedControllers.POTOK_S, AllowedControllers.SWARCO):
            return oids.Oids.swarcoUTCTrafftechPhaseStatus
        else:
            raise NotImplementedError()

    def check_if_process_need_to_run(self) -> bool:
        if self._stage_oid in self._processed_varbinds:
            return True
        return False

    @cached_property
    def stage_handlers(self):
        return {
            AllowedControllers.POTOK_S: [
                (Fields.stage_val, get_val_as_str),
                (Fields.stage_num, snmp_utils.StageConverterMixinPotokS.get_num_stage_from_oid_val),
            ]
        }

    def process_event(self):
        print(f'process_stage')
        try:
            stage_oid_val = self._processed_varbinds[self._stage_oid]
        except KeyError:
            return

        self.time_ticks_current_event = int(self._processed_varbinds.get(self.time_ticks_oid))
        self.set_delta_time_ticks()
        self.time_ticks_delta = self.time_ticks_current_event - self.time_ticks_last_event
        # td_curr_stage = dt.timedelta(seconds=self.time_ticks_delta / 100)
        num_stage = snmp_utils.StageConverterMixinPotokS.get_num_stage_from_oid_val(stage_oid_val)
        td_curr_stage_as_seconds = self.time_ticks_delta / 100
        self._cyc_counter += td_curr_stage_as_seconds

        num_stg, prom_tact = self._stages_data[num_stage]
        self._stages_times[num_stg] = f'stage={num_stg}[green={td_curr_stage_as_seconds - prom_tact} prom={prom_tact} green+prom={td_curr_stage_as_seconds}]'

        if num_stage == self._reset_cyc_stage_point:
            stages_info = ' | '.join(v for v in self._stages_times.values())
            cyc_data = (
                f'\nCycle={dt.timedelta(seconds=self._cyc_counter)} | {self._cyc_counter} seconds, Stages info: {stages_info}'
            )
            self._cyc_counter = 0
        else:
            cyc_data = ''



        print(f'self.time_ticks_delta: {self.time_ticks_delta}')
        print(f'td: {td_curr_stage_as_seconds}')

        msg = (
            f'Source: {self._name_source} | {Fields.stage_num}={num_stage} | '
            f'{Fields.stage_val}={get_val_as_str(stage_oid_val)} | Time Ticks={self.time_ticks_current_event} | '
            # f'Last stage was change {td_curr_stage.seconds} seconds {td_curr_stage.microseconds} microseconds ago'
            f'Last stage was change {td_curr_stage_as_seconds} seconds ago'
            f'{cyc_data}'
        )
        reduce_logger.info(msg)
        self.time_ticks_last_event = self.time_ticks_current_event





