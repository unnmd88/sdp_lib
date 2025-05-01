"""
Модуль для получения данных из конфигурации, а также формирования нового файла
конфигурации ITC-PC контроллера Swarco
"""

import os
from datetime import datetime
from io import BytesIO
from typing import Generator
import enum

from xml.etree import ElementTree as ET


class NamesForSwarcoXML(enum.Enum):
    BASE = 'base'
    GENERAL = 'general'
    GROUPS = 'groups'
    INTERGREEN = 'intergreen'
    ITC_PC_CONFIG = 'itcpc-config'
    CONFLICTS_F006 = 'conflicts_f006'
    INSTRUCTIONS = 'instructions'
    DEFINITIONS = 'definitions'
    CONTROL_BLOCKS = 'control-blocks'
    DETECTOR_LOGICS = 'detector-logics'


class SwarcoParseConfigXML:
    xml_itc_config_name = 'itc-config.xml'

    def __init__(self, source: str | BytesIO):
        self.source = source
        self.tree = ET.parse(source)
        self.root = self.tree.getroot()
        self.general_intersection_data = None

    def __eq__(self, other):
        return self.source == other.source

    @staticmethod
    def set_curr_datetime() -> str:
        # self.request_time = datetime.today().strftime("%Y-%m-%d %H:%M:%S")
        return datetime.today().strftime("%Y-%m-%d %H-%M-%S")

    # def _create_property(self):
    #
    #     for el in self.root.iter():
    #         # print(el.tag, el.attrib)
    #         if el.tag == 'general':
    #             if not el.attrib.get('control-blocks'):
    #                 continue
    #             self.create_general_attribs(el.attrib)
    #         elif el.tag == 'itcpc-config':
    #             self._main_config = el.text
    #         elif el.tag == 'intergreen':
    #             self._matrixF006 = self.create_matrix_F006(el)
    #         elif el.tag == 'instructions':
    #             self._cb_instructionsF016 = self.create_instructions(el)
    #             # for instruction in self.create_instructions2(el):
    #             #     print(instruction)
    #             #     pass
    #         elif el.tag == 'definitions':
    #             self._definitionsF015 = self.create_definitions(el)
    #             # for definition in self.create_definitions(el):
    #             #     print(definition)
    #             #     pass

    def parser(self, tag_names: list[str]) -> list[ET.Element | None]:

        matches = {
            val: i for i, val in enumerate(tag_names)
        }
        result = [None for _ in range(len(tag_names))]
        # print(matches)
        # print(result)
        self.general_intersection_data = {}
        flag_found_general_intersection_data = False
        for el in self.root.iter():
            if not tag_names and flag_found_general_intersection_data:
                return result
            if el.tag == NamesForSwarcoXML.GENERAL.value:
                self.general_intersection_data |= el.attrib
                flag_found_general_intersection_data = True
                continue
            if NamesForSwarcoXML.CONFLICTS_F006.value in tag_names:
                if el.tag == NamesForSwarcoXML.INTERGREEN.value and not el.attrib:
                    # print(el.tag, el.attrib)
                    result[matches.get(NamesForSwarcoXML.CONFLICTS_F006.value)] = el
                    tag_names.remove(NamesForSwarcoXML.CONFLICTS_F006.value)
                    continue
            if el.tag in tag_names:
                result[matches.get(el.tag)] = el
                tag_names.remove(el.tag)
        return result

    # def create_general_attribs(self, attrs):
    #     self._general_attribs = attrs
    #     # print(self._general_attribs)
    #     self._num_groups = self._general_attribs['groups']
    #     # print(self._num_groups)
    #     self._num_control_blocks = self._general_attribs['control-blocks']
    #     # print(self._num_control_blocks)
    #     self._num_detector_logics = self._general_attribs['detector-logics']
    #     # print(self._num_detector_logics)

    def create_matrix_F006(self, intergreen_tag=None, add_dict_matrix=False) -> tuple:
        """
        Формирует матрицу конфликтов на оаснове self.root и записывает её в self.conflict_matix
        :return:
        """

        # print(f'--intergreen tag before = {intergreen_tag}')
        if not intergreen_tag:
            intergreen_tag = self.parser([NamesForSwarcoXML.CONFLICTS_F006.value])[0]
            if not intergreen_tag:
                raise ValueError
        # print(f'--intergreen tag after = {intergreen_tag}')
        num_groups = int(self.general_intersection_data.snmp_get(NamesForSwarcoXML.GROUPS.value))
        # print(f'--num_groups after = {num_groups}')

        not_confl, matrix_dict = '  -  . ;', None
        if add_dict_matrix:
            matrix_dict = {
                str(k + 1): [not_confl if i != k else "X;" for i in range(num_groups)]
                for k in range(num_groups)
            }
        matrix_lst = [
            [not_confl if i != k else "X;" for i in range(num_groups)] for k in range(num_groups)
        ]

        for el in intergreen_tag:
            # print(el.tag, el.attrib)
            curr_group = str(int(el.attrib.get('no')))
            for child in el:
                # print(f'curr_group: {curr_group}')
                # print(child.tag, child.attrib)
                num_enemy_gr, confl_val = (child.attrib.get('value').split('-', maxsplit=1))
                num_enemy_gr = str(int(num_enemy_gr))
                # print(f'num_enemy_gr {num_enemy_gr} | confl_val {confl_val}')
                if num_enemy_gr == '0' or confl_val == '00-00.0':
                    continue
                if matrix_dict:
                    matrix_dict.get(curr_group)[int(num_enemy_gr) - 1] = f'{confl_val};'
                matrix_lst[int(curr_group) - 1][int(num_enemy_gr) - 1] = f'{confl_val};'
        # print(matrix)
        # for m, v in matrix.items():
        #     print(f'gr {m}: {v}')
        # for i, m in enumerate(mtrx):
        #     print(f'i {i}:  {m}')
        # for x in zip(*mtrx):
        #     print(list(x))
        return matrix_lst, matrix_dict

    def create_definitions(self, definitions_tag=None) -> Generator:
        """
        Генератор, перебирает значения для F015(Определения)
        :return: None
        """

        if not definitions_tag:
            definitions_tag = self.parser([NamesForSwarcoXML.DEFINITIONS.value])[0]
            if not definitions_tag:
                raise ValueError

        empty_defin = {'00-000-000', '000'}
        for defin in definitions_tag:
            # print(defin.tag, defin.attrib)
            attr = defin.attrib.get('value') or defin.attrib.get('input')
            if not attr:
                continue
            yield f'{attr};' if attr and (attr not in empty_defin) else ';'

    def create_instructions(self, instructions_tag=None, option_put_to_dict=False) -> Generator:

        if not instructions_tag:
            instructions_tag = self.parser([NamesForSwarcoXML.INSTRUCTIONS.value])[0]
            if not instructions_tag:
                raise ValueError

        all_control_blocks = {} if option_put_to_dict else option_put_to_dict
        for block in instructions_tag:
            _curr_num_control_block = block.attrib.get('no')
            _name, _enable, _signal = block.attrib.get('name'), block.attrib.get('enable'), block.attrib.get('signal')

            _name = f"{_name}{' ' * (20 - len(_name))};"
            _enable = f"{_enable if _enable != '0' else ''};"
            _signal = f"{_signal if _signal != '00-000-000' else ''};"

            # print(block.tag, block.attrib)
            instructions = [
                f"{ins.attrib.get('value') if ins.attrib.get('value') != '00-00-000' else ''};" for ins in block
            ]
            if option_put_to_dict:
                all_control_blocks[_curr_num_control_block] = "".join([_name, _enable, _signal] + instructions)
                yield all_control_blocks
            yield "".join([_name, _enable, _signal] + instructions)


    def repair_string(self, string: str, m_split: int = None):

        content = string.split(';', maxsplit=m_split)
        # print(content)
        repaired_content = ''
        for c in content[:-1]:
            c = c.replace(' ', '')
            # print(f'c after replace: {c}')
            repaired_content += f"{c}{' ' * (20 - len(c))};"
            # print(f'repaired_content +=: {repaired_content}')
        # print(repaired_content + content[-1])
        return repaired_content + content[-1]

    def check_created_file(self, filemane):
        if os.path.exists(filemane):
            return True
        return False

    def create_PTC2(self, filename) -> tuple:

        main_config_elem, matrixF006_elem, definitionsF015_elem, cb_instructionsF016_elem = self.parser(
            [
                NamesForSwarcoXML.ITC_PC_CONFIG.value, NamesForSwarcoXML.CONFLICTS_F006.value,
                NamesForSwarcoXML.DEFINITIONS.value, NamesForSwarcoXML.INSTRUCTIONS.value
            ]
        )

        filename = f"{filename}/{self.general_intersection_data.snmp_get('intersection')} {self.set_curr_datetime()}.PTC2"
        with open(filename, 'w') as file:
            head_Work006 = 'NewSheet  : Work.006'
            head_Work015 = 'NewSheet693  : Work.015'
            head_Work016 = 'NewSheet693  : Work.016'
            NeXt = 'NeXt'
            Work007, Work012, Work017, Work999 = 'Work.007', 'Work.012', 'Work.017', 'Work.999'
            flag_det_logics = flagWork999 = False
            # print(main_config_elem.text.splitlines())
            for line in main_config_elem.text.splitlines(keepends=True):
                if Work012 in line:
                    flag_det_logics = True
                if flag_det_logics and NeXt in line:
                    flag_det_logics = False
                if Work999 in line:
                    flagWork999 = True
                if flagWork999 and NeXt in line:
                    flagWork999 = False

                if Work007 in line:
                    file.write(f"{head_Work006}")
                    for ln in zip(*self.create_matrix_F006(matrixF006_elem)[0]):
                        file.write(f"\n{''.join(list(ln))}")
                    file.write(f"\nNeXt\n")
                elif Work017 in line:
                    file.write(f"{head_Work015}\n")
                    for ln in self.create_definitions(definitionsF015_elem):
                        file.write(f"{ln}")
                    file.write(f"\nNeXt\n{head_Work016}")
                    for ln in self.create_instructions(cb_instructionsF016_elem):
                        file.write(f"\n{ln}")
                    file.write(f"\nNeXt\n")

                if flag_det_logics and Work012 not in line:
                    line = self.repair_string(line, m_split=1)
                if flagWork999 and Work012 not in line:
                    line = self.repair_string(line, m_split=3)
                file.write(f'{line}')

        if not os.path.exists(filename):
            raise FileNotFoundError('errors when creating .PTC2 file')
        return None, [filename, self.general_intersection_data]

