from abc import abstractmethod
from typing import Self, Any

from sdp_lib.data_capture.events import Event


class AbstractProducer:
    def __init__(self, host, event: Event, name):
        self._host = host
        self._event = event
        self._name = name
        self.response = None

    def get_name(self):
        return self._name

    def get_event(self) -> Event:
        return self._event

    @abstractmethod
    async def request_and_process(self) -> tuple[str, Any]:
        """ Реализация метода получения данных и их обработки. """

    def event_process(self):
        self._event.process(*self.response)


class StageProducer(AbstractProducer):

    async def request_and_process(self) -> Self:
        await self._host.get_current_stage()
        err = self._host.response_errors
        try:
            num_stage = int(self._host.current_stage)
        except (TypeError, ValueError):
            err, num_stage = 'Ошибка получения фазы c хоста', None
        self.response = err, num_stage
        return self


