from sdp_lib.management_controllers import api

import asyncio
import logging
import time
from enum import IntEnum, StrEnum, nonmember

from pyModbusTCP.client import ModbusClient
from dotenv import load_dotenv
from sdp_lib.management_controllers.snmp.snmp_requests import snmp_engine
from sdp_lib.management_controllers.snmp import snmp_requests
from sdp_lib.management_controllers.snmp import oids
from sdp_lib.management_controllers.snmp import snmp_utils
from sdp_lib import logging_config


load_dotenv()


#Example
moxa_ip = '10.45.154.22'
c = ModbusClient(host=moxa_ip, port=502, timeout=2)
regs_DI = c.read_discrete_inputs(0, 8)

print(regs_DI)
##########


logger = logging.getLogger('Modbus')
logger_full_file_writer = logging.getLogger('full_log')
logger_reduce_file_writer = logging.getLogger('reduce_log')


class States(StrEnum):
    red = 'Red'
    yellow = 'Yellow'
    green = 'Green'


def get_state(states):

    g1_red, g1_yellow, g1_green = states[1], states[2], states[3]
    g2_red, g2_yellow, g2_green = states[4], states[5], states[6]

    if g1_yellow or g2_green:
        stage = 2
    elif g2_yellow or g1_green:
        stage = 1
    else:
        stage = None
    return stage


def get_host():
    return api.PotokS(ipv4='10.45.154.12', engine=snmp_engine)


async def get_stage():

    res = await snmp_requests.get(
        ip_v4='10.45.154.12',
        community='private',
        oids=[oids.Oids.swarcoUTCTrafftechPhaseStatus],
        engine=snmp_engine,
    )
    try:
        oid, val = res[3][0]
        stage = snmp_utils.StageConverterMixinSwarco.get_num_stage_from_oid_val(str(val))
    except IndexError:
        stage = val = oid = None

    return stage, str(oid), str(val)


async def main(delay=1.0):
    while True:
        regs_DI = c.read_discrete_inputs(0, 8)
        # print(f'regs_list_1: {regs_DI}')
        try:
            stage_moxa = get_state(regs_DI)
        except TypeError as exc:
            print(f'ERROR: {exc}')
            logger_full_file_writer.error(exc)
            await asyncio.sleep(delay)
            continue

        stage_snmp, oid, val = await get_stage()
        stage_snmp = str(stage_snmp) if stage_snmp is None else stage_snmp
        msg = f'Stage moxa modbus: {stage_moxa} | Stage snmp get: num={stage_snmp:<4} | val={val}'

        if stage_moxa != stage_snmp or stage_snmp is None:
            logger_full_file_writer.warning(msg)
            logger_reduce_file_writer.warning(msg)
            # logger_reduce_msg_writer.info(f'Stage moxa: {stage_moxa} | Stage snmp={stage_snmp}')
        else:
            logger_full_file_writer.info(msg)



        # logger.debug(f'Stage moxa: {stage} | Stage snmp={stage}')

        # print(f'stage={stage}, val={str(val)}')
        await asyncio.sleep(delay)
        # print(snmp_host)



if __name__ == '__main__':
    asyncio.run(main(.1))