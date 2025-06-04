import time

from sdp_lib.modbus.client import Modbus


def polling(modbus: Modbus, delay: float):
    pass


if __name__ == '__main__':
    ip = '91.227.113.186'
    port = 502
    bit_to_description = {6: '(Stage=1)', 2: '(Stage=4)', 3: '(Stage=5)', 5: '(Stage=7)'}
    modbus_client = Modbus(ipv4=ip, port=port, bit_address_to_description=bit_to_description)
    polling(modbus_client, 1)

