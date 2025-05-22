import abc
import collections
import ipaddress
import pickle
from collections import deque
from collections.abc import Callable, Sequence
from functools import cached_property
from typing import Any
import logging
import datetime as dt

from sdp_lib.management_controllers.constants import AllowedControllers
from sdp_lib.management_controllers.parsers.snmp_parsers.processing_methods import get_val_as_str
from sdp_lib.management_controllers.snmp import oids, snmp_utils
from sdp_lib.management_controllers.snmp.snmp_utils import parse_varbinds_to_dict
# from sdp_lib.management_controllers.snmp.trap_recv import Fields
from sdp_lib import logging_config
from sdp_lib.management_controllers.snmp.trap_server.events import StageEvents, Cycles

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

    # def _get_time_ticks_oid(self):
    #     if self._type_controller in (AllowedControllers.POTOK_S, AllowedControllers.SWARCO):
    #         return '1.3.6.1.2.1.1.3.0'
    #     else:
    #         raise NotImplementedError()

    def load_processed_varbinds(self, processed_varbinds):
        self._processed_varbinds = processed_varbinds

    def max_stored_messages(self, val: int):
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

    stage_oids: {oids.Oids.swarcoUTCTrafftechPhaseStatus, oids.Oids.utcReplyGn}

    def __init__(
            self,
            type_controller,
            name_source,
            stages_data: dict[int, tuple[int, int]],
            reset_cyc_num_stage=1
    ):
        super().__init__(type_controller, name_source)
        self._stages_data = stages_data
        self._stages_times = {}
        self._stage_oid = self._get_stage_oid()
        self._reset_cyc_num_stage = reset_cyc_num_stage
        self._cyc_counter = 0
        self._current_cycle_stage_events = deque(maxlen=128)
        self.stage_val_to_num_converter = self._get_stage_val_to_num_converter()

    def _get_stage_oid(self):
        if self._type_controller in (AllowedControllers.POTOK_S, AllowedControllers.SWARCO):
            return oids.Oids.swarcoUTCTrafftechPhaseStatus
        elif self._type_controller in (AllowedControllers.POTOK_P, AllowedControllers.PEEK):
            return oids.Oids.utcReplyGn
        else:
            raise ValueError(
                f'Задан некорректный тип контроллера. Допустимые типы: {AllowedControllers.get_all_controllers()}'
            )

    def check_if_process_need_to_run(self) -> bool:
        if self._stage_oid in self._processed_varbinds:
            return True
        return False

    def create_log_message_for_cycle_info(self, cyc_instance: Cycles):
        return (
            f'Cycle info: seconds {cyc_instance.get_cyc_time()}, stage_events={cyc_instance.get_all_stage_events()}'
        )

    def _get_stage_val_to_num_converter(self) -> Callable:
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
            num_stage = self.stage_val_to_num_converter(stage_oid_val)
        except KeyError:
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





        if not num_stage == self._reset_cyc_num_stage:
            self.load_event_to_storage(curr_event)
            print(f'curr_event: {curr_event}')
            print(f'self._event_storage: {self._events_storage}')
        else:
            print('*' * 100)
            # print(f'TT: {self._event_storage[0].time_ticks - curr_event.time_ticks}')
            for s in self._events_storage:
                print(f's: {s}')
            print('*' * 100)

            # for event in self._event_storage:
            cyc = 0
            cyc1 = curr_event.time_ticks - self._events_storage[0].time_ticks
            nw = collections.deque()

            while self._events_storage:
                event = self._events_storage.popleft()
                if self._events_storage:
                    next_event = self._events_storage[0]
                else:
                    next_event = curr_event

                nw.append(
                    f'delta from stage {event.num_stage} to {next_event.num_stage} = {abs(next_event.time_ticks - event.time_ticks)}'
                )
                cyc += abs(next_event.time_ticks - event.time_ticks)


            for s in nw:
                print(s)
            print('*' * 100)

            print(f'self._event_storage: {self._events_storage}')
            self.load_event_to_storage(curr_event)
            print(f'self._event_storage: {self._events_storage}')
            print(f'cyc: {cyc}')
            print(f'cyc1: {cyc1}')
            print('*---*' * 100)


        return


        self.time_ticks_current_event = int(self._processed_varbinds.get(self.time_ticks_oid))
        self.set_delta_time_ticks()
        self.time_ticks_delta = self.time_ticks_current_event - self.time_ticks_last_event
        # td_curr_stage = dt.timedelta(seconds=self.time_ticks_delta / 100)
        num_stage = snmp_utils.StageConverterMixinPotokS.get_num_stage_from_oid_val(stage_oid_val)
        td_curr_stage_as_seconds = self.time_ticks_delta / 100
        self._cyc_counter += td_curr_stage_as_seconds

        num_stg, prom_tact = self._stages_data[num_stage]
        self._stages_times[num_stg] = (
            f'\nstage={num_stg}[green={td_curr_stage_as_seconds - prom_tact:.2f} prom={prom_tact} green+prom={td_curr_stage_as_seconds:.2f}]'
        )

        if num_stage == self._reset_cyc_num_stage:
            stages_info = ' | '.join(v for v in self._stages_times.values())
            cyc_data = (
                f'\nCycle={dt.timedelta(seconds=self._cyc_counter):.2f} | {self._cyc_counter} seconds, Stages info: {stages_info}'
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
        verbose_trap_logger.info(msg)
        self.time_ticks_last_event = self.time_ticks_current_event

    @property
    def stage_oid(self):
        return self._stage_oid



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