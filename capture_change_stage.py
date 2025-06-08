import asyncio
import logging

from openpyxl.reader.excel import load_workbook
from openpyxl.workbook import Workbook

from sdp_lib import logging_config
from sdp_lib.data_capture.events import Event
from sdp_lib.data_capture.main_loop import main
from sdp_lib.data_capture.producers import StageProducer
from sdp_lib.data_capture.storage import RecordsStorage, LogWriter
from sdp_lib.management_controllers.api import PotokS


def load_or_make_wb(filenname):
    try:
        wb = load_workbook(filenname)
    except FileNotFoundError:
        wb = Workbook()
        wb.active.append(['Время', 'Номер фазы', 'Продолжительность фазы'])
        wb.save(filenname)
    return wb


if __name__ == '__main__':
    _wb_filename = 'log_laba2.xlsx'
    _wb = load_or_make_wb(_wb_filename)
    logger = logging.getLogger('penetrate_stage_log')
    log_records_storage = RecordsStorage()
    _log_writer = LogWriter(log_records_storage, logger, _wb, _wb_filename)
    host = PotokS(ipv4='10.45.154.12', host_id='laba_test')
    _producers = [StageProducer(host, Event('Фаза', log_records_storage), name='snmp_change_stage')]

    asyncio.run(main(.2, _producers, _log_writer))