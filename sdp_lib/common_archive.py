import socket
import itertools
import datetime

import time
from datetime import datetime


def time_benchmark(func):
    def wrapper(option=None):
        start_time = time.time()
        func(option)
        print(f'Время выполенения функции: {time.time() - start_time}')

    return wrapper


def find_max_num_napravl(stages: list) -> int:
    max_napr = 0
    for num_stage in range(len(stages)):
        try:
            tmp_max_napr = int(max(stages[num_stage], key=lambda napr: int(napr)))
            # print(tmp_max_napr)
            if max_napr < tmp_max_napr:
                max_napr = tmp_max_napr
        except ValueError:
            pass
    return max_napr


def get_data_from_list(path_to_file):
    try:
        with open(path_to_file, 'r', encoding='UTF-8') as file:
            data_list = []
            for line in file:
                data_list.append(line.strip().split(':'))
    except UnicodeError:
        with open(path_to_file, 'r', encoding='windows-1251') as file:
            data_list = []
            for line in file:
                data_list.append(line.strip().split(':'))
    return data_list


def make_path_to_save_config(path_old: str):
    if '/' in path_old:
        part1_dir = '/'.join(path_old.split('/')[:-1])
        part2_name = '/'.join(path_old.split('/')[-1:])
        # print(f'{part1_dir}/new_{part2_name}')
        return f'{part1_dir}/new_{part2_name}'

    elif '\\' in path_old:
        path_old = remove_quotes(path_old)
        part1_dir = '\\'.join(path_old.split('\\')[:-1])
        part2_name = '\\'.join(path_old.split('\\')[-1:])
        # print(f'{part1_dir}/new_{part2_name}')
        return f'{part1_dir}/new_{part2_name}'


def remove_quotes(user_file):
    """Функция принимает на вход строку, которую ввел пользователь, содержащую путь к каталогу/файлу и
       возвращает строку без кавычек"""
    user_file = user_file.replace('"', '').replace("'", '')
    return user_file


def reverse_slashes(path):
    path = path.replace('\\', '/')
    return path


def check_charchter(chars):
    new_list_chars = []

    for i in range(len(chars)):
        stroka = ''
        for char in chars[i]:
            if char.isdigit() or char == ',':
                stroka = stroka + char
        if stroka != '':
            new_list_chars.append(stroka)
        print(new_list_chars)
    return new_list_chars


def convert_scn(SCN):
    """ Функция получает на вход строку, которую необходимо конвертировать в SCN
        для управления и мониторинга по протоколу UG405.
        Например: convert_scn(CO1111)
    """
    len_scn = str(len(SCN)) + '.'
    convert_to_ASCII = [str(ord(c)) for c in SCN]
    scn = f'.1.{len_scn}{".".join(convert_to_ASCII)}'
    return scn


def check_host_tcp(ip_adress: str, port=80, timeout=2):
    """
        Функция проверят наличие связи через socket с хостом. При наличии свзяи возвращает True, при отсутствии
        связи пишет в лог ошибку и возвращает False
    """
    try:
        socket.setdefaulttimeout(timeout)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((ip_adress, port))
    except OSError as error:
        return False
    else:
        return True


def replace_windows_line_ending_to_unix_line_ending(path_to_file):
    """ Функция заменяет переводы строк CRLF(Windows) на  LF(Unix) в файле по пути: path_to_file """

    WINDOWS_LINE_ENDING = b'\r\n'
    UNIX_LINE_ENDING = b'\n'

    with open(path_to_file, 'rb') as file:
        content = file.read()
    content = content.replace(WINDOWS_LINE_ENDING, UNIX_LINE_ENDING)

    with open(path_to_file, 'wb') as file:
        file.write(content)


def logger(path_to_file_log=None, message='-', flag='-', ip_adress='-', session_time=None):
    """ Функция, делающая запись в файл лог сессии ssh
        flile - название файла, в котрорый пишется лог
        message - сообщение для лога
        flag - флаг, который помогает понять необходимо делать перенос строки при записи
    """
    if path_to_file_log is None:
        return

    if flag == 'zagolovok':
        with open(path_to_file_log, 'a') as file_log:
            file_log.write(f'\n{"*" * 75}\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")}{message}\n')
    elif flag == 'ssh_set_inp_outp_Mreg':
        with open(path_to_file_log, 'a', encoding='latin-1') as file_log:
            file_log.write(f'\n{message}\n'
                           f'{datetime.today().strftime("%Y-%m-%d %H:%M:%S")}\n')
    elif flag == 'new_standart':
        with open(path_to_file_log, 'a') as file_log:
            file_log.write(f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} {message}')
    elif flag == 'standart':
        with open(path_to_file_log, 'a') as file_log:
            file_log.write(f'{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} < {message} >\n')
    elif flag == 'msg_from_ssh':
        with open(path_to_file_log, 'a') as file_log:
            file_log.write(f'{datetime.today().strftime("%Y-%m-%d %H:%M:%S")}:\n{message}\n')
    elif flag == 'put_log_to_ftp_laba_out':
        with open(path_to_file_log, 'a') as file_log:
            file_log.write(f'{datetime.datetime.now()} '
                           f'< Загрузка лога на ноут_лаба 192.168.45.163: {message} >\n')
    elif flag == 'stcip_json':
        with open(path_to_file_log, 'a') as file_log:
            file_log.write(f'\n\n{message}\n')


def time_repr(seconds: int):
    minutes = seconds // 60
    seconds = seconds % 60
    return str(minutes), str(seconds)


def write_to_log(path_to_log, message):
    with open(path_to_log, 'a') as file:
        file.write(f'\n{datetime.today().strftime("%Y-%m-%d %H:%M:%S")} {message}')


def make_va_and_ft_transitions(dat_file):
    with open(dat_file, 'r') as file:
        va = []
        ft = []
        cnt = 0
        flag_table_trans_stage = flag_va = flag_ft = flag_write_record = False

        for line in file:

            if ':TABLE "YSRM_VPLAN_PARM"' in line:
                break

            if ':TABLE "YSRM_UK_STAGE_TRANS"' in line:
                flag_table_trans_stage = True
                continue
            if not flag_table_trans_stage:
                continue

            if flag_table_trans_stage and ':RECORD' in line:
                cnt += 1
                string = line
            elif flag_table_trans_stage and '"TransId"' in line:
                # Номер transition "TransId",
                trans_id = line.strip().split(',')[1]
                string += line
            elif flag_table_trans_stage and '"ModeOfOpp",5' in line:
                flag_va = True
                string += line
            elif flag_table_trans_stage and '"ModeOfOpp",6' in line:
                flag_ft = True
                string += line
            elif flag_table_trans_stage and ':END' in line:
                if flag_va:
                    string += line
                    va.append(string)
                    flag_va = False
                    string = ''
                elif flag_ft:
                    string += line
                    ft.append(string)
                    flag_ft = False
                    string = ''
                else:
                    continue
            else:

                string += line

    return va, ft


def make_utc_and_man_transitions(num_stages):
    utc_transitions = []
    man_transitions = []
    num_transition = 1

    for j in range(1, num_stages + 1):
        for i in range(1, num_stages + 1):
            if j == i:
                continue
            if i != j:
                utc_trans = (
                    f':RECORD\n'
                    f'"ProcessId",1\n'
                    f'"TransId",{num_transition}\n'
                    f'"ModeOfOpp",1\n'
                    f'"FromStage",{j}\n'
                    f'"ToStage",{i}\n'
                    f'"DemandCondition","utc_STG({j},{i})"\n'
                    f'"ExtensionCondition",""\n'
                    f'"InhibitionCondition","utc_i_STG({j},{i})"\n'
                    f':END\n'
                )

                man_tr = (f':RECORD\n'
                          f'"ProcessId",1\n'
                          f'"TransId",{num_transition}\n'
                          f'"ModeOfOpp",3\n'
                          f'"FromStage",{j}\n'
                          f'"ToStage",{i}\n'
                          f'"DemandCondition","man_STG({j},{i})"\n'
                          f'"ExtensionCondition",""\n'
                          f'"InhibitionCondition",""\n'
                          f':END\n'
                          )

                utc_transitions.append(utc_trans)
                man_transitions.append(man_tr)

                # print(f'{j} >> {i}')
            num_transition += 1
    return utc_transitions, man_transitions


def make_dat_file_with_utc_and_man_transitions(path_to_dat_file, num_stages):
    path_to_new_dat = make_path_to_save_config(path_to_dat_file)

    all_va_transitions, all_ft_transitions = make_va_and_ft_transitions(path_to_dat_file)
    all_utc_transitions, all_man_transitions = make_utc_and_man_transitions(num_stages)

    num_transitions = (len(all_utc_transitions) + len(all_man_transitions) + len(all_va_transitions) +
                       len(all_ft_transitions))

    with open(path_to_dat_file, 'r') as file_from, open(path_to_new_dat, 'w') as file_to:
        flag = False
        for line in file_from:
            if not flag and ':TABLE "YSRM_UK_STAGE_TRANS"' not in line:
                file_to.write(line)

            if ':TABLE "YSRM_UK_STAGE_TRANS"' in line:
                flag = True
                file_to.write(f':TABLE "YSRM_UK_STAGE_TRANS",{num_transitions},8,4,4,4,4,4,10,10,10\n')

                for utc_tr, man_tr, va_tr, ft_tr in itertools.zip_longest(
                        all_utc_transitions, all_man_transitions, all_va_transitions, all_ft_transitions):
                    if utc_tr is not None:
                        file_to.write(utc_tr)
                    if man_tr is not None:
                        file_to.write(man_tr)
                    if va_tr is not None:
                        file_to.write(va_tr)
                    if ft_tr is not None:
                        file_to.write(ft_tr)
                continue

            if flag == True:
                pass

            if ':TABLE "YSRM_VPLAN_PARM"' in line:
                file_to.write(':END\n')
                file_to.write(line)
                flag = False


def range_for_label_new_greenroad(span=4):
    cnt = 0
    range_to_change_label = []
    while cnt < 60:
        range_to_change_label += list(range(cnt, cnt + span))
        cnt += span * 2
    return range_to_change_label

