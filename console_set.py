# -*- coding: utf-8 -*-

import telnetlib
import time
from PyQt5 import QtCore
from concurrent.futures import ThreadPoolExecutor
import telnetlib
import re

from PyQt5.QtCore import pyqtSignal


def to_bytes(line):
    return f"{line}\n".encode("utf-8")

class ConsoleThread(QtCore.QThread):

    stop_signal = QtCore.pyqtSignal(bool)

    def __init__(self, host, data):
        super(ConsoleThread, self).__init__()
        self.host = host
        self.type_connect = data['type_connect']
        self.login = data['login']
        self.password = data['password']
        self.operType = data['operType']
        self.file_name = data['file_name']
        self.script_text = data['script_text']
        print("Закончии инициализации функции прописки")
        print(f'''перед запускомм
                один host= {self.host} 
                type_connect={self.type_connect}
                login={self.login}
                password={self.password}
                operType={self.operType}
                file_name={self.file_name}
                data ={self.script_text}
                ''')
        self.stop_signal = False

    def stop(self):
        self.stop_signal = True
        # self.start_signal.emit(False, self.file_name, self.operType)
        print("Стоп прописки")

    def run(self):
        try:
            # Ваш код выполнения console_process для одного host
            result = self.console_process(self.host, self.type_connect, self.operType)
            # self.start_signal.emit(False, self.host, self.operType)
            print(result)
        except Exception as e:
            print(f'Ошибка в мультипотоке: {e}')

    def console_process(self, host, type_connect, operType):
        print(f"тут будем запускать библиотеку {type_connect} для подключения к хосту- {host} для задачи= {operType}")
        connect_result = self.connect_telnetlib(host)
        if connect_result != None:
            self.check_model_kom(host, connect_result)
            self.check_hostname(host)
            if operType == "Настройка коммутатора":
                print("Настройка коммутатора")
                self.write_swich_full(host)
            elif operType in ['msText', 'edit_msText', 'msText+var']:
                self.write_manual_script(host, operType)

    def write_manual_script(self, host, operType):
        print(f"дошли до for text, смотрим data={self.script_text}")
        for line in self.script_text:
            print(f"дошли после for text, line={line}")
            self.tn_lib.write(to_bytes(line + "\r"))
            time.sleep(1)
            all_result = self.tn_lib.read_very_eager().decode('utf-8')
            # self.Wind_Log.TxtBr_Wind_Log.append(all_result) #Потом сигналом вырулим логи
            print(all_result)

    def write_swich_full(self, host):
        print(self.equipment_definition['model'])

        # global selected_model, HostName

        if self.equipment_definition['model'] in ["T2700G-28TQ 4.0", "T2700G-28TQ 2.20", "T2600G-28TS-DC",
                                                        "T2600G-28TS 4.0"]:
            print("будем писать тп-линк")
            # config_tp_link()
        elif self.equipment_definition['model'] in ["DES-3200-26", "DES-3028", "DES-1210-28/ME", "DES-1228/ME"]:
            print("будем писать Д-линк")
            # config_d_link()
        else:
            print("ничего не найдено")

    def connect_telnetlib(self, host):
        # self.Wind_Log.TxtBr_Wind_Log.append("Connect to:" + host)
        print("Connect to:", host)
        # здесь впихнем пинговалку что бы проверялся хост перед подключением
        try:
            self.tn_lib = telnetlib.Telnet(host)
            time.sleep(2)
            all_result = self.tn_lib.read_very_eager().decode('utf-8')
            print(all_result)
            return all_result.split()
        except Exception as e:
            print(f"Проблема при подключении к хосту {host}, ошибка= {e}")
            return None

    def check_model_kom(self, host, connect_result):
        print(f"Дошли до определения модели connect_result= {connect_result}")

        for check_model in connect_result:

            # DES-3200-26------------------------------
            if check_model in (
            "DES-3200-26", "DES-3028", "DES-1210-28/ME", "DES-1228/ME", "DGS-3420-28SC", "DGS-3420-26SC",
            "DGS-3620-28SC"):
                self.equipment_definition = {'vendor': "d-link"}
                # selected_model = check_model
                # self.Wind_Log.TxtBr_Wind_Log.append('D-link обнаружен БИ-Бу-БИП')
                # self.Wind_Log.TxtBr_Wind_Log.append(selected_model)
                # if self.CB_enter_pass.isChecked():
                #     tn_lib.write(b"admin\n\r")
                #     tn_lib.write(to_bytes(admin_pass + "\r"))
                # else:
                self.tn_lib.write(to_bytes(user.strip()))
                self.tn_lib.write(to_bytes(password.strip()))
                self.tn_lib.write(b"\n")
                while True:
                    line = tn_lib.read_until(b"\r")  # Check for new line and CR
                    # line = re.split(r':', line.decode('ISO-8859-1'))

                    if (' '.join(re.findall(selected_model, line.decode('ISO-8859-1')))) in line.decode(
                            'ISO-8859-1'):
                        print("line= " + line.decode('ISO-8859-1'))
                        # if selected_model in line:  # If last read line is the prompt, end loop
                        print("Авторизация прошла")

                        break
                    elif "Fail!" in line.decode('ISO-8859-1'):
                        # self.Wind_Log.TxtBr_Wind_Log.append("Ошибка авторизации")
                        print("Ошибка авторизации")
                        break
                self.tn_lib.write(b"enable admin\n")
                self.tn_lib.read_until(b"enable admin\n")
                # self.Wind_Log.TxtBr_Wind_Log.append("Авторизация прошла")
                self.tn_lib.write(b"\n")

            # TP-link ------------------------------
            elif check_model == "*****************":
                self.equipment_definition = {'vendor': "tp-link"}
                self.check_tp_link(host, self.login, self.password)
            # Huawei ------------------------------
            elif check_model == "Warning:":
                self.equipment_definition = {'vendor': "huawei"}
                # self.Wind_Log.TxtBr_Wind_Log.append('HUAWEI')
                # if self.CB_enter_pass.isChecked():
                #     tn_lib.write(b"admin\n\r")
                #     tn_lib.write(to_bytes(admin_pass + "\r"))
                # else:
                self.tn_lib.write(to_bytes(user.strip()))
                self.tn_lib.read_until(b"Password:")
                self.tn_lib.write(to_bytes(password.strip()))
                self.tn_lib.write(b"system-view\n\r")
                while True:
                    line = self.tn_lib.read_until(b"\r")
                    if "Error:" in line.decode('ISO-8859-1'):
                        print("Проверьте данный для авторизации")
                        # self.Wind_Log.TxtBr_Wind_Log.append('Проверьте логин/пароль')
                        tn_lib.close()
                        break
                    HostName = ' '.join(re.findall(r"<.*>", line.decode('ISO-8859-1')))
                    HostName = HostName.strip("<>")
                    print("До ИФ= " + str(HostName))
                    print("line= " + str(line))
                    # find = re.search(r''+HostName+'', line.decode('ISO-8859-1'))
                    # print("find= " + str(find))
                    # print("HostName= "+HostName.strip("<>"))
                    # print("find1= " + str(find))
                    if HostName != "":
                        if str(HostName) in line.decode('ISO-8859-1'):
                            print("Прошли ИФ0= " + line.decode('ISO-8859-1'))
                            print("Прошли ИФ= " + str(HostName))
                            break

                self.tn_lib.write(b"display version\n\r")
                time.sleep(1)
                all_result = self.tn_lib.read_very_eager().decode('utf-8')
                self.model_result[host] = all_result.split()
                for check_model in self.model_result[host]:
                    # S2320-28TP-EI-AC - 4 гигабитных  порта------------------------------
                    if check_model == "S2320-28TP-EI-AC":
                        selected_model = check_model
                    # S2350-28TP-EI-AC - 8гигабитных портов ------------------------------
                    elif check_model == "S2350-28TP-EI-AC":
                        selected_model = check_model
                    # S5320-28TP-LI-AC 28гигабитных ----------------------------------
                    elif check_model == "S5320-28TP-LI-AC":
                        print("Дошли до проверки модели " + check_model)
                        selected_model = check_model
                    # S5320-28P-LI-AC дальше 2 варианта ------------------------------
                    elif check_model == "S5320-28P-LI-AC":
                        # text_first_win.insert(1.0, check_model + "\n")
                        self.tn_lib.write(b"display interface brief\n\r")
                        self.tn_lib.write(b" \n\r")
                        time.sleep(2)
                        all_result = self.tn_lib.read_very_eager().decode('utf-8')
                        self.model_result[host] = all_result.split()
                        for check_model in self.model_result[host]:
                            print(check_model)
                            if check_model == "GigabitEthernet0/0/28":
                                selected_model = "S5320-28P-LI-AC 28 1g"
                            elif check_model == "XGigabitEthernet0/0/4":
                                selected_model = "S5320-28P-LI-AC 24 1g +4 10g"
                # self.Wind_Log.TxtBr_Wind_Log.append(selected_model)

            # ZTE
            elif check_model == "2928E":
                self.equipment_definition = {'vendor': "ZTE"}
                selected_model = check_model
                self.Wind_Log.TxtBr_Wind_Log.append('ZTE')
                self.Wind_Log.TxtBr_Wind_Log.append('2928E')
            # Брас
            elif check_model == "ER-Telecom.":
                elf.equipment_definition = {'vendor': "alcatel"}
                self.Wind_Log.TxtBr_Wind_Log.append('Alcatel')
                tn_lib.write(to_bytes(user.strip()))
                tn_lib.read_until(b"Password:")
                tn_lib.write(to_bytes(password.strip()))
                while True:
                    line = tn_lib.read_until(b"\r")
                    print(line)

                print("Нашли алкатель")
        # Перенесем авторизацию и вход в режим конфига для d-link сюда чтобы подпись порта работала отдельно от остального тела.

    def check_tp_link(self, host, user, password):
        # Возможно будет доп аргумент task и Type чтобы использовать консоль и другие библлиотеки
        self.tn_lib.write(to_bytes(user.strip() + "\r"))
        self.tn_lib.write(to_bytes(password.strip() + "\r"))
        self.tn_lib.write(b"enable\n\r")
        while True:
            line = self.tn_lib.read_until(b"\n\r")
            print(f'line= {line}')
            line = line.decode('ISO-8859-1')
            if " Login invalid." in line:
                print("Проверьте данный для авторизации")
                # self.Wind_Log.TxtBr_Wind_Log.append('Проверьте логин\пароль')
                self.tn_lib.close()
                break
            if ">" in line:
                print("> нашли - авторизация на тп-линк прошла")
                break
        self.tn_lib.write(b"\n\r")
        self.tn_lib.write(b"show system-info\n\r")
        time.sleep(1)
        all_result = self.tn_lib.read_very_eager().decode('utf-8')
        for line in all_result.split('\n'):
            print(f'перебор all_result= {line}')
            if 'System Name' in line:
                self.equipment_definition.update({'host_name': ''.join(re.findall(r'-\s*(.*)\r', line))})
                print(f'host_name = {self.equipment_definition["host_name"]}')
            if 'Hardware Version' in line:
                self.equipment_definition.update({'model': ''.join(re.findall(r'-\s*(\S.*)\r', line))})
                print(f'model= {self.equipment_definition["model"]}')
            if 'Software Version' in line:
                self.equipment_definition.update({'firmware': ''.join(re.findall(r'-\s*(.*)\r', line))})
                print(f'firmware= {self.equipment_definition["firmware"]}')
            if 'Mac Address' in line:
                self.equipment_definition.update({'mac': ''.join(re.findall(r'-\s*(.*)\r', line))})
                print(f'Mac Address = {self.equipment_definition["mac"]}')
            if 'Serial Number' in line:
                self.equipment_definition.update({'sn': ''.join(re.findall(r'-\s*(.*)\r', line))})
                print(f'Serial Number = {self.equipment_definition["sn"]}')
        # self.Wind_Log.TxtBr_Wind_Log.append(selected_model)
        ####print("Далее определяем hostname")

    def check_hostname(self, host):
        try:
            print(f'host_name = {self.equipment_definition["host_name"]}')
        except:
            print("host_name нет, нужно определять хост в зависимости от vendor")
            if self.equipment_definition['vendor'] == "tp-link":
                print(f"дошли до определения хостнейм")
                while True:
                    self.tn_lib.write(b"\n\r")
                    line = self.tn_lib.read_until(b"\r")
                    HostName = ' '.join(re.findall(r".*#", line.decode('ISO-8859-1')))
                    print("Hostname= " + str(HostName))
                    HostName = HostName.strip("#")
                    print("Hostname= " + str(HostName))
                    if HostName != "":
                        if str(HostName) in line.decode('ISO-8859-1'):
                            print("Прошли ИФ0= " + line.decode('ISO-8859-1'))
                            print("Прошли ИФ= " + str(HostName))
                            break



