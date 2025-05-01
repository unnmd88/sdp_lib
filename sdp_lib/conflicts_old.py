import os
from datetime import datetime as dt


class Conflicts:

    available_controller_types = ['swarco', 'peek', 'undefind']

    allowed_max_stages_swarco = 8
    allowed_max_kolichestvo_napr_swarco = 48
    allowed_min_num_stages_without_controller_type = 2
    allowed_max_num_stages_without_controller_type = 100

    allowed_max_stages_peek = 32
    allowed_max_kolichestvo_napr_peek = 64
    allowed_max_num_kolichestvo_napr_without_controller_type = 100

    msg_no_data_input_stages = 'Ошибка: Некорректный тип данных'
    msg_less_than_2_stages_input_stages = 'Ошибка: Дано менее двух фаз'
    msg_more_than_100_stages_input_stages = 'Ошибка: Дано более ста фаз!'
    msg_data_input_stages_success = 'Успех: проверка входных данных успешно пройдена'
    msg_controller_type_is_not_selected = 'Ошибка: Тип контроллера не выбран'
    msg_more_than_8_stages_swarco = 'Ошибка: Для контрллера swarco выбрано более 8 фаз'
    msg_more_than_32_stages_peek = 'Ошибка: Для контрллера peek выбрано более 32 фаз'
    msg_max_num_stages_success = 'Успех: проверка допустимого количества фаз успешно пройдена'
    msg_more_than_48_groups_swarco = 'Ошибка: Для контрллера swarco выбрано более 48 направлений'
    msg_more_than_64_groups_peek = 'Ошибка: Для контрллера peek выбрано более 64 направлений'
    msg_max_num_groups_success = 'Успех: проверка допустимого количества фаз успешно пройдена'
    msg_more_than_100_groups_without_controller_type = 'Ошибка: Дано более ста фаз!'
    msg_invalid_input_data_type = 'Ошибка: Неверный тип данных предоставлен для расчёта конфликтов.' \
                                  'Тип должен быть str или list'
    msg_error_make_conflicts_and_binary_val = 'Ошибка: Расчёты конфликтов по двум алгоритмам не совпадают!'
    msg_success_make_conflicts_and_binary_val = 'Успех: Конфликты и бинарные значения фаз расчитаны успешно'

    msg_error_make_txt_file_with_conflicts = 'Ошибка: При создании текстового файла с конфликтами возникла ошибка'
    msg_success_make_txt_file_with_conflicts = 'Успех: Текстовый файл с конфликтами создан успешно'

    msg_error_make_config = 'Ошибка: При создании конфигурационного файла возникла ошибка'
    msg_success_make_config = 'Успех: Конфигурационный файл создан успешно'

    msg_success_make_config_and_txt_file = 'Успех: Текстовый файл с конфликтами и файл конфигурации создан'
    msg_only_txt_file_was_created = 'Ошибка: При создании конфигурационного файла возникла ошибка. Создан только' \
                                    'текстовый файл с конфликтами'
    msg_success_make_only_data_matrix = 'Успех: Матрицы и таблицы созданы успешно'



    def __init__(self, controller_type=None, numCO=None):
        """
            Attributes:
                |--- matrix_swarco_F997 - > матрица конфликтов для F997 swarco
                |--- matrix_output -> матрица конфликтов для записи в txt/вывода на экран
                |--- binary_val_swarco_for_write_PTC2 -> бинарные значения фаз для записи в PTC2
                |--- binary_val_swarco_F009 -> бинарные значения фаз для записи txt
                |--- conflict_groups_Peek - > матрица конфликтов для peek
                |--- sum_conflicts_for_peek -> количество конфликтов для peek


                :param self.input_stages -> список списков от польщователя, на основе которого будет
                                            производится расчёт конфликтов и формироваться данные
                                            для вывода/конфига .PTC2(swarco) или .DAT(для peek)
        """
        self.numCO = numCO
        self.input_stages = None
        self.tmp_input_stages = None
        self.controller_type = controller_type

        self.sorted_stages = None
        self.matrix_output = None
        self.matrix_swarco_F997 = None
        self.binary_val_swarco_for_write_PTC2 = None
        self.binary_val_swarco_F009 = None
        self.conflict_groups_F992 = None
        self.conflict_groups_Peek = None
        self.sum_conflicts_for_peek = None
        self.num_stages = None
        self.kolichestvo_napr = 0
        self.sum_conflicts_for_peek = 0
        self.make_config = None

        self.add_conflicts_and_binval_calcConflicts = None

        self.result_input_data_stages = []
        self.result_num_stages = []
        self.result_num_kolichestvo_napr = []
        self.result_calculate_conflicts_and_binvals = []
        self.result_calculate_conflicts_typeF992 = []
        self.result_make_txt = []
        self.result_make_config = []
        self.result_only_matrix_and_tables = []



    def remove_quotes(self, user_file):
        """Функция принимает на вход строку, которую ввел пользователь, содержащую путь к каталогу/файлу и
           возвращает строку без кавычек"""
        user_file = user_file.replace('"', '').replace("'", '')
        return user_file

    def make_path_to_save_file(self, path_old: str, prefix: str = 'new_'):
        """
            Метод формирует и возвращает новый путь к файлу

        :param str path_old: Исходный путь к файлу
        :param str prefix: суффикс, который будет добавлен к названию нового файла
        :return str: новый путь
        """
        if '/' in path_old:
            part1_dir = '/'.join(path_old.split('/')[:-1])
            part2_name = '/'.join(path_old.split('/')[-1:])
            path = f'{part1_dir}/{prefix}{part2_name}'
        elif '\\' in path_old:
            path_old = self.remove_quotes(path_old)
            part1_dir = '\\'.join(path_old.split('\\')[:-1])
            part2_name = '\\'.join(path_old.split('\\')[-1:])
            path = f'{part1_dir}/{prefix}{part2_name}'
        else:
            path = 'Error creating a new file path'

        return path


    def validate_input_data_stages(self, input_data_stages, char_for_split):
        """"
            Метод проверяет, получены ли данных о фазах на вход функции calculate_conflicts
            Записывает в self.result_input_data_stages результат проверки в виде списка,
            где:
                self.result_input_data_stages[0] -> результат
                self.result_input_data_stages[1] -> сообщение(может быть использовано в дальнейшем)
            :param input_data_stages -> данные, список фаз
        """

        if isinstance(input_data_stages, str):
            input_data_stages = input_data_stages.split(char_for_split)

        if len(input_data_stages) < self.allowed_min_num_stages_without_controller_type:
            self.result_input_data_stages = (False, self.msg_less_than_2_stages_input_stages)
            return

        if len(input_data_stages) > self.allowed_max_num_stages_without_controller_type:
            self.result_input_data_stages = (False, self.msg_more_than_100_stages_input_stages)

        self.result_input_data_stages = (True, self.msg_data_input_stages_success)
        return input_data_stages

    def validate_max_stages(self, stages, controller_type=None):
        """"
            Метод проверяет допустимое количество фаз
            Записывает в self.result_input_data_stages результат проверки в виде списка,
            где:
                result_num_stages[0] -> результат
                result_num_stages[1] -> сообщение(может быть использовано в дальнейшем)
            :param stages:
            :param controller_type -> тип контроллера, для которого необходимо рассчитать конфликты
        """
        num_stages = len(stages)
        self.num_stages = num_stages

        if controller_type is None:
            self.result_num_stages = [False, self.msg_controller_type_is_not_selected]
            raise ValueError
        if controller_type == self.available_controller_types[0]:
            if num_stages > self.allowed_max_stages_swarco:
                self.result_num_stages = [False, f'{self.msg_more_than_8_stages_swarco}: {num_stages}']
            else:
                self.result_num_stages = [True, f'{self.msg_max_num_stages_success}']
        elif controller_type == self.available_controller_types[1]:
            if num_stages > self.allowed_max_stages_peek:
                self.result_num_stages = [False, f'{self.msg_more_than_32_stages_peek}: {num_stages}']
            else:
                self.result_num_stages = [True, f'{self.msg_max_num_stages_success}']
        elif controller_type == self.available_controller_types[2]:
            if num_stages > self.allowed_max_num_stages_without_controller_type:
                self.result_num_stages = [False, f'{self.msg_more_than_100_stages_input_stages}: {num_stages}']
            else:
                self.result_num_stages = [True, f'{self.msg_max_num_stages_success}']
        else:
            raise AttributeError

    def validate_max_groups(self, num_groups, controller_type=None):
        """"
            Метод проверяет допустимое количество направлений
            Записывает в self.result_num_kolichestvo_napr результат проверки в виде списка,
            где:
                result_num_kolichestvo_napr[0] -> результат
                result_num_kolichestvo_napr[1] -> сообщение(может быть использовано в дальнейшем)
            :param consider_controller_type -> учитывать ли тип контроллера при проверке
                                               максимально допустимого количества направлений
            :param controller_type -> тип контроллера, для которого необходимо рассчитать конфликты
        """

        if controller_type is None:
            self.result_num_kolichestvo_napr = [False, self.msg_controller_type_is_not_selected]
            raise ValueError


        if controller_type == self.available_controller_types[0]:
            if num_groups > self.allowed_max_kolichestvo_napr_swarco:
                self.result_num_kolichestvo_napr = [False, f'{self.msg_more_than_48_groups_swarco}: {num_groups}']
            else:
                self.result_num_kolichestvo_napr = [True, f'{self.msg_max_num_groups_success}']
        elif controller_type == self.available_controller_types[1]:
            if num_groups > self.allowed_max_kolichestvo_napr_peek:
                self.result_num_kolichestvo_napr = [False, f'{self.msg_more_than_64_groups_peek}: {num_groups}']
            else:
                self.result_num_kolichestvo_napr = [True, f'{self.msg_max_num_groups_success}']
        elif controller_type == self.available_controller_types[2]:
            if num_groups > self.allowed_max_num_kolichestvo_napr_without_controller_type:
                self.result_num_kolichestvo_napr = [False, f'{self.msg_more_than_100_groups_without_controller_type}: {num_groups}']
            else:
                self.result_num_kolichestvo_napr = [True, f'{self.msg_max_num_groups_success}: {num_groups}']
        else:
            self.result_num_kolichestvo_napr = [False, 'ERROR!']

        return self.result_num_kolichestvo_napr[0]

    def remove_chars(self, string):
        """"
            Метод удаляет последний символ строки, если он не является числом
            :param string -> строка, которую необходимо проверить
            :return string -> строка, в которой последний символ число, либо пустая строка, если нет чисел
        """
        for i in range(len(string)):
            if string[-1].isdigit():
                return string
            string = string[:-1]
        return string

    def sort_stages(self, stages,
                    chars_for_identification_all_red=('-', 'всем красный', 'кругом красный', ''),
                    auto_correct_last_char=False,):
        """
            Функция сортирует списки(list) фаза-направление.
            Вложенный список с индексом 0 -> 1 фаза, с индексом 1 -> 2 фаза и т.д.
            Значения в списке - направления, участвующие в фазе
        """

        self.sorted_stages = []
        self.kolichestvo_napr = 0

        for line in stages:
            if ':' in line:
                processed_line = line.replace("\r", '').split(':')[1]
            else:
                processed_line = line.replace("\r", '')
            processed_line = processed_line.replace(" ", '')

            if auto_correct_last_char:
                processed_line = self.remove_chars(processed_line)

            if processed_line in chars_for_identification_all_red:
                self.sorted_stages.append([])
                continue

            processed_line = list(set(processed_line.split(',')))

            # Проверка корректности введенных данных
            for i, char in enumerate(processed_line):
                if not char.isdigit():
                    raise ValueError
                else:
                    processed_line[i] = int(char)

            processed_line = sorted(processed_line)

            self.sorted_stages.append(processed_line)

            if processed_line[-1] > self.kolichestvo_napr:
                self.kolichestvo_napr = processed_line[-1]

            if not self.validate_max_groups(self.kolichestvo_napr, controller_type=self.controller_type):
                return self.result_num_kolichestvo_napr[0]

        return self.sorted_stages


    def make_conflicts_and_binary_val(self, confl_swarco='03.0;'):
        """"
            В даном методе производится расчёт кофликтов и формируется имнформация для вывода
            пользователю/записи в текстовый файл/формирования кофигов(swarco и peek)
            В методе реализовано 2 различных алгоритма по формированию конфликтов, в конце которых прозволится
            проверка на совпдаение расчётов конфликтов. Если итоговые расёты не совпадают, то функция
            возвращает строку 'Error of correct calculation', иначе вернёт True
            supervisor_matrix_swarco_F997 -> матрица конфликтов для F997, ссозданная на основе алгоритма, отличающегося
            от того, по которому формируется matrix_swarco_F997. После создания обеих матриц идёт проверка, равны
            ли они друг другу.

            :param confl_swarco -> згачение, которым будет заполнена матрица, когда есть конфликт

            :return str -> 'Error of correct calculation' если итоговые расёты не совпадают,
            :return bool -> True, если расчёты совпали
        """

        self.matrix_swarco_F997 = []
        self.binary_val_swarco_for_write_PTC2 = []
        self.binary_val_swarco_F009 = []
        supervisor_matrix_swarco_F997 = []
        # Шапка вида | *| |01| |02| |03| |04| |05| |06| |07| |08| |09| |10|
        self.matrix_output = [['| *|' if i == 0 else f'|0{i}|' if i < 10 else f'|{i}|' for i in range(self.kolichestvo_napr + 1)]]

        for i in range(1, self.kolichestvo_napr + 1):
            tmp_matrix_output = ['X;' if x == i - 1 else confl_swarco for x in range(self.kolichestvo_napr)]
            tmp_matrix_swarco_F997 = [f'|0{i}|' if x == 0 and i < 10 else f'|{i}|' if x == 0 and i > 9 else
            '| K|' for x in range(self.kolichestvo_napr + 1)]
            binary_val = 0

            tmp_for_supervisor = []
            tmp_matrix_swarco_F997_supervosor = ['X;' if x == i - 1 else confl_swarco for x in range(self.kolichestvo_napr)]

            for j in range(len(self.sorted_stages)):
                if i in self.sorted_stages[j]:
                    for napr in self.sorted_stages[j]:
                        tmp_matrix_output[napr - 1] = '  . ;'
                        tmp_matrix_output[i - 1] = 'X;'

                        tmp_matrix_swarco_F997[napr] = '| O|'
                        tmp_matrix_swarco_F997[i] = '| *|'
                        # Для проверки(supervisor_matrix_swarco_F997)
                        tmp_for_supervisor = tmp_for_supervisor + self.sorted_stages[j]

                    if j != 7:
                        binary_val = binary_val + 2 ** (j + 1)
                    else:
                        binary_val = binary_val + 2 ** 0
                # Если фаза пустая(без направлений)
                elif i not in self.sorted_stages[j]:
                    tmp_matrix_swarco_F997[i] = '| *|'

            if binary_val < 10:
                self.binary_val_swarco_for_write_PTC2.append([f';00{binary_val};;1;'])
            elif binary_val > 9 and binary_val < 100:
                self.binary_val_swarco_for_write_PTC2.append([f';0{binary_val};;1;'])
            elif binary_val > 99 and binary_val < 256:
                self.binary_val_swarco_for_write_PTC2.append([f';{binary_val};;1;'])
            self.binary_val_swarco_F009.append([f'{binary_val};'])

            self.matrix_swarco_F997.append(tmp_matrix_output)
            self.matrix_output.append(tmp_matrix_swarco_F997)

            # Для проверки(supervisor_matrix_swarco_F997)
            tmp_for_supervisor = sorted(list(set(tmp_for_supervisor)))
            for ii in tmp_for_supervisor:
                tmp_matrix_swarco_F997_supervosor[ii - 1] = '  . ;'
                tmp_matrix_swarco_F997_supervosor[i - 1] = 'X;'
            supervisor_matrix_swarco_F997.append(tmp_matrix_swarco_F997_supervosor)

        if supervisor_matrix_swarco_F997 != self.matrix_swarco_F997:
            self.result_calculate_conflicts_and_binvals = [False, self.msg_error_make_conflicts_and_binary_val]
        else:
            self.result_calculate_conflicts_and_binvals = [True, self.msg_success_make_conflicts_and_binary_val]


    def make_number_coflicts_group_for_swarco_F992(self):
        """ Функция принимает на вход матрицу конфликтов вида F997.
            Рассчитывает и возвращает вложенный список направлений, с которыми есть конфликт у каждой их групп
            Вложенный список с индеком 0 -> группы, с которыми есть конфликт у 1 направления,
            индекс 1 -> группы, с которыми есть конфликт у 2 направления и т.д.
        """

        if self.controller_type == 'swarco':
            self.conflict_groups_F992 = []
            for i in range(len(self.matrix_swarco_F997)):
                tmp = []
                num_group = 1

                for j in self.matrix_swarco_F997[i]:
                    if j == '03.0;':
                        tmp.append(f'{num_group};')
                    num_group += 1
                self.conflict_groups_F992.append(tmp)

        elif self.controller_type == 'peek':
            self.conflict_groups_Peek = []
            self.sum_conflicts_for_peek = 0

            for i in range(len(self.matrix_swarco_F997)):
                tmp2 = []
                num_group = 1
                for j in self.matrix_swarco_F997[i]:
                    if j == '03.0;':
                        tmp2.append(num_group)
                    num_group += 1
                self.conflict_groups_Peek.append(tmp2)
                self.sum_conflicts_for_peek = self.sum_conflicts_for_peek + len(tmp2)



    def calculate_conflicts(self,
                            path_to_txt_conflicts=f'сalculated_conflicts{dt.now().strftime("%d %b %Y %H_%M_%S")}.txt',
                            path_to_config_file=None, prefix_for_new_config_file='calculated_',
                            add_conflicts_and_binval_calcConflicts=False,
                            make_txt_conflicts=False,
                            make_config=False,
                            controller_type=None,
                            input_stages=None,
                            auto_correct_last_char=True,
                            char_for_split='\n'):
        """ Функция формирует матрицу конфликтов на основе алгоритма поиска конфликтных направлений
            Матрица для функции F997 swarco: 0 индекс -> 1 направление, 1 индекс -> 2 направление и т.д.
            Матрица для вывода на экран(oputput)/записи в файл: 0 индекс -> шапка матрицы
            1 индекс -> 1 направление, 2 индекс -> 2 направление и т.д.

            supervisor_matrix_swarco_F997 -> матрица конфликтов для F997, ссозданная на основе алгоритма, отличающегося
            от того, по которому формируется matrix_swarco_F997. После создания обеих матриц идёт проверка, равны
            ли они друг другу. Если не равны -> выходим из функции и пишем в лог

        """

        self.input_stages = input_stages
        self.controller_type = controller_type
        self.make_config = make_config

        # Служебная проверка типа данных в input_stages
        if isinstance(self.input_stages, str):
            self.tmp_input_stages = input_stages.split(char_for_split)
        elif not isinstance(self.tmp_input_stages, list):
            self.result_input_data_stages = [False, self.msg_invalid_input_data_type]
            return self.result_input_data_stages

        # Первая проверка на корректность входных данных в input_stages
        result = self.validate_input_data_stages(input_stages, char_for_split)
        if self.result_input_data_stages[0]:
            self.tmp_input_stages = result
        else:
            return self.result_input_data_stages
        # Вторая проверка на максимально допустимое количество фаз
        self.validate_max_stages(self.tmp_input_stages, controller_type=self.controller_type)
        if not self.result_num_stages[0]:
            return self.result_num_stages

        # Сортировка фаз(направления по возврастанию/выбрасывание дублей/символов, проверка корректности данных)
        # Третья проверка на максимально допустимое количество направлений внутри self.sort_stages()
        if not self.sort_stages(self.tmp_input_stages, auto_correct_last_char=auto_correct_last_char):
            return self.result_num_kolichestvo_napr


        self.make_conflicts_and_binary_val()
        if not self.result_calculate_conflicts_and_binvals[0]:
            return self.result_calculate_conflicts_and_binvals

        self.make_number_coflicts_group_for_swarco_F992()

        if not make_txt_conflicts and not make_config:
            self.result_only_matrix_and_tables = [True, self.msg_success_make_only_data_matrix]
            return self.result_only_matrix_and_tables

        if make_txt_conflicts:
            self.write_conflicts_to_txt_file(
                path_and_name_for_txt_conflicts=path_to_txt_conflicts,
                conflicts_and_binVal_swarco=add_conflicts_and_binval_calcConflicts,)

        if make_config:
            if self.controller_type == self.available_controller_types[0]:
                self.make_PTC2_file(path_to_original_PTC2=path_to_config_file,
                                    prefix_for_new_file=prefix_for_new_config_file)
            elif self.controller_type == self.available_controller_types[1]:
                self.make_dat_file_for_peek(path_to_original_DAT=path_to_config_file,
                                            prefix_for_new_file=prefix_for_new_config_file)
            else:
                self.result_make_config = [False, self.msg_controller_type_is_not_selected]

            if make_txt_conflicts and self.result_make_txt[0] and self.result_make_config[0]:
                return True, self.msg_success_make_config_and_txt_file
            elif not make_txt_conflicts and self.result_make_config[0]:
                return True, self.msg_success_make_config
            elif self.result_make_txt[0]:
                return False, self.msg_only_txt_file_was_created
            else:
                return False, 'ERROR!' #Программная ошибка(Оставил, пока на этапе отладки)
        elif make_txt_conflicts:
            return self.result_make_txt

        else:
            return False, 'ERROR!'  # Программная ошибка(Оставил, пока на этапе отладки)

    def write_conflicts_to_txt_file(self, path_and_name_for_txt_conflicts=None, conflicts_and_binVal_swarco=False):
        """Функция производит запись вычесленных ранее ""Матрица конфликтов "интергрин" F997",
           "Физические конфликты - номера конфликтных групп F992", "Сигнальные группы в фазах F009"(бинарные значения)
           в файл по указанному пользевателем каталогу
        :param path_and_name_for_txt_conflicts -> пусть к текстовому файлу, который будет создан
        :param conflicts_and_binVal_swarco -> флаг для включения в текстовый файл конфликтов и значений для swarco

        """

        # Запись значений в файл
        try:
            with open(path_and_name_for_txt_conflicts, 'w') as file:
                # Запишем в файл общую информацию: Фазы-Направления
                num_stage = 1
                for stage in self.sorted_stages:
                    if stage:
                        file.write(f"Фаза {num_stage}: ")
                        check_last_item = 1
                    else:
                        file.write(f"Фаза {num_stage}:\n")
                        num_stage += 1
                        continue
                    for num_napravleniya in stage:
                        if check_last_item == len(stage):
                            file.write(f'{num_napravleniya}\n')
                        else:
                            file.write(f'{num_napravleniya}, ')
                            check_last_item += 1
                    num_stage += 1
                file.write(f'Количество направлений: {self.kolichestvo_napr}\n\n')

                # Общая "Матрица конфликтов"
                for stroka_napravleine in range(self.kolichestvo_napr + 1):
                    file.write(f'{" ".join(self.matrix_output[stroka_napravleine])}\n')
                file.write('\n')

                if conflicts_and_binVal_swarco:
                    # Запишем в файл "Матрица конфликтов "интергрин" F997"
                    file.write('Матрица конфликтов "интергрин" F997:\n')
                    for num_napravleniya in self.matrix_swarco_F997:
                        for stroka_napravlenie in num_napravleniya:
                            file.write(stroka_napravlenie)
                        file.write('\n')
                    file.write('\n')

                    # Запишем в файл "Физические конфликты - номера конфликтных групп F992"
                    file.write('Физические конфликты - номера конфликтных групп F992:\n')
                    for num_napravleniya in self.conflict_groups_F992:
                        for stroka_napravlenie in num_napravleniya:
                            file.write(stroka_napravlenie)
                        file.write('\n')
                    file.write('\n')

                    # Запишем в файл "Сигнальные группы в фазах F009"(,бинарные значения)
                    file.write('Сигнальные группы в фазах F009: \n')
                    for num_napravleniya in self.binary_val_swarco_F009:
                        for val in num_napravleniya:
                            file.write(val)
        except Exception as err: # определить какую ошибку ловишь
            pass #что-то делать
            return err # например

        if os.path.exists(path_and_name_for_txt_conflicts):
            self.result_make_txt = [True, self.msg_success_make_txt_file_with_conflicts, path_and_name_for_txt_conflicts]
        else:
            self.result_make_txt = [False, self.msg_error_make_txt_file_with_conflicts]


    def make_PTC2_file(self, path_to_original_PTC2, prefix_for_new_file: str, ):
        """
        Метод создает новый .PTC2 файл с рассчитанными конфликтами и фазами
        :param path_to_original_PTC2: путь к исходному файлу, на основе которого будет сформирован новый
        :param prefix_for_new_file -> префикс, который будет добавлен к созданному .DAT фалу.по дефолту 'new_'
        :return str: сообщение
        """
        path_to_new_PTC2 = self.make_path_to_save_file(path_to_original_PTC2, prefix=prefix_for_new_file)

        try:
            with open(path_to_original_PTC2) as file, open(path_to_new_PTC2, 'w') as new_file:
                flag1 = flag2 = flag3 = flag4 = False
                for line in file:
                    if flag1:
                        if 'NeXt' not in line:
                            new_file.write('')
                        else:
                            flag1 = False
                    elif flag2:
                        if 'NeXt' not in line:
                            new_file.write('')
                        else:
                            flag2 = False
                    elif flag3:
                        if 'NeXt' not in line:
                            new_file.write('')
                        else:
                            flag3 = False
                    elif flag4:
                        if 'NeXt' not in line:
                            new_file.write('')
                        else:
                            flag4 = False

                    if 'NewSheet693  : Work.997' in line:
                        flag1 = True
                        new_file.write(line)
                        for group_line in self.matrix_swarco_F997:
                            new_file.write(''.join(group_line))
                            new_file.write('\n')
                    elif 'NewSheet693  : Work.992' in line:
                        flag2 = True
                        new_file.write(line)
                        for group_line in self.matrix_swarco_F997:
                            new_file.write(''.join(group_line))
                            new_file.write('\n')
                    elif 'NewSheet693  : Work.009' in line:
                        flag3 = True
                        new_file.write(line)
                        for group_line in self.binary_val_swarco_for_write_PTC2:
                            new_file.write(''.join(group_line))
                            new_file.write('\n')
                    elif 'NewSheet693  : Work.006' in line:
                        flag4 = True
                        new_file.write(line)
                    elif not flag1 and not flag2 and not flag3 and not flag4:
                        new_file.write(line)
                if os.path.exists(path_to_new_PTC2):
                    self.result_make_config = [True, self.msg_success_make_config, path_to_new_PTC2]
                else:
                    self.result_make_config = [False, self.msg_error_make_config]
        except Exception as err:  # определить какую ошибку ловишь
            pass  # что-то делать

    def make_dat_file_for_peek(self, path_to_original_DAT: str, prefix_for_new_file: str,):
        """
        Метод создает новый .DAT файл с рассчитанными конфликтами и фазами
        :param path_to_original_DAT: путь к исходному файлу, на основе которого будет сформирован новый
        :param prefix_for_new_file -> префикс, который будет добавлен к созданному .DAT фалу.по дефолту 'new_'
        :return str: сообщение
        """
        sum_stages = len(self.sorted_stages)
        new_file_dat = self.make_path_to_save_file(path_to_original_DAT, prefix=prefix_for_new_file)

        table_conflicts = f':TABLE "XSGSG",{str(self.sum_conflicts_for_peek)},4,3,4,4,3\n'
        table_SA_STG = f':TABLE "YSRM_SA_STG",{str(sum_stages)},2,4,10\n'
        table_UK_STAGE = f':TABLE "YSRM_UK_STAGE",{str(sum_stages)},4,4,4,1,10\n'

        try:
            with open(path_to_original_DAT, 'r', encoding='utf-8') as file1, open(new_file_dat, 'w',
                                                                                  encoding='utf-8') as file2:
                flag1 = flag2 = flag3 = False
                count = 0
                for line in file1:
                    if flag1 and 'TABLE "YKLOK"' not in line:
                        pass
                    elif flag1 and 'TABLE "YKLOK"' in line:
                        flag1 = False
                        count += 1
                        file2.write(':END\n')
                        file2.write(line)
                    elif ':TABLE "XSGSG"' in line:
                        file2.write(table_conflicts)
                        for num_group_from in range(len(self.conflict_groups_Peek)):
                            for num_group_to in self.conflict_groups_Peek[num_group_from]:
                                file2.write(f':RECORD\n'
                                            f'"Type",2\n'
                                            f'"Id1",{str(num_group_from + 1)}\n'
                                            f'"Id2",{str(num_group_to)}\n'
                                            f'"Time",30\n'
                                            f':END\n')
                        flag1 = True

                    elif flag2 and ':TABLE "YSRM_STEP"' not in line:
                        pass
                    elif flag2 and ':TABLE "YSRM_STEP"' in line:
                        flag2 = False
                        count += 1
                        file2.write(':END\n')
                        file2.write(line)
                    elif ':TABLE "YSRM_SA_STG"' in line:
                        file2.write(table_SA_STG)
                        for num_stage in range(len(self.sorted_stages)):
                            stage = ','.join(list(map(str, self.sorted_stages[num_stage])))
                            file2.write(f':RECORD\n'
                                        f'"Id",{str(num_stage + 1)}\n'
                                        f'"SGdef","{stage}"\n'
                                        f':END\n')
                        flag2 = True

                    elif flag3 and '"YSRM_UK_STAGE_TRANS"' not in line:
                        pass
                    elif flag3 and '"YSRM_UK_STAGE_TRANS"' in line:
                        flag3 = False
                        count += 1
                        file2.write(':END\n')
                        file2.write(line)
                    elif ':TABLE "YSRM_UK_STAGE"' in line:
                        file2.write(table_UK_STAGE)
                        for num_stage in range(len(self.sorted_stages)):
                            stage = ','.join(list(map(str, self.sorted_stages[num_stage])))
                            file2.write(f':RECORD\n'
                                        f'"ProcessId",1\n'
                                        f'"StageId",{str(num_stage + 1)}\n'
                                        f'"StartUpStage",{str(True) if num_stage == 0 else str(False)}\n'
                                        f'"SignalGroups",",{stage},"\n'
                                        f':END\n')
                        flag3 = True

                    else:
                        file2.write(line)

            if os.path.exists(new_file_dat):
                self.result_make_config = [True, self.msg_success_make_config, new_file_dat]
            else:
                self.result_make_config = [False, self.msg_error_make_config]
        except Exception as err:  # определить какую ошибку ловишь
            pass  # что-то делать
            return err  # например