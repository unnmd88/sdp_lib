from random import randint
from unittest import TestCase, main
from toolkit.sdp_lib.potok_controller import potok_user_api


class TestGetTokens(TestCase):
    """
    Тест получения токенов(функций контроллера Поток) из строки
    условие продления/условие вызова фазы
    """

    def test_get_tokens(self):
        string_condition = '(ddr(D21) ddr(D22) or ddr(D23) or ddr(D24) or ddr(D30)) and mr(G6)'
        tokens = potok_user_api.Tokens(string_condition).get_tokens()
        self.generate_condition_string()
        self.assertEqual(tokens, ['ddr(D21)', 'ddr(D22)', 'ddr(D23)', 'ddr(D24)', 'ddr(D30)', 'mr(G6)'])

    def generate_condition_string(self):
        functions = ['ddr', 'ddo', 'mr', 'ddo', 'not ddr']
        condition_string = ''.join([
            f'{functions[randint(0, len(functions) - 1)]}(D{n}) and ' for n in range(1, randint(10, 20))
        ])


class TestChecker(TestCase):

    def test_check_parens(self):
        self.assertFalse(potok_user_api.Checker('(ddr(D1))').check_parens())
        self.assertFalse(potok_user_api.Checker('ddr(D1) and (not (ddr(D3)))').check_parens())
        self.assertFalse(potok_user_api.Checker('(mr(G1) or (mr(G2) and mr(G3)) or mr(G4))').check_parens())
        self.assertTrue(potok_user_api.Checker('ddr(D1) or (ddr(D1) and ddr(D2)))').check_parens())
        self.assertTrue(potok_user_api.Checker('ddr(D1) or (((((ddr(D1) and ddr(D2)))').check_parens())
        self.assertTrue(potok_user_api.Checker('ddr(D1) and (((ddr(D2) or ddr(D3))').check_parens())


class TestConditionResult(TestCase):

    def test_get_condition_result(self):
        string = "ddr(D4) or ddr(D5) or ddr(D6) or ddr(D7) and mr(G1)"
        """ Тесты на корректность возвращаемого значения. Сравниваю результат парсера и eval """
        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("0 or 0 or 1 or 1 and 0"),
            bool(eval("0 + 0 + 1 + 1 * 0"))
        )
        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("1 or 1 or 1 or 1 and 0"),
            bool(eval("1 + 1 + 1 + 1 * 0"))
        )
        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("(1 or 1 or 1 or 1) and 0"),
            bool(eval("(1 + 1 + 1 + 1) * 0"))
        )
        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("(1 or 1 or 1 or 1) and 0 or 1"),
            bool(eval("(1 + 1 + 1 + 1) * 0 + 1"))
        )
        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("(1 or 1 or 1 or 1) and 0 or 1 and 0"),
            bool(eval("(1 + 1 + 1 + 1) * 0 + 1 * 0"))
        )
        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("(1 or 1 or 1 or 1 and 1) and (0 or 0)"),
            bool(eval("(1 + 1 + 1 + 1 * 1) * (0 + 0)"))
        )

        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("not 1"),
            bool(eval("int(not 1)"))
        )

        self.assertEqual(
            potok_user_api.ConditionResult(string).get_condition_result("not (not(1)) + 1* 1 + 1 * 0"),
            bool(eval("int(not (not 1)) + 1* 1 + 1 * 0"))
        )

        """ Тесты на правильность возращаемого значения выражения(условия перехода/продления) """

        self.assertTrue(potok_user_api.ConditionResult(string).get_condition_result(
            "0 or 0 or 1 or 1 and 0"
        ))
        self.assertTrue(potok_user_api.ConditionResult(string).get_condition_result(
            "0 or 0 or 0 or 1 and 1"
        ))
        self.assertFalse(potok_user_api.ConditionResult(string).get_condition_result(
            "0 or 0 or 0 or 0 and 1"
        ))

        """ Тесты на то, что метод может принимать str или Dict """
        string2 = "(ddr(D4) or ddr(D5) or ddr(D6) or ddr(D7)) and mr(G1)"
        self.assertEqual(
            potok_user_api.ConditionResult(string2).get_condition_result("(1 or 1 or 1 or 1) and 0"),
            potok_user_api.ConditionResult(string2).get_condition_result(
                {'ddr(D4)': 1, 'ddr(D5)': 1, 'ddr(D6)': 1, 'ddr(D7)': 1, 'mr(G1)': 0}
            ),
        )

        """ Тесты на бросание исключения """

        with self.assertRaises(TypeError) as e:
            potok_user_api.ConditionResult(string).get_condition_result(1)
        with self.assertRaises(TypeError) as e:
            potok_user_api.ConditionResult(string).get_condition_result((1, 2, 34,))


if __name__ == '__main__':
    main()
