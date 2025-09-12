import asyncio
import time
from asyncio import create_task
from collections import deque
from collections.abc import Callable, MutableSequence, Iterable

from sdp_lib.modbus.client import Modbus
from sdp_lib.management_controllers.api import PotokS, PotokP, PeekUg405, SwarcoStcip, snmp_engine



class EventNames:
    stage = 'stage'
    cycle = 'cycle'



class State:
    def __init__(self, change_cyc_num_stage):
        self._current_stage = None
        self._prev_stage = None
        self._change_cyc_num_stage = change_cyc_num_stage
        self._stage_counter: float = 0
        self._cyc_counter: float = 0


    def __eq__(self, other):
        if isinstance(other, State):
            return self._current_stage == other.current_state
        return NotImplemented

    def set_curr_val(self, val):
        self._current_stage = val

    def set_prev_val(self, val):
        self._prev_stage = val

    def get_stage_counter_val(self) -> float:
        return time.perf_counter() - self._stage_counter

    def get_cyc_counter_val(self) -> float:
        return time.perf_counter() - self._cyc_counter

    def restart_stage_counter(self):
        self._stage_counter = time.perf_counter()

    def restart_cyc_counter(self):
        self._cyc_counter = time.perf_counter()

    def process(self, err, stage):
        if err:
            print(f'Ошибка запроса: {err}')
            return err
        if stage is None:
            none_value_stage_from_host = 'None в ответе фазы от ДК...'
            print(none_value_stage_from_host)
            return none_value_stage_from_host

        self._current_stage = stage
        stg_cnt = self.get_stage_counter_val()
        cyc_cnt = self.get_cyc_counter_val()

        print(f'prev_val={self._prev_stage}')
        print(f'curr_val={self._current_stage}')
        print(f'Секунда фазы={stg_cnt:.2f}')
        print(f'Секунда цикла={cyc_cnt:.2f}')

        if self._current_stage != self._prev_stage:
            print(f'Время фазы {self._prev_stage}={stg_cnt}')
            self.restart_stage_counter()
            if self._current_stage == self._change_cyc_num_stage:
                print(f'Время цикла={cyc_cnt}')
                self.restart_cyc_counter()
            self._prev_stage = self._current_stage
        return None

    @property
    def current_state(self):
        return self._current_stage



class Logging:
    def __init__(
            self,
            host: PotokS | SwarcoStcip | PotokP | PeekUg405 | Modbus,
            state: State
    ):
        self._host = host
        self._state = state

def save_log(message: str):
    with open('tt_log.log', 'a') as f:
        f.write(message)


def process_snmp(host: PotokS | SwarcoStcip | PotokP | PeekUg405, state: State):

    while True:
        err, stage = yield
        print(f'err: {err}, stage: {stage}')
        try:
            stage = str(int(host.current_stage))
        except TypeError:
            stage = None
        res = state.process(err, stage)
        print(f'res from gen: {res}')




async def polling(
    modbus_host: Modbus,
    snmp_host,
    delay: float
):
    snmp_state_gen = process_snmp(snmp_host, State(change_cyc_num_stage='1'))
    snmp_state_gen.send(None)

    while True:
        pending = [asyncio.create_task(snmp_host.get_current_stage(), name='snmp')]
        while pending:
            done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
            print(f'done: {done}')
            print(f'pending: {pending}')
            for complete_task in done:
                await complete_task
                task_name = complete_task.get_name()
                res = complete_task.result()
                if task_name == 'snmp':
                    snmp_state_gen.send((res.response_errors, res.current_stage))
                create_task(asyncio.to_thread(save_log, f'test message: {time.time()}'))

        await asyncio.sleep(delay)



if __name__ == '__main__':
    ip_moxa = '91.227.113.186'
    port_moxa = 502
    bit_to_description = {6: '(Stage=1)', 2: '(Stage=4)', 3: '(Stage=5)', 5: '(Stage=7)'}
    modbus_client = Modbus(ipv4=ip_moxa, port=port_moxa, matched_bit_addr_to_description=bit_to_description)

    ip_potok_s = '91.227.113.186'
    snmp_client = PotokS(ipv4=ip_potok_s, engine=snmp_engine, host_id='3139')
    asyncio.run(polling(modbus_client, snmp_client, 1))

