# -*- coding: utf-8 -*-
# @Time    : 2020/5/17 14:55
# @Author  : Mat
# @Email   : mat_wu@163.com
# @File    : appWidget.py
# @Software: PyCharm

import tkinter as tk
import tkinter.messagebox as message_box
import tkinter.simpledialog as entry_box
import re
from threading import *
import time
import math
import uiWidget


class _Widget:
    """
    一个控件基类
    """

    def __init__(self, __root, __size, ui_command_dict):
        """
        构造控件基类时必须的要素。
        """
        self._ui_command_dict = ui_command_dict
        self._size = __size
        self._root = tk.Toplevel(__root)
        self._root.title("Output Widget")
        self._root.geometry("{}x{}+{}+{}".format(self._size[0], self._size[1], self._size[2], self._size[3]))
        self._root.transient(__root)


class OutputWidget(_Widget):
    """
    输出控件
    可以设置输出针脚，然后通过改变ui_command_dict来发出命令。
    """
    def __init__(self, __root, __size, ui_command_dict, ui_command_dict_key):
        """
        ui_command_dict_key必须设置为针脚名字。
        """
        super().__init__(__root, __size, ui_command_dict)

        self.__ui_command_dict_key = ui_command_dict_key
        self._ui_command_dict[self.__ui_command_dict_key] = ["", self.show_output_state]

        self._edit_item_list = ["Name", "Pin", "Command"]
        self._edit_input_widgets = dict()
        self._edit_input_message = dict()
        self._edit_input_message_backup = dict()
        for __edit_item in self._edit_item_list:
            self._edit_input_message_backup[__edit_item] = ''

        self._window_widgets = dict()

        self._window = tk.Frame(self._root,
                                width=self._size[0],
                                height=self._size[1])
        self._edit_window = tk.Frame(self._root,
                                     width=self._size[0],
                                     height=self._size[1])

        self._set_edit_window_widgets()
        self._set_edit_window()
        self._set_window_widgets()
        self._set_window()

    def start_widget(self):
        self._edit_window.pack()

    def _set_edit_window_widgets(self):
        __v0 = tk.StringVar()
        __v0.set("Output-{}".format(self.__ui_command_dict_key))
        self._edit_input_widgets[self._edit_item_list[0]] = \
            tk.Entry(self._edit_window, textvariable=__v0)
        self._edit_input_message[self._edit_item_list[0]] = __v0

        __v1 = tk.StringVar()
        __pins = ["DIGITAL(PWM~)-{}".format(__pin) for __pin in range(2, 14)]
        __pin_0 = "DIGITAL(PWM~)-{}".format(re.split(r'D', self.__ui_command_dict_key)[1])
        __v1.set(__pins[__pins.index(__pin_0)])
        self._edit_input_widgets[self._edit_item_list[1]] = \
            tk.OptionMenu(self._edit_window, __v1, *tuple(__pins))
        self._edit_input_message[self._edit_item_list[1]] = __v1

        __v2 = tk.StringVar()
        __commands = ["Auto", "ON", "OFF"]
        __v2. set(__commands[0])
        self._edit_input_widgets[self._edit_item_list[2]] = \
            tk.OptionMenu(self._edit_window, __v2, *tuple(__commands))
        self._edit_input_message[self._edit_item_list[2]] = __v2

    def _set_edit_window(self):
        for __edit_item in self._edit_item_list:
            tk.Label(self._edit_window, text=__edit_item).pack()
            self._edit_input_widgets[__edit_item].pack()
        tk.Button(self._edit_window, text='save', command=self._save_edit).pack()
        tk.Button(self._edit_window, text='cancel', command=self._cancel).pack()

    def _set_window_widgets(self):
        self._window_widgets[self._edit_item_list[0]] = tk.Label(self._window,
                                                                 text=self._edit_input_message[self._edit_item_list[0]]
                                                                 .get())
        self._window_widgets[self._edit_item_list[2]] = tk.Label(self._window,
                                                                 text=self._edit_input_message[self._edit_item_list[2]]
                                                                 .get())
        self._window_widgets["Output"] = tk.Label(self._window, text="Setting...", bg='white',
                                                  width=10, height=10)

    def _set_window(self):
        for __window_widget in self._window_widgets.values():
            __window_widget.pack()
        tk.Button(self._window, text='edit', command=self._edit).pack()

    def _save_edit(self):
        self._edit_window.pack_forget()
        self._update_widget()
        self._show_window()
        self._root.update()
        self._save_cgd()

    def _save_cgd(self):
        __pin_get = self._edit_input_message[self._edit_item_list[1]].get()
        __pin_get_list = re.split(r'-', __pin_get)
        __ui_command_pin = __pin_get_list[0][0] + __pin_get_list[1]
        __dict_com = {"Auto": 'a',
                      "ON": '1',
                      "OFF": '0'}
        __ui_com_get = self._edit_input_message[self._edit_item_list[2]].get()
        __ui_command_pin_command = __dict_com[__ui_com_get]

        __ui_command = "{}:{},".format(__ui_command_pin, __ui_command_pin_command)
        self._ui_command_dict[self.__ui_command_dict_key][0] = __ui_command

    def _show_window(self):
        for __window_widget in self._window_widgets.keys():
            if __window_widget in self._edit_input_message.keys():
                self._window_widgets[__window_widget].config(text=self._edit_input_message[__window_widget].get())

        self._window.update()
        self._window.pack()

    def _update_widget(self):
        for __edit_item in self._edit_item_list:
            self._edit_input_message_backup[__edit_item] = self._edit_input_message[__edit_item].get()

    def _edit(self):
        self._window.pack_forget()
        self._edit_window.pack()
        self._root.update()

    def _cancel(self):
        if message_box.askyesno(
                title="是否保存",
                message="你更改了设置，是否保存?"):
            self._save_edit()
        else:
            for __edit_item in self._edit_item_list:
                self._edit_input_message[__edit_item].set(self._edit_input_message_backup[__edit_item])
            self._edit_window.pack_forget()
            self._show_window()
            self._root.update()

    def show_output_state(self, __c):
        if __c == '?':
            self._window_widgets["Output"].config(text="Setting...", bg='white')
        elif __c == '0':
            self._window_widgets["Output"].config(text="OFF", bg='blue')
        elif __c == '1':
            self._window_widgets["Output"].config(text="ON", bg='red')
        elif __c == 'a':
            self._window_widgets["Output"].config(text="Auto", bg='green')
        self._window.update()


class DataViewer(_Widget):
    def __init__(self, __root, __size, ui_command_dict):
        super().__init__(__root, __size, ui_command_dict)
        self._ui_command_dict["Data Viewer"] = ["", self.print]

    def run_data_viewer(self):
        __canvas = tk.Canvas(self._root,
                             width=self._size[0],
                             height=self._size[1])
        self.app_canvas_text = uiWidget.AppCanvasText(__canvas, 5, 5, 10)
        __canvas.pack()

    def print(self, message):
        self.app_canvas_text.print(message)


class CommandGenerator(_Widget):
    def __init__(self, __root, __size, command_sender, ui_command_dict, __queue):
        super().__init__(__root, __size, ui_command_dict)
        self._on = False
        self._queue = __queue
        self._command_sender = command_sender

        self._start_button = tk.Button(self._root, text='start', bg='green',
                                       font=('Arial', 16), command=self._start_command_generator)
        self._stop_button = tk.Button(self._root, text='stop', bg='red', font=('Arial', 16),
                                      command=self._stop_command_generator)

    def run_command_generator(self):
        self._start_button.pack()
        s_i = Thread(target=self._generate_command, args=())
        s_i.setDaemon(True)
        s_i.start()
        self._root.mainloop()

    def stop_command_generator(self):
        self._on = False

    def _stop_command_generator(self):
        self._on = False
        self._stop_button.pack_forget()
        self._start_button.pack()
        self._root.update()

    def _start_command_generator(self):
        self._on = True
        self._start_button.pack_forget()
        self._stop_button.pack()
        self._root.update()

    def _generate_command(self):
        while True:
            if self._on:
                try:
                    self._send_get_data_command()
                    __data0 = self._queue.get()
                    self._print_data(__data0)

                    self._send_output_command()
                    __data1 = self._queue.get()
                    self._show_widget_state(__data1)
                    time.sleep(1)
                except Exception as e:
                    print("_generate_command")
                    print(e)
            else:
                self._update_widget_state()
                continue

    def _send_get_data_command(self):
        try:
            __command = "cgd"
            self._command_sender(__command)
        except Exception as e:
            print("_send_get_data_command")
            print(e)

    def _send_output_command(self):
        __command = ""
        try:
            for __cgd_list in self._ui_command_dict.values():
                __com = __cgd_list[0]
                if __com == '':
                    continue
                __command += __com
            self._command_sender(__command)
        except Exception as e:
            print("_send_output_command")
            print(e)

    def _print_data(self, __data):
        try:
            __data_viewer_print = self._ui_command_dict["Data Viewer"][1]
            __data_viewer_print(__data)
        except Exception as e:
            print("_print_data")
            print(e)

    def _show_widget_state(self, __data):
        try:
            __widget_state_list = re.split(r',', __data)
            for __widget_state in __widget_state_list:
                __widget_state_key, __widget_state_value = re.split(r':', __widget_state)
                __show_func = self._ui_command_dict[__widget_state_key][1]
                __show_func(__widget_state_value)
        except Exception as e:
            message_box.showinfo(
                title='！',
                message='Please save the output widget information first.')
            print("_show_widget_state")
            print(e)

    def _update_widget_state(self):
        try:
            for __widget_state_v in self._ui_command_dict.values():
                __func = __widget_state_v[1]
                __com = __widget_state_v[0]
                if __com == '':
                    continue
                __func('?')
        except Exception as e:
            print("_update_widget_state")
            print(e)


class Commander:
    def __init__(self, __root, __size, socket, __queue, __queue_t):
        self.__queue = __queue
        self.__socket = socket
        self._command_dict = dict()
        self._window = tk.Frame(__root, width=__size[0], height=__size[1])

        __sc_x = __size[0] / 1600
        __sc_y = __size[1] / 900

        size = [[300, 350, 100, 100],
                  [200, 300, 600, 100],
                  [200, 300, 900, 200],
                  [200, 300, 1200, 300],
                  [300, 150, 100, 500],
                  [1100, 100, 300, 750]]
        # for i in range(len(size)):
        #     size[i][0] = int(size[i][0] * __sc_x)
        #     size[i][2] = 200 + int((size[i][2] + 100) * __sc_x)
        #     size[i][3] = 200 + int((size[i][3] + 100) * __sc_y)

        self._command_dict = dict()

        self._data_viewer = DataViewer(self._window, size[0], self._command_dict)
        self._output_widget0 = OutputWidget(self._window, size[1], self._command_dict, "D9")
        self._output_widget1 = OutputWidget(self._window, size[2], self._command_dict, "D10")
        self._output_widget2 = OutputWidget(self._window, size[3], self._command_dict, "D11")

        self.__queue_t = __queue_t
        self._command_generator = CommandGenerator(self._window, size[4], self.__socket.send_command,
                                                   self._command_dict, self.__queue_t)
        self._dock = tk.Canvas(__root, width=size[5][0], height=size[5][1], bg="yellow") \
            .place(relx=size[5][2], rely=size[5][3], anchor=tk.NE)

    def run(self):
        if self._pair_executor():
            message_box.showinfo(
                title="Paired",
                message="Paired Successfully!"
            )
            __c_t_t = Thread(target=self._transmit_command, args=())
            __c_t_t.setDaemon(True)
            __c_t_t.start()
            self._window.pack()
            self._data_viewer.run_data_viewer()
            self._output_widget0.start_widget()
            self._output_widget1.start_widget()
            self._output_widget2.start_widget()
            self._command_generator.run_command_generator()

    def _pair_executor(self):
        __id_result = entry_box.askstring(
            title="Pairing",
            prompt="Please input the Client ID to be paired",
            initialvalue='User'
        )
        if not __id_result:
            return False
        try:
            __message = "jr {}".format(__id_result)
            self.__socket.send(__message)
            if self.__queue.get() == "S//O//OK":
                self.__socket.set_pairing_status(__id_result)
                __message = "rp {} REQUEST PAIRING".format(__id_result)
                self.__socket.send(__message)
                if self.__queue.get() == "S//O//OK":
                    if self.__queue.get() == "ACCEPT PAIRING":
                        return True
        except Exception as e:
            print("_pair_executor", e)
            return False

    def _transmit_command(self):
        print("start _transmit_command")
        while True:
            __message0 = self.__queue.get()
            if __message0 == "DISCONNECT":
                print("self._command_generator.stop_command_generator()")
                self._command_generator.stop_command_generator()
                return
            if __message0 == "S//O//OK":
                continue
            self.__queue_t.put(__message0)


class Executor:
    def __init__(self, __root, __size, socket, serial_writer, __queue):
        self.__queue = __queue
        self.__socket = socket
        self.__serial_write = serial_writer

        self.__w_p_t = None
        self.__t_d_t = None

        self._root = __root
        self._waiting_client_list = ["WAITING"]

        self._window = tk.Frame(self._root,
                                width=__size[0],
                                height=__size[1])
        self._edit_window = tk.Frame(self._root,
                                     width=__size[0],
                                     height=__size[1])

    def run(self):
        self._ui_update_edit_window()
        self._edit_window.pack()
        self._root.update()
        self.__w_p_t = Thread(target=self._threading_waiting_for_pairing, args=())
        self.__w_p_t.setDaemon(True)
        self.__w_p_t.start()

    def _threading_waiting_for_pairing(self):
        while True:
            try:
                __new_client = self.__queue.get()
                if __new_client == "SHUT//DOWN":
                    return
                if __new_client == "S//O//OK":
                    continue
                print("__new_client:", __new_client)
                self._waiting_client_list.append(__new_client)
                self._ui_update_edit_window()
                self._root.update()
            except Exception as e:
                print("_event_waiting_for_pairing ", e)
                return

    def _ui_update_edit_window(self):
        try:
            self._edit_window_menu.pack_forget()
            self._edit_window_button.pack_forget()
        except:
            self.__paired = tk.StringVar()
            self.__paired.set(self._waiting_client_list[-1])
        finally:
            self._edit_window_menu = tk.OptionMenu(
                self._edit_window, self.__paired,
                *self._waiting_client_list
            )
            self._edit_window_button = tk.Button(
                self._edit_window,
                text="OK",
                command=self._event_save_edit
            )
            self._edit_window_menu.pack()
            self._edit_window_button.pack()
            self._edit_window.update()

    def _event_save_edit(self):
        __client_id = self.__paired.get()
        if __client_id is None or __client_id == "WAITING":
            return

        self.__queue.put("SHUT//DOWN")
        self.__w_p_t.join()

        if message_box.askquestion(
            title="Pair the commander",
            message="Are you sure to pair this commander?\n{}".format(__client_id)
        ):

            _pair_commander_result = self._pair_commander(__client_id)
            if _pair_commander_result:
                self._edit_window.pack_forget()
                self._ui_update_window()
                self._window.pack()
                self._root.update()

                self.__t_d_t = None
                self.__t_d_t = Thread(target=self._threading_transmit_data, args=())
                self.__t_d_t.setDaemon(True)
                self.__t_d_t.start()

    def _threading_transmit_data(self):
        while True:
            try:
                output_command = self.__queue.get()
                if output_command == "SHUT//DOWN":
                    return
                self.__serial_write(output_command)
                serial_response = self.__queue.get()
                self.__socket.send_command(serial_response)
                if self.__queue.get() == "S//O//OK":
                    print("ok")
            except Exception as e:
                print("_transmit_data", e)
                return

    def _pair_commander(self, client_id):
        try:
            __message = "jr {}".format(client_id)
            self.__socket.send(__message)
            if self.__queue.get() == "S//O//OK":
                self.__socket.set_pairing_status(client_id)
                print("set_pairing_status(client_id) :: ",
                      self.__socket.get_paired_status
                      )
                __message = "ACCEPT PAIRING"
                self.__socket.send_command(__message)
                if self.__queue.get() == "S//O//OK":
                    return True
            else:
                print("wrong queue")
        except Exception as e:
            print(e)
            return False

    def _ui_update_window(self):
        try:
            self._window_label1.pack_forget()
            self._window_label2.pack_forget()
            self._window_button.pack_forget()
        except:
            pass
        finally:
            self._window_label1 = tk.Label(
                self._window,
                text=self.__paired.get()
            )
            self._window_label2 = tk.Label(
                self._window,
                bg="red",
                text="Transmitting Data..."
            )
            self._window_button = tk.Button(
                self._window,
                text="Cancel",
                command=self._event_terminate_transmission
            )
            self._window_label1.pack()
            self._window_label2.pack()
            self._window_button.pack()

    def _event_terminate_transmission(self):
        self._root.quit()

    # def _event_terminate_transmission(self):
    #     if message_box.askquestion(
    #         title="Terminate transmission",
    #         message="Are you sure you want to abort the transfer?\n\
    #                 You will need to re-pair."
    #     ):
    #         self.__queue.put("SHUT//DOWN")
    #         self.__t_d_t.join()
    #
    #         __stop_client_id = self.__socket.get_paired_status
    #         __re_pair_commander_result = self._stop_communicator(__stop_client_id)
    #         if __re_pair_commander_result:
    #
    #             self._window.pack_forget()
    #             self._ui_update_edit_window()
    #             self._edit_window.pack()
    #             self._root.update()
    #
    #             self.__w_p_t = None
    #             self._waiting_client_list = ["WAITING"]
    #             self.__w_p_t = Thread(target=self._threading_waiting_for_pairing, args=())
    #             self.__w_p_t.setDaemon(True)
    #             self.__w_p_t.start()
    #         else:
    #             print("_terminate_transmission error")
    #             return
    #
    # def _stop_communicator(self, client_id):
    #     try:
    #         self.__socket.set_pairing_status(None)
    #         __message = "DISCONNECT"
    #         self.__socket.send_command(__message)
    #         if self.__queue.get() == "S//O//OK":
    #             __message = "qr {}".format(client_id)
    #             self.__socket.send(__message)
    #             if self.__queue.get() == "S//O//OK":
    #                 return True
    #     except Exception as e:
    #         print("_re_pair_commander", e)
    #         return False
    #
