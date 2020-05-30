#!/usr/bin/env python
# coding:utf-8

from tkinter import *
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import cv2 as cv
import time
from threading import Thread,_RLock
import multiprocessing as mp


class App():
    def __init__(self):
        self.root = Tk()
        self.vid = cv.VideoCapture(0)
        self.plt_setting()
        Button(self.root, text='draw', command=self.draw_RGB).grid(row=1, column=2, columnspan=3)
        Button(self.root, text='draw by thread', command=self.multi_draw_thread).grid(row=2, column=2, columnspan=3)# it will not work
        Button(self.root, text='draw by process', command=self.multi_draw_process).grid(row=3, column=2, columnspan=3)# it will get the GUI breakdown
        self.root.mainloop()
    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            frame = cv.resize(frame, (640, 480), interpolation=cv.INTER_NEAREST)  # 采用最快的临近点差值
            if ret:
                frame = cv.flip(frame, 1)
                return (ret, cv.cvtColor(frame, cv.COLOR_BGR2RGB))
            else:
                return (ret, None)
        else:
            pass
    def draw_RGB(self):
        # clear the figure or the new figure will be mixed with the old one
        self.f.clf()
        self.a = self.f.add_subplot(111)
        ret,frame = self.get_frame()
        colors = ['b', 'g', 'r']
        for i, color in enumerate(colors):
            hist = cv.calcHist([frame], [i], None, [256], [0, 256])#calculate the hist of frame
            self.a.plot(hist, color=color)  # draw the hist created in plot
        self.canvas_plt.draw()
        self.root.after(500, self.draw_RGB)
    def plt_setting(self):
        self.f = Figure(figsize=(5, 4), dpi=100)#create Figure to be the container of graph created by matplotlib
        self.canvas_plt = FigureCanvasTkAgg(self.f, master=self.root)# #create canvas to be the container of Figure
        self.canvas_plt.get_tk_widget().grid(row=0, columnspan=3)#to place the canvas in self.root
    def multi_draw(self):
        for i in range(3):
            self.draw_RGB()
            time.sleep(1)
            print(i)
    def multi_draw_thread(self):
        runT = Thread(target=self.multi_draw)
        runT.setDaemon(True)
        runT.start()
    def multi_draw_process(self):
        runS = mp.Process(target=self.multi_draw)
        runS.start()
if __name__ == '__main__':
    app = App()

