import asyncio
import time

from sdp_lib.modbus.client import Modbus, AsyncModbus, create_bits_pattern
from sdp_lib.modbus.data_helpers import Description
from sdp_lib.modbus.fields import FieldNames


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


async def apolling(modbus: Modbus, delay: float):
    try:
        print(
            f'> Начинаю чтение DI по протоколу Modbus\nХост: {modbus.ipv4} Порт: {modbus.port}\n'
            f'> Для завершения нажмите Ctrl-C'
        )
        time.sleep(4)
        while True:
            await modbus.read_discrete_inputs_and_process()
            print(modbus.response_data or modbus.response_errors)
            await asyncio.sleep(delay)
    except KeyboardInterrupt:
        print('Останавливаю опрос')
    finally:
        print('Закрываю соединение...')
        modbus.client.close()
        print('Соединение закрыто')


if __name__ == '__main__':
    stage1 = Description('(Stage=1)', 1)
    stage4 = Description('(Stage=4)', 4)
    stage5 = Description('(Stage=5)', 5)
    stage7 = Description('(Stage=7)', 7)
    bit_states_to_description = {
        create_bits_pattern([0, 0, 0, 0, 1, 0, 1, 0]):                               stage1,
        create_bits_pattern([False, False, True, False, True, False, False, False]): stage4,
        create_bits_pattern([0, 0, 0, 1, 1, 0, 0, 0]):                               stage5,
        create_bits_pattern('00001100'):                                             stage7,
        FieldNames.ignored_bits: {4}
    }
    bit_address_to_description = {6: stage1, 2: stage4, 3: stage5, 5: stage7}
    # modbus_client = Modbus(ipv4=ip, port=port, bit_address_to_description=bit_to_description)
    # polling(modbus_client, 1)

    modbus_client = AsyncModbus(
        ipv4='91.227.113.186',
        port=502,
        matched_bit_states_to_description=bit_states_to_description,
        matched_bit_addr_to_description=bit_address_to_description
    )
    asyncio.run(apolling(modbus_client, 1))
