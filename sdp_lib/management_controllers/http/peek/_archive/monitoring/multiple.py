import asyncio
from asyncio import Task
from typing import TypeVar, Coroutine

from sdp_lib.management_controllers.http.peek.monitoring.inputs import InputsPage
from sdp_lib.management_controllers.http.peek.monitoring.main_page import MainPage
from sdp_lib.management_controllers.http.peek.monitoring.monitoring_core import GetData
from sdp_lib.management_controllers.http.peek.peek_core import PeekWeb


T = TypeVar('T', bound=GetData, covariant=True)


class MultipleData(PeekWeb):
    """
    Класс запросов для получения данных различных веб страниц(маршрутов)
    одного контроллера.
    """

    async def get_and_parse(
            self,
            *,
            main_page=True,
            inputs_page=True
    ):
            tasks = self._get_tasks(main_page, inputs_page)
            async with asyncio.TaskGroup() as tg1:
                result = [tg1.create_task(_coro) for _coro in tasks]
            self.add_data_to_data_response_attrs(*self.merge_all_errors_and_responses(result))
            return self

    def _get_tasks(
            self,
            main_page: bool,
            inputs_page: bool
    ) -> list[Coroutine]:
        """
        Собирает список задач(корутин).
        :param main_page: Требуется ли задача с получением контента основной страницы.
        :param inputs_page: Требуется ли задача с получением контента ВВОДОВ.
        :return: Список с задачами(корутинами).
        """
        match [main_page, inputs_page]:
            case [True, True]:
                return [
                    MainPage(self._ipv4, self._driver).get_and_parse(),
                    InputsPage(self._ipv4, self._driver).get_and_parse()
                ]
            case [True, False]:
                return [MainPage(self._ipv4, self._driver).get_and_parse()]
            case [False, True]:
                return [InputsPage(self._ipv4, self._driver).get_and_parse()]
            case _:
                raise ValueError('Не предоставлено данных')

    def merge_all_errors_and_responses(self, results: list[Task]) -> tuple[None | str, dict]:
        """
        Объединяет словари с распарсенными данными контента веб страницы.
        :param results: Список с завершёнными задачами.
        :return:
        """
        error, response = None, {}
        for r in results:
            obj = r.result()
            curr_err, curr_res = obj.data
            response |= curr_res
            error = curr_err or error
        return error, response # Fix me