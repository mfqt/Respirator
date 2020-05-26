# -*- coding: utf-8 -*-
# @Time    : 2020/5/14 16:53
# @Author  : Mat
# @Email   : mat_wu@163.com
# @File    : uiWidget.py
# @Software: PyCharm

import tkinter as tk
import tkinter.font as tk_font
import time


class AppCanvasText:
    def __init__(self, canvas, start_x, start_y, text_size, max_r=20):
        self._canvas = canvas
        self._text_start_x, self._text_start_y = start_x, start_y
        self._text_font = tk_font.Font(family="Consolas", size=text_size)

        self._message = "start"
        self._max_r = max_r
        self.__r = 1

        self._printed_text = self._canvas.create_text((self._text_start_x, self._text_start_y),
                                                      font=self._text_font,
                                                      anchor=tk.NW,
                                                      text=self._message
                                                      )

    def __print(self):
        self._printed_text = self._canvas.create_text((self._text_start_x, self._text_start_y),
                                                      font=self._text_font,
                                                      anchor=tk.NW,
                                                      text=self._message
                                                      )

    def print(self, __message, line_length=40):
        message = "{}".format(__message)
        __len = len(message)
        __insert_position = 0
        while __len > line_length:
            __message_line = message[0+line_length*__insert_position: 0+line_length*(__insert_position+1)]
            self._print(__message_line)
            __insert_position += 1
            __len -= line_length
        self._print(message[-__len:])

    def _print(self, message_line):
        self.__r += 1
        if self.__r > self._max_r:
            self._message = self._message[self._message.find('\n')+1:] + '\n' + message_line
        else:
            self._message += ('\n' + message_line)
        self._canvas.itemconfig(self._printed_text, text=self._message)
        # self._canvas.delete(self._printed_text)
        # self.__print()
        # self._canvas.update()


class AppProgressBar:
    def __init__(self, canvas, style, font_size, frame=10, step_time=0.5):
        self._start_x, self._start_y, self._width, self._height, self._color, self._total_steps = style
        self._canvas = canvas
        self.__frame = frame
        self.__step_time = step_time
        self.__frame_time = self.__step_time / self.__frame
        self._canvas.create_rectangle(self._start_x, self._start_y, self._start_x+self._width,
                                      self._start_y+self._height, width=1,
                                      outline=self._color)
        self._fill_line = self._canvas.create_rectangle(self._start_x, self._start_y, self._start_x,
                                                        self._start_y+self._height, width=0,
                                                        fill=self._color)
        self._completed_steps = 0
        self.__step_width = self._start_x

        self.__progress_text_font = tk_font.Font(family='microsoft yahei', size=font_size, weight='bold')
        self.__progress_text_site = (self._start_x + self._width, self._start_y - self._height/3)
        self.__progress_text = self._canvas.create_text(self.__progress_text_site, text="0%",
                                                        font=self.__progress_text_font,
                                                        fill=self._color,
                                                        anchor=tk.SE)

    def run(self, step=None):
        if step is None:
            step = self._total_steps - self._completed_steps
        new_step = self._completed_steps + step
        if new_step < self._total_steps:
            self.__update(step)
            self._completed_steps = new_step
        else:
            self.__update(self._total_steps - self._completed_steps)

    def __update(self, step):
        __new_width = step / self._total_steps * self._width
        __frame_width = __new_width / self.__frame
        __step_step = self._completed_steps
        __frame_step = step/self.__frame
        for _ in range(self.__frame):
            self.__step_width += __frame_width
            __step_step += __frame_step
            self._canvas.coords(self._fill_line, (self._start_x, self._start_y, self.__step_width,
                                                  self._start_y + self._height))
            self._canvas.itemconfig(self.__progress_text, text="{:.1f}/{}.0".format(__step_step, self._total_steps))
            self._canvas.update()
            time.sleep(self.__frame_time)
