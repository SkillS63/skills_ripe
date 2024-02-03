# -*- coding: utf-8 -*-
from multiprocessing import Process, Queue
from PyQt5 import QtCore
from ping3 import ping
from time import *

class PingProcess_multiprocessing(QtCore.QThread):
    multiproc_ping_signal = QtCore.pyqtSignal(bool)
    stop_signal = QtCore.pyqtSignal(bool)
    multiproc_check_host_signal = QtCore.pyqtSignal(dict, object)

    def __init__(self, list_ip_address, selected_type):
        super(PingProcess_multiprocessing, self).__init__()
        self.list_ip_address = list_ip_address
        self.selected_type = selected_type
        self.stop_signal = False

    def run(self):
        if self.list_ip_address == "":
            print("Список IP-адресов пуст.")
        else:
            try:
                result_queue = Queue()  # Очередь для получения результатов из процессов

                # Создание и запуск процессов
                processes = []
                for ip_address in self.list_ip_address["list_ip"]:
                    if self.stop_signal:
                        break

                    process = Process(target=self.ping_process, args=(ip_address, result_queue))
                    processes.append(process)
                    process.start()

                # Получение результатов из очереди
                while len(processes) > 0 and not self.stop_signal:
                    if not result_queue.empty():
                        result = result_queue.get()
                        if self.selected_type == "_check_host_":
                            self.multiproc_check_host_signal.emit(result, None)
                        time.sleep(1)
                    else:
                        time.sleep(0.1)

                # Ожидание завершения всех процессов
                for process in processes:
                    process.join()

                if self.selected_type == "_to_file_":
                    self.multiproc_ping_signal.emit(True)
                    self.stop_signal = True

            except Exception as e:
                print(f'Ошибка в мультипроцессе: {e}')

    def ping_process(self, ip_address):
        print("08")
        print(f"ping мульипроцесс=  {ip_address} тип пинга= {self.selected_type}")
        try:
            #Работает библиотека pyping проверяется 1 пакет
            response_list = ping(str(ip_address), count=1)
            print(f'response_list {response_list}')
            for response in response_list:
                print(f'response {response}')
                if response.success: #Онлайн
                    #В случае ответа - Идет проверка по типу пинга "в файл" или "постоянный"

                    if self.selected_type == "_to_file_":  # выбрана запись результата в файл
                        if not os.path.isfile(self.list_ip_address["name_file"]):  # Если файл не создан создаем строку с подписью столбцов
                            print("Файла не существует создам новый муха-ха-ха!!!!!!!!!!!!!!!")
                            with open(self.list_ip_address["name_file"], "a", newline="") as file:
                                writer = csv.writer(file, delimiter=";")
                                writer.writerow(['Host_name',
                                                 'Host_ip',
                                                 'Дата\время'
                                                 ])
                        with open(self.list_ip_address["name_file"], "a", newline="") as file:
                            writer = csv.writer(file, delimiter=";")
                            writer.writerow([ip_address,
                                            str(response).split()[2].split(',')[0],
                                            "Online",
                                                 str(strftime("%Y-%m-%d_%H:%M:%S")),
                                                 ])
                    elif self.selected_type == "_constant_":  # выбрана функция постоянного пинга
                        print(f"{ip_address} Online")
                        return True
                    elif self.selected_type == "_check_host_":
                        print(f"{ip_address} Online _check_host_")
                        return ({ip_address:True})
                        print("06")
                else: #Offline
                    # В случае потери - Идет проверка по типу пинга "в файл" или "постоянный"
                    if self.selected_type == "_to_file_":  # выбрана запись результата в файл
                        print(f"{ip_address} Offline")
                        with open(self.list_ip_address["name_file"], "a", newline="") as file:
                            writer = csv.writer(file, delimiter=";")
                            writer.writerow([ip_address,
                                             "-",
                                             "Offline",
                                             str(strftime("%Y-%m-%d_%H:%M:%S"))])
                    elif self.selected_type == "_constant_":  # выбрана функция постоянного пинга
                        print(f"{ip_address} Offline")
                        return False
                    elif self.selected_type == "_check_host_":
                        print(f"{ip_address} Offline _check_host_")
                        return ({ip_address:False})
        except Exception as e:
            if self.selected_type == "_to_file_":  # выбрана запись результата в файл
                print(f"{ip_address} Offline")
                with open(self.list_ip_address["name_file"], "a", newline="") as file:
                    writer = csv.writer(file, delimiter=";")
                    writer.writerow([ip_address,
                                     "-",
                                     "Offline",
                                     str(strftime("%Y-%m-%d_%H:%M:%S"))])
            elif self.selected_type == "_constant_":  # выбрана функция постоянного пинга
                print(f"{ip_address} Offline")
                return False
            elif self.selected_type == "_check_host_":
                print(f"{ip_address} Offline _check_host_")
                return ({ip_address: False})

            print (f'Ошибка с {ip_address}')
            print(f'текст ошибки= {e}')

    def stop(self):
        self.stop_signal = True
