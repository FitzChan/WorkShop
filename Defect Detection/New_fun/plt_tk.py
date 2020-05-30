import math
import numpy as np
# -------------------------------------------------------------------------------------------
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
from matplotlib.figure import Figure
mpl.rcParams['font.sans-serif'] = ['SimHei']  # 中文显示
mpl.rcParams['axes.unicode_minus'] = False  # 负号显示


class From:
    def __init__(self):
        self.root = tk.Tk()  # 创建主窗体
        self.root.geometry('1280x720')
        self.root.resizable(0, 0)  # 窗口不可调节大小
        self.vid = cv.VideoCapture(0)
        self.deploy_matplotlib()
        self.create_form()
        self.root.mainloop()

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            frame = cv.resize(frame, (640, 480),interpolation=cv.INTER_NEAREST)# 采用最快的临近点差值
            if ret:
                 frame = cv.flip(frame, 1)
                 return (ret, cv.cvtColor(frame, cv.COLOR_BGR2RGB))

            else:
                 return (ret, None)
        else:
             ret = 2
             bg_img = cv.imread('D:/Defect Detection/BGimg.jpg')
             return (ret,bg_img)

    '''def create_matplotlib(self):
        # 创建绘图对象f
        f = plt.figure()#num=2, figsize=(16, 12), dpi=80, facecolor="pink", edgecolor='green', frameon=True
        # 创建一副子图
        fig1 = plt.subplot(1, 1, 1)

        x = np.arange(0, 2 * np.pi, 0.1)
        y1 = np.sin(x)
        y2 = np.cos(x)

        line1, = fig1.plot(x, y1, color='red', linewidth=3, linestyle='--')  # 画第一条线
        line2, = fig1.plot(x, y2)
        plt.setp(line2, color='black', linewidth=8, linestyle='-', alpha=0.3)  # 华第二条线

        fig1.set_title("这是第一幅图", loc='center', pad=20, fontsize='xx-large', color='red')  # 设置标题
        line1.set_label("正弦曲线")  # 确定图例
        fig1.legend(['正弦', '余弦'], loc='upper left', facecolor='green', frameon=True, shadow=True, framealpha=0.5,
                    fontsize='xx-large')

        fig1.set_xlabel('横坐标')  # 确定坐标轴标题
        fig1.set_ylabel("纵坐标")
        fig1.set_yticks([-1, -1 / 2, 0, 1 / 2, 1])  # 设置坐标轴刻度
        fig1.grid(which='major', axis='x', color='r', linestyle='-', linewidth=2)  # 设置网格

        return f'''

    def create_form(self, figure):
        # 把绘制的图形显示到tkinter窗口上

        self.canvas = FigureCanvasTkAgg(figure, self.root)
        self.canvas.draw()  # 以前的版本使用show()方法，matplotlib 2.2之后不再推荐show（）用draw代替，但是用show不会报错，会显示警告
        self.canvas.get_tk_widget().pack()#side=tk.TOP, fill=tk.BOTH, expand=1
        # 把matplotlib绘制图形的导航工具栏显示到tkinter窗口上
        '''
        toolbar = NavigationToolbar2Tk(self.canvas,
                                       self.root)  # matplotlib 2.2版本之后推荐使用NavigationToolbar2Tk，若使用NavigationToolbar2TkAgg会警告
        toolbar.update()
        self.canvas._tkcanvas.pack(side=tk.TOP, fill=tk.BOTH, expand=1)'''

    def create_matplotlib(self):
        self.create_matplotlib.f.clf()
        self.create_matplotlib.a = self.create_matplotlib.f.add_subplot(111)
        colors = ['b', 'g', 'r']
        ret, frame = self.get_frame()
        for i, color in enumerate(colors):
            hist = cv.calcHist([frame], [i], None, [256], [0, 256])
            self.create_matplotlib.a.plot(hist, color=color)  # 在已经计算了直方图后,直接plot hist 就可以
            plt.xlim([0, 256])  # 限制横轴参数范围
        self.create_matplotlib.canvas.draw()

    def deploy_matplotlib(self):
        self.create_matplotlib.f = Figure(figsize=(5, 4), dpi=100)
        self.create_matplotlib.canvas = FigureCanvasTkAgg(self.create_matplotlib.f, master=self.root)
        self.create_matplotlib.canvas.draw()
        self.create_matplotlib.canvas.get_tk_widget().grid(row=0, columnspan=3)
'''
    def deploy_plt(self):
        t1 = cv.getTickCount()
        self.ax.clear()
        plt.clf()
        plt.cla()
        self.canvas = tk.Canvas()
        self.canvas.delete("all")
        ret, self.frame = self.get_frame()
        print('frame',type(self.frame))
        if ret != 2:
            self.create_matplotlib2_thread()
            self.create_form_thread()
        if ret == 2:
           pass
        t2 = cv.getTickCount()
        print((t2 - t1)/cv.getTickFrequency())
    def multiply_deploy(self):
        for i in range(3):
            self.deploy_plt()
            time.sleep(2)

    def multiply_deploy_thread(self):
        runT = Thread(target=self.multiply_deploy)
        #runT.setDaemon(True)
        runT.start()
    def create_matplotlib2_thread(self):
        runT = Thread(target=self.create_matplotlib2(self.frame))
        runT.setDaemon(True)
        runT.start()

    def create_form_thread(self):
        runT = Thread(target=self.create_form(self.figure))
        runT.setDaemon(True)
        runT.start()
'''
if __name__ == "__main__":
    form = From()