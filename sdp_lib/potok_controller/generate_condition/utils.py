from sdp_lib.potok_controller.generate_condition.constants import ErrMessages


def remove_left_right_spaces(string: str, left=True, right=True) -> str:
    """
    Удаляет пробельные символы справа/слева у строки.
    :param string: Строка, в которой необходимо удалить пробельные символы.
    :param left:  True -> удаляет все пробельные символы слева.
    :param right: True -> удаляет все пробельные символы справа.
    :return: Строка с удаленными пробельными символами справа/слева.
    """
    if left:
        string = string.lstrip()
    if right:
        string = string.rstrip()
    return string


def get_main_and_mr_stmt(
    cond_string: str,
    sep: str = ','
) -> tuple[None | str, str, str]:
    """
    Делит строку на 2 части по заданному разделителю.
    1-ую часть оставляет без изменений, из 2-й части делает условие
    с функцией "mr" для продления.
    Пример строки: "1|2 & 4, 5"
    ""
    :param cond_string: Строка для обработки и формирования условий.
    :param sep: Разделитель, по которому будет разделена строка.
    :return: Кортеж из 3-х элементов:
             [0] -> Текст ошибки в виде строки, если есть. Иначе None.
             [1] -> 1-ая часть строки до разделителя, без изменений, если нет ошибки.
                    Из примера: "1|2 & 4". Иначе пустая строка "".
             [2] -> 2-ая часть строки после разделителя с условием продления,
                    если разделитель присутствует в строке и после разделителя имеется символ цифры,
                    означающий номер группы. Из примера: "and mr(G5)". Иначе пустая строка "".
            Пример. Из строки "1|2 & 4, 5" вернётся кортеж: (None, "1|2 & 4", "and mr(G5)").
    """
    gr = cond_string.split(sep)
    error = None
    main_expr = mr_expr = ''
    if len(gr) == 2:
        try:
            num_group = int(gr[1])
            main_expr, mr_expr = gr[0], f'and mr(G{num_group})'
        except ValueError:
            error = f'Номер группы после "{sep}" должен быть числом.'
    elif len(gr) == 1:
        main_expr, mr_expr = gr[0], ''
    else:
        error = ErrMessages.invalid_condition
    return error, remove_left_right_spaces(main_expr), remove_left_right_spaces(mr_expr)