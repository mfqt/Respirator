# coding=utf-8
"""
为了便操作与服务器与客户端通信，
将连接的客户端作为一个类

Client: 正常的聊天客户端类

SerialClient：只用作Serial客户端
1.没有聊天房相关的命令
2.连接成功后，开启Serial，然后不间断地从socket接收Serial数据
3.发送给Serial room，结束本次循环。
4.一个input只对应一个Serial room，Serial room里不含有input端的socket。
5.output或者master client 可以加入Serial room，然后即可通过socket获取数据。


！！！
待修改：
命令处理进程：
 -请求返回的结果增加一个附加信息。
 -处理serial客户端的请求返回的结果要和一般客户端一样返回两个结果和一个附加信息。这是为了减少数据损失而降低了传输性能的做法。
服务器进程：客户端种类名称。
"""


class _Client:
    """
    基类，
    基类中定义的方法功能：产生请求附加信息，发送请求，接收请求结果和请求结果附加信息，根据请求结果附加信息自我更新。
    """

    def __init__(self, client_id, client_socket, client_address, client_pipe, queue):
        self.__id = client_id
        self.__client_socket = client_socket
        self.__client_address = client_address
        self.__client_pipe = client_pipe
        self.__input, self.__output = self.__client_pipe
        self.__queue = queue
        self.__room_list = []

    def _run_client(self, client_type, MESSAGE_LIST, COMMAND_LIST):
        self.__client_socket.send(MESSAGE_LIST[0].encode('utf-8'))
        while True:
            try:
                data = self.__client_socket.recv(1024)
            except:
                break
            if not data:  # 客户端已经关闭
                break
            message = data.decode('utf-8')
            # print("get message :: ", message)

            message0, message_str, message1 = message.partition(' ')

            if message0 in COMMAND_LIST.keys():

                try:

                    request_args = self.__generate_request_args(client_type, message0, message1)
                    if not request_args:
                        self.__client_socket.send(MESSAGE_LIST[1].encode('utf-8'))
                        continue
                    __request_message = (COMMAND_LIST[message0][0], self.__id, self.__input, request_args)

                    __result, __result_args = self.__send_request(__request_message)
                    if __result:
                        self.__client_socket.send("{} {}"
                                                  .format(COMMAND_LIST[message0][1], MESSAGE_LIST[2])
                                                  .encode('utf-8'))
                        self.__update(client_type, message0, __result_args)
                    else:
                        self.__client_socket.send("{} {}"
                                                  .format(COMMAND_LIST[message0][1], MESSAGE_LIST[3])
                                                  .encode('utf-8'))
                        for __error_message in __result_args:
                            self.__client_socket.send("{} {}."
                                                      .format(MESSAGE_LIST[4], __error_message)
                                                      .encode('utf-8'))
                except:
                    continue
        self.__client_socket.close()
        return

    def __generate_request_args(self, client_type, message0, message1):
        """产生请求附加信息。为了提高代码复用，把判断命令的过程尽量优化"""
        room_id, message_str, message2 = message1.partition(' ')    # 根据partition方法的特性，一定能得到room_id，后面两个可能为空字符。
        if message0 == "jr":  # 是加入房间的指令或退出房间的指令, >>>room1
            if client_type == "normal":
                if room_id in self.__room_list:
                    print("jr error")
                    return False
                # print("normal client qr")
                return room_id
            elif client_type == "serial":
                # print("serial client qr")
                if message2 == '':
                    output_client_id = self.__id
                else:
                    output_client_id = message2
                return room_id, output_client_id

        if message0 == "qr":  # 是加入房间的指令或退出房间的指令, >>>room1
            if client_type == "normal":
                if room_id not in self.__room_list:
                    # print("qr error")
                    return False
                # print("normal client qr")
                return room_id
            elif client_type == "serial":
                # print("serial client qr")
                if message2 == '':
                    output_client_id = self.__id
                else:
                    output_client_id = message2
                return room_id, output_client_id

        if message0 == "ic":  # 是创建房间指令, >>>r1 c1,c2
            if ' ' in room_id or not room_id:
                return False
            if message2 == '':
                # print("ic error1")
                return False
            if room_id not in self.__room_list:
                # print("ic error2")
                return False
            group = message2.replace(' ', ',').split(',')
            if self.__id in group:
                # print("ic error3")
                return False
            return room_id, group

        if message0 == "cr":  # 是创建房间指令, >>>r1 c1,c2
            if ' ' in room_id or not room_id:
                return False
            if client_type == "normal" and message2 == '':
                # print("cr error")
                return False
            elif client_type == "serial" and message2 == '':
                # print("csr")
                return room_id
            else:
                group = message2.replace(' ', ',').split(',')
                if self.__id in group:
                    # print("cr error3")
                    return False
                return room_id, group

        if message0 == "sr":  # 是向房间发送信息的指令, >>>room1
            if room_id in self.__room_list:
                scr_message = "[{}] :: {}".format(self.__id, message2)
                return room_id, scr_message
            else:
                return False

    def __send_request(self, request_message):
        """发送完请求后会等待命令执行的结果"""
        self.__queue.put(request_message)
        result1 = self.__output.recv()
        result2 = self.__output.recv()
        result_args = self.__output.recv()
        error_list = []

        if result1 and result2:
            if not isinstance(result1, Exception) and not isinstance(result2, Exception):
                return True,result_args
            if isinstance(result1, Exception):
                error_list.append(str(result1))
            if isinstance(result2, Exception):
                error_list.append(str(result2))

        return False, error_list

    def __update(self, client_type, message0, result_args):
        """收到请求结果后，自我更新"""
        if message0 == "cr" or (message0 == "jr" and client_type == "normal"):
            if result_args not in self.__room_list:
                self.__room_list.append(result_args)
        elif message0 == "qr":
            if result_args in self.__room_list:
                self.__room_list.remove(result_args)
        # print("room_list::", self.__room_list)
        return


class NormalClient(_Client):
    """
    一般类型的客户端，具有最基础的聊天功能。
    """
    __type = "normal"
    __COMMAND_LIST = {"cr": ("CCR", "Created chatting room"),
                      "jr": ("JCR", "Joined chatting room"),
                      "qr": ("QCR", "Quited chatting room"),
                      "sr": ("SCR", "Sent to chatting room"),
                      "ic": ("IVC", "Invited clients to room")
                      }
    __MESSAGE_LIST = ("Connected Successfully!\nHello, {} client.".format(__type), "Wrong command.", "successfully.", "failed.", "ERROR :")

    def run_client(self):
        """开始交互过程"""
        self._run_client(self.__type, self.__MESSAGE_LIST, self.__COMMAND_LIST)


class SerialClient(_Client):
    """
    连接成功后开启Serial，并且创建一个空的Serial room，此Serial room的id与client id保持一致。
    input和output只有一个serial room，所以不需要room list。
    客户端可能只需要得知处理结果就可，不需要与人的交互，所以给客户端发送的信息越简单越好。
    循环：
        从socket接受数据，并请求发送给Serial room
        发送给Serial room 成功，获取下一个数据
        若失败，发送给socket一个失败指令，令其关闭socket
    """
    __type = "serial"
    __COMMAND_LIST = {"cr": ("CSR", "Created Serial room"),
                      "jr": ("JSR", "Joined Serial room"),
                      "qr": ("QSR", "Quited Serial room"),
                      "sr": ("SSR", "Sent to Serial room")
                      }
    __MESSAGE_LIST = ("Connected Successfully!\nHello, {} client.".format(__type), "Wrong command.", "successfully.", "failed.", "ERROR :")

    def run_client(self):
        """开始交互过程"""
        self._run_client(self.__type, self.__MESSAGE_LIST, self.__COMMAND_LIST)

