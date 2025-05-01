import abc
import json
import math
import os.path
import pathlib
import time
from enum import Enum
from pathlib import Path
from typing import Dict, Set, Tuple, List, Iterator, TextIO
import logging

from toolkit.sdp_lib.utils_common import set_curr_datetime

logger = logging.getLogger(__name__)

class DataFields(Enum):
    sorted_stages_data = 'sorted_stages_data'
    number_of_groups = 'number_of_groups'
    number_of_stages = 'number_of_stages'
    all_num_groups = 'all_num_groups'
    sorted_all_num_groups = 'sorted_all_num_groups'
    errors = 'errors'
    allow_make_config = 'allow_make_config'
    always_red_groups = 'always_red_groups'
    always_red = 'always_red'
    always_green = 'always_green'
    conflicts = 'conflicts'
    enemy_groups = 'enemy_groups'
    stages = 'stages'
    groups_property = 'groups_property'
    type_controller = 'type_controller'
    conflict_K = '| K|'
    no_conflict_O = '| O|'
    cross_group_star_matrix = '| *|'
    output_matrix = 'base_matrix'
    conflictF997 = '03.0;'
    no_conflictF997 = '  . ;'
    cross_group997 = 'X;'
    matrix_F997 = 'matrix_F997'
    numbers_conflicts_groups = 'numbers_conflicts_groups'
    stages_bin_vals = 'stages_bin_vals'
    stages_bin_vals_f009 = 'stages_bin_vals_f009'
    sum_conflicts = 'sum_conflicts'
    txt_file = 'txt_file'
    config_file = 'config_file'
    path_to_file = 'path_to_file'
    created = 'created'
    swarco = 'Swarco'
    peek = 'Peek'


class Utils:

    @classmethod
    def unpack_matrix(cls, matrix: List[List]) -> str:
        return '\n'.join((''.join(m) for m in matrix)) + '\n'

    @classmethod
    def set_to_list(cls, target: Dict):
        """
        Рекурсивно превращает множества set в список list значения словаря target.
        :param target: Словарь, в котором значения set необходимо заменить на list
        :return:
        """

        for k, v in target.items():
            if isinstance(v, dict):
                cls.set_to_list(v)
            elif isinstance(v, set):
                target[k] = sorted(v)

    @classmethod
    def save_json_to_file(cls, json_data, file_name='conflicts.json', mode: str = 'w') -> None:
        """
        Формирует json и записывает в файл
        :param json_data: словарь, который будет записан как json
        :param file_name: путь к файлу
        :param mode: режим записи в файл
        :return:
        """

        cls.set_to_list(json_data)

        with open(file_name, mode, encoding='utf-8') as f:
            json.dump(json_data, f, ensure_ascii=False, indent=4)
            f.write('\n\n')

    @classmethod
    def stages_to_dict(cls, stages_groups: str) -> Dict:
        return {str(i): groups for i, groups in enumerate(stages_groups.split('\n'), 1)}


class BaseConflictsAndStagesCalculations:

    def __init__(self, stages_groups_data: Dict):

        self.instance_data = {
            'raw_stages_data': stages_groups_data,
            DataFields.sorted_stages_data.value: None,
            DataFields.type_controller.value: None,
            DataFields.number_of_groups.value: None,
            DataFields.number_of_stages.value: None,
            DataFields.all_num_groups.value: set(),
            DataFields.always_red_groups.value: None,
            DataFields.groups_property.value: {},
            DataFields.sorted_all_num_groups.value: None,
            DataFields.allow_make_config.value: True,
            DataFields.errors.value: [],
            DataFields.output_matrix.value: None,
            DataFields.matrix_F997.value: None,
            DataFields.numbers_conflicts_groups.value: None,
            DataFields.stages_bin_vals.value: None,
            DataFields.sum_conflicts.value: None
        }

    def _get_all_data_curr_calculate(self):
        return json.dumps(self.instance_data, indent=4)

    def processing_data_for_calculation(self, separator: str = ','):
        """
        Формирует данные для расчёта конфликтов. Определяет возможность формирования конфига .PTC2 или .DAT
        по следующему правилу: если все группы представляют собой однозначные целые числа int, то
        allow_make_config == True. Если присутствуют группы типа 5.1, 5.2(определяю как float), то
        allow_make_config ==False.
        :param separator: разделитель для формирования списка направлений
        :return:
        """

        processed_stages = {}
        stage = None
        unsorted_num_groups = self.instance_data[DataFields.all_num_groups.value]
        try:
            for stage, groups in self.instance_data['raw_stages_data'].items():
                unsorted_stages = {int(g) if g.isdigit() else float(g) for g in groups.split(separator) if g}
                processed_stages[stage] = unsorted_stages
                unsorted_num_groups |= unsorted_stages
        except ValueError as err:
            self.instance_data[DataFields.errors.value].append(
                f'Некорректный номер направления у фазы '
                f'{stage}: {str(err).split(":")[-1].replace(" ", "")}, должен быть числом'
            )

        unsorted_all_num_groups, always_red_groups = self._get_always_red_and_all_unsorted_groups(unsorted_num_groups)
        if not self._check_data_for_calculate_is_valid(len(unsorted_all_num_groups), len(processed_stages.keys())):
            return

        self._add_data_to_instance_data_dict_for_calc_conflicts(
            processed_stages, unsorted_all_num_groups, always_red_groups
        )

    def _check_data_for_calculate_is_valid(self, num_groups: int, num_stages: int):
        """
        Проверяет валидное количество направлений и фаз. Если передано недопустимое количество фаз
        и направлений, добавляет сообщение об ошибке в self.instance_data[DataFields.number_of_stages.value] и
        возвращает Falsе, иначе возвращает True
        :param num_groups: Количество группю
        :param num_stages: Количество фаз
        :return: True, если количество направлений и фаз допустимо, иначе False.
        """

        self.instance_data[DataFields.number_of_groups.value] = num_groups
        self.instance_data[DataFields.number_of_stages.value] = num_stages
        if num_groups > 48:
            self.instance_data[DataFields.errors.value].append(
                f'Превышено максимально допустимое количество(48) групп: {num_groups}.'
            )
        if num_stages > 128:
            self.instance_data[DataFields.errors.value].append(
                f'Превышено максимально допустимое количество(128) фаз: {num_stages}.'
            )
        return not bool(self.instance_data[DataFields.errors.value])

    def _get_always_red_and_all_unsorted_groups(self, unsorted_all_num_groups: Set) -> Tuple[Set, Set]:
        """
        Определяет для общее количество групп в виде set и группы, являющиеся "постоянно красными" в вид set
        :param unsorted_all_num_groups: set из групп, которые учатсвуют хотя бы в одной фазе.
        :return: Кортеж из set. unsorted_all_num_groups -> все номера групп, always_red_groups -> set
                 из групп, которые являются "Пост. красн."
        """

        always_red_groups = set()
        sorted_groups = sorted(unsorted_all_num_groups)

        for i, group in enumerate(sorted_groups):
            curr_group, prev_group = math.trunc(group), math.trunc(sorted_groups[i - 1])
            if i > 0 and (curr_group - prev_group) in range(2, 20):
                missed_groups = {(prev_group + i) for i in range(1, (curr_group - prev_group))}
                unsorted_all_num_groups |= missed_groups
                always_red_groups |= missed_groups
        return unsorted_all_num_groups, always_red_groups

    def _add_data_to_instance_data_dict_for_calc_conflicts(
            self, processed_stages: Dict, unsorted_all_num_groups: Set, all_red_groups: Set
    ):
        """
        Добавляет элементы словаря(ключ: значение) для self.instance_data
        :param all_red_groups: set из групп, которые не участвуют ни в одной фазе.
        :param processed_stages:
        :param unsorted_all_num_groups:
        :return:
        """
        self.instance_data[DataFields.sorted_stages_data.value] = processed_stages
        self.instance_data[DataFields.all_num_groups.value] = unsorted_all_num_groups
        self.instance_data[DataFields.always_red_groups.value] = all_red_groups
        self.instance_data[DataFields.allow_make_config.value] = self._make_config_allowed(processed_stages)
        self.instance_data[DataFields.sorted_all_num_groups.value] = sorted(unsorted_all_num_groups)

    def _make_config_allowed(self, processed_stages: Dict[str, Set]):
        """
        Проверят доступность создания конфигурационного файла .PTC2/.DAT
        Если одно из направлений или одна из фаз не является целым числом, возвращает False, иначе True.
        :param processed_stages: Словарь вида {фаза: направления}, например:
                                 "1": {1, 2, 4, 5}, "2": {4, 5, 6}, "3": {6, 7, 8}
        :return: True если все направления и фазы представлены в виде целым числом, иначе False
        """

        for stage, groups_in_stage in processed_stages.items():
            if not stage.isdigit() or not all(isinstance(g, int) for g in groups_in_stage):
                return False
        return True

    def calculate_conflicts_and_stages(self) -> None:
        """
        Формирует словарь для всех групп с данными о группе: конфликтами и фазами, в которых участвует направеление
        :return: None
        """

        groups_prop = self.instance_data[DataFields.groups_property.value]
        for group in self.instance_data.get(DataFields.sorted_all_num_groups.value):
            groups_prop[group] = self._get_conflicts_and_stages_properties_for_group(group)

    def _get_conflicts_and_stages_properties_for_group(self, num_group: int):
        """
        Формирует конфликты для группы.
        :param num_group: Номер группы, для котороый будут сформированы конфликты в виде set
        :return: Словарь data для num_group вида:
                 {
                  'stages': {фазы(в которых участвует num_group) типа str},
                  'enemy_groups': {группы, с которыми есть конфликт у группы num_group типа str}
                 }
                Пример data: {'stages': {'1', '2'}, 'enemy_groups': {'4', '5', '6'}}
        """

        group_in_stages = set()
        conflict_groups = {g for g in self.instance_data[DataFields.all_num_groups.value] if g != num_group}
        for stage, groups_in_stage in self.instance_data[DataFields.sorted_stages_data.value].items():
            if num_group in groups_in_stage:
                group_in_stages.add(stage)
                for g in groups_in_stage:
                    conflict_groups.discard(g)
        assert conflict_groups == self._supervisor_conflicts(num_group)
        is_always_red: bool = False if group_in_stages else True
        is_always_green: bool = group_in_stages == set(self.instance_data[DataFields.sorted_stages_data.value].keys())
        assert not ((is_always_red is True) and (is_always_green is True))
        data = {
            DataFields.stages.value: group_in_stages,
            DataFields.enemy_groups.value: conflict_groups,
            DataFields.always_red.value: is_always_red,
            DataFields.always_green.value: is_always_green
        }
        return data

    def _supervisor_conflicts(self, num_group: int) -> Set:
        """
        Метод формирует set из групп, с которыми есть конфликт у группы num_group. Является проверкой
        корректности формирования конфликтных групп метода self.get_conflicts_and_stages_for_group.
        Алгоритм формирования set из конфликтных групп:
        В цикле перебираем все группы из self.instance_data[DataFields.sorted_all_num_groups.value] и
        смотрим, если num_group и очередная перебираемая группа не присутсвуют вместе ни в одной фазе, то
        добавляем очередную перебираемую группу(g) в множество enemy_groups.
        :param num_group: Номер группы, для которой будет сформировано set конфликтных групп
        :return: set из конфликтных групп для группы num_group
        """

        enemy_groups = set()
        for group in (g for g in self.instance_data[DataFields.sorted_all_num_groups.value] if g != num_group):
            for groups_in_stage in self.instance_data[DataFields.sorted_stages_data.value].values():
                if {num_group, group}.issubset(groups_in_stage):
                    break
            else:
                enemy_groups.add(group)
        return enemy_groups


class OutputDataCalculations(BaseConflictsAndStagesCalculations):

    def __repr__(self):
        return (f'output_matrix:\n{self._unpack_matrix(self.instance_data[DataFields.output_matrix.value])}'
                f'f997: \n{self._unpack_matrix(self.instance_data[DataFields.matrix_F997.value])}\n'
                f'f994: \n{self.instance_data[DataFields.numbers_conflicts_groups.value]}\n'
                f'stages_bin_vals: {self.instance_data[DataFields.stages_bin_vals.value]}\n'
                f'sum_conflicts: {self.instance_data[DataFields.sum_conflicts.value]}')

    def _unpack_matrix(self, matrix: List[List]) -> str:
        return '\n'.join((''.join(m) for m in matrix)) + '\n'

    def _create_row_output_matrix(
            self, all_numbers_groups: List, current_group: int = None, enemy_groups: Set = None, first_row=False
    ) -> List[str]:
        """
        Формирует строку для матрицы в виде списка.
        :param all_numbers_groups: Номер всех групп в запросе.
        :param current_group: Номер группы, для которой будет сформирован список.
        :param enemy_groups: Коллекция set из конфликтных групп для current_group.
        :param first_row: Является ли строка первой строкой матрицы("шапка")
        :return: Список-строка для матрицы конфликтов группы current_group, если first_row == False,
                 иначе список-шапка матрицы
        """

        if not first_row:
            row = [f'|0{current_group}|' if len(str(current_group)) == 1 else f'|{current_group}|']
            row += [
                DataFields.no_conflict_O.value if gr not in enemy_groups else DataFields.conflict_K.value
                for gr in all_numbers_groups
            ]
            row[len(self.instance_data[DataFields.output_matrix.value])] = DataFields.cross_group_star_matrix.value
        else:
            row = [DataFields.cross_group_star_matrix.value]
            row += [f'|0{g}|' if len(str(g)) == 1 else f'|{g}|' for g in all_numbers_groups]
        print(f'row: {row}')
        return row

    def _create_row_f997(self, num_groups, current_group: int, enemy_groups: Set[int]) -> List[str]:
        """
        Формирует строку матрицы для F997 конфигурации Swarco.
        :param num_groups: Количетсво групп в запросе.
        :param current_group: Номер группы, для которой будет сформирован список.
        :param enemy_groups: Коллекция set из конфликтных групп для current_group.
        :return: Список-строка для матрицы конфликтов группы current_group
        """

        row = [
            DataFields.cross_group997.value if i + 1 == current_group else
            DataFields.conflictF997.value if i + 1 in enemy_groups else DataFields.no_conflictF997.value
            for i in range(num_groups)
        ]
        return row

    def _get_bin_val_stages(self, stages: Set[int]) -> int:
        """
        Формирует бинарное значение всех фаз из коллекции.
        :param stages: set с фазами, бинарное значение которых необходимо вычислить.
        :return: Бинарное значение, представленное в виде целого натурального числа.
        """

        return sum(map(lambda x: 2 ** x if x != 8 else 2 ** 0, (int(s) for s in stages)))

    def _get_bin_vals_stages_for_swarco_f009(self, bin_vals: list[int] = None) -> str | None:
        """
        Получает строку привязки направлений к фазам бинарных значений.
        :return: строка привязки напрвлий к фазе. Пример:
                 '006;002;014;018;018;020;004;008;008;008;000;000;008;'
        """
        bin_vals = bin_vals or self.instance_data[DataFields.stages_bin_vals.value]
        if bin_vals is None:
            return
        # Добавить нули перед значением. Значение всегда состоит из 3 символов.
        # Например: если бинарное значение фазы "2", то добавляем два нуля, чтобы получилось "002"
        # если бинарное значение фазы "16", то добавляем один ноль, чтобы получилось "016" и т.д
        # Пример возвращаемой строки для десяти групп: "002;002;002;004;004;000;004;000;016;016", где каждое
        # значение соответсвует номеру группы(начало отсчёта с 1 группы)
        return "".join((f'{"0" * 1 * (3 - len(str(val)))}{val};' for val in bin_vals))

    def create_data_for_output(self):

        num_groups = self.instance_data[DataFields.number_of_groups.value]
        groups_property = self.instance_data[DataFields.groups_property.value]
        all_numbers_groups = sorted(self.instance_data[DataFields.all_num_groups.value])
        create_bin_vals_stages = self.instance_data[DataFields.allow_make_config.value]

        self.instance_data[DataFields.output_matrix.value] = [
            self._create_row_output_matrix(all_numbers_groups, first_row=True)
        ]
        f997, numbers_conflicts_groups, stages_bin_vals = [], [], []
        sum_conflicts = 0

        for num_group, property_group in groups_property.items():
            enemy_groups = property_group[DataFields.enemy_groups.value]
            self.instance_data[DataFields.output_matrix.value].append(
                self._create_row_output_matrix(all_numbers_groups, num_group, enemy_groups)
            )
            if self.instance_data[DataFields.allow_make_config.value]:
                f997.append(self._create_row_f997(num_groups, num_group, enemy_groups))
                numbers_conflicts_groups.append(f"{';'.join(map(str, sorted(enemy_groups)))};")
            sum_conflicts += len(enemy_groups)
            if create_bin_vals_stages:
                stages_bin_vals.append(self._get_bin_val_stages(stages=property_group[DataFields.stages.value]))

        self.instance_data[DataFields.matrix_F997.value] = f997
        self.instance_data[DataFields.numbers_conflicts_groups.value] = numbers_conflicts_groups
        self.instance_data[DataFields.stages_bin_vals.value] = stages_bin_vals
        self.instance_data[DataFields.stages_bin_vals_f009.value] = self._get_bin_vals_stages_for_swarco_f009()
        self.instance_data[DataFields.sum_conflicts.value] = sum_conflicts

    # def create_data_for_output(self):
    #
    #     num_groups = self.instance_data[DataFields.number_of_groups.value]
    #     groups_property = self.instance_data[DataFields.groups_property.value]
    #     all_numbers_groups = sorted(self.instance_data[DataFields.all_num_groups.value])
    #     create_bin_vals_stages = self.instance_data[DataFields.allow_make_config.value]
    #
    #     output_matrix = [self._create_row_output_matrix(all_numbers_groups, first_row=True)]
    #     f997, numbers_conflicts_groups, stages_bin_vals = [], [], []
    #     sum_conflicts = 0
    #
    #     for num_group, property_group in groups_property.items():
    #         enemy_groups = property_group[DataFields.enemy_groups.value]
    #         output_matrix.append(self._create_row_output_matrix(all_numbers_groups, num_group, enemy_groups))
    #         f997.append(self._create_row_f997(num_groups, num_group, enemy_groups))
    #         numbers_conflicts_groups.append(f"{';'.join(map(str, sorted(enemy_groups)))};")
    #         sum_conflicts += len(enemy_groups)
    #         if create_bin_vals_stages:
    #             stages_bin_vals.append(self._get_bin_val_stages(stages=property_group[DataFields.stages.value]))
    #
    #     self.instance_data[DataFields.output_matrix.value] = output_matrix
    #     self.instance_data[DataFields.matrix_F997.value] = f997
    #     self.instance_data[DataFields.numbers_conflicts_groups.value] = numbers_conflicts_groups
    #     self.instance_data[DataFields.stages_bin_vals.value] = stages_bin_vals
    #     self.instance_data[DataFields.stages_bin_vals_f009.value] = self._get_bin_vals_stages_for_swarco_f009()
    #     self.instance_data[DataFields.sum_conflicts.value] = sum_conflicts


class CommonConflictsAndStagesAPI(OutputDataCalculations):
    """
    API для получения свойств и данных после различных расчетов, таких как конфликты, направления в фазах, матрицы
    и т.д, а также формирования текстового файла с учётом рассчитанных даных
    """
    controller_type = 'Общий'

    def __init__(self, stages_groups_data: Dict, create_txt: bool = False, path_to_save_txt: str = None):
        super().__init__(stages_groups_data)
        self.instance_data[DataFields.type_controller.value] = self.get_controller_type()
        self.create_txt = create_txt
        self.path_to_save_txt = path_to_save_txt

    @classmethod
    def get_controller_type(cls) -> str:
        return cls.controller_type

    def _get_bin_vals_stages_for_write_to_txt(self) -> str:
        """
        Получает строку привязки направлений к фазам бинарных значений.
        :return: строка привязки напрвлий к фазе. Пример:
                 '006;002;014;018;018;020;004;008;008;008;000;000;008;'
        """
        data = ''
        for val in self.instance_data[DataFields.stages_bin_vals.value]:
            zeros = f'{"0" * 1 * (3 - len(str(val)))}'
            data += f'{zeros}{val};'
        return data

    def _get_binding_stage_groups(self) -> str:
        """
        Получает строку привязки направлений к фазам.
        :return: строка привязки напрвлий к фазе. Пример:
                 'Фаза 1: 1,2,3,4,5\nФаза 2: 1,3,6,7\nФаза 3: 3,8,9,10,13\nФаза 4: 4,5,6\n'
        """

        data = ''
        for stage, groups_in_stage in self.instance_data[DataFields.sorted_stages_data.value].items():
            data += f'Фаза {stage}: {",".join(map(str, groups_in_stage))}\n'
        return data

    def create_txt_file(self):
        """
        Создает текстовый файл с различными расчётами: фазы, направления, матрицы конфликтов и т.д.
        :return:
        """

        self.path_to_save_txt = self.path_to_save_txt or f"calculated_data {set_curr_datetime('-')}.txt"

        with open(self.path_to_save_txt, 'w') as f:
            logger.debug(self.instance_data[DataFields.sorted_stages_data.value])
            write_data = ''
            write_data += self._get_binding_stage_groups()
            write_data += (
                f'Количество направлений: {self.instance_data[DataFields.number_of_groups.value]}\n\n'
                f'Матрица конфликтов общая:\n'
                f'{self._unpack_matrix(self.instance_data[DataFields.output_matrix.value])}\n'
                f'Матрица конфликтов F997 Swarco:\n'
                f'{self._unpack_matrix(self.instance_data[DataFields.matrix_F997.value])}\n'
                f'Конфликтные направления F994 Swarco:\n'
                f'{self._unpack_matrix(self.instance_data[DataFields.numbers_conflicts_groups.value])}\n'
                f'Бинарные значения фаз F009 Swarco:\n'
            )
            write_data += self._get_bin_vals_stages_for_write_to_txt()
            f.write(write_data)

        try:
            os.path.exists(self.path_to_save_txt)
            err = None
        except FileExistsError:
            err = f'Ошибка при создании файла с расчитанными данными'

        self.instance_data[DataFields.txt_file.value] = {
            DataFields.errors.value: err,
            DataFields.path_to_file.value: None if err else str(Path(self.path_to_save_txt).absolute()),
            DataFields.created.value: True if err is None else False
        }

    def build_data(self, create_json=False):
        """
        Основной метод для получения данных по расчетам конфликтов, привзяки фаз и прочих значений.
        :param create_json: формирует файл .json с данными, полученными в результате расчетов(self.instance_data)
        :return:
        """

        functions: tuple = (
            self.processing_data_for_calculation, self.calculate_conflicts_and_stages, self.create_data_for_output
        )
        for func in functions:
            if self.instance_data[DataFields.errors.value]:
                break
            func()
        if create_json:
            Utils.save_json_to_file(self.instance_data)
        else:
            Utils.set_to_list(self.instance_data)
        if self.create_txt:
            self.create_txt_file()


class CreateConfigurationFileBase(CommonConflictsAndStagesAPI):
    """
    Базовый класс для формирования конфигурационных файлов различных контроллеров.
    """

    def __init__(
            self, stages_groups_data: Dict,
            create_txt: bool = False,
            path_to_save_txt: str = None,
            path_to_src_config: str = None,
            prefix_new_config: str = 'new_'
    ):
        super().__init__(stages_groups_data, create_txt, path_to_save_txt)
        self.path_to_src_config = path_to_src_config
        self.prefix_new_config = prefix_new_config

    @abc.abstractmethod
    def create_config(self):
        ...

    def build_data(self, create_json=False):
        """
        Основной метод для получения данных по расчетам конфликтов, привзяки фаз и прочих значений.
        :param create_json: формирует файл .json с данными, полученными в результате расчетов(self.instance_data)
        :return:
        """

        super().build_data(create_json)
        if self.path_to_src_config is not None:
            self.create_config()
        Utils.save_json_to_file(self.instance_data)

    def push_result_to_instance_data(self, path_to_config: str | Path):
        """
        Проверяет результат формирования конфига и добавляет результат в self.instance_data.
        :param path_to_config: Пусть к созданному конфигу
        :return:
        """

        try:
            os.path.exists(path_to_config)
            err = None
        except FileExistsError:
            err = f'Ошибка при создании файла с расчитанными данными'

        self.instance_data[DataFields.config_file.value] = {
            DataFields.errors.value: err,
            DataFields.path_to_file.value: None if err else str(Path(path_to_config).absolute()),
            DataFields.created.value: True if err is None else False
        }


class SwarcoConflictsAndStagesAPI(CreateConfigurationFileBase):
    """
    API для получения свойств и данных после различных расчетов, таких как конфликты, направления в фазах, матрицы
    и т.д, а также формирования конфигурационного файла .PTC с учётом рассчитанных даных для контроллера Swarco.
    """

    controller_type = 'Swarco'

    def write_data_to_file(
            self,
            file_for_write: TextIO,
            file_for_read: Iterator,
            curr_line_from_file_for_write: str,
            matrix=None,
            stages_bin_vals=None
    ):
        """
        Записывает данные в файл конфигурации .PTC2
        :param file_for_write: Файл, в который будут записаны данные
        :param file_for_read: Файл, из которого читаются данные
        :param curr_line_from_file_for_write: текущая прочитанная строка из file_for_read
        :param matrix: матрица в виде двумерного списка. Если не None, будет записана в файл для F994, F997, F006
        :param stages_bin_vals: список с бинарныт значениями  принадлжености направлений в фазам дл F009
        :return:
        """

        file_for_write.write(f'{curr_line_from_file_for_write}')
        if matrix is not None:
            for matrix_line in matrix:
                file_for_write.write(f'{"".join(matrix_line)}\n')
        elif stages_bin_vals is not None:
            for val in stages_bin_vals:
                zeros = f'{"0" * 1 * (3 - len(str(val)))}'
                file_for_write.write(f';{zeros}{val};;1;\n')
        while 'NeXt' not in curr_line_from_file_for_write:
            curr_line_from_file_for_write = next(file_for_read)
        file_for_write.write(curr_line_from_file_for_write)

    def create_config(self):
        """
        Создает .PTC2 файл конфигурации с учетов произведённых расчетов конфликтов и бинарных значений фаз.
        Алгоритм:
                 исходный файл конфига .PTC2 читается построчно. Каждая прочитанная строчка записывается в
                 новый файл, кроме строк, принадлежащих функциям F994, F997, F006, F009. Строки для
                 этих функций будут взяты из self.instance_data
        :return:
        """

        p = pathlib.Path(self.path_to_src_config)
        path_to_new_PTC2 = p.parent / f'{self.prefix_new_config}{p.name}'
        conflicts_f997 = 'NewSheet693  : Work.997'
        conflicts_f992 = 'NewSheet693  : Work.992'
        conflicts_f006 = 'NewSheet693  : Work.006'
        stage_bin_vals_f009 = 'NewSheet693  : Work.009'

        with open(self.path_to_src_config) as src, open(path_to_new_PTC2, 'w') as new_file:
            for line in src:
                if conflicts_f997 in line or conflicts_f992 in line:
                    self.write_data_to_file(
                        file_for_write=new_file,
                        file_for_read=src,
                        curr_line_from_file_for_write=line,
                        matrix=self.instance_data[DataFields.matrix_F997.value]
                    )
                elif conflicts_f006 in line:
                    self.write_data_to_file(
                        file_for_write=new_file,
                        file_for_read=src,
                        curr_line_from_file_for_write=line
                    )
                elif stage_bin_vals_f009 in line:
                    self.write_data_to_file(
                        file_for_write=new_file,
                        file_for_read=src,
                        curr_line_from_file_for_write=line,
                        stages_bin_vals=self.instance_data[DataFields.stages_bin_vals.value]
                    )
                else:
                    new_file.write(line)

        self.push_result_to_instance_data(path_to_new_PTC2)


class PeekConflictsAndStagesAPI(CreateConfigurationFileBase):
    """
    API для получения свойств и данных после различных расчетов, таких как конфликты, направления в фазах, матрицы
    и т.д, а также формирования конфигурационного файла .DAT с учётом рассчитанных даных для контроллера Peek.
    """

    controller_type = 'Peek'

    def get_conflicts_for_write(self) -> str:
        """
        Формирует строку :TABLE "XSGSG" для записи в новый DAT файл.
        :return: строка :TABLE "XSGSG" для записи в новый DAT файл.
        """

        table_conflicts = f':TABLE "XSGSG",{str(self.instance_data[DataFields.sum_conflicts.value])},4,3,4,4,3\n'
        for group, properties in self.instance_data[DataFields.groups_property.value].items():
            for enemy_group in properties[DataFields.enemy_groups.value]:
                table_conflicts += (
                    f':RECORD\n'
                    f'"Type",2\n'
                    f'"Id1",{group}\n'
                    f'"Id2",{str(enemy_group)}\n'
                    f'"Time",30\n'
                    f':END\n'
                )
        return f'{table_conflicts}:END\n'

    def get_ysrm_sa_stage_and_ysrm_uk_stage(self) -> Tuple[str, str]:
        """
        Аккумулирует строки таблиц :TABLE "YSRM_SA_STG" и :TABLE "YSRM_UK_STAGE" для записи в новый DAT файл.
        :return: Кортеж из двух строк ysrm_sa_stage и ysrm_uk_stage для записи в новый DAT файл.
        """

        sum_stages = str(self.instance_data[DataFields.number_of_stages.value])
        ysrm_sa_stage = f':TABLE "YSRM_SA_STG",{sum_stages},2,4,10\n'
        ysrm_uk_stage = f':TABLE "YSRM_UK_STAGE",{sum_stages},4,4,4,1,10\n'

        for stage, groups_in_stage in self.instance_data[DataFields.sorted_stages_data.value].items():
            groups_in_stage = f"{','.join(map(str, groups_in_stage))}"
            ysrm_sa_stage += (
                f':RECORD\n'
                f'"Id",{stage}\n'
                f'"SGdef","{groups_in_stage}"\n'
                f':END\n'
            )
            ysrm_uk_stage += (
                f':RECORD\n'
                f'"ProcessId",1\n'
                f'"StageId",{stage}\n'
                f'"StartUpStage",{str(True) if stage == "1" else str(False)}\n'
                f'"SignalGroups",",{groups_in_stage},"\n'
                f':END\n'
            )
        return f'{ysrm_sa_stage}:END\n', f'{ysrm_uk_stage}:END\n'

    def skipping_lines(self, file: Iterator, stopper: str) -> str:
        """
        Итерируется по строкам исходного DAT файла, которые не требуется записывать в новый файл DAT.
        :param file: Исходный DAT файл.
        :param stopper: Строка-стоппер, до которой будет вызываться next()
        :return: Строка-стоппер
        """

        line = ''
        while stopper not in line:
            line = next(file)
        return line

    def create_config(self):
        """
        Формирует новый DAT файл конфигурации на основе расчётов.
        :return:
        """

        p = pathlib.Path(self.path_to_src_config)
        path_to_new_DAT = p.parent / f'{self.prefix_new_config}{p.name}'
        ysrm_sa_stage, ysrm_uk_stage = self.get_ysrm_sa_stage_and_ysrm_uk_stage()

        with (
            open(self.path_to_src_config, 'r', encoding='utf-8') as src,
            open(path_to_new_DAT, 'w', encoding='utf-8') as file2
        ):
            for line in src:
                if ':TABLE "XSGSG"' in line:
                    file2.write(self.get_conflicts_for_write())
                    file2.write(self.skipping_lines(src, ':TABLE "YKLOK"'))
                elif ':TABLE "YSRM_SA_STG"' in line:
                    file2.write(ysrm_sa_stage)
                    file2.write(self.skipping_lines(src, ':TABLE "YSRM_STEP"'))
                elif ':TABLE "YSRM_UK_STAGE"' in line:
                    file2.write(ysrm_uk_stage)
                    file2.write(self.skipping_lines(src, ':TABLE "YSRM_UK_STAGE_TRANS"'))
                else:
                    file2.write(line)

        self.push_result_to_instance_data(path_to_new_DAT)


if __name__ == '__main__':
    import logging_config

    # example = {
    #     '1': '1,4,2,3,5,5,5,5,3,4,2',
    #     '2': '',
    #     '3': '9,10,8,13,3,10,',
    #     '4': '5,6,4'
    # }
    example = {
        '1': '1,2,3',
        '2': '4,5,6',
        '3': '7,8,9',
        '4': '10'
    }
    start_time = time.time()
    obj = PeekConflictsAndStagesAPI(example, create_txt=True, path_to_src_config='CO3992.DAT')
    obj.build_data()
    print(obj)
    print(f'ВРемя выполеения составило: {time.time() - start_time}')
