# coding=utf-8
"""
连接客户端，从客户端获取信息，向命令处理器发送请求。
"""


from multiprocessing import Process, Pipe
from threading import Thread
from socket import*
from RespiratorServer import respirator_client


class _Server:

    def __init__(self, queue, max_number_of_clients_to_connect):
        self.__queue = queue
        self.__max = max_number_of_clients_to_connect
        self.__TYPE_NAME_LIST = [ "normal" ]
        self.__CLIENT_TYPES_LIST = [respirator_client.NormalClient, respirator_client.SerialClient]

        self.__TYPE_LIST = {"normal": ("CNC1", respirator_client.NormalClient),
                            "serial": ("CNC2", respirator_client.SerialClient)}
        self.__server_process = None


class Server(_Server):

    def run_server(self):
        __server_process = Process(target=self._server_process, args=())
        __server_process.start()

    def join(self):
        self.__server_process.join()

    def __get_client_type(self, client_socket):
        """从客户端获取客户端类型"""
        client_socket.send(str(list(self.__TYPE_LIST.keys())).encode("UTF-8"))
        client_type = client_socket.recv(20).decode("UTF-8")
        if client_type in self.__TYPE_LIST.keys():
            return client_type
        return None

    def __create_client_id(self, client_type, client_socket, client_pipe, client_information):
        """
        获取客户端ID，并检查是否可用
        只给5次机会，8次机会之后要重新连接再试
        """
        chance_number = 5
        while chance_number >= 1:

            client_socket.send("You have {} chances to Create client ID.\nPlease input your ID:: ".format(chance_number).encode("UTF-8"))

            client_id = client_socket.recv(1024).decode("UTF-8")

            if ' ' in client_id:
                client_socket.send("Create client ID FILED. You cannot use space characters in id.".encode("UTF-8"))
                chance_number -= 1
                continue

            _input, _output = client_pipe

            request_message = (self.__TYPE_LIST[client_type][0], client_id, _input, client_information)

            self.__queue.put(request_message)

            result = _output.recv()

            if isinstance(result, Exception):
                __mess = "Create client ID FLIED. This ID is already used."
                client_socket.send(__mess.encode("UTF-8"))
                chance_number -= 1
                continue
            else:
                return client_id
        client_socket.send("Create new client FAILED. Please connect again.".encode("UTF-8"))
        return False

    def _fourth_handshake(self, client_socket, client_pipe, client_information):
        """获取客户端类型和ID的过程。TCP连接三次握手后，自动完成。"""

        client_type = self.__get_client_type(client_socket)

        if client_type is None:
            client_type = "normal"

        try:
            client_id = self.__create_client_id(client_type, client_socket, client_pipe, client_information)
            if not client_id is False:
                return client_type, client_id
            else:
                # print("Fourth handshake failed.2")
                return False
        except:
            # print("Fourth handshake failed.1")  # 说明在创建输入id的过程中关闭了socket
            return False

    def _client_threading(self, client_socket, client_address, client_pipe ):

        client_information = {"address": client_address,
                              "socket": client_socket,
                              "pipe": client_pipe,
                              }

        result = self._fourth_handshake(client_socket, client_pipe, client_information)
        if result is False:
            return
        else:
            client_type, client_id = result
            if isinstance(client_type, str):  # 获取客户端类型成功，动态建立该类型的客户端实例
                user = type("User", (self.__TYPE_LIST[client_type][1],), {})\
                            (client_id, client_socket, client_address, client_pipe, self.__queue)
                user.run_client()

    def _server_process(self):
        server = socket(AF_INET, SOCK_STREAM)
        server.bind(('127.0.0.1', 9999))
        # server.bind(('', 9402))
        server.listen(self.__max)
        print('Waiting for connection...')
        while True:
            client_socket, client_address = server.accept()
            client_pipe = Pipe()
            client_threading = Thread(target=self._client_threading, args=(client_socket, client_address, client_pipe,))
            client_threading.start()
