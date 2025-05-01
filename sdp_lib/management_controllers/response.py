from typing import Any

from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.structures import HostResponseStructure


class Responses:

    def __init__(self, protocol: str):
        self._protocol = protocol
        self._errors = []
        self._data_response = {}
        self._raw_response = tuple()
        self._response: list = [self._errors, self._data_response, self._raw_response]

    @property
    def protocol(self) -> str:
        return self._protocol

    @property
    def full(self) -> list[Any]:
        return self._response

    @property
    def errors(self) -> list:
        return self._response[HostResponseStructure.ERRORS]

    @property
    def data(self) -> dict:
        return self._response[HostResponseStructure.DATA_RESPONSE]

    def build_as_dict(self, ip_v4: str):
        """
        Формирует словарь их self.response.
        После запроса, self.response принимает кортеж из 2 элементов:
        i[0] -> Строка с сообщением об ошибке, если в процессе запроса было возбуждено исключение, иначе None
        i[1] -> Словарь с распарсенными данными из ответа.
        :return: Словарь вида:
                 Если self.response[0] -> None(Нет ошибки):
                     "response": {
                          "protocol": "snmp",
                          "ip_address": "10.179.122.113",
                          "error": None,
                          "fixed_time_status": "0",
                          "plan_source": "7",
                          "current_status": "3_light",
                          "current_stage": 1,
                          "current_plan": "2",
                          "num_detectors": "5",
                          "status_soft_flag180_181": "00",
                          "current_mode": "VA"
                     }
                 Если self.response[0] -> "No SNMP response received before timeout"(Есть ошибка):
                     "response": {
                          "protocol": "snmp",
                          "ip_address": "10.45.154.16",
                          "error": "No SNMP response received before timeout"
                     }

        """
        return {
            str(FieldsNames.protocol): self._protocol,
            str(FieldsNames.ipv4_address): ip_v4,
            str(FieldsNames.errors): [str(e) for e in self._errors],
            str(FieldsNames.data): self._data_response
        }

    def add_data_to_attrs(
            self,
            error: Exception | str = None,
            data: dict[str, Any] = None
    ):
        if isinstance(data, dict):
            self._data_response |= data
        if isinstance(error, (Exception, str)):
            self._errors.append(error)

    def remove_data_from_data_response(self):
        self._data_response = {}

    def remove_errors_from_errors(self):
        self._errors = []