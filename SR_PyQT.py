# -*- coding: utf-8 -*-
# from threading import Thread
# from multiprocessing import Process
# import webbrowser
import re
import time
import telnetlib
import subprocess, threading, os, serial
from scapy.all import *
from all_qthreads import ConsoleController

from wgt_ping import PingThread_multiprocessing
from QT_MAIN import Ui_QT_MAIN
from QW_Wind_Log import Ui_Wgt_Wind_Log
from DW_edit_file_of_script import Ui_DW_edit_file_of_script
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import QTimeLine, Qt
from PyQt5.QtGui import QColor, QTextCursor, QTextCharFormat, QBrush
from PyQt5.QtWidgets import QWidget, QPushButton, QLineEdit, QInputDialog, QApplication, QDialog, QTextEdit, QStyledItemDelegate
from time import strftime
import sip



combobox_city = ("Выбери город", "Самара", "Пермь", "НижнийНовгород", "Волгоград")  # Список городов для спец настроек
run_serial = False
Eaaauser = "admin"  # Стандартный логин
Eaaapass = "admin"  # Стандартный пароль
Ehost_connect = "192.168.0.1"  # Стандартный Ip
Ehost = "10.x.x.x"  # Стандартный вид ip коммутаторов ЕР-Телеком
Emask = "255.255.255.0"  # Стандартная Маска коммутаторов ЕР-Телеком
Egwkom = "10.x.x.254"  # Стандартный шлюх УК ЭР-Телеком Самара
Ehostname = "Ulica_dX_pX"  # Шаблон подписи коммутатора
Emgmvlan = "x99"  # Шаблон влана управления
Epcvlan = "Стартовый"  # Коментарий
Eoutport = "24"  # Рекомендованный начальный распред порт
list_type_ports = [u"Выбрать", u"Подписать", u"ОП", u"УСИ", u"Физ.Лицо", u"Распред_Порт", u"Юр.Лицо", u"РМ", u"HS_ZT",
                   u"IPoE", u"Сигнализатор", u"КС"]
summ = 0





##################====================>>>>
# Телнет, старая функция может убрать
def to_bytes(line):
    return f"{line}\n".encode("utf-8")

#Диагностика, работа с com портом, на скорую руку.
def find_serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result


class QT_MAIN(QtWidgets.QMainWindow, Ui_QT_MAIN):

    """QT_MAIN название класса в основной программу и имя конвертированного файла,
        Ui_QT_MAIN название класса в файле PYQT5
        Вызывает окно,добавлет дополнительные параметры и выполняет часть функций"""
    resized = QtCore.pyqtSignal()

    print("01")

    #Скрипт Запуск потоков
    def run_ms_in_threads(self, value, text):
        if type(text) == dict:
            data = text.copy()
        else:
            data = self.create_dict_for_scripts('msText', self.create_string_list(text))
        print(f'run_ms_in_threads передали text=data={data}')
        if value:
            # рекурсивная часть кода, которое обычно пропускается
            if data['operType'] == 'msText+var':
                print(f'data после присвоения в рекурсии = {data}')
                # эта часть кода пропускается если нет перменных и не нужно создавать доп окно
                # При наличии переменных создает окно для ввода их значений,после обработки возвращают необходимы для запуска словарь
                if self.btn_run_costume_MS.text() == "RUN":
                    self.multi_telnet_threads[data['file_name']] = ConsoleController(text)
                    self.multi_telnet_threads[data['file_name']].start_signal.connect(self.run_manualScript_decor_menu)
                    self.multi_telnet_threads[data['file_name']].start()
            # Для запуска из обычного окна или окна редактирования
            else:

                print(f'посчитали data={data}')
                if data['operType'] == 'msText':
                    print(f"имя будущего потока типа ms_{data['operType'], data['file_name'][2:]}")
                    self.multi_telnet_threads[data['file_name']] = ConsoleController(data)
                    self.multi_telnet_threads[data['file_name']].start_signal.connect(self.run_manualScript_decor_menu)
                    print(f"!дошли до старта потока скрипта= {self.multi_telnet_threads}")
                    for key, value in self.multi_telnet_threads.items():
                        if data['file_name'] in key:
                            print('поток с таким файлом есть= ' + data['file_name'])
                    self.multi_telnet_threads[data['file_name']].start()

        else:
            self.multi_telnet_threads[data['file_name']].stop()

    #Ping Запуск потоков
    def run_ping_in_threads(self, value, data):

        print(f'в run_ping_in_threads text={data}')
        print(f'value={value} в run_ping_in_threads data={data}')

        # список для передачи в функцию класса пинг, путь указан обрезанный, возможно подпапки могут не подходиьть по шаблону отрубания 2х пеервых симоволов
        if value: # True
            self.multi_ping_threads[data['name_file']] = PingThread_multiprocessing(data)
            if data['operType'] in ['_check_host_']:
                self.multi_ping_threads[data['name_file']].multiproc_check_host_signal.connect(self.run_ping_decor_menu)
            if data['operType'] in ['_to_file_']:
                #Подключать сигналы нужно будет, думаю будут в run_ping_decor_menu, там еще индекс по имени файла затегирован будем использовать его
                # self.multi_ping_threads[data['name_file']].multiproc_ping_signal.connect(lambda value:self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().setText("Разовый пинг в файл") if value else None)# при сработки сигнала об окончании функции возвращает текст надписи
                # self.multi_ping_threads[data['name_file']].multiproc_ping_signal.connect(lambda value: self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().setStyleSheet("background-color:green") if value else None)#при сработки сигнала об окончании функции возвращает цвет надписи
                pass


            self.multi_ping_threads[data['name_file']].start()

        else:  # False

            self.multi_ping_threads[data['name_file']].stop()

    #Пинг, запуск потока в строки connect to для раздела SWICH
    def run_CB_swich_ping_host(self):

        """
        Функция нажатия "чек буттон" - пинг хостов в разделе SWICH
        Если отметка стоит проверяем тип пинга групповой(группбокс) или одиночный
        :return:Отправляет True\False для запуска и остановки потока,
                и словарь с неоюходимы данными
        """
        if self.CB_swich_ping_host.isChecked():#Если стоит отметка о запуске пинга
            # Старт потока
            print("запуск потока")
            if self.CB_host_group.isChecked():# Если выбран групповой список хостов
                if self.list_more_ip==[]: #Но групповой список пустой
                    print("Введите адрес хоста")
                    self.CB_swich_ping_host.setChecked(False)#убираем отметку выдем соощение
                    self.run_btn_more_ip()#Запускаем окно для ввода списка
            else:# Если выбран пинг одного хоста
                if self.Ehost_connect.text()=="":#но поле ввода пустое
                    print("Введите адрес хоста")
                    self.CB_swich_ping_host.setChecked(False)#убираем отметку,! пока не выдаем соощение
            self.run_ping_in_threads(True,
                                     {"list_ip": ( self.list_more_ip if self.CB_host_group.isChecked()
                                                   else [self.Ehost_connect.text()]),
                                      "name_file": "_check_host_",
                                      'operType':"_check_host_"})
        else: #Стоп потока
            if not self.CB_host_group.isChecked(): #Остановка потока если выбран пинг группового списка
                self.stop_ping_check_host_decor()
                print("смена оформления одиночного пинга")

            self.run_ping_in_threads(False,{"list_ip": None, "name_file": "_check_host_",
                                          'operType': "_check_host_"})
            print("Стоп потока  пинга")


    #Script+Ping 01-Запуск заточенный на отдельное общее окно - Редактирование
    def run_ms_or_ping(self, text):
        """
        Эта функция завязана на кнопки общего окна редактирования
        для функция пинга и скритов
        Запуск из этого окна передает в функции соего класса текст из поля ввода, который ранее был подгружен из файла
        """

        print("Запуск\чтение файла скрипта")
        print(f'run_ms_or_ping проверяем text= {text}')

        ######## Общее начало
            # Меняем тект кнопки окна редактирования (даже если запускается из основного окна)
        if self.DW_FoS.btn_run_files_sr.text() == "Запустить":
            self.DW_FoS.btn_run_files_sr.setText("Остановить")
            self.DW_FoS.btn_run_files_sr.setStyleSheet("background-color: red;")
            ########## Скрипт старт
            if self.TabWgt_MENU.currentIndex() == 0:#Раздел Swich
                self.run_ms_in_threads(True, text)
            ########## PING старта
            elif self.TabWgt_MENU.currentIndex() == 2:#Раздел ping
                self.run_ping_in_threads(True,self.create_string_list(text,"_to_file_editMenu_"))
        #######################################################################
        else: ################остановка потоков Скрипта или Пинга
            self.DW_FoS.btn_run_files_sr.setText("Запустить")
            self.DW_FoS.btn_run_files_sr.setStyleSheet("background-color: green;")
            ########## Скрипт стоп
            if self.TabWgt_MENU.currentIndex() == 0:#Раздел Swich
                print("остановка потока мануал скрипт")
                self.run_ms_in_threads(False, text)
            ########## PING стоп
            elif self.TabWgt_MENU.currentIndex() == 2:#Раздел ping
                print("стопаем пинг")
                self.run_ping_in_threads(False, self.create_string_list(text,"_to_file_editMenu_"))
        print("Запуск пинга или скрипта из из окна редактирования")
    #Скрипт, 1-Запуск своих скриптов с своими перменными#
    def create_dict_for_scripts(self,operType, data):
        print(f"""create_dict_for_scripts:
                operType={operType}
                data={data}""")
        ####Формируем список хостов#####################
        if self.CB_host_group.isChecked():
            all_items = [self.combobox_list_ip.itemText(index) for index in range(self.combobox_list_ip.count())]
            host = all_items
        else:
            host = self.Ehost_connect.text()
        #########################

        if operType in ['msText']:
            print('operType')
            #Перенесем оформление

            # встроенная функция для скриптов, при наличии переменных, при нажатии кнопки сначала подменяет переменные их значениями перебирая диалоговое окно
            # а потом возвращает правленный список строк

            print("перед script_text_ms")
            script_text_ms=data
            # script_text_ms = self.create_string_list(data)  # Обработка переданных сктрок, выявление перменных, создание диалогового окна для ввода переменных
            print(f'script_text_ms= {script_text_ms}')
            if script_text_ms['variable'] == []: # Если переменных в скрипте нет то в поток будем возвращать это
                print("Перед возвратом в режиме редактирования")
                return {
                    'host': host,
                    'login': self.Eaaauser.text(),
                    'password': self.Eaaapass.text(),
                    'type_connect': self.comboBox_type_connect.currentText(),
                    'type_connect_protocol': self.comboBox_type_connect_protocol.currentText(),
                    'operType': operType,
                    'file_name': script_text_ms['file_name'],
                    'script_text': script_text_ms['text'],
                }

            else: # если список переменных не пустой создаем окно для ввода их значений
                self.DW_FoS.btn_run_files_sr.setText("Запустить")
                print("должны создавать поля для ввода переменных")
                self.btn_run_costume_MS = QtWidgets.QPushButton("RUN", self.Dialog_costume_menu_MS)
                # чтобы не блочить кнопку RUN, будем закрывать окно и выполнять функцию, стопать будем другие кнопки
                self.btn_run_costume_MS.clicked.connect(lambda: self.run_ms_or_ping( {
                                                                            'host': host,
                                                                            'login': self.Eaaauser.text(),
                                                                            'password': self.Eaaapass.text(),
                                                                            'type_connect': self.comboBox_type_connect.currentText(),
                                                                            'type_connect_protocol': self.comboBox_type_connect_protocol.currentText(),
                                                                            'operType': 'msText+var',
                                                                            'file_name': script_text_ms['file_name'],
                                                                            'script_text': self.varible_to_text(script_text_ms),
                                                                        }))

                print("Здесь остановка для диалога ввода значений переменных")
                self.layout_in_Dialog_costume_menu_MS.addWidget(self.btn_run_costume_MS)
                self.Dialog_costume_menu_MS.exec()
                return {'operType': 'close_msText+var'}#'close_msText+var' любое значение ддя корректно закрытия диалогового окна

    #Script+ping, 2-обработчик переданного сиписка (Ip или скрипта), для возврата полученных  данных в виде словаря
    def create_string_list(self, index_or_text, operType):
        """-Если запуск произошел с основного окна\закладки, то index_or_text приходят в типе int(индекс запущенного лайаута) и требуется дополнительное преобразование для получения пути
                Переопределяем тип переменной и содержимое в путь к файлу
                Открываем файл по полученному пути
                -для скриптов
                    Преобразуем его в список lines_script
                -для пинга
                    Превращаем файл в список  list_ip
                    возвращаем словарь с списком ip(list_ip), временем запуска, и именем файла в котормвсе далали (будут использоваться для пинга в файл)
            -Если запуск произошел из окна редактирования получаем текст
                Преобразуем его в список lines_script
            -Для скриптов Запускаем цикл проверки содержимого
                -создаем переменные variable и text которые в итоге каждую строчку фильтруют, значение их будет использоваться в последующей итерации elif
                    Если в списке находимстрочку <SHOW_MENU>, то создаем меню с титулом типа ("RUN-" + index) и layout
                    Если есть начало строчки типа <L записываем отфильтрованню первую частьв список для перменных второю часть использую для создания lineedit в диалоговом окне
                    Если(когда) дойдем до строчки <RUN> используем ее индекс+1 и весь остальной текст списка записываем в другой для дальнейшей обработки и запуска
                    Если список с переменными не пустой значит добавляем в диалог кнопку выполнения скрипта и выводим диалог на экран
            -Для пинга
                Превращаем текст в список  list_ip
                озвращаем словарь с списком ip(list_ip), временем запуска, и именем файла в котормвсе далали (будут использоваться для пинга в файл)
        """

        print("если прошло проверку числа, то этот индекс виджета нужно приеобразовать в путь к файлу")
        print(f'index_or_text в начале={index_or_text}')
        # print(f'self.temp_path_to_file[2:]={self.temp_path_to_file[2:]}')
        #Для скриптов
        if self.TabWgt_MENU.currentIndex() == 0:
            # self.temp_path_to_file  - создается только при откртытии окна редактирования!!!
            
            variable_list_ms = [] #переменные от наличия которых зависит будет ли меню создавться или нет
            text_list_ms = [] # вроде обнуляем перменную с будующим списком строк для скрипта
            if type(index_or_text) == int: #запуск из основного окна
                path = self.list_all_path_to_scripts[index_or_text - 1]  # вычисляем путь на основе переменной с cписком путей на основе индекса, который передается при вызове из основного окна
                file_name= str(path)
                print(path)
                with open(path, 'r') as file:
                    # list_ms=list(filter(None, map(str.rstrip, file))) #создаем список из содержимого файла  и очищаем от пустых строк
                    list_ms = list(file) # создаем список из содержимого файла
                    print(f'запуск из основного окна list_ms==={list_ms}')
            else:# значит будет переменная с текстом из окна редактирования
                file_name= str(self.temp_path_to_file)
                print("запуск скрипта из окна редактирования")
                list_ms = list(index_or_text.split('\n')) #делаем список из текста, может прийдется добавлять символ переноса в конец
                print(f'запуск из окна редактирования list_ms==={list_ms}')
            for line in list_ms:  # перебираем спсок для поиска разделительных ключей
                variable = ' '.join(re.findall(r"<L.*>", line))
                print(variable.strip())
                text = ' '.join(re.split(r"<L.*>", line))
                print(text.strip())
                try:  # Здесь создается меню если есть соответсвующие строки в тексте
                    if line.strip("\n") == "<SHOW_MENU>":  # strip("\n") нужен, т.к. новая строка может отсутствовать
                        print("Начинаем содавть меню на основе последующих строк")
                        self.Dialog_costume_menu_MS = QDialog(self)

                        self.Dialog_costume_menu_MS.setWindowTitle(file_name) #Название окна в созданном диалоге, если запущено через окно редактироывния там при создании окна создается переменная с путем
                        print("мы тут стопаемся?")
                        self.layout_in_Dialog_costume_menu_MS = QtWidgets.QVBoxLayout(self.Dialog_costume_menu_MS)
                    elif line[:2] == "<L":  #проверяем первые два символа
                        variable_list_ms.append(variable)
                        Line_MS = QtWidgets.QLineEdit(self.Dialog_costume_menu_MS)
                        Line_MS.setFixedSize(200, 20)
                        Line_MS.setPlaceholderText(text.strip())
                        self.layout_in_Dialog_costume_menu_MS.addWidget(Line_MS)
                    elif line.strip("\n") == "<RUN>":
                        text_list_ms = list_ms[list_ms.index(line) + 1:]
                        break
                except Exception as e:
                    print(e)
                    print("Есть строки короче 2х символов")
            print(f'return={text_list_ms}-{variable_list_ms}-{file_name}')
            return {'text':text_list_ms, 'variable':variable_list_ms,'file_name':file_name}
        #Для пинга
        if self.TabWgt_MENU.currentIndex() == 2:
            if type(index_or_text) == int: # Для запуска из основного спика
                path = self.list_all_path_to_ping_ip[index_or_text - 1]  # Для списка кнопок нет 0 элемента
                print(path)
                with open(path, 'r') as file:
                    list_ip = list(filter(None, map(str.rstrip,file)))
                    list_ip.remove("<SR_PING_LIST>")  # Очищаем от системной строки список с целевыми хостами
                    print("дошли до конца очистки и создания списка для пинга")
                    return {"list_ip": list_ip, "name_file": path,'operType':operType}  # список для передачи в функцию класса пинг, путь указан обрезанный, возможно подпапки могут не подходиьть по шаблону отрубания 2х пеервых симоволов

            else: # Для запуска из окна редактирования, приходит текст
                list_ip = list(filter(None, map(str.rstrip, index_or_text.split(
                    '\n'))))  # превращаем текст в список убирая переносы, пустые строки
                print(f"list_ip= {list_ip}")
                list_ip.remove("<SR_PING_LIST>")  # Очищаем от системной строки список с целевыми хостами
                print("дошли до конца очистки и создания списка для пинга")
                return {"list_ip": list_ip, "name_file": self.temp_path_to_file,'operType':operType}#список для передачи в функцию класса пинг, путь указан обрезанный, возможно подпапки могут не подходиьть по шаблону отрубания 2х пеервых симоволов

    #Скрипт, 3-создает готовый список строк для выполннения - перед запуском ищит переменные и подменяет их переданными значениями
    def varible_to_text(self, data):
        print(f'data в перменных = {data}')
        manual_script = []
        for line in data['text']:
            for variable in data['variable']:
                if variable in line:
                    print(variable)  # переменная
                    # print(self.variable_list_ms.index(variable)) #индекс переменной в списке с переменными
                    # print(self.layout_in_Dialog_costume_menu_MS.itemAt(data['variable'].index(variable)).widget().text()) #индекс
                    line = "".join(re.sub(variable, self.layout_in_Dialog_costume_menu_MS.itemAt(
                        data['variable'].index(variable)).widget().text(),
                                          line))  # строка с заменой переменной на ее значение
                    print(f'''Переменая из=====

                    {self.layout_in_Dialog_costume_menu_MS.itemAt(
                        data['variable'].index(variable)).widget()}
                    {self.layout_in_Dialog_costume_menu_MS.itemAt(
                        data['variable'].index(variable)).widget().text()}
                    ''')
                    print(f'line====={line}')


                manual_script += [line]
        print(f'manual_script= {manual_script}')
        return manual_script

    # SWICH, кнопка для прописки, требует доработок
    def btn_write_coper_start(self, btn_text):
        """"Кнопка в разделе *настройка по меди*"""
        # tl=threading.Thread(target=self.write_by_cooper)
        print(btn_text)
        if btn_text == "-Остановаить-":
            self.tl.stop()
            self.btn_write_coper.setText("-Прописать-")

        if btn_text == "-Прописать-":
            self.btn_write_coper.setText("-Остановаить-")
            ################################################### перенес
            if self.CB_host_group.isChecked():
                all_items = [self.combobox_list_ip.itemText(index) for index in
                             range(self.combobox_list_ip.count())]
                host = all_items
            else:
                host = self.Ehost_connect.text()
            ##############################
            self.tl = ConsoleThread_multiprocessing(host,
                                                    self.Eaaauser.text(),
                                                    self.Eaaapass.text(),
                                                    {"type_connect": self.comboBox_type_connect.currentText(),
                                                     "type_connect_protocol": self.comboBox_type_connect_protocol.currentText()},
                                                    "Настройка коммутатора",
                                                    )
            self.tl.start()
            # print("Проверка?!")

    #? Лог, Реакция на закрытие окна логов, не нашел где использовал
    def closeEvent(self, event):
        """Закрывает второе окно если оно закрыто при закрытии первого"""
        print("закрыть")
        if self.CB_Wind_Log.isChecked():
            self.Wind_Log.close()

    # Лог, Реакция на изменение\перемещение
    def set_frame_func(self, frame):

        """Функция реакции перемещения фрейма"""
        if self.frame_geometry != self.frameGeometry():  # !!!
            self.frame_geometry = self.frameGeometry()
            print(f' set_frame_func: -> {self.frame_geometry}')
            if self.CB_Wind_Log.isChecked():
                self.Wind_Log.move(self.frame_geometry.x() + window.frameSize().width(), self.frame_geometry.y())
        ##################Чтобы сворачивалось все вместе с первым окном##########
        if self.isMinimized():
            if self.CB_Wind_Log.isChecked():  # Сворачивает второе окно если свернуть первое
                # print("свернул первое")
                self.Wind_Log.showMinimized()
            # else:
            #
            #     self.Wind_Log.showNormal()
        # else:
        #     if self.CB_Wind_Log.isChecked():
        #         self.Wind_Log.showNormal()

    #Maine, Реакция на изменение\перемещение формы
    def resizeEvent(self, event):
        """Функция реакции изменения размер фрейма"""
        self.resized.emit()
        super(QT_MAIN, self).resizeEvent(event)
        self.w = self.size().width()
        # self.timeline.setFrameRange(0, self.w + 100)
        # duration = self.w * 20
        # self.timeline.setDuration(duration)
        self.frame_geometry = self.frameGeometry()  # !!!
        print(f'+++ releaseEvent -> {self.frame_geometry}')

    #!!!Скрипт, Обработка сигнала для изменения цвета и текста Ping
    def run_manualScript_decor_menu(self, value, name, operType):

        print("Сигнал пришел1=",value, name,f' id кнопки= ',(self.list_all_path_to_scripts.index(name) if name in self.list_all_path_to_scripts else None))
        print(f"Работате декор operType={operType}")
        index=1+(self.list_all_path_to_scripts.index(name) if name in self.list_all_path_to_scripts else None)
        if value:
            if operType in ['msText+var']:
                self.btn_run_costume_MS.setText('>STOP<')
                self.btn_run_costume_MS.setStyleSheet("background-color: red;")
            self.layout_ScrlArea_MS.itemAt(index).widget().layout().itemAt(0).widget().setText("Остановка")
            self.layout_ScrlArea_MS.itemAt(index).widget().layout().itemAt(0).widget().setStyleSheet("background-color: red;")
        else:
            if operType in ['msText+var']:
                self.btn_run_costume_MS.setText("RUN")
                self.btn_run_costume_MS.setStyleSheet("background-color: green;")
            self.layout_ScrlArea_MS.itemAt(index).widget().layout().itemAt(0).widget().setText("Запуск скрипта")
            self.layout_ScrlArea_MS.itemAt(index).widget().layout().itemAt(0).widget().setStyleSheet("background-color: green;")
            self.DW_FoS.btn_run_files_sr.setText("Запустить")
            self.DW_FoS.btn_run_files_sr.setStyleSheet("background-color: green;")
            try:
                print('удалить из словаря завершенного потока=')
                del self.multi_telnet_threads[name]
                print(f"удалили self.multi_telnet_threads[{name}]")
            except Exception as e:
                print(f'проблема при удалении из словаря завершенного потока= {e}')

    #Пинг, сммена оформление меню
    def run_ping_decor_menu(self, data): #Меняет оформление кнопок чтобы было видно окончание потока
        #
        # index = 1 + (self.list_all_path_to_scripts.index(name) if name in self.list_all_path_to_scripts else None)
        print("меняем оформление на основе сигналов")
        if self.CB_swich_ping_host.isChecked():
            if self.CB_host_group.isChecked(): #Если групповой пинг хоста
            # if type(data) == dict:
            #     print("Это словарь")
                for index, host in enumerate(self.list_more_ip):
                    if host in data:
                        # print(f'нашел {host} index= {index} result ={data[host]}')
                        if data[host] == True:#При остановке функции возвращает раскраску, т.к. бывает задержка тут лучше место
                            self.combobox_list_ip.setItemData(index, QColor(Qt.green), Qt.BackgroundColorRole)
                            if self.combobox_list_ip.currentText()== host:
                                self.combobox_list_ip.setStyleSheet("background-color: green;")
                        else:
                            self.combobox_list_ip.setItemData(index, QColor(Qt.red), Qt.BackgroundColorRole)
                            if self.combobox_list_ip.currentText()== host:
                                self.combobox_list_ip.setStyleSheet("background-color: red;")
                        if  not self.CB_swich_ping_host.isChecked():#При остановке функции возвращает раскраску, т.к. бывает задержка тут лучше место
                            self.combobox_list_ip.setStyleSheet("background-color:None")
                            self.combobox_list_ip.setItemData("background-color:None")

            else: #Если одиночный пинг хоста
                print("проверка одного хоста")
                print(f'data[self.Ehost_connect.text()]= {data[self.Ehost_connect.text()]}')
                if data[self.Ehost_connect.text()] == True: #Если доступен
                    # print(self.Ehost_connect.text(), "active")
                    self.Ehost_connect.setStyleSheet("color: green")
                    self.Wind_Log.TxtBr_Wind_Log.setTextColor(QColor(0, 204, 0))
                    # self.Wind_Log.TxtBr_Wind_Log.append(time_ping + " ===ping_ip=== " + self.Ehost_connect.text() + " UP")
                    self.Wind_Log.TxtBr_Wind_Log.append(" ===ping_ip=== " + self.Ehost_connect.text() + " UP")
                else: #Если не доступен
                    # print(self.Ehost_connect.text(), "no active")
                    self.Ehost_connect.setStyleSheet("color: red")
                    self.Wind_Log.TxtBr_Wind_Log.setTextColor(QColor(255, 51, 0))
                    # self.Wind_Log.TxtBr_Wind_Log.append(time_ping + " ===ping_ip=== " + self.Ehost_connect.text() + " down")
                    self.Wind_Log.TxtBr_Wind_Log.append(" ===ping_ip=== " + self.Ehost_connect.text() + " DOWN")
                if  not self.CB_swich_ping_host.isChecked():#При остановке функции возвращает раскраску, т.к. бывает задержка тут лучше место
                    self.Ehost_connect.setStyleSheet("color: black")

    #Пинг, Смена оформления для основного меню connect to где lineEdit и combobox
    def stop_ping_check_host_decor(self):
        try:
            if self.multi_ping_threads["_check_host_"]:
                print("Процесс запущен, сбросить")
                self.Ehost_connect.setStyleSheet("color: black")
                self.CB_swich_ping_host.setChecked(False)
                self.multi_ping_threads["_check_host_"].stop()
                self.combobox_list_ip.clear()
                self.combobox_list_ip.setStyleSheet("background-color:white")
        except:
            print("такого потока не существует")



#---------Пока не юзаем--------
    # Включение\отключение окна логов
    def on_off_CB_Wind_Log(self):
        """Включает/отключает дополнительное окно с логами
        """
        if self.CB_Wind_Log.isChecked():
            print("Надо открыть")
            print("Номер потока? " + str(threading.activeCount()))
            self.Wind_Log.move(self.frame_geometry.x() + window.frameSize().width(),
                               self.frame_geometry.y())  # Меняет размер второго окна относительно первого
            # self.Wind_Log.show()
            self.Wind_Log.showNormal()

        else:
            print("Надо закрывать")
            self.Wind_Log.close()

    # Тестовая функция для проверки состояния вкладок
    def Change_TabWgt_MENU(self):
        print("Семена вкладки swich", self.TabWgt_MENU.currentIndex())
# ---------Пока не юзаем--------

    # SWICH, скрыть показать маску и шдюз
    def on_off_CB_manual_set_network(self):
        """Включает\отключает(скрывает) дополнительные поля для настройки коммутаторов
        """
        if self.CB_manual_set_network.isChecked():
            self.Lmask.setVisible(True)
            self.Emask.setVisible(True)
            self.Lgwkom.setVisible(True)
            self.Egwkom.setVisible(True)
        else:
            self.Lmask.setVisible(False)
            self.Emask.setVisible(False)
            self.Lgwkom.setVisible(False)
            self.Egwkom.setVisible(False)

    # Пинг, создание стартовых кнопок в лайауте
    def create_first_btn_ping_lists(self):
        groupbox_ping_lists = QtWidgets.QGroupBox("Управление списками IP", self)
        self.layout_in_groupbox_ping_lists = QtWidgets.QHBoxLayout(groupbox_ping_lists)
        btn_create_ping_lists = QtWidgets.QPushButton(groupbox_ping_lists)
        btn_create_ping_lists.setText("Создать свой Список")
        btn_create_ping_lists.clicked.connect(lambda x: self.create_new_file_of_ms_or_ping())
        self.layout_in_groupbox_ping_lists.addWidget(btn_create_ping_lists)
        btn_find_ping_lists = QtWidgets.QPushButton(groupbox_ping_lists)
        btn_find_ping_lists.setText("Обновить списки")
        btn_find_ping_lists.clicked.connect(lambda x: self.find_files_of_ms_or_ping())
        self.layout_in_groupbox_ping_lists.addWidget(btn_find_ping_lists)
        text_for_filtre = QtWidgets.QLineEdit(groupbox_ping_lists)
        text_for_filtre.setPlaceholderText("Без фильра")
        # print("текст= "+text_for_filtre.text())
        self.layout_in_groupbox_ping_lists.addWidget(text_for_filtre)
        # layout_in_groupbox_SP.addStretch(1)
        return groupbox_ping_lists

    # Пинг, создание кнопок для найденных файлов
    def create_btn_for_ping_lists(self, patch_to_script, index):
        """
        :param patch_to_script: путь к файлу
        :param index: индекс layout для дальнейшего использования
        :return:
        Фильтрем путь к файлу для получения его имени
        Содаеем групбокс с меним из индекса переведенного в строку и имени (индекс 0 остается за панелью управления, поэтомувсе кнопки начинаются с 1 - это норм)
        Здаем в нем виджет слоев и заполняем кнопками
        В кнопке удаления, при вызове функции, используем индекс с вычетом единицы(-1), т.к. отсчет в списках(list) начинается с нуля.
        """
        print(patch_to_script)
        name_script = re.search(r'[^\\]+.txt', patch_to_script, flags=0)
        print(name_script.group(0))
        print("Кнопки для файлов готовы")
        groupbox_ping_lists = QtWidgets.QGroupBox("№" + str(index) + " - " + name_script.group(0), self)
        # self.layout_in_groupbox_ping_lists = QtWidgets.QHBoxLayout(groupbox_ping_lists)
        self.layout_in_groupbox_ping_lists = QtWidgets.QGridLayout(groupbox_ping_lists)

        btn_run_ping_lists_in_file = QtWidgets.QPushButton(groupbox_ping_lists)
        btn_run_ping_lists_in_file.setText("Разовый пинг в файл")
        btn_run_ping_lists_in_file.clicked.connect(lambda x: self.run_ping_any_type(int(index),'_to_file_'))
        self.layout_in_groupbox_ping_lists.addWidget(btn_run_ping_lists_in_file)

        btn_run_ping_lists_constant = QtWidgets.QPushButton(groupbox_ping_lists)
        btn_run_ping_lists_constant.setText("Пинг без остановки")
        btn_run_ping_lists_constant.clicked.connect(lambda x: self.run_ping_any_type(int(index),'_constant_'))
        self.layout_in_groupbox_ping_lists.addWidget(btn_run_ping_lists_constant)

        btn_edit_ping_lists = QtWidgets.QPushButton(groupbox_ping_lists)
        btn_edit_ping_lists.setText("Редактировать список")
        btn_edit_ping_lists.clicked.connect(lambda x: self.edit_files_of_ms_or_ping(int(index) - 1))
        # btn_edit_MS.clicked.connect(self.dialog.exec)
        self.layout_in_groupbox_ping_lists.addWidget(btn_edit_ping_lists)

        btn_delete_ping_lists = QtWidgets.QPushButton(groupbox_ping_lists)
        btn_delete_ping_lists.setText("Удалить список")
        btn_delete_ping_lists.clicked.connect(lambda x: self.delete_file_of_ms_or_ping(int(index) - 1))
        self.layout_in_groupbox_ping_lists.addWidget(btn_delete_ping_lists)

        # layout_in_groupbox_SP.addStretch(1)
        return groupbox_ping_lists

    # Пинг, ~1-запуск потоков пинга в файл и постоянный для вкладки Ping
    def run_ping_any_type(self, index, operType): #Пинг в файл и постоянный
        """
        :param index: нужно считать +1 т.к. 0 отвечает за кнопки управления
        :return: выполняет изменени в меню и запуск функции
        Путь выглядит так layout_scrollArea_ping_lists - панель с кнопками  который мы учитываем itemAt(index).widget()
        .layout().itemAt(0).widget().text() его подвиджет с кнопками где itemAt(0) первая кнопка
        """
        data=self.create_string_list(index,operType)
        # data.update({'operType': operType})

        print("Запуск\чтение файла списка адресов пинга")
        # if operType=='_to_file_':

        if self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().text() == "Разовый пинг в файл":#Включает поток меняет оформление кнопки
            print("индекс= ",index)
            print(self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().text())
            self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().setText("Остановить запись в файл")
            self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().setStyleSheet("background-color:red;")
            # self.run_ping_in_threads
            self.run_ping_in_threads(True, data)

        else:#Отключает поток, меняет оформление кнопки
            self.run_ping_in_threads(False, data)
            self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().setText("Разовый пинг в файл")
            self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(0).widget().setStyleSheet("background-color:green")
            # self.multi_ping_threads[operType + str(index)].stop()
        # if type == '_constant_':
        #     if self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(1).widget().text() == "Пинг без остановки": #Включает поток меняет оформление кнопки
        #         print("индекс= ", index)
        #         print(self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(1).widget().text())
        #         self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(1).widget().setText("Остановить пинг без остановки")
        #         self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(1).widget().setStyleSheet("background-color:red;")
        #         self.multi_ping_threads[operType + str(index)] = PingThread_multiprocessing(self.create_string_list(index), operType)  # в квадратных скобках генерируется имя переменной для потока
        #         self.multi_ping_threads[operType + str(index)].start()
        #     else:#Отключает поток, меняет оформление кнопки
        #         self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(1).widget().setText("Пинг без остановки")
        #         self.layout_scrollArea_ping_lists.itemAt(index).widget().layout().itemAt(1).widget().setStyleSheet("background-color:green")
        #         self.multi_ping_threads[operType + str(index)].stop()

    # Пинг, Переключатель списка (LineEdit или combobox) connect to для подключения для раздела SWICH
    def check_list_host(self):
        if self.CB_host_group.isChecked():

            print("переключить в список хостов")
            self.btn_more_ip.setVisible(True)
            self.combobox_list_ip.setVisible(True)
            self.Ehost_connect.setVisible(False)
            self.CB_swich_ping_host.setChecked(False)
            try:
                self.multi_ping_threads["_check_host_"].stop()
            except:
                print("потока одиночного нет")
            # self.ping_thread = PingThread(self.Ehost_connect.text())
            # self.ping_thread.ping_signal.connect(self.run_ping_decor_menu)
            # self.ping_thread.start()
        else:
            print("переключить Один хост")
            self.btn_more_ip.setVisible(False)
            self.combobox_list_ip.setVisible(False)
            self.Ehost_connect.setVisible(True)
            self.CB_swich_ping_host.setChecked(False)
            try:
                self.multi_ping_threads["_check_host_"].stop()
            except: print("потока группового нет")
        #     self.ping_thread.terminate()
            self.Ehost_connect.setStyleSheet("color: black")

    #Пинг, сохранение списка IP в вызываемом окне раздел swich
    def run_btn_save_list_ip(self, text):
        """Создаем глобальную переменную для списка ip адресов
        Если окно ввода списка не пустое
            очищаем список
            добавляем содержимое текста в переменную списка"""

        # self.list_more_ip = []  #создаем\очищаем переменную для переноса очищенного списка
        print("список ip заполнен")
        print(text)
        self.list_more_ip = list(filter(None, map(str.rstrip, text.split("\n"))))#Разделяем по переносам, удаляем пустые строчки филтром
        print(self.list_more_ip)
        # self.Ehost_connect.setText("") #Очищаем поле ввода для одиночного подключения\проверки, может и ненужна строчка будет
        self.combobox_list_ip.addItems(self.list_more_ip)

    # Пинг, вызов диалога для ввода нескольких ip раздел Swich
    def run_btn_more_ip(self):

        """Создание окна для создания списка адресов\ip
        создаем лайаут для удобства масшатбирования
        содаем поле ввода текста
        если глобальная перменная со списком ip НЕпустая возвращаем ее содержимое в поле ввода
        окно ввода добавляем в лейаут
        создаем кнопку для сохранения списка ip и привязываем ему две функции:
            1)обрабатывает  введенные данные и передает в combobox
            2)закрывает диалог
        """
        self.stop_ping_check_host_decor()#Запускаем функцию на случай запущенного потока для его сброса

        print("Запуск окна для ввода списка Ip")

        self.Dialog_more_ip = QDialog(self)
        self.Dialog_more_ip.setWindowTitle("Списко ip в столбец")
        self.layout_Dialog_more_ip = QtWidgets.QVBoxLayout(self.Dialog_more_ip)
        self.text_edit_more_ip = QTextEdit(self)
        try:
            if self.list_more_ip != []: #Если ранее сохранялось то восстанавливаем его перенося данные из переменной
                for address in self.list_more_ip:
                    self.text_edit_more_ip.append(address)
        except:
            self.list_more_ip=[]
            print("Списка не существует, создал пустой")
        self.layout_Dialog_more_ip.addWidget(self.text_edit_more_ip)
        btn_save_list_ip = QPushButton(self)
        btn_save_list_ip.setText("Сохранить список")
        btn_save_list_ip.clicked.connect(lambda x: self.run_btn_save_list_ip(self.text_edit_more_ip.toPlainText()))#выполняе функцию по обработке поля ввода и переносе данных в комбо бокс
        btn_save_list_ip.clicked.connect(lambda x: self.Dialog_more_ip.close())#кнопка сохранения списка закрывает окно
        self.layout_Dialog_more_ip.addWidget(btn_save_list_ip)
        self.Dialog_more_ip.exec()

    # TABWgt, крипт отображает\скрывает часть кнопок
    def ChangeTabSwich(self):
        """
        Здесь отрабатываются события при переключении вкладок TABWgt
        0 Настройка коммуатора
        1 Настройка спец портов
        2 Ручные скрипты
        """
        if self.TabWgt_Swich.currentIndex() == 0:
            self.TabWgt_Swich.setGeometry(QtCore.QRect(10, 100, 391, 161))
            self.ScrlArea_ports.setGeometry(QtCore.QRect(10, 279, 381, 151))
            self.btn_more_ip.setVisible(False)

            print("0")
            if self.CB_ShowPorts.isChecked():
                self.ScrlArea_ports.setVisible(True)
                self.btn_add_SP.setVisible(True)
                self.btn_del_SP.setVisible(True)
            else:
                self.ScrlArea_ports.setVisible(False)
                self.btn_add_SP.setVisible(False)
                self.btn_del_SP.setVisible(False)

        if self.TabWgt_Swich.currentIndex() == 1:
            self.TabWgt_Swich.setGeometry(QtCore.QRect(10, 100, 391, 50))
            self.ScrlArea_ports.setGeometry(QtCore.QRect(10, 150, 391, 280))
            self.ScrlArea_ports.setVisible(True)
            self.btn_add_SP.setVisible(True)
            self.btn_del_SP.setVisible(True)
            # self.btn_more_ip.setVisible(False)
            print("1")
        if self.TabWgt_Swich.currentIndex() == 2:
            self.TabWgt_Swich.setGeometry(QtCore.QRect(10, 100, 391, 320))
            self.ScrlArea_ports.setVisible(False)
            self.btn_add_SP.setVisible(False)
            self.btn_del_SP.setVisible(False)
            # self.btn_more_ip.setVisible(True)

    # Скрипт, создание стартовых кнопок
    def create_first_btn_manual_scripts(self):
        """
        Добавляем стартовые кнопки на страницу со скриптами
        :return:
        """
        groupbox_MS = QtWidgets.QGroupBox("Управление скриптами", self)
        self.layout_in_groupbox_MS = QtWidgets.QHBoxLayout(groupbox_MS)
        btn_create_MS = QtWidgets.QPushButton(groupbox_MS)
        btn_create_MS.setText("Созда свой скрипт")
        btn_create_MS.clicked.connect(lambda x: self.create_new_file_of_ms_or_ping())
        self.layout_in_groupbox_MS.addWidget(btn_create_MS)
        btn_find_MS = QtWidgets.QPushButton(groupbox_MS)
        btn_find_MS.setText("Обновить список")
        btn_find_MS.clicked.connect(lambda x: self.find_files_of_ms_or_ping())
        self.layout_in_groupbox_MS.addWidget(btn_find_MS)
        text_for_filtre = QtWidgets.QLineEdit(groupbox_MS)
        text_for_filtre.setPlaceholderText("Без фильра")
        # print("текст= "+text_for_filtre.text())
        self.layout_in_groupbox_MS.addWidget(text_for_filtre)
        # layout_in_groupbox_SP.addStretch(1)
        return groupbox_MS

    # Скрипт, создание кнопок в layaut для каждого найденного файла
    def create_btn_for_manual_scripts(self, patch_to_script, index):
        """

        :param patch_to_script: путь к файлу
        :param index: индекс layout для дальнейшего использования
        :return:
        Фильтрем путь к файлу для получения его имени
        Содаеем групбокс с меним из индекса переведенного в строку и имени (индекс 0 остается за панелью управления, поэтомувсе кнопки начинаются с 1 - это норм)
        Здаем в нем виджет слоев и заполняем кнопками
        В кнопке удаления, при вызове функции, используем индекс с вычетом единицы(-1), т.к. отсчет в списках(list) начинается с нуля.
        """
        print(patch_to_script)
        name_script = re.search(r'[^\\]+.txt', patch_to_script, flags=0)
        print(name_script.group(0))
        print("Кнопки для файлов готовы")
        groupbox_MS = QtWidgets.QGroupBox("№" + str(index) + " - " + name_script.group(0), self)
        self.layout_in_groupbox_MS = QtWidgets.QHBoxLayout(groupbox_MS)

        btn_run_MS = QtWidgets.QPushButton(groupbox_MS)

        if self.multi_telnet_threads.items() and patch_to_script in self.multi_telnet_threads:
            # try:
            #     if patch_to_script in self.multi_telnet_threads and self.multi_telnet_threads[patch_to_script].is_alive():
            #         print("процесс активен!!!!!")
            # except Exception as e:
            #     print (e)

            print(f'Поток с таким файлом есть: {patch_to_script}, поток={self.multi_telnet_threads}')

            btn_run_MS.setText("Остановка")
            btn_run_MS.setStyleSheet("background-color: red;")

        else:
            print(f'Поток с таким файлом отсутствует {patch_to_script}, поток={self.multi_telnet_threads}')
            btn_run_MS.setText("Запуск скрипта")
            btn_run_MS.setStyleSheet("background-color: None;")

        btn_run_MS.clicked.connect(lambda x: self.run_ms_or_ping(int(index)))

        self.layout_in_groupbox_MS.addWidget(btn_run_MS)
        btn_edit_MS = QtWidgets.QPushButton(groupbox_MS)
        btn_edit_MS.setText("Редактировать скрипт")
        btn_edit_MS.clicked.connect(lambda x: self.edit_files_of_ms_or_ping(int(index) - 1))
        # btn_edit_MS.clicked.connect(self.dialog.exec)
        self.layout_in_groupbox_MS.addWidget(btn_edit_MS)
        btn_delete_MS = QtWidgets.QPushButton(groupbox_MS)
        btn_delete_MS.setText("Удалить скрипт")
        btn_delete_MS.clicked.connect(lambda x: self.delete_file_of_ms_or_ping(int(index) - 1))
        self.layout_in_groupbox_MS.addWidget(btn_delete_MS)

        # layout_in_groupbox_SP.addStretch(1)
        return groupbox_MS

    #Script+Ping Поиск файлов для пингка и скрипта
    def find_files_of_ms_or_ping(self):
        """
        Если ранее запускалось и что-то нашел, удаляет старый список
        Потом сканирует папку и подпапки на наличие текстовых файлов
        Все текстовые файлы проверяются на совпадению по фильтру если он не пустой.
        Если фильтру не соответствует, то дальше по скрипту не идет а продолжает цикл со следующего элемента
        В найденных файлах проверяется первая строчка, которая должа быть"<SR_SCRIPT>"
        Потом создает новые кнопки для каждого найденного файла
        :return:
        """
        if self.TabWgt_MENU.currentIndex() == 0: #LДЛя скрипта
            if self.layout_ScrlArea_MS.count() > 1:
                print("Удалять все проме первой строки=" + str(self.layout_ScrlArea_MS.count()))
                for i in range(self.layout_ScrlArea_MS.count(), 1, -1):
                    print("lay" + str(self.layout_ScrlArea_MS.count()))
                    print(i)
                    sip.delete(self.layout_ScrlArea_MS.itemAt(i - 1).widget())

            # print("Ищу файлы с конфигом по содержимому <SR_SCRIPT>")
            self.list_all_path_to_scripts = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith(".txt"):
                        path_to_file = os.path.join(root, file)
                        if self.layout_ScrlArea_MS.itemAt(0).widget().layout().itemAt(2).widget().text() != "":
                            if re.search(self.layout_ScrlArea_MS.itemAt(0).widget().layout().itemAt(2).widget().text(),
                                         path_to_file) == None:
                                continue
                        print("путь к файлу= " + path_to_file)
                        f = open(path_to_file, "r")
                        line = f.readlines()
                        f.close()

                        if "<SR_SCRIPT>" in line[0]:
                            self.layout_ScrlArea_MS.addWidget(
                                self.create_btn_for_manual_scripts(path_to_file, self.layout_ScrlArea_MS.count()))
                            self.list_all_path_to_scripts.append(path_to_file)
                            print(self.list_all_path_to_scripts)
                            # self.layout_ScrlArea_MS.addWidget(self.create_btn_for_manual_scripts(file_name.group(0)))

        elif self.TabWgt_MENU.currentIndex() == 2: #Для пинга
            if self.layout_scrollArea_ping_lists.count() > 1:
                print("Удалять все проме первой строки=" + str(self.layout_scrollArea_ping_lists.count()))
                for i in range(self.layout_scrollArea_ping_lists.count(), 1, -1):
                    print("lay" + str(self.layout_scrollArea_ping_lists.count()))
                    print(i)
                    sip.delete(self.layout_scrollArea_ping_lists.itemAt(i - 1).widget())

            # print("Ищу файлы с конфигом по содержимому <SR_SCRIPT>")
            self.list_all_path_to_ping_ip = []
            for root, dirs, files in os.walk("."):
                for file in files:
                    if file.endswith(".txt"):
                        path_to_file = os.path.join(root, file)
                        if self.layout_scrollArea_ping_lists.itemAt(0).widget().layout().itemAt(2).widget().text() != "":
                            if re.search(self.layout_scrollArea_ping_lists.itemAt(0).widget().layout().itemAt(2).widget().text(),
                                         path_to_file) == None:
                                continue
                        print("путь к файлу= " + path_to_file)
                        f = open(path_to_file, "r")
                        line = f.readlines()
                        f.close()
                        if "<SR_PING_LIST>" in line[0]:

                            self.layout_scrollArea_ping_lists.addWidget(self.create_btn_for_ping_lists(path_to_file, self.layout_scrollArea_ping_lists.count()))
                            self.list_all_path_to_ping_ip.append(path_to_file)
                            print(self.list_all_path_to_ping_ip)

    #Script+Ping, общая функция для редактирования файлов
    def edit_files_of_ms_or_ping(self, index):
        """
        Выполняется при открытии окна редавтирования файла скрита\пинга
        Создаем глобальную переменную для хранения пути к файлу со скриптом
        Очищаем поле ввода текста
        Отображаем окно
        :param index:Присваеваем глобальной переменной данные. Открываем файл со скриптами, находя его по списку, получив индекс из предыдущей фукции от нажатой кнопки
        :return: Построчно читаем файл, заполняем текстовое поле содержимым файла.
        """
        self.temp_index_to_file=index
        self.DW_FoS.TextEdit_dw_sr.clear()
        if self.TabWgt_MENU.currentIndex() == 0:
            self.DW_FoS.setWindowTitle(self.list_all_path_to_scripts[index])
            self.DW_FoS.show()
            self.temp_path_to_file = self.list_all_path_to_scripts[index]
            file_of_script = open(self.list_all_path_to_scripts[index])
            for lines in file_of_script:  # читает все строчки файла, нужно перенести
                self.DW_FoS.TextEdit_dw_sr.append(lines.strip())
        if self.TabWgt_MENU.currentIndex() == 2:
            self.DW_FoS.setWindowTitle(self.list_all_path_to_ping_ip[index])
            self.DW_FoS.show()
            self.temp_path_to_file = self.list_all_path_to_ping_ip[index]
            file_of_script = open(self.list_all_path_to_ping_ip[index])
            for lines in file_of_script:  # читает все строчки файла, нужно перенести
                self.DW_FoS.TextEdit_dw_sr.append(lines.strip())

    #Script+Ping, общая функция для создания файлов
    def create_new_file_of_ms_or_ping(self):
        """
        Используем Try т.к. при вызове фунции могут быть некорректный ввод ноового имени файла
        :return:
        После ввода данных создает файл
        Записывает строчку для дальнейшец инициализации в списке
        Обновления списка для тображения нового файла.
        """
        print("Создаем новый файл")
        try:
            with open(self.Dialog_new_name_files_of_ms_or_ping().strip() + '.txt', 'a') as f:
                if self.TabWgt_MENU.currentIndex() == 0:
                    f.write("<SR_SCRIPT>\n")
                    f.write("<RUN>")
                elif self.TabWgt_MENU.currentIndex() == 2:
                    f.write("<SR_PING_LIST>\n")

                f.close()
            self.find_files_of_ms_or_ping()
        except:
            print("отмена")

    #Script+Ping, бщая функция для переименования файлов
    def Dialog_new_name_files_of_ms_or_ping(self):
        """
        :return:
        Вызывает диалоговое окно для ввода имени файла
        В функциях с испольованием этого окна используется Try чтобы без вылетов отрабатывалась кнопка отмены и закрытия
        """
        print("Задать имя новому файлу")
        text, ok = QInputDialog.getText(self, 'Сменить имя', 'Введите имя файла:')
        if ok:
            return text

    # Script+Ping, переименовать файл
    def rename_files_of_ms_or_ping(self):
        """
        Создаем временную переменную с путем к файлу с вырезом его имени в конце строки (вырезаем часть и глобальной, временной переменной с путем к файлу, по индексу)
        Содаем переменную с новым именем на основе функции диалога
        :return:
                Если имя введено(не пустое)
                Выполняется переименование с уазанием временной переменной и нового пути на основе новых переменных
                Меняем заголовок окна на новый путь к файлу
                Обновляем список файлов с их новыми именам
        """
        try:
            print("Переименовать файл")
            temp_patch_without_name = ' '.join(re.split(r'\w+.txt', self.temp_path_to_file))
            print(self.temp_path_to_file)
            new_name = self.Dialog_new_name_files_of_ms_or_ping().strip()
            if new_name != "":
                os.rename(self.temp_path_to_file, temp_patch_without_name.strip() + new_name + ".txt")
            self.DW_FoS.setWindowTitle(temp_patch_without_name.strip() + new_name + ".txt")
            self.find_files_of_ms_or_ping()

        except:
            print("Отмена")

    #Script+Ping, сохранение файла, выполняется при нажатии кнопки
    def save_edited_files_of_ms_or_ping(self):
        """
        Создаем временную переменную mytext и заносим туда текст из окна редактироывания
        :return:
        Если в окне редактирования затерли марке <SR_SCRIPT> программа не сможет найти этот файл потом,
        поэтому дописваем эту строчку в начале а потом добавлем строчки из окна редактирования.
        Если строчка имеется, переписываем все строки
        Очищаем окно редактирования
        Переоткрываем файл для отображения содержимого
        """
        print("Сохранить файл")
        mytext = self.DW_FoS.TextEdit_dw_sr.toPlainText()
        if self.TabWgt_MENU.currentIndex() == 0:
            if mytext[
               0:11] != "<SR_SCRIPT>":  # !!!!!!!!!!!!!!!!!!!!Если поменяем текст метки, нужно поменять количество символов, сейчас 0:11=11 для <SR_SCRIPT>
                f = open(self.temp_path_to_file, "w")
                f.write("<SR_SCRIPT>\n")
                f.write(mytext)
            else:
                open(self.temp_path_to_file, "w").write(mytext)
        elif self.TabWgt_MENU.currentIndex() == 2:
            if mytext[
               0:14] != "<SR_PING_LIST>":  # !!!!!!!!!!!!!!!!!!!!Если поменяем текст метки, нужно поменять количество символов, сейчас 0:11=14 для <SR_SCRIPT>
                f = open(self.temp_path_to_file, "w")
                f.write("<SR_PING_LIST>\n")
                f.write(mytext)
            else:
                open(self.temp_path_to_file, "w").write(mytext)

        self.DW_FoS.TextEdit_dw_sr.clear()
        f = open(self.temp_path_to_file)
        for lines in f:  # читает все строчки файла, нужно перенести
            self.DW_FoS.TextEdit_dw_sr.append(lines.strip())

    # Script+Ping, удаление файла
    def delete_file_of_ms_or_ping(self, index):
        """
        :param index:  Используя индекс (приходит с -1 чтобы список проходил с 0)
        :return:
        Удаляем файл на основе пути найденного в списке self.list_all_path_to_scripts
        Запускаем функцию обновления списка файлов скриптов чтобы удаленный ушел из списка.
        """
        if self.TabWgt_MENU.currentIndex() == 0:
            os.remove(self.list_all_path_to_scripts[index])
        if self.TabWgt_MENU.currentIndex() == 2:
            os.remove(self.list_all_path_to_ping_ip[index])
        self.find_files_of_ms_or_ping()

    #!!!!SWICH, Подумать о словаре вместо кортежа для данной функции
    def create_corteg_SP(self):
        """
        Создание Список
        Очищается
        Создается переключатель чтобы не собирать кортеж если тип порта не создан
        Если окно с пец портами открыто и добавлен хоть один порт
        Перебираем первый слой чтобы перебрать второй слой в котором находятся конечные виджеты
        дальше из них выдернивается текст если выбран тип порта
        Gрисваеваем лист кортежу"""

        list_SP = []  # Очищаем лист
        type_ports = False  # Переменная отвечает за сбор данных если тип порта выбран

        if self.btn_del_SP.isVisible() and self.layout_ScrlArea_SP.count() > 0:
            for x_in_ScrlArea_SP in range(self.layout_ScrlArea_SP.count()):
                for y_in_groupbox_SP in range(self.layout_in_groupbox_SP.count()):
                    if isinstance(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(
                            y_in_groupbox_SP).widget(), QtWidgets.QComboBox):
                        if self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(
                                y_in_groupbox_SP).widget().currentText() != "Выбрать":
                            type_ports = True
                            list_SP.append(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(
                                y_in_groupbox_SP).widget().currentText())
                        else:
                            type_ports = False
                        print(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(
                            y_in_groupbox_SP).widget().currentText())
                    else:
                        if type_ports == True:
                            list_SP.append(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(
                                y_in_groupbox_SP).widget().text())
                        print(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(
                            y_in_groupbox_SP).widget().text())
            list_SP = list(filter(None, list_SP))  # Чистим список от пустых полей
            print(list_SP)
            corteg_SP = tuple(list_SP)
            print(corteg_SP)

            # if self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(0).widget().currentText() != "Выбрать":

            # print(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(0).widget().currentText())
            # print(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(1).widget().text())
            # print(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(2).widget().text())
            # print(self.layout_ScrlArea_SP.itemAt(x_in_ScrlArea_SP).widget().layout().itemAt(3).widget().text())

    # SWICH, добавить спец порт
    def add_SP(self):
        """
        Создает лайаут в ScrlArea_SP выполняя доп функцию по его заполнению groupbox'ами с лайаутом
        :return:
        """
        print("layout_ScrlArea_SP= ", self.layout_ScrlArea_SP.count())
        self.layout_ScrlArea_SP.addWidget(self.createLayout_groupbox_SP(self.layout_ScrlArea_SP.count() + 1))

    # SWICH, создает строки для настройки спец портов
    def createLayout_groupbox_SP(self, number):
        groupbox_SP = QtWidgets.QGroupBox("Port-{}:".format(number), self)
        self.layout_in_groupbox_SP = QtWidgets.QHBoxLayout(groupbox_SP)
        combobox_type_ports = QtWidgets.QComboBox(groupbox_SP)
        combobox_type_ports.addItems(list_type_ports)
        combobox_type_ports.activated.connect(lambda x: self.select_combobox_type_ports(combobox_type_ports))
        num_SP = QtWidgets.QLineEdit(groupbox_SP)
        num_SP.setPlaceholderText("№")
        num_SP.setFixedSize(20, 20)
        name_port = QtWidgets.QLineEdit(groupbox_SP)
        name_port.setPlaceholderText("Подпись")
        untagged_vlan = QtWidgets.QLineEdit(groupbox_SP)
        untagged_vlan.setPlaceholderText("untagVL")
        tagget_vlan = QtWidgets.QLineEdit(groupbox_SP)
        tagget_vlan.setPlaceholderText("tagVL")
        self.layout_in_groupbox_SP.addWidget(combobox_type_ports)
        self.layout_in_groupbox_SP.addWidget(num_SP)
        self.layout_in_groupbox_SP.addWidget(name_port)
        self.layout_in_groupbox_SP.addWidget(untagged_vlan)
        self.layout_in_groupbox_SP.addWidget(tagget_vlan)
        # layout_in_groupbox_SP.addStretch(1)
        return groupbox_SP

    # SWICH, переключение спец портов
    def select_combobox_type_ports(self, index):
        """
        [u"Выбрать", u"Подписать", u"ОП", u"УСИ",u"Физ.Лицо", u"Распред_Порт",u"Юр.Лицо",u"РМ",u"HS_ZT",u"IPoE",u"Сигнализатор,u"КС""
        itemAt(1)-номер порта настройки
        itemAt(2)-Подпись порта
        itemAt(3)-untagged влан
        itemAt(4)-tagged влан
        Где ненадо лишних ячеек, скрваем их и чистим текст для нормальной сборки листа\кортежа
        """
        if index.currentText() == "Подписать" or index.currentText() == "ОП" or index.currentText() == "УСИ":
            index.parent().layout().itemAt(2).widget().show()
            index.parent().layout().itemAt(3).widget().hide()
            index.parent().layout().itemAt(3).widget().setText("")
            index.parent().layout().itemAt(4).widget().hide()
            index.parent().layout().itemAt(4).widget().setText("")

        if index.currentText() == "Физ.Лицо" or index.currentText() == "Распред_Порт" or index.currentText() == "Юр.Лицо" or index.currentText() == "РМ" or index.currentText() == "HS_ZT" or index.currentText() == "Сигнализатор":
            index.parent().layout().itemAt(2).widget().hide()
            index.parent().layout().itemAt(2).widget().setText("")
            index.parent().layout().itemAt(3).widget().hide()
            index.parent().layout().itemAt(3).widget().setText("")
            index.parent().layout().itemAt(4).widget().hide()
            index.parent().layout().itemAt(4).widget().setText("")

        if index.currentText() == "Выбрать" or index.currentText() == "КС":
            index.parent().layout().itemAt(2).widget().show()
            index.parent().layout().itemAt(3).widget().show()
            index.parent().layout().itemAt(4).widget().show()

    # SWICH, удалить порт из списка
    def dell_SP(self):
        """
        Если в списке портов есть хоть один добавленный порт
        :return:
        Удаляется последний порт в списке
        """
        if self.layout_ScrlArea_SP.count() > 0:
            sip.delete(self.layout_ScrlArea_SP.itemAt(self.layout_ScrlArea_SP.count() - 1).widget())
            print("layout_ScrlArea_SP= ", self.layout_ScrlArea_SP.count())

    # !!SWICH раздел
                    #Функция выполняется из двух мест, прописка портов и прописка коммутатора по меди
                    #надо усложнить для выбора предназначения в зависимости от запроса и определить какие переменные передвть в поток

    def btn_config_SP_start(self):

        """"Кнопка на в разделе *настройка по меди*"""
        # tl=threading.Thread(target=self.write_by_cooper)
        tl = threading.Thread(target=self.create_corteg_SP)
        tl.start()

        print("Проверка?!")

    # Диагностика, обновление меню
    def update_menu_com_ports(self):
        if self.btn_run_repair.setText("RUN"):
            self.serialPort.close()

        self.comboBox_com_port.clear()
        for text in find_serial_ports():
            print("Список портов для меню", text)
            self.comboBox_com_port.addItem(str(text))

    #Диагностика, запуск потока бут меню
    def run_thread_serial_port(self, text):
        print("ну тыкни уже", text)
        if text == "RUN":
            self.btn_run_repair.setText("STOP")
            self.thread_run_serial_port = threading.Thread(target=self.run_serial)
            self.thread_run_serial_port.start()
        else:
            self.btn_run_repair.setText("RUN")

    # Диагностика, скрипт для сброса
    def run_serial(self):
        try:
            self.serialPort.close()
            print("Консоль отключена")
        except:
            print ("Коносль еще не подключена")
        # print("запуск серийного порта", self.comboBox_com_port.currentText())
        while self.btn_run_repair.text() == "STOP":
            if self.CB_repeat_operations.isChecked():
                print("Проверяем репит!!!!!")
                list_repair_operation=(self.CB_reset_password.isChecked(),self.CB_reset_swich.isChecked(),self.CB_image_change.isChecked())
                print(list_repair_operation)
            # QtCore.QThread.msleep(1000)
            print(str(self.comboBox_com_port.currentText()), str(self.comboBox_speed_com.currentText()))
            self.serialPort = serial.Serial(port=str(self.comboBox_com_port.currentText()),
                                            baudrate=int(self.comboBox_speed_com.currentText()), bytesize=8, timeout=2,
                                            stopbits=serial.STOPBITS_ONE)
            serialString = ""  # Used to hold data coming over UART
            while self.btn_run_repair.text() == "STOP":
                # Wait until there is data waiting in the serial buffer
                if self.serialPort.in_waiting > 0:
                    # Проверяем галочку повтора операций


                    try:
                        line = self.serialPort.read_until(b"\r").decode("Ascii")
                        #исключение пустых строк, чтобы их не выводить
                        if line.strip() != (""):
                            print(line)
                            self.Wind_Log.TxtBr_Wind_Log.append(" ===COM=== " + line)
                            if self.CB_reset_password.isChecked():
                                self.run_CB_reset_password(line)
                                continue
                            elif self.CB_reset_swich.isChecked():
                                self.run_CB_reset_swich(line)
                                continue
                            elif self.CB_image_change.isChecked():
                                self.run_CB_image_change(line)
                                continue
                            elif self.CB_repeat_operations.isChecked():
                                self.CB_reset_password.setChecked(bool(list_repair_operation[0]))
                                self.CB_reset_swich.setChecked(bool(list_repair_operation[1]))
                                self.CB_image_change.setChecked(bool(list_repair_operation[2]))
                                continue

                    except:
                        self.serialPort.close()
                        print("возможно обрыв связи")
                        self.serialPort = serial.Serial(port=str(self.comboBox_com_port.currentText()),
                                                        baudrate=int(self.comboBox_speed_com.currentText()),
                                                        bytesize=8, timeout=2,
                                                        stopbits=serial.STOPBITS_ONE)
                        continue

    # Диагностика, часть скрипта для сброса
    def run_CB_reset_password(self, line):
        """Выполняет алгоритм для сброса пароля"""
        print("Сброс пароля")
        if "Hit any key to stop autoboot:" in line:
            self.serialPort.write(bytes("b\r", encoding='ascii'))
        elif "Enter your choice(0-6)" in line:
            self.serialPort.write(bytes("6\r", encoding='ascii'))
        elif "Enter your choice(0-5)" in line:
            print("В этой моделе нет сброса учетки")
            self.CB_reset_password.setChecked(False)

        elif "This will delete all the previously created accounts. Continue?[Y/N]:" in line:
            self.serialPort.write(bytes("y\r", encoding='ascii'))
        elif "Operation OK!" in line:
            self.serialPort.write(bytes("0\r", encoding='ascii'))
            self.CB_reset_password.setChecked(False)

    # Диагностика, часть скрипта для сброса
    def run_CB_reset_swich(self, line):
        """Выполняет алгоритм для сброса настроек"""
        print("Сброс до заводских")
        if "Hit any key to stop autoboot:" in line:
            self.serialPort.write(bytes("b\r", encoding='ascii'))
        elif "Enter your choice" in line:
            self.serialPort.write(bytes("2\r", encoding='ascii'))
        elif "Are you sure to reset the device?[Y/N]:" in line:
            self.serialPort.write(bytes("y\r", encoding='ascii'))
        elif "resetting" in line:
            self.CB_reset_swich.setChecked(False)

    # Диагностика, часть скрипта для сброса
    def run_CB_image_change(self, line):
        """Выполняет алгоритм для смены образа загрузчика"""

        print("Смена образа Загрузчика")
        if "Hit any key to stop autoboot:" in line:
            self.serialPort.write(bytes("b\r", encoding='ascii'))
        elif "Enter your choice(0-6)" or 'Enter your choice(0-5)' in line:
            self.serialPort.write(bytes("4\r", encoding='ascii'))
        elif "Are you sure to set the Backup Image as Startup Image?[Y/N]:" in line:
            self.serialPort.write(bytes("y\r", encoding='ascii'))
        elif "1      (b)" in line:
            self.serialPort.write(bytes("1\r", encoding='ascii'))
        elif "2      (b)" in line:
            self.serialPort.write(bytes("2\r", encoding='ascii'))
        ####Текст вопроса может меняться, reset Или reboot, поэтому урезал
        elif "Are you sure" in line:
            self.serialPort.write(bytes("y\r", encoding='ascii'))
        elif "rebooting" or "resetting ..." in line:
            self.CB_image_change.setChecked(False)

    #Swich, смена оформления
    def change_comboBox_type_connect(self, index):
        """
        :param index: выбранный тип для подключения
        :return: Меняет оформление
        Пока скрывает комбобокс протокола для подключения
        !!!!!!Нужно добавть изменение оформление для строчки с ip адресом - скрывать

        """
        selected_item = self.comboBox_type_connect.itemText(index)
        print(f"ComboBox_type_connect= {index} {selected_item} ")
        if index!= 0:
            self.comboBox_type_connect_protocol.setVisible(False)
        else:
            self.comboBox_type_connect_protocol.setVisible(True)

    def __init__(self, parent=None):
        super(QT_MAIN, self).__init__(parent)
        self.Wind_Log = Wgt_Wind_Log()
        self.DW_FoS = DW_edit_file_of_script()
        self.delegate = CustomDelegate()
        self.setupUi(self)

        ##############timeline Для сцепки окон#########################
        self.w = self.size().width()
        # print("print в самом начале кода", self.w)

        self.timeline = QTimeLine(6000 * 2, self)
        self.timeline.setFrameRange(0, self.w + 100)
        self.timeline.frameChanged.connect(self.set_frame_func)
        self.timeline.setLoopCount(0)
        self.timeline.start()
        self.frame_geometry = None  # !!!

        ###############ScrlArea_ports###################
        self.btn_add_SP.setText("+1 Порт")

        self.btn_add_SP.clicked.connect(self.add_SP)
        self.btn_add_SP.setVisible(False)
        self.btn_del_SP.setText("-1 Порт")
        self.btn_del_SP.setVisible(False)

        self.btn_del_SP.clicked.connect(self.dell_SP)
        ###############TabWgt_MENU######################
        self.TabWgt_Swich.currentChanged.connect(self.ChangeTabSwich) # прявзка событий на переключение вкладки раздела SWICH
        # self.TabWgt_MENU.currentChanged.connect(self.Change_TabWgt_MENU) # прявзка событий на переключение вкладки раздела ping

        self.btn_reboot_swich.setText("REBOOT")
        self.btn_reset_swich.setText("!!!!!Reset!!!!!")
        self.CB_Wind_Log.setText("Вкл.Окно логов")
        self.CB_Wind_Log.setChecked(False)  # В скопбках отключение включение (Falls/True)
        self.CB_Wind_Log.toggled.connect(self.on_off_CB_Wind_Log)
        ################Wgt_SWICH#######################
        self.ScrlArea_ports.setVisible(False)

        self.CB_enter_pass.setText("Использовать пароль города")
        self.Laaauser.setText("UserName=")
        self.Laaapass.setText("Password=")
        self.Lhost_connect.setText("Connect to=")
        self.combobox_city.addItems(combobox_city)
        self.Eaaauser.setText(Eaaauser)
        self.Eaaapass.setText(Eaaapass)
        self.Ehost_connect.setText(Ehost_connect)
        self.Ehost_connect.cursorPositionChanged.connect(self.stop_ping_check_host_decor) # привязываем к установке курсора отмену скрипта
        # self.Ehost_connect.setStyleSheet("color: red")
        # user_Ehost_connect=self.Ehost_connect.text()

        ################TabWgt_Swich####################
        # создадим поток
        # self.ping_thread = PingThread(self.Ehost_connect.text())
        # self.ping_thread.ping_signal.connect(self.run_ping_decor_menu)
        # self.ping_thread.start()
        #
        self.CB_swich_ping_host.setChecked(False) #переключатель пинг потока
        self.CB_swich_ping_host.clicked.connect(self.run_CB_swich_ping_host)
        self.CB_host_group.setChecked(False) #переключатель списка ip
        self.CB_host_group.clicked.connect(self.check_list_host)
        self.btn_more_ip.setVisible(False) #отключаем кнопку для ввода списка хостов
        self.combobox_list_ip.setVisible(False) #отключаем окно с списком хостов
        self.comboBox_type_connect.addItems(["По сети(IP)","Через стенд(IP)","Через Console(COM)"])
        self.comboBox_type_connect.currentIndexChanged.connect(self.change_comboBox_type_connect)
        self.comboBox_type_connect_protocol.addItems(["Telnet","Shh"])
        self.layout_ScrlArea_SP = QtWidgets.QVBoxLayout(
            self.Wgt_for_ScrlArea_ports)  # лайаут для настройки ук и спец портов, видим на первых двух вкладках
        self.layout_ScrlArea_MS = QtWidgets.QVBoxLayout(self.Wgt_for_ScrlArea_MS)  # лайаут видим на вкладке мои скрипты
        self.layout_ScrlArea_MS.addWidget(self.create_first_btn_manual_scripts())  # Добавляем стартовую кнопку

        self.btn_fw_update_manual.setText("Обновить Прошивку")
        self.btn_write_coper.setText("-Прописать-")
        self.btn_write_coper.clicked.connect(lambda: self.btn_write_coper_start(self.btn_write_coper.text()))
        self.CB_fw_update_auto.setText("Автообновление FW")
        self.CB_fw_update_auto.setChecked(True)  # Включено при запуске
        self.CB_vl_an_ports.setText("Один влан на все клиентские порты")
        self.CB_manual_set_network.setText("Доп. настройки")
        self.CB_manual_set_network.setChecked(False)  # Отключено при запуске
        self.CB_manual_set_network.toggled.connect(self.on_off_CB_manual_set_network)
        self.CB_ShowPorts.setText("Показать порты")
        self.CB_ShowPorts.toggled.connect(self.ChangeTabSwich)

        self.Lhost.setText("New ip=")
        self.Lmask.setText("Mask=")  ###### Cкрыты при запуске
        self.Lmask.setVisible(False)  ### Cкрыты при запуске
        self.Lgwkom.setText("GateWay=")  #### Cкрыты при запуске
        self.Lgwkom.setVisible(False)  ## Cкрыты при запуске
        self.Lhostname.setText("HostName=")
        self.Lmgmvlan.setText("MGM_Vlan=")
        self.Lpcvlan.setText("PCVlan=")
        self.Loutport.setText("Распред порт начальный=")
        self.Ehost.setText(Ehost)
        self.Emask.setText(Emask)  ###### Cкрыты при запуске
        self.Emask.setVisible(False)  ### Cкрыты при запуске
        self.Egwkom.setText(Egwkom)  #### Cкрыты при запуске
        self.Egwkom.setVisible(False)  ## Cкрыты при запуске
        self.Ehostname.setText(Ehostname)
        self.Emgmvlan.setText(Emgmvlan)
        self.Epcvlan.setText(Epcvlan)
        self.Eoutport.setText(Eoutport)

        ################Nastroyka_portov####################
        self.btn_config_SP.setText("-Настроить-")
        self.btn_config_SP.clicked.connect(self.btn_config_SP_start)


        ###############Manual scripts#######################################
        self.btn_more_ip.setVisible(
            False)  # кнопка для вызыва окна для ввода дополнительных ip, прячем при старте программы
        self.btn_more_ip.clicked.connect(lambda x: self.run_btn_more_ip())

        ###############################################################
        ######################
        # ####PING######################################
        # кнопка для вызыва окна для ввода дополнительных ip, в разделе ping

        self.layout_scrollArea_ping_lists = QtWidgets.QVBoxLayout(self.Wgt_for_scrollArea_ping_lists)  # лайаут видим на вкладкеgbyu
        self.layout_scrollArea_ping_lists.addWidget(self.create_first_btn_ping_lists())  # Добавляем стартовую кнопку пинг

        self.DW_FoS.btn_run_files_sr.clicked.connect(lambda x: self.run_ms_or_ping(self.DW_FoS.TextEdit_dw_sr.toPlainText()))
        self.DW_FoS.btn_rename_files_sr.clicked.connect(lambda x: self.rename_files_of_ms_or_ping())
        self.DW_FoS.btn_save_files_sr.clicked.connect(lambda x: self.save_edited_files_of_ms_or_ping())
        self.multi_ping_threads={} #при запуске программы создает пустой словарь для потоков пинга
        self.multi_telnet_threads = {}
        self.list_more_ip = [] #Создаем будующий список хостов для пинга\подключения
        ###############################################################
        ###################DW_edit_file_of_script#######################
        # self.btn_ping_stop_multi.setEnabled(False)

        self.btn_update_menu_com_ports.clicked.connect(self.update_menu_com_ports)
        self.update_menu_com_ports()

        #####################
        """Кнопка для запуска потока с функциями по работе с сом портами"""
        self.btn_run_repair.clicked.connect(lambda x: self.run_thread_serial_port(self.btn_run_repair.text()))


        # self.ping_thread.ping_color_signal.connect(self.update_color_ping)

class DW_edit_file_of_script(QtWidgets.QMainWindow, Ui_DW_edit_file_of_script):
    """QW_Wind_Log название класса в основной программу и имя конвертированного файла,
        Ui_QW_Wind_Log название класса в файле PYQT5
        Вызывает окно,добавлет дополнительные параметры и выполняет часть функций"""

    def __init__(self, parent=None):
        super(DW_edit_file_of_script, self).__init__(parent)

        self.setupUi(self)

class Wgt_Wind_Log(QtWidgets.QMainWindow, Ui_Wgt_Wind_Log):
    """QW_Wind_Log название класса в основной программу и имя конвертированного файла,
        Ui_QW_Wind_Log название класса в файле PYQT5
        Вызывает окно,добавлет дополнительные параметры и выполняет часть функций"""

    def __init__(self, parent=None):
        super(Wgt_Wind_Log, self).__init__(parent)

        self.setupUi(self)
        # self.setWindowFlags(
        #     QtCore.Qt.Window | QtCore.Qt.CustomizeWindowHint | QtCore.Qt.WindowStaysOnTopHint)  # Запрещает передвигать отключив панель заголовка
        self.btn_clear_log.clicked.connect(self.run_btn_clear_log)

    def run_btn_clear_log(self):
        print("Очистить окно логов")
        self.TxtBr_Wind_Log.clear()

class CustomDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        # Вызываем базовый метод paint()
        super().paint(painter, option, index)

        # Получаем модель данных
        model = index.model()

        # Получаем значение текущей строки
        value = model.data(index)

        # Получаем цвет для текущей строки
        color = QColor(Qt.white)
        x = int(strftime("%S"))
        if x % 2 != 0:
            if value == "Red":
                color = QColor(Qt.green)
            elif value == "Green":
                color = QColor(Qt.red)
            elif value == "Blue":
                color = QColor(Qt.green)
        else:
            if value == "Red":
                color = QColor(Qt.red)
            elif value == "Green":
                color = QColor(Qt.green)
            elif value == "Blue":
                color = QColor(Qt.red)

        # Устанавливаем цвет фона и текста для текущей строки
        painter.fillRect(option.rect, color)
        painter.setPen(color)
        painter.drawText(option.rect, Qt.AlignCenter, value)


if __name__ == '__main__':
    import sys

    app = QtWidgets.QApplication(sys.argv)
    window = QT_MAIN()
    window2 = Wgt_Wind_Log(

        window)  # В скобки вписал окно от которого будет зависить второе окно, чтобы закрывалось вместе с ним
    # window.move(window.width() * -3, 0) # Говорят надо так убирать окно за рамку чтобы не моргало, пока не понадобилось

    window.move(0, 0)
    window.show()
    sys.exit(app.exec_())





