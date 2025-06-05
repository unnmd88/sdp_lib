import asyncio
import time

from sdp_lib.modbus.client import Modbus
from sdp_lib.management_controllers.api import PotokS, snmp_engine

async def polling(
    modbus_host: Modbus,
    snmp_host,
    delay: float
):
    cycle_restart_stage = '1'
    curr_stage_snmp = None
    prev_stage_snmp = None
    cyc_timer_modbus = time.perf_counter()
    cyc_timer_snmp = time.perf_counter()
    stage_timer_modbus = time.perf_counter()
    stage_timer_snmp = time.perf_counter()


    while True:
        snmp_instance = await snmp_host.get_current_stage()
        err = snmp_instance.response_errors
        curr_stage_snmp = snmp_instance.response_data.get('current_stage')
        curr_stage_snmp = str(curr_stage_snmp) if curr_stage_snmp is not None else curr_stage_snmp
        if err:
            print(err)
        elif prev_stage_snmp is None: # Initial
            prev_stage_snmp = snmp_instance
        if not err and curr_stage_snmp != prev_stage_snmp and curr_stage_snmp == cycle_restart_stage:
            print(f'Время цикла составило {time.perf_counter() - cyc_timer_snmp}')
            cyc_timer_snmp = time.perf_counter()

        prev_stage_snmp = curr_stage_snmp
        print(f'err: {err}')
        print(f'stage: {curr_stage_snmp}')
        print(f'Текущая секунда цикла: {int(time.perf_counter() - cyc_timer_snmp)}')
        await asyncio.sleep(delay)


if __name__ == '__main__':
    ip_moxa = '91.227.113.186'
    port_moxa = 502
    bit_to_description = {6: '(Stage=1)', 2: '(Stage=4)', 3: '(Stage=5)', 5: '(Stage=7)'}
    modbus_client = Modbus(ipv4=ip_moxa, port=port_moxa, bit_address_to_description=bit_to_description)

    ip_potok_s = '91.227.113.186'
    snmp_client = PotokS(ipv4=ip_potok_s, engine=snmp_engine, host_id='3139')
    asyncio.run(polling(modbus_client, snmp_client, 1))

