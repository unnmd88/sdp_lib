from unittest import TestCase, main
from toolkit.sdp_lib.conflicts.calculate_conflicts import BaseConflictsAndStagesCalculations, DataFields


class TestConflicts(TestCase):
    def setUp(self) -> None:
        raw_data_stages = {
            '1': '1,4,2,3,5,5,5,5,3,4,2',
            '2': '1,6,7,7,3',
            '3': '9,10,8,13,3,10,',
            '4': '5,6,4'
        }
        self.current_calculation = BaseConflictsAndStagesCalculations(raw_data_stages)
        self.current_calculation.build_data()

    def test_no_duplicates_and_sorted(self):
        """
        Проверят отсутсвие дубликатов направлений после расчёта конфликтов и отсортированность списка
        направлений в порядке возрастания
        :return:
        """

        self.assertEqual(
            self.current_calculation.instance_data[DataFields.sorted_stages_data.value]['1'],
            [1, 2, 3, 4, 5]
        )
        self.assertEqual(
            self.current_calculation.instance_data[DataFields.sorted_stages_data.value]['2'],
            [1, 3, 6, 7]
        )

    def test_num_group_and_num_stages(self):
        """
        Проверяет корректность определения количества направлений и количества фаз
        :return:
        """
        self.assertEqual(self.current_calculation.instance_data[DataFields.number_of_groups.value], 13)
        self.assertEqual(self.current_calculation.instance_data[DataFields.number_of_stages.value], 4)
        self.assertEqual(
            self.current_calculation.instance_data[DataFields.all_num_groups.value], [i for i in range(1, 14)]
        )

    def test_allow_make_config_true(self):
        """
        Проверят корректность определения ключа "allow_make_config" из словаря self.instance_data.
        Если все номера направлений приналжежат типу int, значение ключа
        DataFields.allow_make_config.value в словаре instance_data должно быть True.
        :return:
        """
        self.assertTrue(
            self.current_calculation.instance_data[DataFields.allow_make_config.value], True
        )

    def test_test_allow_make_config_false(self):
        """
        Проверят корректность определения ключа "allow_make_config" из словаря self.instance_data.
        Если хотя бы один из номеров направлений не является числом типа int, значение ключа
        DataFields.allow_make_config.value в словаре instance_data должно быть False.
        :return:
        """
        raw_stages = {
            '1': '1,2,3,4',
            '2': '2,5,6',
            '3': '4.1,4.2,8,9'
        }
        curr_calc = BaseConflictsAndStagesCalculations(raw_stages)
        curr_calc.build_data()
        self.assertTrue(
            self.current_calculation.instance_data[DataFields.allow_make_config.value], False
        )




if __name__ == '__main__':
    main()
