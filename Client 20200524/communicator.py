# -*- coding: utf-8 -*-
# @Time    : 2020/5/21 18:25
# @Author  : Mat
# @Email   : mat_wu@163.com
# @File    : communicator.py
# @Software: PyCharm

import serial
import serial.tools.list_ports
from socket import *
import re
import random
import tkinter.messagebox as message_box
import tkinter.simpledialog as entry_box
from threading import *


class Serial_c:
    def __init__(self, queue_to_dp):
        self.__tdp = queue_to_dp
        self.__serial = None

    def config_serial(self, baud=115200):
        while True:
            __ports = list(map(lambda s: str(s).split(' ')[0], serial.tools.list_ports.comports()))
            if len(__ports) == 0:
                if message_box.askretrycancel(
                        title='Find ports.',
                        message='No Serial Port Available.\n'
                                'Please check the ports and try again.'):
                    continue
                else:
                    return False

            __input_port = entry_box.askstring(
                title='Input Port',
                prompt='Please input port from {}'.format(__ports),
                initialvalue='{}'.format(__ports[-1])
            )

            if not __input_port:
                return False

            if __input_port in __ports:
                try:
                    self.__serial = serial.Serial(__input_port, baud)
                    message_box.showinfo(title='Success！',
                                         message='Serial Started.')
                    return True
                except Exception as e:
                    message_box.showerror(title='Fail',
                                          message='Serial Started Failed.\n{}'.format(e))
                    continue
            else:
                message_box.showerror(title='Fail',
                                      message='Serial Started Failed.\nCan\'t Find This Port.')
                continue

    def start_serial_communication(self):
        self.__serial.flushInput()
        self.__serial.flushOutput()
        yield "Starting serial communication, please wait a moment..."
        while True:

            begin_serial_data = self.__serial.readline()
            if begin_serial_data == b's\n':
                break
        serial_communication_thread_r = Thread(target=self.__communication_r, args=('[',))
        serial_communication_thread_r.setDaemon(True)
        serial_communication_thread_r.start()
        yield "Started serial read threading..."

    def writer(self, se_output_data, end_mark=']'):
        try:
            se_output_data += end_mark
            self.__serial.write(se_output_data.encode())
            return "Serial Data has been Sent."
        except Exception as e:
            return e

    def __communication_r(self, end_mark):
        # 获取serial数据的一个字符，添加到字符串，当收到的字符为终止符时，将字符串发送给数据中心，并清空字符串。
        se_input_data = ''
        while True:
            try:
                read_d = self.__serial.read().decode()
                if read_d == end_mark:
                    se_receiver_data2 = se_input_data[:-1]
                    # print(se_receiver_data2)
                    self.__tdp.put(se_receiver_data2)
                    se_input_data = ''
                else:
                    se_input_data += read_d
            except Exception as e:
                return e


class Socket_c:
    def __init__(self, queue_to_dp):
        self.__tdp = queue_to_dp
        self.__socket = socket(AF_INET, SOCK_STREAM)
        self.__type = "SERIAL"
        self.__client_id = None
        self.__paired = None

    def config_socket(self):
        __ip_pattern = re.compile(r'((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})(\.((2(5[0-5]|[0-4]\d))|[0-1]?\d{1,2})){3}')
        __port_pattern = re.compile(r'\d{4}')

        while True:
            __server_ip = entry_box.askstring(
                title="Connect Server",
                prompt='Please Input the IP address of the server.',
                initialvalue='127.0.0.1')
            if not __server_ip:
                message_box.showerror(title='Error',
                                      message='Quit.')
                return False
            if not __ip_pattern.match(__server_ip):
                message_box.showerror(title='Wrong IP Address',
                                      message='Please input again.')
                continue

            __server_port = entry_box.askstring(title="Connect Server",
                                            prompt='Please Input the port of the server.',
                                            initialvalue='9999')
            if not __server_port:
                message_box.showerror(title='Error',
                                      message='Quit.')
                return False

            if not __port_pattern.match(__server_port):
                message_box.showerror(title='Wrong IP port',
                                      message='Please input again.')
                continue

            __server_port_int = eval(__server_port)
            try:
                self.__socket.connect((__server_ip, __server_port_int))
                return True
            except Exception as e:
                print('socket.connect', e)
                if message_box.askretrycancel(title='Failed',
                                              message='Failed to connect to the server.'):
                    continue
                else:
                    return False

    def start_socket_communication(self):
        __fourth_handshake_process_result = self._fourth_handshake_process()
        if __fourth_handshake_process_result is not False:
            self.__client_id = __fourth_handshake_process_result
        yield __fourth_handshake_process_result
        create_send_room_result = self._create_send_room()
        yield create_send_room_result

        socket_communication_thread_r = Thread(target=self._receiver, args=())
        socket_communication_thread_r.setDaemon(True)
        socket_communication_thread_r.start()
        yield "Started socket receiving threading..."

    def _fourth_handshake_process(self):
        try:
            __fhp_message = self.__socket.recv(1024).decode('utf-8')
            __client_type = None
            type_list = eval(__fhp_message[3:])
            print(type_list)
            if self.__type in type_list:
                __client_type = self.__type
            self.__socket.send(str(__client_type).encode("UTF-8"))

            while True:
                __server_messages = re.split(r'//', self.__socket.recv(1024).decode('utf-8'))
                if __server_messages[0] == 'S':
                    if __server_messages[1] == 'A':
                        __client_id = entry_box.askstring(
                            title="Create Client",
                            prompt='Please Input your client ID.\n\
                                    Others can find you and match by ID.\n',
                            initialvalue='User{}'.format(random.randint(0, 999))
                        )
                        if not __client_id:
                            message_box.showerror(title='Error',
                                                  message='Quit.')
                            return False
                        self.__socket.send(__client_id.encode("UTF-8"))
                        continue
                    if __server_messages[1] == 'E':
                        message_box.showerror(title='Create Client',
                                              message=__server_messages[2])
                        continue
                    if __server_messages[1] == 'ID':
                        message_box.showinfo(
                            title='Create Client',
                            message="Success! This is your ID :: {}".format(__server_messages[2])
                        )
                        message_box.showinfo(
                            title='Create Client',
                            message=self.__socket.recv(1024).decode('utf-8')
                        )
                        return __server_messages[2]
        except Exception as e:
            print("_fourth_handshake_process", e)
            return False

    def _create_send_room(self):
        try:
            self.__socket.send("cr {}".format(self.__client_id).encode("UTF-8"))
            __server_messages = re.split(r'//', self.__socket.recv(1024).decode('utf-8'))
            if __server_messages[0] == 'S' and __server_messages[1] == 'O':
                return True
        except Exception as e:
            print("create_send_room",e)
            return False

    def send_command(self, message):
        __socket_message = "sr {} {}".format(self.__client_id, message)
        try:
            self.__socket.send(__socket_message.encode("UTF-8"))
        except Exception as e:
            print("command_sender", e)
        return

    def send(self, message):
        try:
            self.__socket.send(message.encode("UTF-8"))
        except Exception as e:
            print("sender", e)
        return

    def set_pairing_status(self, client_id):
        self.__paired = client_id
        return

    @property
    def get_paired_status(self):
        return self.__paired

    def _receiver(self):
        while True:
            try:
                so_receiver_data_list = re.split(r'//', self.__socket.recv(1024).decode('utf-8'))
                if so_receiver_data_list[0] == "S" and \
                        so_receiver_data_list[1] == "O":
                    self.__tdp.put("S//O//OK")
                    continue
                if so_receiver_data_list[0] == "D":
                    if not self.__paired and \
                            so_receiver_data_list[-1] == "REQUEST PAIRING":
                        self.__tdp.put(so_receiver_data_list[1])
                        continue
                    if so_receiver_data_list[1] == self.__paired:
                        self.__tdp.put(so_receiver_data_list[-1])
            except:
                return
