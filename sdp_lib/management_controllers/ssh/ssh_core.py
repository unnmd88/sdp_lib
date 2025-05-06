import asyncio
import os
from typing import Self, Sequence
from collections import deque

import asyncssh
from asyncssh import SSHClientProcess

from sdp_lib.management_controllers.exceptions import ReadFromInteractiveShellError
from sdp_lib.management_controllers.fields_names import FieldsNames
from sdp_lib.management_controllers.hosts_core import Host
# from sdp_lib.management_controllers.parsers.parsers_swarco_ssh import process_stdout_instat
from sdp_lib.management_controllers.ssh.constants import (
    kex_algs,
    enc_algs,
    term_type,
    proc_ssh_encoding,
    itc_login,
    itc_passwd
)

from sdp_lib.management_controllers.ssh.swarco_terminal import (
    ItcTerminal,
    is_log_l2,
    get_commands_set_stage, login_commands, instat102_and_display, process_stdout_instat, process_terminal_stdout
)


FIELD_NAME               = 0
PROCESSING_STDOUT_METHOD = 0

async def read_timed(
    stream: asyncssh.SSHReader,
    timeout: float = .6,
    bufsize: int = 1024
) -> str:
    """
    Читает данные из потока вывода в течение установленного таймаута.
    :param stream: Поток обмена данными.
    :param timeout: Таймаут на чтение данных из потока в секундах.
    :param bufsize: Размер буфера в байтах.
    :return: Вывод данных в строковом представлении.
    """
    ret = ''
    print(f'in func read_timed')
    while True:
        try:
            ret += await asyncio.wait_for(stream.read(bufsize), timeout)
            ret = ret.replace('\u0000', '')
            # print(f'ret >>>> {ret}')
        except (asyncio.TimeoutError, asyncio.CancelledError):
            return ret
        # return ret

        # if cnt > 3 and not ret:
        #     raise ReadFromInteractiveShellError()


class SwarcoItcUserConnectionsSSH:
    """
    Класс ssh соединений.
    """
    def __init__(
            self,
            ip: str,
            connect_timeout: float = 20,
            login_timeout: float = 10,
            open_interactive_process_timeout: float = 2,
    ):
        self._ipv4 = ip
        self._connect_timeout = connect_timeout
        self._login_timeout = login_timeout
        self._open_interactive_process_timeout = open_interactive_process_timeout
        self._ssh_connection = None
        self._ssh_process = None
        self._last_conn_time = None
        self.command_timeout = .2
        self._connection_errors = deque(maxlen=1)

    async def create_connect(self) -> bool:
        """
        Создает ssh соединение.
        """
        try:
            self._ssh_connection = await asyncssh.connect(
                host=self._ipv4,
                username=itc_login,
                password=itc_passwd,
                options=asyncssh.SSHClientConnectionOptions(connect_timeout=self._connect_timeout,
                                                            login_timeout=self._login_timeout),
                kex_algs=kex_algs,
                encryption_algs=enc_algs,
                known_hosts=None,
            )
            return True
        except (OSError, asyncssh.Error):
            self.add_connection_error('SSH connection failed')
        return False

    async def create_proc(self):
        """
        Создает процесс оболочки shell.
        """
        try:

            self._ssh_process = await asyncio.wait_for(
                self._ssh_connection.create_process(
                    term_type=term_type,
                    encoding=proc_ssh_encoding,
                ),
                timeout=self._open_interactive_process_timeout
            )
            return True
        except (asyncio.TimeoutError, asyncio.CancelledError):
            return False

    def add_connection_error(self, error: str | Exception) -> str | Exception:
        """
        Добавляет ошибку в стек.
        :param error: Текст ошибки или экземпляр класса Exception.
        :return: Текст или экземпляр класса Exception, добавленной в стек.
        """
        self._connection_errors.append(error)
        return error

    def set_login_timeout(self, value: float) -> float:
        """
        Устанавливает таймаут для процесса логина при создании ssh-соединения.
        :param value: Значение в секундах.
        :return: Установленное значение.
        """
        if 0 < value < 60:
            self._login_timeout = value
        return self._login_timeout

    def set_connect_timeout(self, value: float) -> float:
        """
        Устанавливает таймаут для ssh-соединения.
        :param value: Значение в секундах.
        :return: Установленное значение.
        """
        if 0 < value < 60:
            self._connect_timeout = value
        return self._connect_timeout

    @property
    def ssh_connection(self):
        """
        Возвращает объект ssh-соединения.
        """
        return self._ssh_connection

    @property
    def ssh_process(self):
        """
        Возвращает объект процесса оболочки shell.
        """
        return self._ssh_process

    @property
    def stack_connection_errors(self) -> deque:
        """
        Возвращает стек ошибок.
        """
        return self._connection_errors

    def get_err_from_stack_or_none(self) -> str | Exception | None:
        """
        Достаёт последнюю справа ошибку из стека, если стек не пуст.
        :return: Последнюю справа ошибку из стека, если стек не пуст, иначе None
        """
        try:
            return self._connection_errors.pop()
        except IndexError:
            return None

    def write_to_shell(self, data: str) -> None:
        """
        Записывает данные в stdin сеанса интерактивной оболочки.
        :param data: Данные для записи в stdin.
        :return: None
        """
        self._ssh_process.stdin.write(f'{data}\n')

    async def write_and_read_shell(self, data: str, timeout: float = .6) -> str:
        """
        Записывает данные в stdin сеанса интерактивной оболочки и ожидает ответа.
        :param data: Данные для записи в stdin.
        :return: Stdout сеанса интерактивной оболочки.
        """
        self.write_to_shell(data)
        return await read_timed(self._ssh_process.stdout, timeout=timeout)

    async def check_connection_and_interactive_session(self) -> bool:
        """
        Проверяет состояние ssh-подключения и сеанса интерактивной оболочки.
        Сначала происходит проверка сеанса интерактивной оболочки. Если сеанс неактивен, пробует
        открыть новый сеанс. Если сеанс открыть не удается, инициирует новое ssh-соединение,
        затем пытается открыть сеанса интерактивной оболочки.
        :return: True, если соендинение утсановлено и сеанс интерактивной оболочки готов
                 для чтения и записи данных, иначе False.
        """
        ok = False
        try:
            self.write_to_shell(ItcTerminal.echo)
            r = await read_timed(self._ssh_process.stdout)
            if 'Ok' in r or 'ITC' in r:
                return True
        except (AttributeError, BrokenPipeError, ConnectionResetError):
            ok = False

        try:
            success = await self.create_proc()
            if success:
                r = await read_timed(self._ssh_process.stdout)
                if 'ITC' in r:
                    return True
        except (AttributeError, BrokenPipeError, ConnectionResetError):
            ok = False

        await self.create_connect()
        if self._connection_errors:
            return False

        success = await self.create_proc()
        if not success:
            self.add_connection_error('SSH connection failed')
            return False

        if self._connection_errors:
            return False

        r = await read_timed(self._ssh_process.stdout)
        print(f'r2: {r}')
        if 'ITC' in r:
            return True
        self.add_connection_error('AAAAAAAAAA!!!')
        return False


class SwarcoSSH(Host):

    protocol = FieldsNames.protocol_ssh

    def __init__(self, ip=None, host_id=None, driver: SwarcoItcUserConnectionsSSH = None):

        super().__init__(
            ipv4=ip, host_id=host_id, driver=driver
        )
        self._sent_commands = None
        self.pretty_output = None
        self.raw_stdout = None
        self.timeout = .2

    def create_and_set_driver(self):
        self.set_driver(SwarcoItcUserConnectionsSSH(self.ip_v4))

    async def check_ssh_session_with_interactive_shell_and_reconnect_if_need(
            self,
            add_err_to_response_data_if_has = True
    ) -> bool:
        """
        Проверяет соединение и сеанс интерактивной оболочки. Если соединение/сеанс
        неактивен, пробует переподключиться.

        :return: True, если соединение и сеанс интерактивной оболочки установлены
                 успешно, иначе False.
        """

        success_conn = await self.driver.check_connection_and_interactive_session()
        if not success_conn and add_err_to_response_data_if_has:
            self.add_data_to_data_response_attrs(self.driver.get_err_from_stack_or_none())
        return success_conn

    async def _send_commands(self, terminal_commands_entity):

        states = {}
        sent_commands = []
        self.raw_stdout = []
        self._sent_commands = []
        print(f'argsargs: {terminal_commands_entity}')
        for group_commands in terminal_commands_entity:
            for data in group_commands:
                print(f'data: {data}')
                command, need_processing = data
                try:
                    stdout = await self.driver.write_and_read_shell(command)
                    self.raw_stdout.append((command, stdout))
                    self._sent_commands.append(command)
                    if need_processing:
                        field_name, processed_data = process_terminal_stdout(command, stdout)
                        states[field_name] = processed_data

                except ReadFromInteractiveShellError as exc:
                    raise TypeError('ALARM! FAULT IN SENDING DATA TO SHELL')

                self.add_data_to_data_response_attrs(data={
                    'states_after_shell_session': states,
                    'sent_commands': self._sent_commands
                })



    def _add_to_send_varbinds_attr(self, *args):

        for data in args:
            self._varbinds_for_request.append(data)


    async def set_stage(self, stage: int) -> Self:

        success_conn = await self.check_ssh_session_with_interactive_shell_and_reconnect_if_need()
        if not success_conn:
            return self

        self._varbinds_for_request = []

        stdout = await self.driver.write_and_read_shell(ItcTerminal.instat102)
        if not is_log_l2(stdout):
            self._add_to_send_varbinds_attr((command, None) for command in login_commands)

        instat102_111_state = process_stdout_instat(stdout)[-1]

        stage_commands = get_commands_set_stage(stage, instat102_111_state)
        self._add_to_send_varbinds_attr(
            ((command, None) for command in stage_commands), instat102_and_display
        )
        await self._send_commands(self._varbinds_for_request)
        # for command in self._varbinds_for_request:
        #     r = await self.driver.write_and_read_shell(command)
        #     print(f'RRRR: {r:8}')

        # stdout = await self.driver.write_and_read_shell(ItcTerminal.instat102)
        #
        # print(f'process_stdout_instat(stdout): {process_stdout_instat(stdout)}')
        # self.add_data_to_data_response_attrs(data={'stdout': process_stdout_instat(stdout)})
        return self


        # self._varbinds_for_request = [(comm, False) for comm in swarco_terminal.get_commands_set_stage(stage)]

        # for comm in instat_start_102_and_display_commands:
        #     self._varbinds_for_request.append((comm, True))
        # return await self.main_send_commands()



"""" Archive """
# class SwarcoSSH(Host):
#
#     protocol = FieldsNames.protocol_ssh
#
#     def __init__(self, ip=None, host_id=None, driver: SSHClientConnection =None, process=None):
#
#         super().__init__(
#             ipv4=ip, host_id=host_id, driver=driver
#         )
#         self._ssh_process: SSHClientProcess = process
#         self._success_conn_time = None
#         self.pretty_output = None
#         self.raw_stdout = None
#         self.timeout = .2
#
#     async def create_connect(self, connect_timeout: float = 10, login_timeout: float = 10) -> bool:
#         try:
#             self._driver = await asyncssh.connect(
#                 host=self._ipv4,
#                 username=itc_login,
#                 password=itc_passwd,
#                 options=asyncssh.SSHClientConnectionOptions(connect_timeout=connect_timeout,
#                                                             login_timeout=login_timeout),
#                 kex_algs=kex_algs,
#                 encryption_algs=enc_algs,
#                 known_hosts=None,
#             )
#             SWARCO_SSH_CONNECTIONS[self.ip_v4] = self
#             return True
#         except (OSError, asyncssh.Error):
#             self.add_data_to_data_response_attrs('SSH connection failed')
#         return False
#
#     async def create_proc(self):
#         self._ssh_process = await self._driver.create_process(
#             term_type=term_type,
#             encoding=proc_ssh_encoding,
#         )
#
#     # async def _send_commands(self, commands, parse=False):
#     #
#     #     for command in commands:
#     #         self._ssh_process.stdin.write(f'{command}\n')
#     #         try:
#     #             command_response = await read_timed(self._ssh_process.stdout, timeout=.5, bufsize=4096)
#     #             self.raw_stdout.append((command, command_response))
#     #         except ReadFromInteractiveShellError as exc:
#     #             self.add_data_to_data_response_attrs(exc)
#     #             break
#
#     async def main_send_commands(self) -> typing.Self:
#         """
#
#         :param commands: Список комманд, которые будут отправлены в shell
#         :return: errorIndication, stdout(вывод сеанса shell)
#         """
#
#         print(self._varbinds_for_request)
#         self.last_response = []
#         self.raw_stdout = []
#         try:
#             self._driver = await self.create_connect()
#             self._ssh_process = await self.create_proc(self._driver)
#             await read_timed(self._ssh_process.stdout, timeout=.8, bufsize=4096)
#             await self._send_commands(*self._varbinds_for_request)
#
#             # self.add_data_to_data_response_attrs(data={'pretty_output': self.last_response,
#             #                                            'raw_output': self.raw_stdout})
#         except (OSError, asyncssh.Error):
#             self.add_data_to_data_response_attrs('SSH connection failed')
#         finally:
#             # self._ssh_process.close()
#             # self._ssh_process.terminate()
#             # await self._ssh_process.wait()
#             # await self._driver.wait_closed()
#             # self._driver = None
#             # self._ssh_process = None
#             print(f'self.last_response send_commands4: {self.last_response}')
#         return self
#
#     async def _send_commands(self, *args):
#
#         last_states = {}
#         sent_commands = []
#         print(f'argsargs: {args}')
#         for command, need_processing in args:
#             self._ssh_process.stdin.write(f'{command}\n')
#             sent_commands.append(command)
#
#             try:
#                 stdout = await read_timed(self._ssh_process.stdout, timeout=.5, bufsize=4096)
#                 self.raw_stdout.append((command, stdout))
#
#                 if need_processing:
#                     field_name, processed_data = parsers_swarco_ssh.process_terminal_stdout(command, stdout)
#                     last_states[field_name] = processed_data
#
#             except ReadFromInteractiveShellError as exc:
#                 self.add_data_to_data_response_attrs(exc)
#                 break
#
#             # self.add_data_to_data_response_attrs(data={'raw_response': self.raw_stdout})
#             if last_states:
#                 self.add_data_to_data_response_attrs(data={'states_after_shell_session': last_states})
#
#
#     # async def _check_connection_and_interactive_session(self) -> bool:
#     #     print(f'self.driver: {self.driver}')
#     #     print(f'self.process: {self.process}')
#     #     skip_check_interactive_shell = False
#     #     if not self._driver or isinstance(self._driver, SSHClientConnection) and self._driver.is_closed():
#     #         await self.create_connect()
#     #         if self.response_errors:
#     #             return False
#     #         await self.create_proc()
#     #         stdout = await read_timed(self._ssh_process.stdout)
#     #         if 'ITC' not in stdout:
#     #             self.add_data_to_data_response_attrs('<SSH connection failed>')
#     #             return False
#     #
#     #         skip_check_interactive_shell = True
#     #
#     #     if not skip_check_interactive_shell:
#     #         shell_is_active = await self._check_interactive_session()
#     #         if not shell_is_active:
#     #             self.add_data_to_data_response_attrs('SSH connection failed!!')
#     #             return False
#     #
#     #     return True
#
#     def write_to_shell(self, data):
#         self.process.stdin.write(f'{data}\n')
#
#     async def write_and_read_shell(self, data: str) -> str:
#         self.write_to_shell(data)
#         return await read_timed(self.process.stdout, timeout=.4)
#
#     async def check_connection_and_interactive_session(self, timeout=.4) -> bool:
#         print(f'self.driver: {self.driver}')
#         print(f'self.process: {self.process}')
#         ok = False
#         try:
#             self.write_to_shell(ItcTerminal.echo)
#             r = await read_timed(self._ssh_process.stdout, timeout=timeout)
#             if 'Ok' in r or 'ITC' in r:
#                 return True
#         except (AttributeError, BrokenPipeError, ConnectionResetError):
#             ok = False
#
#         try:
#             await self.create_proc()
#             r = await read_timed(self._ssh_process.stdout, timeout=timeout)
#             if 'ITC' in r:
#                 return True
#         except (AttributeError, BrokenPipeError, ConnectionResetError):
#             ok = False
#
#         await self.create_connect()
#         await self.create_proc()
#
#         if self.response_errors:
#             return False
#
#         r = await read_timed(self._ssh_process.stdout, timeout)
#         print(f'r2: {r}')
#         if 'ITC' in r:
#             return True
#         self.add_data_to_data_response_attrs('AAAAAAAAAA!!!')
#         return False
#
#     async def set_stage(self, stage: int):
#
#         success_conn = await self.check_connection_and_interactive_session()
#         if not success_conn:
#             print(f'if not success_conn: {success_conn}')
#             return self
#
#         stdout = await self.write_and_read_shell(ItcTerminal.instat102)
#
#         self._varbinds_for_request = [str(ItcTerminal.lang_uk), str(ItcTerminal.l2_login,), str(ItcTerminal.l2_pass)]
#         for num, inp_state in enumerate(process_stdout_instat(stdout)[-1], 1):
#             if num == 1 and inp_state == '0':
#                 self._varbinds_for_request.append(get_inp_command('102', '1'))
#
#         for command in self._varbinds_for_request:
#             r = await self.write_and_read_shell(command)
#             print(f'RRRR: {r:8}')
#
#
#         print(f'process_stdout_instat(stdout): {process_stdout_instat(stdout)}')
#         print(f'list(process_stdout_instat(stdout)): {list(process_stdout_instat(stdout)[-1])}')
#         self.add_data_to_data_response_attrs(data={'stdout': process_stdout_instat(stdout)})
#         return self
#
#
#         # self._varbinds_for_request = [(comm, False) for comm in swarco_terminal.get_commands_set_stage(stage)]
#
#         # for comm in instat_start_102_and_display_commands:
#         #     self._varbinds_for_request.append((comm, True))
#         # return await self.main_send_commands()
#
#     @property
#     def process(self) -> SSHClientProcess:
#         return self._ssh_process



async def main():
    connectt =None

    try:
        connectt = await asyncssh.connect(
            host='10.45.154.18',
            username=itc_login,
            password=itc_passwd,
            options=asyncssh.SSHClientConnectionOptions(login_timeout=10, connect_timeout=6),
            kex_algs=kex_algs,
            encryption_algs=enc_algs,
            known_hosts=None,
        )
        procx = await connectt.create_process(
            term_type=term_type,
                encoding=proc_ssh_encoding,)
        r = await read_timed(procx.stdout, timeout=.8, bufsize=4096)
        print(f'read_timed r :: {r}')
        rr = None
        while True:
            commands = input()
            if commands == 'stop':
                break

            commands = commands.split(';')
            for command in commands:
                procx.stdin.write(f'{command}\n')
                rr = await read_timed(procx.stdout, timeout=.5, bufsize=4096)
            print(f'read_timed rr :: {rr}')
            print('****' * 20)

        print(f'procx.stdout: {procx}')
        print(f'procx.stdout: {procx.stdout}')
        print('****' * 20)
        procx.kill()
        await procx.wait()

        procx = await connectt.create_process(
            term_type=term_type,
                encoding=proc_ssh_encoding,)
        await read_timed(procx.stdout, timeout=.8, bufsize=4096)

        print(f'procx.stdout: {procx.stdout}')
        print(f'procx.stdout: {procx}')
        print('****' * 20)


        print(f'connectt.is_closed(): {connectt.is_closed()}')
    except ValueError as exc:
        print(f'exc: + {exc}')
    finally:
        pass
        # await connectt.wait_closed()
    await asyncio.sleep(2)
    print(f'connectt: {connectt}')
    print(f'connectt.is_closed(): {connectt.is_closed()}')

    # obj = SwarcoSSH()
    # obj.set_ipv4('10.179.108.177')
    # await obj.create_connection()
    # await obj.create_process()



    # await obj.send_commands2(['lang UK', 'l2', '2727','SIMULATE DISPLAY --poll'])
    #
    # print(f'obj.last_response: {obj.last_response}')
    # to_write = obj.last_response.encode(stdout_encoding).decode(stdout_decoding)
    # print(f'type (obj.last_response): {type(to_write)}')
    # with open('swarco_ssh_stdout.txt', 'w') as f:
    #     f.write(to_write)
if __name__ == '__main__':
    asyncio.run(main())




