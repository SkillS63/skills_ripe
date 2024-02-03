# -*- coding: utf-8 -*-
from scapy.all import *
from pythonping import ping
from PyQt5 import  QtCore
from time import strftime
import csv

from concurrent.futures import ThreadPoolExecutor

class PingThread_multiprocessing(QtCore.QThread):
    multiproc_ping_signal = QtCore.pyqtSignal(bool)
    stop_signal = QtCore.pyqtSignal(bool)
    multiproc_check_host_signal = QtCore.pyqtSignal(dict, object)

    def __init__(self, data):
        super(PingThread_multiprocessing, self).__init__()
        self.data = data
        self.resulPingFile=str(strftime("%Y-%m-%d_%H=%M=%S--") + self.data["name_file"][
                                                          2:] + ".csv")
        self.opertType = data['operType']
        self.stop_signal = False

    def run(self):
        if self.data == "":
            print("Список IP-адресов пуст.")
        else:
            try:
                with ThreadPoolExecutor() as executor:
                    while not self.stop_signal:
                        for ip_address in self.data["list_ip"]:
                            if self.stop_signal:
                                break

                            future = executor.submit(self.ping_process, ip_address)
                            result = future.result()
                            if self.opertType == "_check_host_":
                                self.multiproc_check_host_signal.emit(result, None)
                                time.sleep(1)

                        if self.opertType in ["_to_file_","_to_file_editMenu_"]:
                            self.multiproc_ping_signal.emit(True)
                            self.stop_signal = True

            except Exception as e:
                print(f'Ошибка в мультипотоке: {e}')


    def ping_process(self, ip_address):
        print("08")
        print(f"ping мульипроцесс=  {ip_address} тип пинга= {self.opertType}")
        try:
            #Работает библиотека pyping проверяется 1 пакет
            response_list = ping(str(ip_address), count=1)
            print(f'response_list {response_list}')
            for response in response_list:
                print(f'response {response}')
                if response.success: #Онлайн
                    #В случае ответа - Идет проверка по типу пинга "в файл" или "постоянный"

                    if self.opertType in ["_to_file_","_to_file_editMenu_"]:  # выбрана запись результата в файл
                        if not os.path.isfile(self.data["name_file"]):  # Если файл не создан создаем строку с подписью столбцов
                            print("Файла не существует создам новый муха-ха-ха!!!!!!!!!!!!!!!")
                            with open(self.data["name_file"], "a", newline="") as file:
                                writer = csv.writer(file, delimiter=";")
                                writer.writerow(['Host_name',
                                                 'Host_ip',
                                                 'Дата\время'
                                                 ])
                        with open(self.data["name_file"], "a", newline="") as file:
                            writer = csv.writer(file, delimiter=";")
                            writer.writerow([ip_address,
                                            str(response).split()[2].split(',')[0],
                                            "Online",
                                                 str(strftime("%Y-%m-%d_%H:%M:%S")),
                                                 ])
                    elif self.opertType == "_constant_":  # выбрана функция постоянного пинга
                        print(f"{ip_address} Online")
                        return True
                    elif self.opertType == "_check_host_":
                        print(f"{ip_address} Online _check_host_")
                        return ({ip_address:True})
                        print("06")
                else: #Offline
                    # В случае потери - Идет проверка по типу пинга "в файл" или "постоянный"
                    if self.opertType in ["_to_file_","_to_file_editMenu_"]:  # выбрана запись результата в файл
                        print(f"{ip_address} Offline")
                        with open(self.data["name_file"], "a", newline="") as file:
                            writer = csv.writer(file, delimiter=";")
                            writer.writerow([ip_address,
                                             "-",
                                             "Offline",
                                             str(strftime("%Y-%m-%d_%H:%M:%S"))])
                    elif self.opertType == "_constant_":  # выбрана функция постоянного пинга
                        print(f"{ip_address} Offline")
                        return False
                    elif self.opertType == "_check_host_":
                        print(f"{ip_address} Offline _check_host_")
                        return ({ip_address:False})
        except Exception as e:
            if self.opertType in ["_to_file_","_to_file_editMenu_"]:  # выбрана запись результата в файл
                print(f"{ip_address} Offline")
                with open(self.data["name_file"], "a", newline="") as file:
                    writer = csv.writer(file, delimiter=";")
                    writer.writerow([ip_address,
                                     "-",
                                     "Offline",
                                     str(strftime("%Y-%m-%d_%H:%M:%S"))])
            elif self.opertType == "_constant_":  # выбрана функция постоянного пинга
                print(f"{ip_address} Offline")
                return False
            elif self.opertType == "_check_host_":
                print(f"{ip_address} Offline _check_host_")
                return ({ip_address: False})

            print (f'Ошибка с {ip_address}')
            print(f'текст ошибки= {e}')

    def stop(self):
        self.stop_signal = True



