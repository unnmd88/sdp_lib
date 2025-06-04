import asyncio
import time

from sdp_lib.modbus.client import Modbus
from sdp_lib.management_controllers.api import PotokS, snmp_engine

async def polling(
    modbus_host: Modbus,
    snmp_host,
    delay: float
):
    while True:
        r = await snmp_host.get_current_stage()
        print(snmp_host)
        print(r)
        await asyncio.sleep(delay)


if __name__ == '__main__':
    ip_moxa = '91.227.113.186'
    port_moxa = 502
    bit_to_description = {6: '(Stage=1)', 2: '(Stage=4)', 3: '(Stage=5)', 5: '(Stage=7)'}
    modbus_client = Modbus(ipv4=ip_moxa, port=port_moxa, bit_address_to_description=bit_to_description)

    ip_potok_s = '91.227.113.186'
    snmp_client = PotokS(ipv4=ip_potok_s, engine=snmp_engine, host_id='3139')
    asyncio.run(polling(modbus_client, snmp_client, 1))

