# -*- coding: utf-8 -*-
# @Time    : 2020/5/19 14:48
# @Author  : Mat
# @Email   : mat_wu@163.com
# @File    : app0.py
# @Software: PyCharm

# pyinstaller -D -w app0.py -p communicator.py -p appWidget.py -p uiWidget.py --hidden-import communicator --hidden-import appWidget --hidden-import uiWidget

import tkinter as tk
import tkinter.messagebox as message_box
import tkinter.font as tk_font
import math
import communicator
import queue
import uiWidget
import appWidget


class App:
    def __init__(self, width=1600, height=900):

        self._window_width = width
        self._window_height = height
        self._window_size_scale = self._window_height/900   # 为了调整窗口大小而设置的比例。
        self.__queue_to_data_processor = queue.Queue()

    def start_app(self):
        self._start_app()

    def _start_app(self):
        self._window = tk.Tk()
        self._window.title("APP")

        __window_start_x = 200
        __window_start_y = 100
        __geometry = "{}x{}+{}+{}".format(self._window_width,
                                          self._window_height,
                                          __window_start_x,
                                          __window_start_y)
        self._window.geometry(__geometry)
        self._app_start_screen()
        self._window.mainloop()

    def _app_start_screen(self):
        self._canvas = tk.Canvas(self._window,
                                 width=self._window_width,
                                 height=self._window_height,
                                 bg='GhostWhite')

        # 绘制一个左边矩形
        __rectangle_width, __rectangle_height = self._window_width/5, self._window_height
        self._canvas.create_rectangle(0, 0, __rectangle_width, __rectangle_height,
                                      outline='',
                                      fill='SlateGray')

        # 绘制文字
        __text_start_x, __text_start_y = self._window_width*3/5, self._window_height/4
        __start_screen_font = tk_font.Font(family='Fixdsys',
                                           size=int(140*self._window_size_scale),
                                           weight=tk_font.BOLD,
                                           slant='italic',
                                           )
        self._canvas.create_text((__text_start_x, __text_start_y),
                                 font=__start_screen_font,
                                 anchor="center",   # anchor是指定的点(__text_start_x, __text_start_y)位于文字的中心等位置。
                                 text="Welcome! ",
                                 fill="Green",
                                 tags=('start_tag', 'start text')
                                 )

        # 绘制启动图案
        __tag0_circle_x, __tag0_circle_y, __tag0_circle_r = \
            (self._window_width-__rectangle_width)/2+__rectangle_width, self._window_height*3/4, self._window_height*1/6

        self._canvas.create_oval(__tag0_circle_x - __tag0_circle_r,
                                 __tag0_circle_y - __tag0_circle_r,
                                 __tag0_circle_x + __tag0_circle_r,
                                 __tag0_circle_y + __tag0_circle_r,
                                 outline='SkyBlue',
                                 width=int(30 * self._window_size_scale),
                                 tags=('start_tag', 'tag0')
                                 )
        __triangle_points = [__tag0_circle_x+__tag0_circle_r, __tag0_circle_y,
                             __tag0_circle_x-__tag0_circle_r/2, __tag0_circle_y+math.sqrt(3)/2*__tag0_circle_r,
                             __tag0_circle_x - __tag0_circle_r / 2 , __tag0_circle_y-math.sqrt(3) / 2 * __tag0_circle_r,
                             ]
        self._canvas.create_polygon(__triangle_points,
                                    outline='SkyBlue',
                                    width=int(10 * self._window_size_scale),
                                    fill='GhostWhite',
                                    tags=('start_tag', 'tag0')
                                    )

        self.__c = 0
        self._canvas.tag_bind('tag0', '<Enter>', self.__start_screen_enter_event)
        self._canvas.tag_bind('tag0', '<Leave>', self.__start_screen_leave_event)
        self._canvas.tag_bind('tag0', '<Button-1>', self.__start_screen_over_event)
        self._canvas.pack()

    def __start_screen_enter_event(self, event):
        __text_list = ['Start.  ', 'Start.. ', 'Start...']
        self._canvas.itemconfig('tag0', outline='red')
        self._canvas.itemconfig('start text', text=__text_list[self.__c])
        self._canvas.update()
        if self.__c < 2:
            self.__c += 1
        else:
            self.__c = 0

    def __start_screen_leave_event(self, event):
        self._canvas.itemconfig('tag0', outline='SkyBlue')
        self._canvas.itemconfig('start text', text='Welcome! ')
        self._canvas.update()

    def __start_screen_over_event(self, event):
        self._canvas.delete('start_tag')
        self._configuration_process()

    def _configuration_process(self):
        """
        配置过程
        """
        # 设置进度条。
        __progress_bar_width, __progress_bar_height = self._window_width*4/5*4/5, self._window_height/32
        __progress_bar_start_x, __progress_bar_start_y = \
            self._window_width/5+self._window_width*4/5/5/2, self._window_height*3/4
        __progress_bar_style = __progress_bar_start_x, __progress_bar_start_y, \
            __progress_bar_width, __progress_bar_height, 'Peru', 30
        __progress_bar = uiWidget.AppProgressBar(self._canvas, __progress_bar_style, int(30*self._window_size_scale))

        # 设置文字框
        __config_text = uiWidget.AppCanvasText(self._canvas, self._window_width/5+self._window_width/100, self._window_height/32,
                                      int(18*self._window_size_scale), 20)

        # 确定客户端类型
        if message_box.askyesno(title="Please select client type",
                                message="Use local client as hardware input and output device?"):
            # 开启serial
            __config_text.print("Starting serial communication...")  # "开启Serial通信"
            __config_text.print("Please select serial port...")

            self.__se = communicator.Serial_c(self.__queue_to_data_processor)
            if self.__se.config_serial() is False:
                message_box.showerror(title='Error',
                                      message='Quit.')
                self._canvas.pack_forget()
                self._window.quit()
                return

            for mess in self.__se.start_serial_communication():
                __config_text.print(mess)
                __progress_bar.run(1)
                if not mess:
                    return

            __config_text.print("Started serial communication...")
            # self._config_file.set('APP', 'Serial', 'True')
            __progress_bar.run(1)

            # 是否开启socket接受命令？
            if message_box.askyesno(title="Please select client type",
                                    message="Need to get orders from the Internet?\n\
                                    Click 'OK' to match the commander on the Internet.\n\
                                    Click 'Cancel' to use the local commander."):
                __config_text.print("Connecting to the server...")  # "连接Socket服务器"
                __progress_bar.run(1)
                self.__so = communicator.Socket_c(self.__queue_to_data_processor)
                if self.__so.config_socket():
                    for mess in self.__so.start_socket_communication():
                        if not mess:
                            message_box.showerror(title='Error',
                                                  message='Quit.')
                            self._canvas.pack_forget()
                            self._window.quit()
                            return
                        __config_text.print(mess)
                        __progress_bar.run(1)

                # 创建一个Executor
                self.__exe = appWidget.Executor(self._window,
                                               (1600, 900, 200, 200),
                                               self.__so,
                                               self.__se.writer,
                                               self.__queue_to_data_processor)

                __config_text.print("Starting project...")  # "创建样本工程"
                __progress_bar.run(1)
                self.__run = self.__exe.run

            else:  # 否则启用本地命令生成器。
                self._command_dict = dict()
                __size = [(300, 350, 200, 100),
                          (200, 300, 700, 100),
                          (200, 300, 1000, 200),
                          (200, 300, 1300, 300),
                          (300, 150, 200, 500),
                          (1100, 100, 400, 750)]
                self._data_viewer = \
                    appWidget.DataViewer(self._window, __size[0], self._command_dict)
                self._output_widget0 = \
                    appWidget.OutputWidget(self._window,
                                           __size[1],
                                           self._command_dict,
                                           "D9")
                self._output_widget1 = \
                    appWidget.OutputWidget(self._window,
                                           __size[2],
                                           self._command_dict,
                                           "D10")
                self._output_widget2 = \
                    appWidget.OutputWidget(self._window,
                                           __size[3],
                                           self._command_dict, "D11")
                self._command_generator = \
                    appWidget.CommandGenerator(self._window,
                                               __size[4],
                                               self.__se.writer,
                                               self._command_dict,
                                               self.__queue_to_data_processor)
                self.__run = self._run_local_app

        else:  # 不开启serial，只开起socket作为一个命令生成器。
            __q_t_2 = queue.Queue()
            self.__so = communicator.Socket_c(self.__queue_to_data_processor)
            if self.__so.config_socket():
                for mess in self.__so.start_socket_communication():
                    if not mess:
                        message_box.showerror(title='Error',
                                              message='Quit.')
                        self._canvas.pack_forget()
                        self._window.quit()
                        return
                    __config_text.print(mess)
                    __progress_bar.run(1)

            self.__cmd = appWidget.Commander(self._window,
                                      (1600, 900, 200, 100),
                                      self.__so,
                                      self.__queue_to_data_processor,
                                      __q_t_2)
            self.__run = self.__cmd.run

        __config_text.print("Starting main screen...")
        __progress_bar.run()

        self._start_main_screen()

    def _start_main_screen(self):
        # 在这里先把工程内部ui展示在底层。
        self._canvas.pack_forget()
        self.__run()

    def _run_local_app(self):
        try:
            self._data_viewer.run_data_viewer()
            self._output_widget0.start_widget()
            self._output_widget1.start_widget()
            self._output_widget2.start_widget()
            self._command_generator.run_command_generator()
        except Exception as e:
            print("_run_local_app : ", e)
            return

if __name__ == '__main__':
    a = App()
    a.start_app()
