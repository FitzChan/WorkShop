import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pylab import mpl
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk  # NavigationToolbar2TkAgg
# ------------------------------------------------------------------------------------------
import tkinter as tk
import cv2 as cv
import time
# ------------------------------------------------------------------------------------------
from threading import Thread
def drawPic():
    # 清空图像，以使得前后两次绘制的图像不会重叠
    drawPic.f.clf()
    drawPic.a = drawPic.f.add_subplot(111)
    # 绘制图像所需要的x,y
    x = list(range(len(hxplot)))
    y = hxplot
    # 将这些点绘制成曲线
    drawPic.a.plot(x, y)
    drawPic.a.set_title("Respiratory waveform")
    drawPic.canvas.show()


if __name__ == '__main__':
    matplotlib.use('TkAgg')
    # 在Tk的GUI上放置一个画布，并用.grid()来调整布局
    drawPic.f = plt.Figure(figsize=(7, 2), dpi=100)
    drawPic.canvas = FigureCanvasTkAgg(drawPic.f, master=Leida)
    drawPic.canvas.show()
    drawPic.canvas.get_tk_widget().grid(row=0, columnspan=3)
    Button(Leida, text='画图', command=drawPic, state=ACTIVE).grid(row=1, column=2, columnspan=3)
    drawPic.canvas.show()