import asyncio
import time
from collections import deque
from collections.abc import Callable, MutableSequence, Iterable

from sdp_lib.modbus.client import Modbus
from sdp_lib.management_controllers.api import PotokS, PotokP, PeekUg405, SwarcoStcip, snmp_engine



class EventNames:
    stage = 'stage'
    cycle = 'cycle'



class State:
    def __init__(self, change_cyc_val):
        self._current_val = None
        self._prev_val = None
        self._change_cyc_val = change_cyc_val
        self._stage_counter: float = 0
        self._cyc_counter: float = 0
        # self._timestamp_point: float = 0
        # self.check_if_state_has_changed: Callable = self._get_check_state_func()

    # def _get_check_state_func(self) -> Callable:
    #     if self._change_cyc_val is None:
    #         return self._check_is_different_curr_prev
    #     else:
    #         return self._check_is_different_curr_expected_value

    def __eq__(self, other):
        if isinstance(other, State):
            return self._current_val == other.current_state
        return NotImplemented

    def set_curr_val(self, val):
        self._current_val = val

    def set_prev_val(self, val):
        self._prev_val = val
    # def set_timestamp_point(self):
    #     self._timestamp_point = time.perf_counter()

    def get_stage_counter_val(self) -> float:
        return time.perf_counter() - self._stage_counter

    def get_cyc_counter_val(self) -> float:
        return time.perf_counter() - self._cyc_counter

    def restart_stage_counter(self):
        self._stage_counter = time.perf_counter()

    def restart_cyc_counter(self):
        self._cyc_counter = time.perf_counter()

    def process(self, val):
        self._current_val = val
        stg_cnt = self.get_stage_counter_val()
        cyc_cnt = self.get_cyc_counter_val()

        print(f'prev_val={self._prev_val}')
        print(f'curr_val={self._current_val}')
        print(f'Секунда цикла={cyc_cnt}')
        print(f'Секунда цикла={cyc_cnt}')

        if self._current_val != self._prev_val:
            print(f'Время фазы {self._prev_val}={stg_cnt}')
            self.restart_stage_counter()
            if self._current_val == self._change_cyc_val:
                print(f'Время цикла={cyc_cnt}')
                self.restart_cyc_counter()
            self._prev_val = self._current_val

    @property
    def current_state(self):
        return self._current_val

    # def _check_is_different_curr_prev(self) -> bool:
    #     return self._current_val != self._prev_val
    #
    # def _check_is_different_curr_expected_value(self) -> bool:
    #     return self._current_val != self._change_cyc_val




class Logging:
    def __init__(
            self,
            host: PotokS | SwarcoStcip | PotokP | PeekUg405 | Modbus,
            state: State
    ):
        self._host = host
        self._state = state







async def logging_snmp(
    snmp_instance: PotokS | SwarcoStcip | PotokP | PeekUg405,
    state: State
) -> MutableSequence[str]:
    log_messages = deque(maxlen=8)





async def polling(
    modbus_host: Modbus,
    snmp_host,
    delay: float
):
    snmp_state = State(change_cyc_val='1')

    while True:
        await snmp_host.get_current_stage()

        err_snmp = snmp_host.response_errors

        curr_stage_snmp = snmp_host.response_data.get('current_stage')
        curr_stage_snmp = str(curr_stage_snmp) if curr_stage_snmp is not None else curr_stage_snmp

        if err_snmp:
            print(err_snmp)
            await asyncio.sleep(delay)
            continue

        elif curr_stage_snmp is None: # Initial
            print('None в ответе фазы от ДК...')
            await asyncio.sleep(delay)
            continue

        if snmp_state._prev_val is None:
            snmp_state.set_prev_val(curr_stage_snmp)
            await asyncio.sleep(delay)
            continue

        snmp_state.process(curr_stage_snmp)

        await asyncio.sleep(delay)


if __name__ == '__main__':
    ip_moxa = '91.227.113.186'
    port_moxa = 502
    bit_to_description = {6: '(Stage=1)', 2: '(Stage=4)', 3: '(Stage=5)', 5: '(Stage=7)'}
    modbus_client = Modbus(ipv4=ip_moxa, port=port_moxa, bit_address_to_description=bit_to_description)

    ip_potok_s = '91.227.113.186'
    snmp_client = PotokS(ipv4=ip_potok_s, engine=snmp_engine, host_id='3139')
    asyncio.run(polling(modbus_client, snmp_client, 1))

