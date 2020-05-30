#!/usr/bin/env python
# coding:utf-8
import numpy as np
from tkinter import *
import matplotlib
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
import cv2 as cv
import matplotlib.pyplot as plt

vid = cv.VideoCapture(0)

def get_frame():
    if vid.isOpened():
        ret, frame = vid.read()
        frame = cv.resize(frame, (640, 480), interpolation=cv.INTER_NEAREST)  # 采用最快的临近点差值
        if ret:
            frame = cv.flip(frame, 1)
            return (ret, cv.cvtColor(frame, cv.COLOR_BGR2RGB))

        else:
            return (ret, None)
    else:
        ret = 2
        bg_img = cv.imread('D:/Defect Detection/BGimg.jpg')
        return (ret, bg_img)
def drawPic():

    # 清空图像，以使得前后两次绘制的图像不会重叠
    drawPic.f.clf()
    drawPic.a = drawPic.f.add_subplot(111)
    ret,frame = get_frame()
    colors = ['b', 'g', 'r']
    for i, color in enumerate(colors):
        hist = cv.calcHist([frame], [i], None, [256], [0, 256])
        print('type',type(hist))
        print('shape', hist.shape)
        drawPic.a.plot(hist, color=color)  # 在已经计算了直方图后,直接plot hist 就可以
        plt.xlim([0, 256])  # 限制横轴参数范围
    drawPic.canvas.draw()
def deploy():
    drawPic.f = Figure(figsize=(5, 4), dpi=100,facecolor = 'gray')
    drawPic.canvas = FigureCanvasTkAgg(drawPic.f, master=root)
    drawPic.canvas.draw()
    drawPic.canvas.get_tk_widget().grid(row=0, columnspan=3)

if __name__ == '__main__':
    #matplotlib.use('TkAgg')
    root = Tk()
    # 在Tk的GUI上放置一个画布，并用.grid()来调整布局
    deploy()


    # 放置标签、文本框和按钮等部件，并设置文本框的默认值和按钮的事件函数
    Button(root, text='画图', command=drawPic).grid(row=1, column=2, columnspan=3)

    # 启动事件循环
    root.mainloop()