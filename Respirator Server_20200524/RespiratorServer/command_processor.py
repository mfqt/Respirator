# coding=utf-8
"""
在服务器运行之前先运行。
+从数据库获得最近信息储存到缓存
循环：
    等待queue的获取命令请求
    +如果queue时服务器主进程发来的结束命令，进行数据备份到数据库
    每获取一个命令请求，开启一个新线程：
            处理命令(更新数据库,回复给客户端连接进程处理结果)
            结束线程   

Serial room
不包含创建者的socket，默认为空列表。(空列表迭代操作时不会报错。)
从input获取data，直接发送给其对应的Serial room，
output和master可以加入Serial room

"""


from multiprocessing import Process
from threading import Thread
from RespiratorServer import session


class Processor:
    def __init__(self, queue):
        self.__queue = queue
        self.__chatting_clients = session.ChattingClientInformation()
        self.__chatting_rooms = session.RoomInformation()
        self.__serial_clients = session.SerialClientInformation()
        self.__serial_rooms = session.RoomInformation()
        self.__processing = None

    def run_processor(self):
        self.__processing = Process(target=self._main_threading, args=())
        self.__processing.start()

    def join(self):
        self.__processing.join()

    def _processing_threading(self, request_message):

        (command, client_id, client_pipe_input, command_args) = request_message
        #print("request_message ::", request_message)

        if command == "CNC1":
            # create new client
            # command_args : client_information
            client_information = command_args
            self.__chatting_clients.create_new_client(client_id, client_pipe_input, client_information )
            return
        if command == "CNC2":
            # create new client
            # command_args : client_information
            client_information = command_args
            self.__serial_clients.create_new_client(client_id, client_pipe_input, client_information )
            return

        if command == "IVC":
            # invite client to room
            room_id, client_list = command_args
            sockets = self.__chatting_clients.get_sockets(client_list)
            for client_socket in sockets:
                __mess = "Server//Your friend {} is inviting you to join the a clients room( room ID :: {})." \
                    .format(client_id, room_id)
                client_socket.send(__mess.encode('utf-8'))
            client_pipe_input.send(True)
            client_pipe_input.send(True)
            client_pipe_input.send(True)
            return

        if command == "RP":
            # request pairing
            client_id_to_pair = command_args
            client_list = [client_id_to_pair]
            sockets = self.__serial_clients.get_sockets(client_list)
            for client_socket in sockets:
                __mess = "D//{}//REQUEST PAIRING".format(client_id)
                client_socket.send(__mess.encode('utf-8'))
            client_pipe_input.send(True)
            client_pipe_input.send(True)
            client_pipe_input.send(True)
            return

        if command == "CCR":
            # create new chatting room
            # command_args : room_id, (client1, client2)
            # 这里client list的作用只是向客户端发送邀请，至于是否存在这些客户端，并不关心。
            room_id, client_list = command_args

            result = self.__chatting_clients.create_chatting_room(
                self.__chatting_rooms, room_id, client_id, client_pipe_input)
            client_pipe_input.send(room_id)
            if not isinstance(result, Exception):

                sockets = self.__chatting_clients.get_sockets(client_list)
                for client_socket in sockets:
                    __mess = "Server//Your friend {} is inviting you to join the a clients room( room ID :: {})."\
                        .format(client_id, room_id)
                    client_socket.send(__mess.encode('utf-8'))

            return

        if command == "CSR":
            # create serial room
            # command_args : room_id,其实就是input client id
            room_id = command_args
            self.__serial_clients.create_serial_room(self.__serial_rooms, room_id, client_pipe_input)
            client_pipe_input.send(room_id)
            return

        if command == "JCR":
            # join chatting room
            # command_args : room_id
            room_id = command_args
            self.__chatting_clients.join_chatting_room(self.__chatting_rooms, room_id, client_id,
                                                       client_pipe_input)
            client_pipe_input.send(room_id)
            return

        if command == "JSR":
            # join serial room
            # command_args : room_id,output_client_id
            # 这个命令一般是master client发送的，output_client_id是指定的output client的id，client_pipe_input是master client的。
            # 如果是master client对自己进行操作，只需要使用自身room_id即可。
            room_id, output_client_id = command_args
            self.__serial_clients.join_serial_room(self.__serial_rooms, room_id, output_client_id,
                                                   client_pipe_input)
            client_pipe_input.send(room_id)
            return

        if command == "QCR":
            # quit chatting room
            # command_args : room_id
            # QCR 不需要将自己的id包装到command_args，直接使用client_id即可
            room_id = command_args
            self.__chatting_clients.quit_chatting_room(self.__chatting_rooms, room_id, client_id, client_pipe_input)
            client_pipe_input.send(room_id)
            return

        if command == "QSR":
            # quit serial room
            # command_args : room_id,output_client_id
            # 这个命令一般是master client发送的，client_id是指定的output client的id，client_pipe_input是master client的。
            # 如果是master client对自己进行操作，只需要使用自身room_id即可。
            room_id, output_client_id = command_args
            self.__serial_clients.quit_serial_room(self.__serial_rooms, room_id, output_client_id,
                                                   client_pipe_input)
            client_pipe_input.send(room_id)
            return

        if command == "SCR":
            # send (message) to chatting room
            # command_args : room_id, scr_message
            room_id, scr_message = command_args
            self.__chatting_rooms.send_message(room_id, scr_message, client_pipe_input)
            client_pipe_input.send(room_id)
            return

        if command == "SSR":
            # send (message) to serial room
            # command_args : room_id, ssr_message
            room_id, ssr_message = command_args
            self.__serial_rooms.send_message(room_id, ssr_message, client_pipe_input)
            client_pipe_input.send(room_id)
            return
        return

    def _main_threading(self):
        __i = 0
        while True:
            # print("Waiting for request...")
            _request_message = self.__queue.get()
            # print(__i,"===>let's do this ::",_request_message)
            _threading = Thread( target= self._processing_threading, args=( _request_message, ) )
            _threading.start()
            # print(__i,"===>Over")
            __i += 1
