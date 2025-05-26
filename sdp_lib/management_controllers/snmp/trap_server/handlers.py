import abc
import collections
import ipaddress
import pickle
from collections import deque
from collections.abc import (
    Callable,
    Sequence, MutableMapping
)
from functools import cached_property
from typing import Any
import logging

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.snmp import (
    oids,
    snmp_utils
)
from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
from sdp_lib.management_controllers.snmp.gen_default_config.events import (
    StageEvents,
    Cycles
)
from sdp_lib import logging_config


verbose_trap_logger = logging.getLogger('trap_verbose')


class HandlersManagement:
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


class AbstractHandler:
    def __init__(self, type_controller: AllowedControllers, name_source: str = ""):
        self._name_source = name_source
        self._type_controller = type_controller
        self._max_stored_messages = 20
        self._max_stored_events = 1024
        self._events_storage = collections.deque(maxlen=self._max_stored_events)
        self._messages_storage = collections.deque(maxlen=self._max_stored_messages)
        # self.time_ticks_oid = self._get_time_ticks_oid()
        self._processed_varbinds: dict | None = None
        self._snmp_notification_timestamp = 0
        self._current_event = None

    def __call__(
            self,
            processed_varbinds: dict[str, Any],
            snmp_notification_timestamp: int,
            *args,
            **kwargs
    ):
        self._snmp_notification_timestamp = snmp_notification_timestamp
        if processed_varbinds:
            self.load_processed_varbinds(processed_varbinds)
        if self.check_if_process_need_to_run():
            self.process_event()

    @abc.abstractmethod
    def check_if_process_need_to_run(self) -> bool:
        """ Если возвращает True, self.process_event будет запущен. """

    @abc.abstractmethod
    def process_event(self, *args, **kwargs):
        """ Основной метод обработки события. """

    def set_max_stored_messages(self, val: int):
        try:
            val = int(val)
        except ValueError:
            print('Устанавливаемое значение должно быть целым числом')
            raise

        if not 1 < val < 128:
            raise ValueError('Устанавливаемое значение должно быть в диапазоне от 1 до 128')
        self._max_stored_messages = val

    def set_max_stored_events(self, val: int):
        try:
            val = int(val)
        except ValueError:
            print('Устанавливаемое значение должно быть целым числом')
            raise
        if not 1 < val < 4096:
            raise ValueError('Устанавливаемое значение должно быть в диапазоне от 1 до 4096')
        self._max_stored_events = val

    def load_processed_varbinds(self, processed_varbinds):
        self._processed_varbinds = processed_varbinds

    def load_event_to_storage(self, event):
        self._events_storage.append(event)

    def load_message_to_storage(self, message):
        self._messages_storage.append(message)

    def clear_event_storage(self):
        self._events_storage.clear()

    def get_time_ticks_from_processed_varbinds(self):
        try:
            return int(self._processed_varbinds[oids.Oids.time_ticks])
        except KeyError:
            return int(self._processed_varbinds[oids.Oids.time_ticks][:-2])

    @property
    def last_event(self):
        try:
            return self._events_storage[-1]
        except IndexError:
            return None

    @property
    def first_event(self):
        try:
            return self._events_storage[0]
        except IndexError:
            return None


class CycleAndStagesHandler(AbstractHandler):

    stage_oids = frozenset([oids.Oids.swarcoUTCTrafftechPhaseStatus, oids.Oids.utcReplyGn])

    def __init__(
            self,
            type_controller: AllowedControllers,
            name_source: str,
            prom_tacts: MutableMapping[int | str, float] = None,
            reset_cyc_num_stage=1
    ):
        super().__init__(type_controller, name_source)
        self._current_cycle_stage_events = deque(maxlen=128)
        self._stage_val_to_num_converter = self._get_method_stage_val_to_num_converter()
        self._stage_oid = self._get_controller_instance_stage_oid()
        self._reset_cyc_num_stage = reset_cyc_num_stage
        self._prom_tacts = prom_tacts or {}
        self._stages_times = {}

    def _get_controller_instance_stage_oid(self):
        if self._type_controller in (AllowedControllers.POTOK_S, AllowedControllers.SWARCO):
            return oids.Oids.swarcoUTCTrafftechPhaseStatus
        elif self._type_controller in (AllowedControllers.POTOK_P, AllowedControllers.PEEK):
            return oids.Oids.utcReplyGn
        else:
            raise ValueError(
                f'Задан некорректный тип контроллера. Допустимые типы: {AllowedControllers.get_all_controllers()}'
            )

    def check_if_process_need_to_run(self) -> bool:
        return bool(self.stage_oids & self._processed_varbinds.keys())

    def _get_method_stage_val_to_num_converter(self) -> Callable:
        if self._type_controller in (AllowedControllers.PEEK, AllowedControllers.POTOK_P):
            return snmp_utils.StageConverterMixinUg405.get_num_stage_from_oid_val
        elif self._type_controller == AllowedControllers.POTOK_S:
            return snmp_utils.StageConverterMixinPotokS.get_num_stage_from_oid_val
        elif self._type_controller == AllowedControllers.POTOK_S:
            return snmp_utils.StageConverterMixinSwarco.get_num_stage_from_oid_val
        raise ValueError(f'Недопустимый тип контроллера: {self._type_controller}')

    def process_event(self):
        try:
            stage_oid_val = self._processed_varbinds[self._stage_oid]
            num_stage = self._stage_val_to_num_converter(stage_oid_val)
        except KeyError:
            verbose_trap_logger.critical(f'Ошибка извлечения номера фазы из оида')
            return

        self._current_event = StageEvents(
            varbinds=self._processed_varbinds,
            time_ticks=self.get_time_ticks_from_processed_varbinds(),
            num_stage=num_stage,
            val_stage=stage_oid_val,
            is_restart_cycle_stage_point=(num_stage == self._reset_cyc_num_stage),
            prev_event=self.last_event
        )

        self._current_cycle_stage_events.append(self._current_event)
        verbose_trap_logger.info(self._current_event.create_log_message())

        if self._current_event.is_restart_cycle_stage_point:
            cyc = Cycles(self._current_cycle_stage_events)
            self._events_storage.append(cyc)
            self._current_cycle_stage_events.clear()
            self._current_cycle_stage_events.append(self._current_event)
            verbose_trap_logger.info(cyc.create_log_message())

        print(f'self._cyc_stage_events: {self._current_cycle_stage_events}')
        print('*' * 100)
        print(f'self._events_storage: {self._events_storage}')
        print('-' * 100)
        return



if __name__ == '__main__':

    with open('vb.pkl' , 'rb') as f:
        obj = pickle.load(f)
        print(obj)
    vb = parse_varbinds_to_dict(obj)

    print(vb)

    c = collections.deque('12345')

    print(c)
    print(c[0])
    print(c[-1])
    print('------')

    while c:
        print(c.pop())