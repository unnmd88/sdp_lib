import json
import pprint
import time
from collections.abc import MutableMapping, MutableSequence
from dataclasses import dataclass, make_dataclass, field
from enum import StrEnum
from functools import cached_property
from typing import (
    Any,
    TypeAlias
)

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.parsers.parser_core import Parsers


properties: TypeAlias = dict[str, tuple[str, ...]]



def get_xp_data_as_dict(xp_data: tuple[str, str, str, str]):
    """
    Формирует словарь с данными из xp_data.
    :param xp_data: Кортеж из self.all_xp_data. Пример: ('1', 'УПРАВЛЕНИЕ', 'FT', '3')
    :return: Словарь с данными из xp_data.
             Пример:
                {
                    "xp": "1",
                    "current_status": "УПРАВЛЕНИЕ",
                    "current_mode": "FT",
                    "current_stage": "3"
                }
    """
    return {
        str(FieldsNames.curr_xp): xp_data[0],
        str(FieldsNames.curr_status): xp_data[1],
        str(FieldsNames.curr_mode): xp_data[2],
        str(FieldsNames.curr_stage): xp_data[3],
    }


@dataclass
class MainPageData:
    address: str  = None
    plan: str  = None
    plan_param: str  = None
    current_time: str  = None
    alarms: str  = None
    num_streams: int = None
    all_xp_data: MutableSequence = field(default_factory=list)

    @cached_property
    def as_dict(self):
        return {
            str(FieldsNames.curr_address): self.address,
            str(FieldsNames.curr_plan): self.plan,
            str(FieldsNames.curr_plan_param): self.plan_param,
            str(FieldsNames.curr_time): self.current_time,
            str(FieldsNames.curr_alarms): self.alarms,
            str(FieldsNames.num_streams): len(self.all_xp_data),
            str(FieldsNames.streams_data): [get_xp_data_as_dict(xp_data) for xp_data in self.all_xp_data],
        }


@dataclass
class InputsPageData:
    inputs: MutableMapping[str, Any] = field(default_factory=dict)

    @cached_property
    def as_dict(self):
        return {str(FieldsNames.inputs): self.inputs}


# class ParserBase(Parsers):
#     """
#     Базовый класс интерфейса парсера Peek web.
#     """
#     def __init__(self):
#         super().__init__()
#         # self._main_page_data: MainPageData = MainPageData()
#         # self.content_as_list = None
#
#     def base_extract_data_from_line(self, line: str, pattern: str):
#         """
#         Базовый метод извлечения данных из строки спарсенного контента с web страницы.
#         Делит строку на 2 части, где вторая часть - искомые данные(номер плана/адрес и т.д.)
#         :param line: Строка, из которой будут излечены данные.
#         :param pattern: Шаблон, по которому будет разделена строка для извлечения данных.
#         :return: Данные, если переданная строка валидна, иначе исходная строка.
#         """
#         try:
#             return line.split(pattern)[-1]
#         except IndexError:
#             pass
#         return None
#
#     def build_attr_data_for_response(self, props: list[tuple[str, Any]]) -> dict[str, properties]:
#         # self.data_for_response = {k: v for k, v in props}
#         self.parsed_content_as_dict = {k: v for k, v in props}
#         return self.parsed_content_as_dict


class MainPageParser(Parsers):
    """
    Парсер контента главной web страницы ДК Peek.
    """

    _pattern_address = ':SUBTITLE;'
    _pattern_plan = ':D;;##T_PLAN##;'
    _pattern_plan_param = '##T_TIMINGSET##;'
    _pattern_time = ':D;;##T_TIME##;'
    _pattern_alarms = ':D;;##T_ALARMS##;'
    _pattern_end_table = ':ENDTABLE'

    _pattern_stream = '<b>##T_STREAM## '
    _pattern_state = ':D;;##T_STATE##;'
    _pattern_cycle = ':D;;##T_CYCLE##;'
    _pattern_mode_and_stage = ':D;;##T_MODE## (##T_STAGE##);'

    def __init__(self):
        super().__init__()
        self._page_data: MainPageData = MainPageData()
        # self.address = None
        # self.current_plan = None
        # self.current_plan_param = None
        # self.current_time = None
        # self.current_alarms = None
        # self._num_xp = None
        # self.all_xp_data = []

    def __repr__(self):
        return (
            # f'self.address: {self.address!r}\n'
            # f'self.current_plan: {self.current_plan!r}\n'
            # f'self.current_plan_param: {self.current_plan_param!r}\n'
            # f'self.current_time: {self.current_time!r}\n'
            # f'self.alarms: {self.current_alarms!r}\n'
            # f'self.num_xp: {self._num_xp!r}\n'
            # f'self.all_xp_data: {self.all_xp_data!r}\n'
            # f'self.parsed_content_as_dict: {json.dumps(self.parsed_content_as_dict, indent=4, ensure_ascii=False)}'
        )

    def _base_extract_data_from_line(self, line: str, pattern: str):
        """
        Базовый метод извлечения данных из строки спарсенного контента с web страницы.
        Делит строку на 2 части, где вторая часть - искомые данные(номер плана/адрес и т.д.)
        :param line: Строка, из которой будут излечены данные.
        :param pattern: Шаблон, по которому будет разделена строка для извлечения данных.
        :return: Данные, если переданная строка валидна, иначе исходная строка.
        """
        try:
            return line.split(pattern)[-1]
        except IndexError:
            pass
        return None

    def _extract_address(self, line: str) -> str:
        """
        Извлекает адрес из переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая адрес.
                     Пример: ":SUBTITLE;Moscow: Панфиловс пр / Андреевка"
        :return: Адрес объекта. Пример: "Moscow: Панфиловс пр / Андреевка"
        """
        return self._base_extract_data_from_line(line, self._pattern_address)

    def _extract_current_plan(self, line: str) -> str | None:
        """
        Извлекает номер текущего плана ДК из переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая номер плана.
                     Пример: ":D;;##T_PLAN##;006 -             "
        :return: Текущий номер плана. Пример: "006"
        """
        try:
            return line.split(self._pattern_plan)[-1].split(maxsplit=1)[0]
        except IndexError:
            pass
        return None

    def _extract_current_plan_param(self, line: str) -> str | None:
        """
        Извлекает параметр текущего плана ДК из переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая параметр плана.
                     Пример: ":D;;##T_TIMINGSET##;005"
        :return: Текущий параметр плана. Пример: "005"
        """
        return self._base_extract_data_from_line(line, self._pattern_plan_param)

    def _extract_current_time(self, line: str) -> str | None:
        """
        Извлекает текущее время ДК из переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая текущее время.
                     Пример: ":D;;##T_TIME##;2025-03-01 16:39:57"
        :return: Текущее время. Пример: "2025-03-01 16:39:57"
        """
        return self._base_extract_data_from_line(line, self._pattern_time)

    def _extract_current_alarms(self, line: str) -> str | None:
        """
        Извлекает текущие ошибки ДК из переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
                     Пример: ":D;;##T_ALARMS##;ISWC"
        :return: Текущие ошибки. Пример: "ISWC"
        """
        return self._base_extract_data_from_line(line, self._pattern_alarms)

    def _extract_current_num_xp(self, line: str) -> str | None:
        """
        Извлекает номер текущего потока(xp) переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
                     Пример: "<b>##T_STREAM## 1</b>"
        :return: Номер текущего потока(xp). Пример: "1"
        """
        try:
            return line.split(self._pattern_stream)[-1].replace('</b>', '')
        except IndexError:
            pass
        return line

    def _extract_current_xp_state(self, line: str) -> str | None:
        """
        Извлекает номер текущего потока(xp) переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
                     Пример: ":D;;##T_STATE##;УПРАВЛЕНИЕ"
        :return: Номер текущего потока(xp). Пример: "УПРАВЛЕНИЕ"
        """
        return self._base_extract_data_from_line(line, self._pattern_state)

    def _extract_current_xp_mode_and_stage(self, line: str) -> tuple[str | None, str | None]:
        """
        Извлекает текущий режим и фазу потока(xp) переданной строки line.
        :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
                     Пример: ":D;;##T_MODE## (##T_STAGE##);FT (5)"
        :return: Кортеж из значений текущего режима и фазы потока(xp). Пример: ("FT", "5")
        """
        try:
            mode, stage = self._base_extract_data_from_line(line, self._pattern_mode_and_stage).split()
            return mode, stage.replace('(', '').replace(')', '')
        except IndexError:
            return None, None

    def _parse_xp_data(self, lines: list[str]) -> tuple[str, str, str, str]:
        """
        Извлекает текущую информацию для потока(xp) переданного списка lines.
        :param lines: Список с web страницы ДК Peek, содержащий строки с данными о потоке.
                      len(lines) == 7.
                      Пример: ["<b>##T_STREAM## 1</b>",
                              ":BEGINTABLE",
                              ":W;;200px;",
                              ":D;;##T_STATE##;УПРАВЛЕНИЕ",
                              ":D;;##T_CYCLE##;0 (0)",
                              ":D;;##T_MODE## (##T_STAGE##);FT (6)",
                              ":ENDTABLE"]
        :return: Кортеж из значений текущего режима и фазы потока(xp). Пример: ("FT", "6")
        """
        # print(f'lines::: {lines}')
        num_xp = self._extract_current_num_xp(lines[0])
        state = self._extract_current_xp_state(lines[3])
        mode, stage = self._extract_current_xp_mode_and_stage(lines[5])
        return num_xp, state, mode, stage

    def parse(self, content: str):
        """
        Парсит данные с основной web страницы ДК Peek, присваивая их соответствующим атрибутам.
        :param get_parsed_data_as_dict: Параметр является опцией.
                                        При True -> формирует атрибут self.parsed_content_as_dict.
        :return: None.
        """
        print(f'content: {content}')
        content_as_list_lines = content.splitlines()
        common_data_is_extracted = False
        for i, line in enumerate(content_as_list_lines):
            if not common_data_is_extracted:
                if self._pattern_address in line:
                    self._page_data.address = self._extract_address(line)
                elif self._pattern_plan in line:
                    self._page_data.plan = self._extract_current_plan(line)
                elif self._pattern_plan_param in line:
                    self._page_data.plan_param = self._extract_current_plan_param(line)
                elif self._pattern_time in line:
                    self._page_data.current_time = self._extract_current_time(line)
                elif self._pattern_alarms in line:
                    self._page_data.alarms = self._extract_current_alarms(line)
                elif self._pattern_end_table in line:
                    common_data_is_extracted = True
            elif self._pattern_stream in line:
                stream_data = content_as_list_lines[i: i + 7]
                self._page_data.all_xp_data.append(self._parse_xp_data(stream_data))
        # self.parsed_content_as_dict = self._main_page_data.as_dict
        print(self._page_data.as_dict)
        return self._page_data.as_dict

    # def _get_xp_data_as_dict(self, xp_data: tuple[str, str, str, str]):
    #     """
    #     Формирует словарь с данными из xp_data.
    #     :param xp_data: Кортеж из self.all_xp_data. Пример: ('1', 'УПРАВЛЕНИЕ', 'FT', '3')
    #     :return: Словарь с данными из xp_data.
    #              Пример:
    #                 {
    #                     "xp": "1",
    #                     "current_status": "УПРАВЛЕНИЕ",
    #                     "current_mode": "FT",
    #                     "current_stage": "3"
    #                 }
    #     """
    #     return {
    #         str(FieldsNames.curr_xp): xp_data[0],
    #         str(FieldsNames.curr_status): xp_data[1],
    #         str(FieldsNames.curr_mode): xp_data[2],
    #         str(FieldsNames.curr_stage): xp_data[3],
    #     }

    # def build_attr_data_for_response(self) -> dict[str, properties]:
    #     """
    #     Формирует словарь с распарменными данными о состоянии ДК. Данные берёт из соответствующих атрибутов.
    #     :return: Словарь с данными о текущем состоянии ДК.
    #              Пример:
    #              {
    #                 "current_address": "Moscow: Панфиловс пр / Андреевка",
    #                 "current_plan": "005",
    #                 "current_plan_parameter": "005",
    #                 "current_time": "2025-03-01 16:08:41",
    #                 "current_alarms": "ISWC",
    #                 "number_of_streams": 2,
    #                 "streams_data": [
    #                     {
    #                         "xp": "1",
    #                         "current_status": "УПРАВЛЕНИЕ",
    #                         "current_mode": "FT",
    #                         "current_stage": "3"
    #                     },
    #                     {
    #                         "xp": "2",
    #                         "current_status": "УПРАВЛЕНИЕ",
    #                         "current_mode": "FT",
    #                         "current_stage": "6"
    #                     }
    #                 ]
    #             }
    #     """
    #     self.data_for_response = {
    #         str(FieldsNames.curr_address): self.address,
    #         str(FieldsNames.curr_plan): self.current_plan,
    #         str(FieldsNames.curr_plan_param): self.current_plan_param,
    #         str(FieldsNames.curr_time): self.current_time,
    #         str(FieldsNames.curr_alarms): self.current_alarms,
    #         str(FieldsNames.num_streams): len(self.all_xp_data),
    #         str(FieldsNames.streams_data): [self._get_xp_data_as_dict(xp_data) for xp_data in self.all_xp_data]
    #     }
    #     return self.data_for_response

    # def _get_properties(self) -> list[tuple[str, Any]]:
    #     return [
    #         (str(FieldsNames.curr_address), self.address),
    #         (str(FieldsNames.curr_plan), self.current_plan),
    #         (str(FieldsNames.curr_plan_param), self.current_plan_param),
    #         (str(FieldsNames.curr_time), self.current_time),
    #         (str(FieldsNames.curr_alarms), self.current_alarms),
    #         (str(FieldsNames.num_streams), len(self.all_xp_data)),
    #         (str(FieldsNames.streams_data), [self._get_xp_data_as_dict(xp_data) for xp_data in self.all_xp_data])
    #     ]


# class MainPageParser(ParserBase):
#     """
#     Парсер контента главной web страницы ДК Peek.
#     """
#
#     pattern_address = ':SUBTITLE;'
#     pattern_plan = ':D;;##T_PLAN##;'
#     pattern_plan_param = '##T_TIMINGSET##;'
#     pattern_time = ':D;;##T_TIME##;'
#     pattern_alarms = ':D;;##T_ALARMS##;'
#     pattern_end_table = ':ENDTABLE'
#
#     pattern_stream = '<b>##T_STREAM## '
#     pattern_state = ':D;;##T_STATE##;'
#     pattern_cycle = ':D;;##T_CYCLE##;'
#     pattern_mode_and_stage = ':D;;##T_MODE## (##T_STAGE##);'
#
#     def __init__(self):
#         super().__init__()
#         self.address = None
#         self.current_plan = None
#         self.current_plan_param = None
#         self.current_time = None
#         self.current_alarms = None
#         self._num_xp = None
#         self.all_xp_data = []
#
#     def __repr__(self):
#         return (
#             f'self.address: {self.address!r}\n'
#             f'self.current_plan: {self.current_plan!r}\n'
#             f'self.current_plan_param: {self.current_plan_param!r}\n'
#             f'self.current_time: {self.current_time!r}\n'
#             f'self.alarms: {self.current_alarms!r}\n'
#             f'self.num_xp: {self._num_xp!r}\n'
#             f'self.all_xp_data: {self.all_xp_data!r}\n'
#             f'self.parsed_content_as_dict: {json.dumps(self.parsed_content_as_dict, indent=4, ensure_ascii=False)}'
#         )
#
#     def extract_address(self, line: str) -> str:
#         """
#         Извлекает адрес из переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая адрес.
#                      Пример: ":SUBTITLE;Moscow: Панфиловс пр / Андреевка"
#         :return: Адрес объекта. Пример: "Moscow: Панфиловс пр / Андреевка"
#         """
#         return self.base_extract_data_from_line(line, self.pattern_address)
#
#     def extract_current_plan(self, line: str) -> str | None:
#         """
#         Извлекает номер текущего плана ДК из переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая номер плана.
#                      Пример: ":D;;##T_PLAN##;006 -             "
#         :return: Текущий номер плана. Пример: "006"
#         """
#         try:
#             return line.split(self.pattern_plan)[-1].split(maxsplit=1)[0]
#         except IndexError:
#             pass
#         return None
#
#     def extract_current_plan_param(self, line: str) -> str | None:
#         """
#         Извлекает параметр текущего плана ДК из переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая параметр плана.
#                      Пример: ":D;;##T_TIMINGSET##;005"
#         :return: Текущий параметр плана. Пример: "005"
#         """
#         return self.base_extract_data_from_line(line, self.pattern_plan_param)
#
#     def extract_current_time(self, line: str) -> str | None:
#         """
#         Извлекает текущее время ДК из переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая текущее время.
#                      Пример: ":D;;##T_TIME##;2025-03-01 16:39:57"
#         :return: Текущее время. Пример: "2025-03-01 16:39:57"
#         """
#         return self.base_extract_data_from_line(line, self.pattern_time)
#
#     def extract_current_alarms(self, line: str) -> str | None:
#         """
#         Извлекает текущие ошибки ДК из переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
#                      Пример: ":D;;##T_ALARMS##;ISWC"
#         :return: Текущие ошибки. Пример: "ISWC"
#         """
#         return self.base_extract_data_from_line(line, self.pattern_alarms)
#
#     def extract_current_num_xp(self, line: str) -> str | None:
#         """
#         Извлекает номер текущего потока(xp) переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
#                      Пример: "<b>##T_STREAM## 1</b>"
#         :return: Номер текущего потока(xp). Пример: "1"
#         """
#         try:
#             return line.split(self.pattern_stream)[-1].replace('</b>', '')
#         except IndexError:
#             pass
#         return line
#
#     def extract_current_xp_state(self, line: str) -> str | None:
#         """
#         Извлекает номер текущего потока(xp) переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
#                      Пример: ":D;;##T_STATE##;УПРАВЛЕНИЕ"
#         :return: Номер текущего потока(xp). Пример: "УПРАВЛЕНИЕ"
#         """
#         return self.base_extract_data_from_line(line, self.pattern_state)
#
#     def extract_current_xp_mode_and_stage(self, line: str) -> tuple[str | None, str | None]:
#         """
#         Извлекает текущий режим и фазу потока(xp) переданной строки line.
#         :param line: Строка с web страницы ДК Peek, содержащая текущие ошибки.
#                      Пример: ":D;;##T_MODE## (##T_STAGE##);FT (5)"
#         :return: Кортеж из значений текущего режима и фазы потока(xp). Пример: ("FT", "5")
#         """
#         try:
#             mode, stage = self.base_extract_data_from_line(line, self.pattern_mode_and_stage).split()
#             return mode, stage.replace('(', '').replace(')', '')
#         except IndexError:
#             return None, None
#
#     def parse_xp_data(self, lines: list[str]) -> tuple[str, str, str, str]:
#         """
#         Извлекает текущую информацию для потока(xp) переданного списка lines.
#         :param lines: Список с web страницы ДК Peek, содержащий строки с данными о потоке.
#                       len(lines) == 7.
#                       Пример: ["<b>##T_STREAM## 1</b>",
#                               ":BEGINTABLE",
#                               ":W;;200px;",
#                               ":D;;##T_STATE##;УПРАВЛЕНИЕ",
#                               ":D;;##T_CYCLE##;0 (0)",
#                               ":D;;##T_MODE## (##T_STAGE##);FT (6)",
#                               ":ENDTABLE"]
#         :return: Кортеж из значений текущего режима и фазы потока(xp). Пример: ("FT", "6")
#         """
#         # print(f'lines::: {lines}')
#         num_xp = self.extract_current_num_xp(lines[0])
#         state = self.extract_current_xp_state(lines[3])
#         mode, stage = self.extract_current_xp_mode_and_stage(lines[5])
#         return num_xp, state, mode, stage
#
#     def parse(self, content: str):
#         """
#         Парсит данные с основной web страницы ДК Peek, присваивая их соответствующим атрибутам.
#         :param get_parsed_data_as_dict: Параметр является опцией.
#                                         При True -> формирует атрибут self.parsed_content_as_dict.
#         :return: None.
#         """
#         self.content_as_list = content.splitlines()
#         common_data_is_extracted = False
#         for i, line in enumerate(self.content_as_list):
#             if not common_data_is_extracted:
#                 if self.pattern_address in line:
#                     self.address = self.extract_address(line)
#                 elif self.pattern_plan in line:
#                     self.current_plan = self.extract_current_plan(line)
#                 elif self.pattern_plan_param in line:
#                     self.current_plan_param = self.extract_current_plan_param(line)
#                 elif self.pattern_time in line:
#                     self.current_time = self.extract_current_time(line)
#                 elif self.pattern_alarms in line:
#                     self.current_alarms = self.extract_current_alarms(line)
#                 elif self.pattern_end_table in line:
#                     common_data_is_extracted = True
#             elif self.pattern_stream in line:
#                 stream_data = self.content_as_list[i: i + 7]
#                 self.all_xp_data.append(self.parse_xp_data(stream_data))
#
#         # assert self.all_xp_data and self.data_for_response #DEBUG
#         # print(f'main_page.build_data_for_response(): {self.build_attr_data_for_response(self._get_properties())}')
#         return self.build_attr_data_for_response(self._get_properties())
#
#     def _get_xp_data_as_dict(self, xp_data: tuple[str, str, str, str]):
#         """
#         Формирует словарь с данными из xp_data.
#         :param xp_data: Кортеж из self.all_xp_data. Пример: ('1', 'УПРАВЛЕНИЕ', 'FT', '3')
#         :return: Словарь с данными из xp_data.
#                  Пример:
#                     {
#                         "xp": "1",
#                         "current_status": "УПРАВЛЕНИЕ",
#                         "current_mode": "FT",
#                         "current_stage": "3"
#                     }
#         """
#         return {
#             str(FieldsNames.curr_xp): xp_data[0],
#             str(FieldsNames.curr_status): xp_data[1],
#             str(FieldsNames.curr_mode): xp_data[2],
#             str(FieldsNames.curr_stage): xp_data[3],
#         }
#
#     # def build_attr_data_for_response(self) -> dict[str, properties]:
#     #     """
#     #     Формирует словарь с распарменными данными о состоянии ДК. Данные берёт из соответствующих атрибутов.
#     #     :return: Словарь с данными о текущем состоянии ДК.
#     #              Пример:
#     #              {
#     #                 "current_address": "Moscow: Панфиловс пр / Андреевка",
#     #                 "current_plan": "005",
#     #                 "current_plan_parameter": "005",
#     #                 "current_time": "2025-03-01 16:08:41",
#     #                 "current_alarms": "ISWC",
#     #                 "number_of_streams": 2,
#     #                 "streams_data": [
#     #                     {
#     #                         "xp": "1",
#     #                         "current_status": "УПРАВЛЕНИЕ",
#     #                         "current_mode": "FT",
#     #                         "current_stage": "3"
#     #                     },
#     #                     {
#     #                         "xp": "2",
#     #                         "current_status": "УПРАВЛЕНИЕ",
#     #                         "current_mode": "FT",
#     #                         "current_stage": "6"
#     #                     }
#     #                 ]
#     #             }
#     #     """
#     #     self.data_for_response = {
#     #         str(FieldsNames.curr_address): self.address,
#     #         str(FieldsNames.curr_plan): self.current_plan,
#     #         str(FieldsNames.curr_plan_param): self.current_plan_param,
#     #         str(FieldsNames.curr_time): self.current_time,
#     #         str(FieldsNames.curr_alarms): self.current_alarms,
#     #         str(FieldsNames.num_streams): len(self.all_xp_data),
#     #         str(FieldsNames.streams_data): [self._get_xp_data_as_dict(xp_data) for xp_data in self.all_xp_data]
#     #     }
#     #     return self.data_for_response
#
#     def _get_properties(self) -> list[tuple[str, Any]]:
#         return [
#             (str(FieldsNames.curr_address), self.address),
#             (str(FieldsNames.curr_plan), self.current_plan),
#             (str(FieldsNames.curr_plan_param), self.current_plan_param),
#             (str(FieldsNames.curr_time), self.current_time),
#             (str(FieldsNames.curr_alarms), self.current_alarms),
#             (str(FieldsNames.num_streams), len(self.all_xp_data)),
#             (str(FieldsNames.streams_data), [self._get_xp_data_as_dict(xp_data) for xp_data in self.all_xp_data])
#         ]


input_data: TypeAlias = tuple[str, str, str, str, str, str]


class InputsPageParser(Parsers):

    INDEX    = 0
    NUMBER   = 1
    NAME     = 2
    STATE    = 3
    TIME     = 4
    ACTUATOR = 5

    pattern_input_data = ':D;'

    def __init__(self):
        super().__init__()
        self._page_data: InputsPageData = InputsPageData()

    def _extract_data_from_line(self, line: str):
        return line.split(';')[1:]

    def parse(self, content: str):
        """
        Парсит данные с основной web страницы ДК Peek, присваивая их соответствующим атрибутам.
        :param get_parsed_data_as_dict: Параметр является опцией.
                                        При True -> формирует атрибут self.parsed_content_as_dict.
        :return: None.
        """
        content_as_list = content.splitlines()
        for line in content_as_list:
            if self.pattern_input_data in line:
                index, num, name, state, _time, actuator = self._extract_data_from_line(line)
                # self.parsed_content_as_dict[name] = (index, num, name, state, _time, actuator)
                self._page_data.inputs[name] = (index, num, name, state, _time, actuator)
        # print(f'inputs_self.build_data_for_response(): {self.build_attr_data_for_response()}')
        return self._page_data.as_dict
        # return self.build_attr_data_for_response(
        #     [(str(FieldsNames.inputs), self.parsed_content_as_dict)]
        # )


class PeekWebPagesParser:
    def __init__(self):
        self._main_page_parser = MainPageParser()
        self._inputs_page_parser = InputsPageParser()

    @cached_property
    def main_page_parser(self):
        return self._main_page_parser

    @cached_property
    def inputs_page_parser(self):
        return self._inputs_page_parser


class SetInputsPageParser(Parsers):

    def parse(self, content):
        return content


if __name__ == '__main__':
    s = ':TITLE;##MENU_001a##\n:SUBTITLE;Moscow: Панфиловс пр / Андреевка\n:TFT_NAVBAR;10\n:REFRESH_LOCK;1\n\n:BEGINTABLE\n:W;;200px;\n\n:D;;##T_PLAN##;005 -             \n\n:D;;##T_TIMINGSET##;005\n\n:D;;##T_TIME##;2025-03-01 16:08:41\n:D;;##T_ALARMS##;ISWC\n\n\n:ENDTABLE\n\n<b>##T_STREAM## 1</b>\n:BEGINTABLE\n:W;;200px;\n:D;;##T_STATE##;УПРАВЛЕНИЕ\n:D;;##T_CYCLE##;0 (0)\n:D;;##T_MODE## (##T_STAGE##);FT (3)\n:ENDTABLE\n\n<b>##T_STREAM## 2</b>\n:BEGINTABLE\n:W;;200px;\n:D;;##T_STATE##;УПРАВЛЕНИЕ\n:D;;##T_CYCLE##;0 (0)\n:D;;##T_MODE## (##T_STAGE##);FT (6)\n:ENDTABLE\n\n\n\n\n\n\n\n\n\n\n\n:BEGIN_TFT_ONLY\n<div id="nav_home">\n<br /><br />\n<ul>\n<li><button type=button OnClick=\'top.doDataHref("cell1370.hvi",1)\'>##CELL_1370##</button></li>\n<li><button type=button OnClick=\'top.doDataHref("cell1240.hvi",1)\'>##CELL_1240##</button></li>\n<li><button type=button OnClick=\'top.doHref("detswico.hvi",1)\'>##T_DETSWICO##</button></li>\n</ul>\n</div>\n:END_TFT_ONLY\n'

    start_time = time.perf_counter()
    p = PeekWebPagesParser()



    # print(o)
    print(json.dumps(p.main_page_parser.parse(s), indent=4, ensure_ascii=False))

    print(f'Время составило: {time.perf_counter() - start_time:.8f}')

