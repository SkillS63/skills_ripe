# -*- coding: utf-8 -*-
from PyQt5.QtCore import QThread, pyqtSignal
from console_set import ConsoleThread

class ConsoleController(QThread):
    start_signal = pyqtSignal(bool, str, str)
    stop_signal = pyqtSignal()

    def __init__(self, data):
        super(ConsoleController, self).__init__()
        self.data=data
        self.host_list = ([data['host']] if type(data['host']) == str else data['host'])
        self.operType = data['operType']
        self.file_name = data['file_name']
        print("Закончии инициализации функции прописки")
        self.stop_signal = False
    def run(self):
        self.start_signal.emit(True, self.file_name,  self.operType)

        print("дошли до run в новом файле")
        host_list = self.host_list

        self.thread={}
        for host in host_list:
            print(f'дошли до for host={host}')
            self.thread[host] = ConsoleThread(host, self.data)

            self.thread[host].start()
        for thread in self.thread.values():
            thread.wait()

        self.start_signal.emit(False, self.file_name, self.operType)
        self.exec_()

    def stop(self):
        print("пришла команда останавливать потоки")
        for thread in self.thread.values():
            thread.terminate()
        self.start_signal.emit(False, self.file_name, self.operType)

