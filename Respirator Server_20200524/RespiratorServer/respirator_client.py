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

master类型其实就是一种serial类型，对于服务器的命令完全一致，只在客户端的代码上不同。
若要新增新的客户端类型：
 1.创建一个新的子类
 2.修改基类的__generate_request_args方法和__update方法

注意命令处理进程新增的方法：
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
        self._id = client_id
        self._client_socket = client_socket
        self.__client_address = client_address
        self.__client_pipe = client_pipe
        self.__input, self.__output = self.__client_pipe
        self.__queue = queue
        self.__room_list = []

    def _run_client(self, client_type, MESSAGE_LIST, COMMAND_LIST):
        self._client_socket.send((MESSAGE_LIST[0] + "  Hello, {}!".format(self._id)).encode('utf-8'))
        __nono = 0
        while True:
            try:
                data = self._client_socket.recv(1024)

            except:
                break
            if not data:  # 客户端已经关闭
                break
            message = data.decode('utf-8')
            print("get message :: {}//{}".format(self._id, message))
            # print("get message :: ", message)

            message0, message_str, message1 = message.partition(' ')

            if message0 in COMMAND_LIST.keys():

                try:

                    request_args = self.__generate_request_args(client_type, message0, message1)
                    if not request_args:
                        self._client_socket.send(MESSAGE_LIST[1].encode('utf-8'))
                        continue
                    __request_message = (COMMAND_LIST[message0][0], self._id, self.__input, request_args)
                    print("__request_message(client)", __request_message)
                    __result, __result_args = self.__send_request(__request_message)

                    if __result:
                        print(self._id, __nono )
                        __nono += 1
                        self._client_socket.send("S//O//{} {}"
                                                  .format(COMMAND_LIST[message0][1], MESSAGE_LIST[2])
                                                  .encode('utf-8'))
                        self.__update(client_type, message0, __result_args)
                    else:
                        self._client_socket.send("S//E//{} {}"
                                                  .format(COMMAND_LIST[message0][1], MESSAGE_LIST[3])
                                                  .encode('utf-8'))
                        for __error_message in __result_args:
                            self._client_socket.send("S//{} {}."
                                                      .format(MESSAGE_LIST[4], __error_message)
                                                      .encode('utf-8'))
                except:
                    continue
        self._client_socket.close()
        return

    def __generate_request_args(self, client_type, message0, message1):
        """
                产生请求附加信息。为了提高代码复用，把判断命令的过程尽量优化
                为了以后能扩展更多的客户端类型，按照客户端种类来归类，而不是按照命令。
                """
        room_id, message_str, message2 = message1.partition(' ')  # 根据partition方法的特性，一定能得到room_id，后面两个可能为空字符。
        if message0 == "sr":
            if room_id in self.__room_list:
                scr_message = "{}//{}".format(self._id, message2)
                return room_id, scr_message
            else:
                return
        if client_type == "NORMAL":
            if message0 == "cr":
                if ' ' in room_id or not room_id:
                    return
                if message2 == '':
                    # print("cr error")
                    return
                group = message2.replace(' ', ',').split(',')
                if self._id in group:
                    # print("cr error3")
                    return
                return room_id, group
            if message0 == "jr":
                if room_id in self.__room_list:
                    # print("jr error")
                    return
                # print("normal client qr")
                return room_id
            if message0 == "qr":
                if room_id not in self.__room_list:
                    # print("qr error")
                    return
                # print("normal client qr")
                return room_id
            if message0 == "ic":  # 是创建房间指令, >>>r1 c1,c2
                if ' ' in room_id or not room_id:
                    return
                if message2 == '':
                    # print("ic error1")
                    return
                if room_id not in self.__room_list:
                    # print("ic error2")
                    return
                group = message2.replace(' ', ',').split(',')
                if self._id in group:
                    # print("ic error3")
                    return
                return room_id, group
        if client_type == "SERIAL":
            if message0 == "cr":
                if ' ' in room_id or not room_id:
                    return
                return room_id
            if message0 == "jr":
                if room_id in self.__room_list:
                    # print("jr error")
                    return
                if message2 == '':
                    output_client_id = self._id
                else:
                    output_client_id = message2
                return room_id, output_client_id
            if message0 == "qr":
                if room_id not in self.__room_list:
                    # print("qr error")
                    return
                if message2 == '':
                    output_client_id = self._id
                else:
                    output_client_id = message2
                return room_id, output_client_id
            if message0 == "rp":
                return room_id
        return

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
        if message0 == "cr" or (message0 == "jr" and client_type == "NORMAL"):
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
    __type = "NORMAL"
    __COMMAND_LIST = {"cr": ("CCR", "Created chatting room"),
                      "jr": ("JCR", "Joined chatting room"),
                      "qr": ("QCR", "Quited chatting room"),
                      "sr": ("SCR", "Sent to chatting room"),
                      "ic": ("IVC", "Invited clients to room")
                      }
    __MESSAGE_LIST = ("Server//Connected Successfully!({} client)".format(__type.lower()),
                      "Server//Server can't execute this command.",
                      "successfully.",
                      "failed.",
                      "ErrorType//")

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
    __type = "SERIAL"
    __COMMAND_LIST = {"cr": ("CSR", "Created Serial room"),
                      "jr": ("JSR", "Joined Serial room"),
                      "qr": ("QSR", "Quited Serial room"),
                      "sr": ("SSR", "Sent to Serial room"),
                      "rp": ("RP", "Request Pairing")
                      }
    __MESSAGE_LIST = ("S//O//Connected Successfully!",
                      "S//E//Server can't execute this command.",
                      "successfully.",
                      "failed.",
                      "ErrorType//")

    def run_client(self):
        """开始交互过程"""
        self._client_socket.send("S//ID//{}".format(self._id).encode('utf-8'))
        self._run_client(self.__type, self.__MESSAGE_LIST, self.__COMMAND_LIST)

