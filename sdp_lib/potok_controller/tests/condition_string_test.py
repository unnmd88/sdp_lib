from unittest import TestCase, main
from toolkit.sdp_lib.potok_controller import condition_string


class TestConditionParse(TestCase):

    def test_create_valid_tokens_get_token(self):
        """
        Тест метода get_token(self). Из строки условия перехода/продления tcl контроллера Поток
        должен быть сгенерирован список с токенами(функциями) доступными для данного типа ДК
        :return:
        """

        expected_tokens = [
            'ddr(D41)', 'ddr(D41)', 'ddr(D41)', 'ddr(D45)', 'ddr(D43)', 'ddr(D44)', 'mr(G1)', 'ddr(D41)',
            'ddr(D42)', 'ddr(D43)', 'ddr(D44)', 'ddr(D45)', 'ddr(D46)', 'ddr(D47)', 'mr(G1)', 'fctg(G1) >= 40'
        ]

        string = (
            '(ddr(D41) and (ddr(D41) or ddr(D41) or ddr(D45)) or (not ddr(D43) and ddr(D44)) and mr(G1) and '
            'ddr(D41) or ddr(D42) or ddr(D43) or ddr(D44) or ddr(D45) or ddr(D46) or ddr(D47)) and mr(G1) '
            'and fctg(G1) >= 40'
        )
        tokens = condition_string.ConditionStringPotokTlc(string).create_tokens()
        print(tokens)

        self.assertEqual(tokens, expected_tokens)

        string2 = (
            '(ddr(D41))) and (ddr(D41) or ddr(D41) or ddr(D45)) or (not ddr(D43) and ddr(D44)) and mr(G1) and '
            'ddr(D41))))))))))))) or (((ddr(D42) or ddr(D43) or ddr(D44) or '
            '((((ddr(D45) or ddr(D46) or ddr(D47)) and mr(G1))))) and fctg(G1) >= 40'
        )
        tokens2 = condition_string.ConditionStringPotokTlc(string2).create_tokens()
        self.assertEqual(tokens2, expected_tokens)


if __name__ == '__main__':
    main()
