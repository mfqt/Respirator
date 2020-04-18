# coding=utf-8
"""
暂时为了先完成服务器的逻辑。
只是一个储存数据的类，包含一些简单的处理和交互方法。
不关心数据库的交互，不关心缓存的交互。
服务器运行开始前设定最大数，然后创建新实例，
服务器运行中不断访问和修改，
服务器结束时直接全部淘汰。

        
self.__item = {"password" : None, "address" : None,"socket" : None, "pipeOutput" : None,}
        if data is None:
            self.__data = dict()
"""


from threading import Lock


class _Session:
    def __init__(self, max_size=None, data=None):
        self.__max_size = max_size
        if data is None:
            self.__sheet = {}
        else:
            self.__sheet = data

    def _get_item(self, item_id):
        item = self.__sheet[item_id]
        return item

    def _get_session(self):
        return self.__sheet

    def _set_session(self, new_sheet):
        self.__sheet = new_sheet
        return

    def _id_exists(self, _id):
        return _id in self.__sheet.keys()


class Session(_Session):
    """
    a session is a sheet：
     { item_id1 : item1, item_id2 : item2, item_id3 : item3, ...}
    a line is a sheet with only one item_id and one item
     { item_id : item }
    an item is a dict:
     { key1 : value1, key2 : value2, ...}
    an element is a dict with only one key-value pair
     { key : value }
    """
    __lock = Lock()

    def _get_item(self, item_id):
        """获得某一行"""
        self.__lock.acquire()
        try:
            result = super(Session, self)._get_item(item_id)
        except Exception as e:
            result = e
        finally:
            self.__lock.release()
        return result

    def _add_new_line(self, new_line):
        """添加一个项目行"""
        new_id = list(new_line.keys())[0]
        self.__lock.acquire()
        try:
            if self._id_exists(new_id):
                raise Exception("This ID already exists!")
            sheet = self._get_session()
            sheet.update(new_line)
            self._set_session(sheet)
            result = True
        except Exception as e:
            result = e
        finally:
            self.__lock.release()
        return result

    def _update_line(self, item_id, element):
        """更新某个项目行的信息"""
        self.__lock.acquire()
        try:
            item = super(Session, self)._get_item(item_id)
            if isinstance(item, list):
                item.append(element)
            elif isinstance(item, dict):
                item.update(element)
            self.__sheet[item_id] = item
            result = True
        except Exception as e:
            result = e
        finally:
            self.__lock.release()
        return result

    def _delete_line(self, item_id):
        """
        删除某个项目行的信息
        其实就是先获取整个信息表，然后删除某个项目的项目行，然后更新整个信息表
        """
        self.__lock.acquire()
        try:
            sheet = self._get_session()
            del sheet[item_id]
            self._set_session(sheet)
            result = True
        except KeyError as e:
            result = e
        finally:
            self.__lock.release()
        return result

    def _delete_values(self, item_id, element):
        self.__lock.acquire()
        try:
            item = super(Session, self)._get_item(item_id)
            if isinstance(item, list):
                item.remove(element)
            elif isinstance(item, dict):
                del item[element]
            self.__sheet[item_id] = item
            result = True
        except Exception as e:
            result = e
        finally:
            self.__lock.release()
        return result


class _ClientInformation(Session):
    """
    为了不出现死锁的情况，这个子类不能使用锁。
    进行和客户端进程的交互。
    """
    def create_new_client(self, client_id, client_pipe_input, client_information):
        new_client = {client_id: client_information}
        result = self._add_new_line(new_client)
        client_pipe_input.send(result)
        return

    def get_sockets(self, client_list):
        socket_list = []
        for client_id in client_list:
            result = self._get_item(client_id)
            if not isinstance(result, Exception):
                socket_list.append(result["socket"])
        return socket_list

    # def get_values(self, client_id, keys, client_pipe):
    #     result = self._get_item(client_id)
    #     if isinstance(result, Exception):
    #         client_pipe.send(result)
    #         return
    #     value_list = []
    #     for key in keys:
    #         value_list.append(result[key])
    #         client_pipe.send(value_list)
    #     return

    def _create_room(self, room_list, room_id, client_id, client_pipe_input):
        """
        客户端进程在申请这个命令后会收到两条结果信息.
        第一步：获得信息，检验client_id是否可以创建房间
        第二步：添加room
        """
        client_information = self._get_item(client_id)
        if isinstance(client_information, Exception):
            client_pipe_input.send(client_information)
            client_pipe_input.send(False)
            return client_information
        client_pipe_input.send(True)
        client_socket = client_information["socket"]
        new_room = {room_id: [client_socket]}
        result = room_list.add_new_room(new_room)
        client_pipe_input.send(result)
        return result

    def _join_room(self, room_list, room_id, client_id, client_pipe_input):
        """
        客户端进程在申请这个命令后会收到两条结果信息：
        第一步：获得信息，检验client_id是否存在在信息库中
        第二步：添加room的sockets
        """
        client_information = self._get_item(client_id)
        if isinstance(client_information, Exception):
            client_pipe_input.send(client_information)
            client_pipe_input.send(False)
            return
        client_pipe_input.send(True)
        client_socket = client_information["socket"]
        result = room_list.update_socket_list(room_id, client_socket)
        client_pipe_input.send(result)
        return

    def _quit_room(self, room_list, room_id, client_id, client_pipe_input):
        """
        客户端进程在申请这个命令后会收到两条结果信息：
        第一步：获得信息，检验client_id是否存在在信息库中
        第二步：删除room的sockets
        """
        client_information = self._get_item(client_id)
        if isinstance(client_information, Exception):
            client_pipe_input.send(client_information)
            client_pipe_input.send(False)
            return
        client_pipe_input.send(True)
        client_socket = client_information["socket"]
        result = room_list.delete_socket(room_id, client_socket)
        client_pipe_input.send(result)
        return


class ChattingClientInformation(_ClientInformation):
    """
    Normal聊天客户端
    """

    def create_chatting_room(self, room_list, room_id, client_id, client_pipe_input):
        result = self._create_room(room_list, room_id, client_id, client_pipe_input)
        return result

    def join_chatting_room(self, room_list, room_id, client_id, client_pipe_input):
        self._join_room(room_list, room_id, client_id, client_pipe_input)
        return

    def quit_chatting_room(self, room_list, room_id, client_id, client_pipe_input):
        self._quit_room(room_list, room_id, client_id, client_pipe_input)
        return


class SerialClientInformation(_ClientInformation):
    """
    serial client, 包括input 和 output
    """

    def create_serial_room(self, room_list, room_id, client_pipe_input):
        """
        直接添加room字典，不需要creator_id，所以
        new_room = {room_id: []}
        """
        client_pipe_input.send(True)
        new_room = {room_id: []}
        result = room_list.add_new_room(new_room)
        client_pipe_input.send(result)
        return result

    def join_serial_room(self, room_list, room_id, client_id, client_pipe_input):
        self._join_room(room_list, room_id, client_id, client_pipe_input)

    def quit_serial_room(self, room_list, room_id, client_id, client_pipe_input):
        self._quit_room(room_list, room_id, client_id, client_pipe_input)


class RoomInformation(Session):
    """
    为了不出现死锁的情况，这个子类不能使用锁。
    进行和客户端进程的交互。
    { room_id1 : [ socket1, socket2, socket3,...] }
    serial room 和 chatting room是一样的，没有区别。唯一的区别并不体现在这个类，
    而是在serial client 创建房间时，不需要把自身的socket添加到房间里，
    所以只是在调用add_new_room方法的时候，传递的参数有所区别：
        serial room ===> {room_id : []}
        chatting room ===> {room_id : [creator_id]}
    """
    def add_new_room(self, new_room):
        """
        修改的是字典
        """
        result = self._add_new_line(new_room)
        return result

    def update_socket_list(self, room_id, client_socket):
        result = self._update_line(room_id, client_socket)
        return result

    def delete_socket(self, room_id, client_socket):
        result = self._delete_values(room_id, client_socket)
        return result

    def _get_socket_list(self, room_id):
        result = self._get_item(room_id)
        return result

    def send_message(self, room_id, message, client_pipe_input):
        """发送信息不会出现失败的情况"""
        sockets = self._get_socket_list(room_id)
        client_pipe_input.send(True)
        if isinstance(sockets, list):
            for socket in sockets:
                socket.send(message.encode("UTF-8"))
            client_pipe_input.send(True)
            return
        return
