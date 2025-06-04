import time

from sdp_lib.modbus.client import Modbus


def polling(modbus: Modbus, delay: float):
    try:
        print(
            f'Начинаю чтение DI по протоколу Modbus\nХост: {modbus.ipv4} Порт: {modbus.port}\n'
            f'Для завершения нажмите Ctrl-C'
        )
        time.sleep(4)
        while True:
            modbus.read_discrete_inputs_and_process()
            print(modbus.response_data or modbus.response_errors)
            time.sleep(delay)
    except KeyboardInterrupt:
        print('Останавливаю опрос')
    finally:
        print('Закрываю соединение...')
        modbus.client.close()
        print('Соединение закрыто')


if __name__ == '__main__':
    ip = '91.227.113.186'
    port = 502
    bit_to_description = {6: '(Stage=1)', 2: '(Stage=4)', 3: '(Stage=5)', 5: '(Stage=7)'}
    modbus_client = Modbus(ipv4=ip, port=port, bit_address_to_description=bit_to_description)
    polling(modbus_client, 1)

