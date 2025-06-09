from collections import deque
from collections.abc import Iterable
from functools import cached_property
from logging import Logger

from openpyxl.workbook import Workbook


class RecordsStorage:
    """ Класс представляет собой хранилище сообщений для логгирования событий. """
    def __init__(self):
        self._filelog_records = deque(maxlen=1024)
        self._excel_records = deque(maxlen=1024)

    def put_to_filelog_storage(self, *records: str):
        """ Добавляет записи в хранилище. """
        for msg in records:
            self._filelog_records.append(msg)

    def put_to_excel_records_storage(self, *records: Iterable):
        """ Добавляет записи в хранилище. """
        for msg in records:
            self._excel_records.append(msg)

    def clear_filelog_storage(self):
        """ Очищает хранилище записей. """
        self._filelog_records.clear()

    def clear_excel_storage(self):
        """ Очищает хранилище записей. """
        self._excel_records.clear()

    @cached_property
    def filelog_records(self):
        return self._filelog_records

    @cached_property
    def excel_records(self):
        return self._excel_records


class LogWriter:
    """ Класс записей логов. """
    def __init__(
            self,
            record_storage: RecordsStorage,
            logger: Logger,
            wb: Workbook,
            excel_filename: str
    ):
        self._record_storage = record_storage
        self._logger = logger
        self._wb = wb
        self._excel_filename = excel_filename

    def write_filelog(self):
        """
        Осуществляет запись в соответствующий хендлер из настройки логгера(StreamHandler, FileHandler и т.д.)
        """
        while self._record_storage.filelog_records:
            self._logger.info(self._record_storage.filelog_records.popleft())

    def write_excel(self):
        """ Осуществляет запись в соответствующий эксель файл. """
        while self._record_storage.excel_records:
            self._wb.active.append(self._record_storage.excel_records.popleft())
        self._wb.save(self._excel_filename)

    def write_all(self):
        """ Осуществляет все доступные варианты записей. """
        self.write_filelog()
        self.write_excel()



