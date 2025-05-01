import os
from enum import StrEnum

from dotenv import load_dotenv


load_dotenv()


class ItcTerminal(StrEnum):

    alias_itc = 'itc'
    alias_display = 'display'

    field_name_itc = 'itc'
    field_name_display = 'display'

    field_name_instat102 = 'instat102'

    display_command = 'SIMULATE DISPLAY --poll'
    itc_command = 'itc'

    lang_uk = 'lang UK'
    l2_login = os.getenv('level2_login')
    l2_pass = os.getenv('level2_passwd')

    inp101_1 = 'inp101=1'
    inp101_0 = 'inp101=0'

    inp102_1 = 'inp102=1'
    inp102_0 = 'inp102=0'

    inp103_1 = 'inp103=1'
    inp103_0 = 'inp103=0'
    instat102 = 'instat102 ?'

    echo = 'ECHO'
    l2_identifier = '&&>'



def process_stdout_itc(content):
    return content.splitlines()[1:-1]

def process_stdout_instat(content):
    """
    Пример
    :param content: stdout из сеанса интерактивной оболочки:
     content:
         instat102 ?\r\n'
         '\r\n'
         '     '
         '1111111111111111111111111111111111111111111111111111111111111111111111\r\n'
         '     '
         '0000000011111111112222222222333333333344444444445555555555666666666677\r\n'
         '     '
         '2345678901234567890123456789012345678901234567890123456789012345678901\r\n'
         ' 68: 0000000000000000000000000000000000000000000000000000000000000000000000\r'
         '\r\n'
         '&&>

     content.splitlines()[1:-1] :
           ['', '     "
            "1111111111111111111111111111111111111111111111111111111111111111111111', "
            "'     "
            "0000000011111111112222222222333333333344444444445555555555666666666677', "
            "'     "
            "2345678901234567890123456789012345678901234567890123456789012345678901', ' "
            "72: 0000000000000000000000000000000000000000000000000000000000000000000000', "
            "'']
    :return: Список из 2 строк состояния входов со 102 по 111:
            Пример: ['2345678901', '0000000000']
    """
    splited_stdout = content.splitlines()[1:-1]
    return [splited_stdout[3].replace(" ", '')[:10], splited_stdout[4].split(": ")[-1][:10]]


def process_stdoud_cbmem(content):
    return content

def process_stdoud_display(content):
    return content.splitlines()[1:-1]

itc_terminal = {
    ItcTerminal.itc_command: (ItcTerminal.field_name_itc, process_stdout_itc),
    ItcTerminal.display_command: (ItcTerminal.field_name_display, process_stdoud_display)
}

def process_terminal_stdout(command, content):
    r = itc_terminal.get(command)
    if r is not None:
        return r[0], r[1](content)

    if 'instat' in command.lower():
        return command.replace(' ?', ""), process_stdout_instat(content)
    elif 'cbmem' in command.lower():
        return command.replace(' ?', ""), process_stdoud_cbmem(content)

    return command, None


login_commands = [ItcTerminal.lang_uk, ItcTerminal.l2_login, ItcTerminal.l2_pass]

def get_instat_command(instat):
    try:
        return f'instat{int(instat.split("instat")[-1])} ?'
    except ValueError:
        pass
    return f'{instat} ?'

def get_inp_command(num_inp, val):
    return f'inp{num_inp}={val}'

matches_set_stage = {
    num_stage:  f'inp{num_inp}=1' for num_stage, num_inp in zip(range(1, 9), range(104, 112))
}

matches_stage_to_num_inp = {
    num_stage: num_inp for num_stage, num_inp in zip(range(1, 9), range(104, 112))
}

matches_num_inp_to_stage = {
    num_inp: num_stage for num_inp, num_stage  in zip(range(104, 112), range(1, 9))
}

reset_inputs_104_111_exclude_103 = [f'inp{num_inp}=0' for num_inp in range(4, 12)]
reset_inputs_102_111_exclude_103 = [f'inp{num_inp}=0' for num_inp in range(2, 12) if num_inp != 3]
reset_inputs_101_111 = [f'inp{num_inp}=0' for num_inp in range(1, 12)]

instat_start_102_and_display_commands = [get_instat_command('instat102'), ItcTerminal.display_command]


instat102_and_display = [
    (ItcTerminal.itc_command, (ItcTerminal.field_name_itc, process_stdout_itc)),
    (ItcTerminal.instat102, (ItcTerminal.field_name_instat102, process_stdout_instat)),
    (ItcTerminal.display_command, (ItcTerminal.field_name_display, process_stdoud_display))
]


def is_log_l2(stdout: str) -> bool:
    return ItcTerminal.l2_identifier in stdout

def get_commands_set_stage(stage: int, instat_start_102=None) -> list[str]:

    set_inp_commands = []

    if stage == 0 or instat_start_102 is None:
        set_inp_commands.append(ItcTerminal.inp102_0)
    else:
        stage_as_num_inp = matches_stage_to_num_inp.get(stage)
        for inp_cnt, inp_state in enumerate(instat_start_102[2:], 104):
            if inp_state != '0' and inp_cnt != stage_as_num_inp:
                set_inp_commands.append(get_inp_command(inp_cnt, 0))
        if instat_start_102[0] == '0':
            set_inp_commands.append(get_inp_command(102, 1))

        if instat_start_102[stage + 1] == '0':
            set_inp_commands.append(get_inp_command(stage_as_num_inp, 1))
    return set_inp_commands

if __name__ == '__main__':
    print(matches_num_inp_to_stage)
    print(matches_stage_to_num_inp)

    # state = ["2345678901", "1000000000"]
    state = "0000001010"
    print(get_commands_set_stage(4, instat_start_102=state))


