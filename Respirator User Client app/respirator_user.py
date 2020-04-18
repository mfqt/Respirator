# coding=utf-8

"""
command

"""


# 重要！！！
# python中子进程不支持input()函数输入



from socket import *
from threading import Thread

class ClientUser:
    def __init__(self, clientType="normal"):
        self.__sock = socket(AF_INET, SOCK_STREAM)
        self.__type = clientType
        self.__receive_process = None

    def run_client(self):
        self.__sock.connect(('127.0.0.1', 9999))
        self._fourth_handshake_process()
        self.__receive_process = Thread(target= self._receive_process , args=())

        self.__receive_process.start()
        self.main_process()
        # print("receive process close")
        self.__sock.close()
        # print("socket close")

    def _fourth_handshake_process(self):
        message = self.__sock.recv(100).decode('utf-8')
        client_type = None
        type_list = eval(message)
        print(type_list)
        if self.__type in type_list:
            client_type = self.__type
        self.__sock.send(str(client_type).encode("UTF-8"))
        return

    def _receive_process(self):
        print("start receive")
        while True:
            # socket有可能已经关闭了。
            try:
                print(self.__sock.recv(1024).decode('utf-8'))
            except:
                break


    # def check_command_format(self, command):
    #     command0, message_str, command1 = command.partition(' ')
    #     if self.__type == "normal":
    #         if command0 == "cr":



    def main_process(self):
        while True:
            data = input()
            if data.lower() == 'q':
                return

            self.__sock.send(data.encode('utf-8'))


if __name__ == '__main__':

    user = ClientUser("serial")
    user.run_client()