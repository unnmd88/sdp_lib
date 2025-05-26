content = """title = "Trap receiver configuration"

# Доступные типы контроллеров:
# Поток (S) -> Поток, протокол stcip
# Поток (P) -> Поток, протокол ug-405
# Swarco    -> Swarco, протокол stcip
# Peek      -> Peek, протокол ug-405


# Список списков интерфейсов для получения trap.
# Каждый вложенный список - один зарегистрированный интерфейс,
# где индекс 0 -> ip(строка), индекс 1 -> порт(целое число)
network_interfaces = [ ["192.168.45.248", 164] ]

# Community
community = [ ["public", "public"], ["UTMC", "UTMC"] ]

# Обработчики
[handlers]
# Если all_incoming_notifications установлен в true ->
# будут логгироваться в файл все входящие trap уведомления.
all_incoming_notifications = true
# Если stdout_incoming_notifications установлен в true ->
# в stdout будет выводиться входящее trap уведомление.
stdout_incoming_notifications = true
# Обработчики "cycles" - список вложенных списков,
# где у вложенного списка:
# index[0] = ip-addr (строка)
# index[1] = тип контроллера (строка)
# index[2] = стартовая фаза смены цикла (целое число)
cycles = [ ]
"""

def gen_default_cfg():
    with open('config.toml', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    gen_default_cfg()