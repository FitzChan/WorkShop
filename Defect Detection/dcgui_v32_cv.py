#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 修改红外串口代码
#注意到 单次拍照 需要 再写一个方法，因为多次拍照会将 输入路径改掉
import numpy as np
import cv2 as cv
import tkinter as tk
import PIL.Image, PIL.ImageTk
from tkinter import *
from tkinter import ttk ,scrolledtext,filedialog as fd,messagebox as mBox
from threading import Thread,Event,_RLock
import time
import glob
from os import path,makedirs,startfile,getcwd
import serial
import random
import tkinter.font as font
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from queue import Queue
import widgets_29 as widgets# 包含 MyVideoCapture
import serial.tools.list_ports
class App:


    def __init__(self, win, window_title,video_source = 0):
        self.win = win
        self.win.title(window_title)
        self.win_width, self.win_height = self.set_screen_size(self.win)#设置gui
        self.canvas_width = int(4*self.win_height/5)#设置所有画布的宽高
        self.canvas_height = int(3*self.win_height/5)
        self.win.resizable(0, 0) #窗口不可调节大小
        self.video_source = video_source
        # open video source
        self.vid = widgets.MyVideoCapture(self.canvas_width,self.canvas_height)
        self.widfun = widgets.WidFun()#实例化widgets里的函数
        self.pic_sum = 0 #记录从软件运行开始拍摄照片的数量
        self.delay = 40  #视频刷新delay 1000/dely = 帧数
        self.pic_count = 0  #读取的原始图片
        self.defect_pic_count = 0 # 循环播放缺陷图片用初始0
        self.pic_seq = 0 # 上下键对比播放图片计数
        self.defect_count = 0  # 缺陷计数
        self.defect_src_list = [] # 存在缺陷的原图
        self.defect_dst_list = []# 存在缺陷的dst图
        self.defect_info_list=[]
        self.COM_plc = None
        #self.COM = serial.Serial('COM1',9600,bytesize=8,stopbits=1,parity='N',timeout=0.5)
        self.state_read_flag = Event()      # 设置平台读取状态开关
        self.state_read_flag.set() # 将读取开关设置为true
        self.platform_position = 0
        self.platform_state = 0
        self.lock = _RLock()
             # 总计重复自动拍照 次数
        self.timer_interval = 0 # 两次间隔拍照之间的时间
        self.timer_times_count = 0 # 自动拍照计数
        #放置组件
        self.create_tab()
        self.create_menu()
        self.create_widgets() # 第一页 视频显示 图像采集页
        self.create_widgets_2() # 第二页 图像播放 参数设置页
        #self.create_widgets_3()  # 第三页 缺陷信息汇总页
        self.widfun.defaultFileEntries(fileEntry=self.fileEntry,dstEntry=self.dstEntry,snapPathEntry=self.snapPathEntry)#设置初始路径
        self.plt_setting()
        self.draw_RGB()
        self.update_cam()
        self.win.mainloop()
    #创建实时显示  和 缺陷检测 分页
    def create_tab(self):
        tabControl = ttk.Notebook(self.win)  # 创建 TabControl

        self.tab_video = ttk.Frame(tabControl)  #创建分页
        tabControl.add(self.tab_video, text='实时显示')  # 在tab control中布置tab_video

        self.tab_process = ttk.Frame(tabControl)
        tabControl.add(self.tab_process, text='缺陷检测')

        tabControl.pack(expand=1, fill="both")  # 在window中放置tabcontrol
    #创建菜单
    def create_menu(self):
        menuBar = tk.Menu(self.win)
        Manipmenu = tk.Menu(menuBar, tearoff=0)
        menuBar.add_cascade(label='操作', menu=Manipmenu)
        #Manipmenu.add_command(label='运行', command=self.start)
        Manipmenu.add_command(label='退出', command=self.quit)
        self.win.config(menu=menuBar)
#######################创建 第 1 页的 按钮 和 标签 #######################################
    def create_widgets(self):
        l0 = tk.Label(self.tab_video, text='设置',fg = 'blue')
        l0.place(relx=0.15, rely=0.02)
        l1 = tk.Label(self.tab_video, text='逐帧拍摄间隔(毫秒)')
        l2 = tk.Label(self.tab_video, text='自动拍摄次数')
        l3 = tk.Label(self.tab_video, text = '自动拍摄间隔(分钟)')
        '''
        l4 = tk.Label(self.tab_video, text = '每天定时拍照')
        l4.place(relx = 0.01, rely = 0.20)'''
        snapPath = tk.StringVar()
        self.entryLen = int(self.win_height/30)
        self.snapPathEntry = ttk.Entry(self.tab_video, width=self.entryLen, textvariable=snapPath)
        but_snap_path = ttk.Button(self.tab_video, text = '图片保存路径',command = self.setSnapPath)

        self.pic_delay = tk.IntVar()  # 拍照时间间隔
        value_pic_delay = ttk.Combobox(self.tab_video, width=5, textvariable=self.pic_delay)
        value_pic_delay['values'] = (50, 100, 150, 200)
        value_pic_delay.current(1)

        self.timer_total_times = tk.IntVar()  # 自动拍摄总次数
        value_timer_total_times = ttk.Combobox(self.tab_video, width=5, textvariable=self.timer_total_times)
        value_timer_total_times['values'] = (1, 2, 3, 4, 5)
        value_timer_total_times.current(0)

        self.timer_interval = tk.IntVar()  # 自动拍摄间隔
        value_timer_interval = ttk.Combobox(self.tab_video, width=5, textvariable=self.timer_interval)
        value_timer_interval['values'] = (1, 2, 3, 4)
        value_timer_interval.current(0)

        initial_position_x = 0.025 #label c初始位置
        initial_position_y = 0.02
        list_labels = [l1,l2,l3,but_snap_path]# 设置，逐帧拍摄间隔，自动拍摄次数，自动拍摄间隔，图片保存路径
        list_combo_entry = [value_pic_delay, value_timer_total_times, value_timer_interval, self.snapPathEntry]
        step = 0.05
        for i in list_labels:
            i.place(relx = initial_position_x,rely = initial_position_y + step )
            step += 0.05
        initial_position_x = 0.225
        step = 0.05
        for j in list_combo_entry:
            j.place(relx = initial_position_x,rely = initial_position_y + step )
            step += 0.05
        self.button_font = font.Font(family='Symbol',size = int(self.win_height/50))# 设置按钮的字体和大小

        but_open_com = tk.Button(self.tab_video,text = '串口通信', relief = GROOVE,font = self.button_font,fg = 'black',bg = '#DCDCDC',command = self.open_COM_plc)
        but_open_com.place(relx = 0.525,rely = 0.04)

        but_start_motor_program = tk.Button(self.tab_video, text='打开红外', relief = GROOVE,font = self.button_font,fg = 'black',bg = '#DCDCDC',
                                            command=self.widfun.start_infrared_program)
        but_start_motor_program.place(relx=0.625, rely=0.04)

        but_get_pic = tk.Button(self.tab_video,text = '自动拍照' ,relief = GROOVE,font = self.button_font,fg = 'blue',bg = '#DCDCDC',command = self.set_timer_thread)#auto_take_pic_thread
        but_get_pic.place(relx = 0.525 , rely = 0.12)

        but_platform_move = tk.Button(self.tab_video, text='平台移动',relief = GROOVE,font = self.button_font,fg = 'black',bg = '#DCDCDC',
                                command=self.slow_move)
        but_platform_move.place(relx=0.625, rely=0.12)

        but_platform_reset = tk.Button(self.tab_video, text='平台复位',relief = GROOVE,font = self.button_font,fg = 'black',bg = '#DCDCDC',
                                command=self.reset)
        but_platform_reset.place(relx=0.725, rely=0.12)

        self.label_timer_msg = tk.Label(self.tab_video,text = ' 当前没有拍摄任务 ',font = self.button_font,bg = '#DCDCDC')
        self.label_timer_msg.place(relx = 0.725,rely = 0.0425 )

        self.temp_msg = tk.Label(self.tab_video,text = ' 温度: 无 ',font = self.button_font,fg = 'black')
        self.temp_msg.place(relx = 0.4,rely = 0.0425 )

        but_click_move = tk.Button(self.tab_video, text='平台点动',relief = GROOVE,font = self.button_font,fg = 'black',bg = '#DCDCDC',
                                       command=self.click_move)
        but_click_move.place(relx=0.525, rely=0.2)

        self.click_move_pos = tk.IntVar()  # 点动距离
        combobox_click_move_pos = ttk.Combobox(self.tab_video, width=10, height = 10 ,textvariable=self.click_move_pos)
        combobox_click_move_pos['values'] = (0,500, 1000, 1500, 2000, 2400)
        combobox_click_move_pos.current(0)
        combobox_click_move_pos.place(relx=0.625, rely=0.2)

        but_manual_forward = tk.Button(self.tab_video, text='手动前进', relief=GROOVE, font=self.button_font, fg='black',
                                   bg='#DCDCDC',
                                   command=self.manual_forward)
        but_manual_forward.place(relx=0.725, rely=0.2)

        but_manual_backward = tk.Button(self.tab_video, text='手动后退', relief=GROOVE, font=self.button_font, fg='black',
                                   bg='#DCDCDC',
                                   command=self.manual_backward)
        but_manual_backward.place(relx=0.825, rely=0.2)

        but_emergency_stop = tk.Button(self.tab_video, text='紧急停止', relief=GROOVE, font=self.button_font, fg='red',
                                   bg='#DCDCDC',
                                   command=self.emergency_stop)
        but_emergency_stop.place(relx=0.825, rely=0.12)



        list_buttons = [but_open_com, but_start_motor_program, but_get_pic, but_platform_move, but_platform_reset,
                        but_click_move, combobox_click_move_pos]

        # 截屏按钮
        self.btn_snapshot = tk.Button(self.tab_video, text="保存图片",width=28,fg = 'blue',bg = 'white', font = 'Symbol' ,command=self.creat_thread0)
        #self.btn_snapshot.place(relx = 0.52 , rely = 0.9)
        # 视频画布
        self.canvas = tk.Canvas(self.tab_video, width=self.canvas_width, height=self.canvas_height,bg = 'grey' )
        self.canvas.place(relx = 0.525 , rely = 0.325)


#####################创建  第 2 页 的 按钮和标签####################################################
    def create_widgets_2(self):
        l0 = tk.Label(self.tab_process, text='参数设置',fg ='blue')
        l0.place(relx=0.125, rely=0.02)
        l1 = tk.Label(self.tab_process, text='自适应阈值常数')
        l2 = tk.Label(self.tab_process, text='卷积核大小')
        l3 = tk.Label(self.tab_process, text='对比度常数')
        l4 = tk.Label(self.tab_process, text='缺陷面积下限')

        self.value_Threshold_constant = tk.StringVar()  # 自适应阈值常数
        value_set1 = ttk.Combobox(self.tab_process, width=5, textvariable=self.value_Threshold_constant)
        value_set1['values'] = (10, 20, 30, 40)
        value_set1.current(1)

        self.value_Convolution_kernel = tk.StringVar()  # 卷积核大小
        value_set2 = ttk.Combobox(self.tab_process, width=5, textvariable=self.value_Convolution_kernel)
        value_set2['values'] = (3, 5, 7)
        value_set2.current(0)

        self.value_Brightness = tk.StringVar()  # 亮度 增强对比度
        value_set3 = ttk.Combobox(self.tab_process, width=5, textvariable=self.value_Brightness)
        value_set3['values'] = (10, 20, 30, 40)
        value_set3.current(1)

        self.value_Lower_defect_area = tk.StringVar()  # 缺陷面积下限
        value_set4 = ttk.Combobox(self.tab_process, width=5, textvariable=self.value_Lower_defect_area)
        value_set4['values'] = (10, 15, 20, 25, 30)
        value_set4.current(2)

        #but_load_pic = tk.Button(self.tab_process,text = '进行缺陷识别', relief = GROOVE,font = self.button_font,fg = 'black',bg = '#DCDCDC',command = self.creat_thread_process_pic)
        #but_load_pic.place(relx = 0.07 , rely = 0.32)
        # 用于显示图片的canvas
        # self.canvas2 = tk.Canvas(self.tab_process,  width=self.canvas_width, height=self.canvas_height,bg = 'grey')
        # self.canvas2.place(relx=0.37, rely=0.005)

        self.canvas_src= tk.Canvas(self.tab_process, width=self.canvas_width, height=self.canvas_height, bg='grey')
        self.canvas_src.place(relx=0.025, rely=0.325)

        self.canvas_dst= tk.Canvas(self.tab_process, width=self.canvas_width, height=self.canvas_height, bg='grey')
        self.canvas_dst.place(relx=0.525, rely=0.325)
        #放置 label 和 commbox

        # 输出图片路径按钮
        dstbut = ttk.Button(self.tab_process, text="输出图片路径", command=self.setDstPath)

        # 读取路径Entry
        file = tk.StringVar()
        self.entryLen = 20
        self.fileEntry = ttk.Entry(self.tab_process, width=self.entryLen, textvariable=file)
        #self.fileEntry.place(relx=0.15, rely=0.6)
        # 输出路径Entry
        dst = tk.StringVar()
        self.entryLen = 20
        self.dstEntry = ttk.Entry(self.tab_process, width=self.entryLen, textvariable=dst)


        initial_position_x = 0.025  # label c初始位置
        initial_position_y = 0.02
        list_labels = [l1, l2, l3, l4, dstbut]  # 自适应阈值常数，卷积核大小，对比度常数，缺陷面积下线
        list_combo_entry = [value_set1, value_set2, value_set3, value_set4,self.dstEntry]
        step = 0.05
        for i in list_labels:
            i.place(relx=initial_position_x, rely=initial_position_y + step)
            step += 0.05
        initial_position_x = 0.225
        step = 0.05

        for j in list_combo_entry:
            j.place(relx=initial_position_x, rely=initial_position_y + step)
            step += 0.05

        last_but = tk.Button(self.tab_process,text ="⬆", bg='white', fg='blue', font='Symbol',
                              command=self.paging_last)
        last_but.place(relx=0.49, rely=0.55)

        next_but = tk.Button(self.tab_process, text="⬇", bg='white', fg='blue', font='Symbol',
                              command=self.paging_next)
        next_but.place(relx=0.49, rely=0.65)

        label = tk.Label(self.tab_process, text='缺陷信息', fg='blue')
        label.place(relx=0.625, rely=0.02)
        self.defect_info_st = scrolledtext.ScrolledText(self.tab_process, width=int(self.canvas_width / 10),
                                                        height=int(self.canvas_height / 40), wrap=tk.WORD)
        self.defect_info_st.place(relx=0.525, rely=0.075)

        write_but = tk.Button(self.tab_process, text="保存缺陷信息", relief=GROOVE, font=self.button_font, fg='black',
                              bg='#DCDCDC', command=self.write_defect_log)
        write_but.place(relx=0.875, rely=0.225)


############################ 设置第 3 页 用到的 widgets###########################
    def set_screen_size(self,win):
        ratio = 1.2
        screenwidth = win.winfo_screenwidth()
        screenheight = win.winfo_screenwidth()
        width = win.winfo_screenwidth()/ratio
        height = win.winfo_screenheight()/ratio
        size ='%dx%d+%d+%d' % (width, height, (screenwidth - width)/2, (screenheight - height)/16)
        win.geometry(size)
        return width , height
    def start(self):
        pass
    #退出程序
    def quit(self):
        self.win.quit()
        self.win.destroy()
        exit()
################### 第 1 页 用到方法################################################
    #更新视频
    def update_cam(self):
        ret,frame = self.vid.get_frame()
        if ret != 2:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0,0,image = self.photo,anchor = tk.NW)
            self.win.after(self.delay,self.update_cam)
        if ret == 2:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
    def draw_RGB(self):
        # clear the figure or the new figure will be mixed with the old one
        self.f.clf()
        self.a = self.f.add_subplot(111,)
        ret,frame = self.vid.get_frame()
        colors = ['b', 'g', 'r']
        for i, color in enumerate(colors):
            hist = cv.calcHist([frame], [i], None, [256], [0, 256])#calculate the hist of frame
            self.a.plot(hist, color=color)  # draw the hist created in plot
        self.canvas_plt.draw()
        self.win.after(500, self.draw_RGB)
    def plt_setting(self):
        self.f = Figure(figsize=(4, 3), dpi=self.win_height/5)
        self.canvas_plt = FigureCanvasTkAgg(self.f, master=self.tab_video)
        self.canvas_plt.get_tk_widget().place(relx = 0.025,rely = 0.325)
    # 用于1次拍照
    def creat_thread0(self):
        runT = Thread(target=self.snapshot)
        runT.setDaemon(True)
        runT.start()

    def open_COM_plc(self):
        port_list = list(serial.tools.list_ports.comports())
        #self.COM_plc = serial.Serial('COM1', 9600, bytesize=8, stopbits=1, parity='N', timeout=0.5)

        if len(port_list) != 0:
            try:
                self.COM_plc = serial.Serial('COM1', 9600, bytesize=8, stopbits=1, parity='N', timeout=0.5)
                print('串口打开成功')
                self.receive_state_thread()
            except:
                try:
                    self.COM_plc = serial.Serial('COM2', 9600, bytesize=8, stopbits=1, parity='N', timeout=0.5)
                    print('串口打开成功')
                    self.receive_state_thread()
                except:
                    try:
                        self.COM_plc = serial.Serial('COM3', 9600, bytesize=8, stopbits=1, parity='N', timeout=0.5)
                        print('串口打开成功')
                        self.receive_state_thread()
                    except:
                        print('没有检索到可用串口')
        else:
            print('未读取到可用串口')
            mBox.showinfo(title='无可用串口', message='无可用串口')

    def take_photo_new_thread(self):
        runT = Thread(target=self.take_photo_new)
        runT.setDaemon(True)
        runT.start()

    def receive_state_thread(self):
        runT = Thread(target=self.receive_state)
        runT.setDaemon(True)
        runT.start()

    def set_timer_thread(self):
        runT = Thread(target=self.start_timer)
        runT.setDaemon(True)
        runT.start()

    def keep_draw_RGB_thread(self):
        runT = Thread(target=self.draw_RGB)
        runT.setDaemon(True)
        runT.start()

    def snapshot(self):
       # 拍摄一张图片
        snap_path_head = self.snapshot_folder_path
        self.pic_sum += 1 # 记录总计拍照次数
        current_position = self.get_platform_position()
        current_state = self.get_platform_state()
        if self.COM_plc is not None:
            if current_position > 160 and current_position < 2401: #and self.platform_state == '04':
                print('第' + str(self.timer_times_count) + '次拍照')
                ret,frame = self.vid.get_frame()
                if ret:
                    pic_time = time.strftime("%d-%m-%Y-%H-%M-%S")
                    snap_path = snap_path_head +'/'+ 'L'+str(current_position)+'-'+ pic_time + ".jpg"
                    print(snap_path)
                    frame = cv.cvtColor(frame,cv.COLOR_RGB2BGR)
                    cv.imwrite(snap_path, frame)
            else:
                print('不在拍摄范围',current_position,current_state)
                # 间隔获取照片
        else:
            ret,frame = self.vid.get_frame()
            if ret:
                pic_time = time.strftime("%d-%m-%Y-%H-%M-%S")
                snap_path = snap_path_head + '/' + 'L' + str(current_position) + '-' + pic_time + ".jpg"
                print(snap_path)
                frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
                cv.imwrite(snap_path, frame)

    # 自动拍照
    def auto_take_pic(self):
        self.timer_times_count += 1
        if self.COM_plc != None:
            self.slow_move()
            time.sleep(0.1)
            if self.platform_position == 0:
                self.slow_move()
                time.sleep(0.1)
            print('开始拍照')
            self.get_pics()
        else:
            print('开始脱离平台拍照')
            self.get_pics_in_test_mode()

    def get_pics(self):
        shot_flag = True
        new = 0
        old = 0
        pic_delay = self.pic_delay.get()/1000.0# tk.IntVar 要加上 .get()
        folder_time = time.strftime("%d-%m-%Y-%H-%M-%S")
        folder_path = self.snapPathEntry.get()
        self.snapshot_folder_path=self.widfun.create_folder(folder_time,folder_path) # 保存自动拍照的文件夹地址

        while shot_flag:
            temp = self.platform_position
            if temp - new < 50:# 防止噪声
                new = self.platform_position
                if old < new or new == old:
                    shot_flag = True
                else:
                    shot_flag = False
                    #mBox.showinfo(title='拍摄完成', message='拍摄完成')
                    break
                self.snapshot()
                time.sleep(pic_delay)
                old = new
    def get_pics_in_test_mode(self):
        if self.COM_plc is None:
            pic_delay = self.pic_delay.get() / 1000.0  # tk.IntVar 要加上 .get()
            folder_time = time.strftime("%d-%m-%Y-%H-%M-%S")
            folder_path = self.snapPathEntry.get()
            self.snapshot_folder_path = self.widfun.create_folder(folder_time, folder_path)
            for i in range(10):
                self.snapshot()
                time.sleep(pic_delay)

    def start_timer(self):
        self.timer_times_count = 0 # 每次启动计时器都是从0开始
        interval = self.timer_interval.get()  #从gui中得到两次拍照间隔时长
        interval = int(interval)*60  # 间隔分钟  小时则改为 3600
        total_times = self.timer_total_times.get()
        print('interval = ',interval,'s')
        for times in range(total_times):
            next_time = time.strftime('%H:%M',time.localtime(time.time()+interval))# 正常运行时，需再加上电机运行时间
            timer_message = '当前' + str(times + 1) + '/' + str(total_times) + '次拍照'
            self.label_timer_msg.configure(text=timer_message)
            self.auto_take_pic()
            if times != total_times -1:
                timer_message = '完成'+ str(times + 1) +'/'+str(total_times)+ '拍照，预计下次拍照 '+str(next_time)
            else:
                timer_message = '第' + str(times + 1) + '/' + str(total_times) + '次拍照完成'
            self.label_timer_msg.configure(text=timer_message)
            self.start_process()
            if times != total_times -1:
                time.sleep(interval)
        timer_message = '当前没有拍摄任务'
        self.label_timer_msg.configure(text=timer_message)
        mBox.showinfo(title='拍照结束', message='拍照结束')
        if self.defect_count == 0:
            mBox.showinfo(title='未检出疑似缺陷', message='未检出疑似缺陷')



    # 读取log
    '''
    def read_log(self):
        log_list = ['run_log0.txt','run_log1.txt']
        self.log_info = []# 信息栏
        present_dir = getcwd() # 获取文件位子
        while True:
            for i in log_list:
                if path.exists(i):#判断log是否存在
                    #print('Obj exists')
                    if self.read_flag != i:# 判断log是否之前读取过，防止反复读取
                        #print('log is new')
                        self.log_info = [] #若为新log 则清空之前的log_info
                        with open(i) as log_obj:
                            for line in log_obj:
                                self.log_info.append(line.rstrip())
                            self.read_flag = i #记录读取后的 log 名
    '''
    # 获取导轨位置和温度状态
    def receive_state(self):  # 发送函数
        if self.COM_plc != None:
            print('读取到串口存在')
            while True:
                self.state_read_flag.wait()
                if self.COM_plc.is_open:
                    myinput = bytes([0X01, 0X03, 0X00, 0X00, 0X00, 0X02, 0XC4, 0X0B])
                    # x.write("\X01\X03\X00\X00\X00\X02\XC4\X0B".encode('gbk'))
                    self.COM_plc.write(myinput)
                    time.sleep(0.05)
            #读取状态
                while self.COM_plc.inWaiting() > 0:
                    myout = self.COM_plc.read(9)   # 读取串口传过来的字节流，接收 9 个字节的数据
                    datas = ''.join(map(lambda x: ('/x' if len(hex(x)) >= 4 else '/x0') + hex(x)[2:], myout))  # 将数据转成十六进制的形式
                    #print('datas:', datas)  #datas: /x01/x03/x04/x00/x00/x00/x76/x7b/xd5
                    new_datas = datas.split("/x")  # 将字符串分割，拼接下标4和5部分的数据
                    #print('newdatas', new_datas) #newdatas ['', '01', '03', '04', '00', '00', '00', '76', '7b', 'd5']
                    if len(new_datas) == 10:
                        self.platform_position = int(new_datas[4], 16) * 256 + int(new_datas[5], 16)
                        self.platform_state = new_datas[6]  # 0 停止 2 复位 4 连续运行 8 点动运行
                    time.sleep(0.05)  #防止读取后无法 发送
            #读取温度
                    myinput = bytes([0XB2, 0X01])  # 读取温度 B2为探头地址 01为读取温度指令
                    self.COM_plc.write(myinput)
                    time.sleep(0.05)
                    # 读取返回
                while self.COM_plc.inWaiting() > 0:
                    myout = self.COM_plc.read(2)  # 读取串口传过来的字节流，接收 2 个字节的数据
                    # 对myout中的每个数据数据转成十六进制的形式
                    datas = ''.join(map(lambda x: ('/x' if len(hex(x)) >= 2 else '/x0') + hex(x)[2:], myout))
                    new_datas = datas.split("/x")  # 将字符串分割
                    temperature = (int(new_datas[1], 16) * 256 + int(new_datas[2], 16) - 1000) / 10
                    if temperature > 0 and temperature < 60:
                        text = '温度：'+ str(temperature)
                        self.temp_msg.configure(text=text,fg = 'green')
                        time.sleep(0.05)
                    elif temperature > 60 and temperature < 100:
                        text = '温度：' + str(temperature)
                        self.temp_msg.configure(text=text,fg = 'red')
                    else:
                        pass
        else:
            print('串口未连接')
                #print(self.platform_position)
          #print(self.platform_state,self.platform_position)
    def get_platform_position(self):
        if self.COM_plc != None:
            position = self.platform_position
        else:
            r = random.randint(1,9999)
            position = r
        return position
    def get_platform_state(self):
        if self.COM_plc != None:
            state = self.platform_state
        else:
            state = 'Test'
        return state
    #平台复位
    def reset(self):
        if self.COM_plc != None:
            #self.lock.acquire()
            self.state_read_flag.clear()
            if self.COM_plc.is_open:
                myinput = bytes([0X01, 0X05, 0X00, 0X00, 0XFF, 0X00, 0X8C, 0X3A])
                self.COM_plc.write(myinput)
                time.sleep(0.1)
            self.state_read_flag.set()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法复位')

    #平台缓慢移动
    def slow_move(self):
        if self.COM_plc != None:
            self.lock.acquire()
            #self.state_read_flag.clear()
            if self.COM_plc.is_open:
                myinput = bytes([0X01, 0X05, 0X00, 0X01, 0XFF, 0X00, 0XDD, 0XFA])
                self.COM_plc.write(myinput)
                time.sleep(0.05)
            #self.state_read_flag.set()
            self.lock.release()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法移动平台')
    def click_move(self): #点动
        if self.COM_plc != None:
            self.state_read_flag.clear()
            self.lock.acquire()
            pos_get = self.click_move_pos.get()
            print(pos_get)
            pos_high8 = int(pos_get / 256) + 128
            pos_low8 = int(pos_get) % 256
            crch = 0xFF
            crcl = 0xFF
            for i in [0X01, 0X06, 0X00, 0X02, pos_high8, pos_low8]:
                crcl = crcl ^ i
                for i in range(8):
                    if crcl % 2 == 1:
                        crcl = crcl // 2 + (crch % 2) * 128
                        crch = crch // 2
                        crch = crch ^ 0xA0
                        crcl = crcl ^ 0x1
                    else:
                        crcl = crcl // 2 + (crch % 2) * 128
                        crch = crch // 2
            parity_high_8 = crcl
            parity_low_8 = crch
            if self.COM_plc.is_open:
                myinput= bytes([0X01, 0X06, 0X00, 0X02, pos_high8, pos_low8,parity_high_8 ,parity_low_8])
                #print(myinput)
                self.COM_plc.write(myinput)
                time.sleep(0.1)
            self.lock.release()
            self.state_read_flag.set()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法移动平台')

    def manual_forward(self):
        if self.COM_plc != None:
            self.state_read_flag.clear()
            if self.COM_plc.is_open:
                myinput = bytes([0X01, 0X05, 0X00, 0X04, 0XFF, 0X00, 0XCD, 0XFB])
                self.COM_plc.write(myinput)
                time.sleep(0.1)
            self.state_read_flag.set()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法移动')

    def manual_backward(self):
        if self.COM_plc != None:
            self.state_read_flag.clear()
            if self.COM_plc.is_open:
                myinput = bytes([0X01, 0X05, 0X00, 0X05, 0XFF, 0X00, 0X9C, 0X3B])
                self.COM_plc.write(myinput)
                time.sleep(0.1)
            self.state_read_flag.set()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法移动')

    def emergency_stop(self):
        if self.COM_plc != None:
            self.state_read_flag.clear()
            if self.COM_plc.is_open:
                myinput = bytes([0X01, 0X05, 0X00, 0X03, 0XFF, 0X00, 0X7C, 0X3A])
                self.COM_plc.write(myinput)
                time.sleep(0.1)
            self.state_read_flag.set()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法操作')

    def receive_temp(self):  # 温度接收函数
        if self.COM_plc != None:
            while True:
                if self.COM_plc.is_open:
                    myinput = bytes([0XB2,0X01])#读取温度 B2为探头地址 01为读取温度指令
                    self.COM_plc.write(myinput)
                    time.sleep(0.05)
            #读取返回
                while self.COM_plc.inWaiting() > 0:
                    myout = self.COM_plc.read(2) # 读取串口传过来的字节流，接收 2 个字节的数据
                    # 对myout中的每个数据数据转成十六进制的形式
                    datas = ''.join(map(lambda x: ('/x' if len(hex(x)) >= 2 else '/x0') + hex(x)[2:], myout))
                    new_datas = datas.split("/x")  # 将字符串分割
                    temperature = (int(new_datas[1], 16) * 256 + int(new_datas[2], 16)-1000)/10
                    if temperature:
                        self.temp_msg.configure(text=temperature)
                        time.sleep(0.05)

    def setSnapPath(self):
        fDir = path.dirname(__file__)  ## 获取文件所在文件夹路径
        self.dPath = fd.askdirectory(parent=self.win, initialdir='D:/Defect Detection')  # 设置截图保存路径
        # print(self.dPath)
        self.snapPathEntry.config(state='enabled')
        self.snapPathEntry.delete(0, tk.END)
        self.snapPathEntry.insert(0, self.dPath)
################### 第 2 页 用到方法################################################

    def start_process(self):#拍照后，开始处理图片
        #self.defect_src_list = [] #每次处理前清空 list of src with defect
        img_list, self.list_len = self.widfun.get_img_list(self.snapshot_folder_path)  # 获取待处理图片 list 与 Length 防止在没加载图片
        q = Queue()#用来获取 widgets里的返回值
        args = (self.value_Brightness,self.value_Threshold_constant,self.value_Convolution_kernel,
                self.value_Lower_defect_area,self.defect_info_st,self.fileEntry,self.dstEntry,q)
        runThread = Thread(
            target=self.widfun.process_pic(self.value_Brightness,self.value_Threshold_constant,
                                           self.value_Convolution_kernel,self.value_Lower_defect_area,self.defect_info_st,
                                           self.snapshot_folder_path,self.dstEntry,q))
        #runThread.join()

        return_list = q.get(block=False)
        self.dst_folder_add = return_list[0]
        self.defect_src_list_from_widfun = return_list[1]
        self.defect_dst_list_from_widfun = return_list[2]
        for defect_src_add in self.defect_src_list_from_widfun:
            self.defect_src_list.append(defect_src_add)

        for defect_dst_add in self.defect_dst_list_from_widfun:
            self.defect_dst_list.append(defect_dst_add)
        print(self.dst_folder_add)
        self.dst_set()
        self.src_set()
        self.defect_count += len(return_list[2])


    #设置 输出图片 所在文件夹路径
    def setDstPath(self):
        fDir = path.dirname(__file__)  ## 获取文件所在文件夹路径
        self.dPath = fd.askdirectory(parent=self.win, initialdir='D:\Defect Detection\dst_directory') #设置输出路径
        #print(self.dPath)
        self.dstEntry.config(state='enabled')
        self.dstEntry.delete(0, tk.END)
        self.dstEntry.insert(0, self.dPath)

################### 第 3 页 用到方法################################################
    # 获取 处理后图片 文件夹中文件的list 和 length
    def get_defect_img_list(self,dst_folder_add):
        read_pic_add = dst_folder_add

        glob_add = read_pic_add + '/*.jpg'
        defect_imgs_list = glob.glob(glob_add)
        list_len = len(defect_imgs_list)
        return defect_imgs_list,list_len

    def write_defect_log(self):
        with open('defect info.txt','w') as f_obj:
            for info in self.defect_info_list:
                f_obj.write(info)
    def contrast(self):
        self.contrast_win = tk.Toplevel(self.win)
        self.contrast_win.title('对比')
        self.contrast_win.geometry('1320x640')
        self.contrast_win.resizable(0, 0)

        self.canvas_src= tk.Canvas(self.tab_process, width=self.canvas_width, height=self.canvas_height, bg='grey')
        self.canvas_src.place(relx=0.025, rely=0.325)

        self.canvas_dst= tk.Canvas(self.tab_process, width=self.canvas_width, height=self.canvas_height, bg='grey')
        self.canvas_dst.place(relx=0.525, rely=0.325)


        self.dst_set()
        self.src_set()
        # 放置src
    def src_set(self):
        if self.defect_src_list:
            if self.pic_seq < len(self.defect_src_list):
                src = cv.imread(self.defect_src_list[self.pic_seq])
                src_rgb = cv.cvtColor(src, cv.COLOR_BGR2RGB)
                global src_PIL
                src_PIL = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(src_rgb))#image 需为全局变量
                self.canvas_src.create_image(0, 0, image=src_PIL, anchor=tk.NW)
        #放置dst
    def dst_set(self):
        if self.defect_dst_list:
            dst = cv.imread(self.defect_dst_list[self.pic_seq])
            dst_rgb = cv.cvtColor(dst, cv.COLOR_BGR2RGB)
            global   dst_PIL
            dst_PIL = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(dst_rgb))
            self.canvas_dst.create_image(0, 0, image=dst_PIL, anchor=tk.NW)
    #缺陷照片翻页 下一页
    def paging_next(self):
        if self.pic_seq < len(self.defect_src_list) - 1:
            self.pic_seq += 1
            self.src_set()
            self.dst_set()
    # 缺陷照片翻页 上一页
    def paging_last(self):
        if self.pic_seq > 0:
            self.pic_seq -= 1
            self.src_set()
            self.dst_set()

#============================================================
    # 形态学操作 ，k 为卷积核大小
    def xingtai_demo(self,img, k):
        kernel_1 = np.ones((k, k), np.uint8)
        kernel_2 = np.ones((2, 2), np.uint8)
        kernel_3 = np.ones((10, 10), np.uint8)
        img_1 = cv.erode(img, kernel_2)
        dst = cv.morphologyEx(img_1, cv.MORPH_CLOSE, kernel_1) #闭操作 填充小的黑色区域
        src = cv.dilate(dst, kernel_3)
        return src

    # 图片处理后，亮度br=20，灰度阈值上升thr_g_r=10,卷积核大小k=3,瑕疵值the_cl=10
    def process(self,source, br, thr_g_r, k, the_cl):
        self.defect_flag = 0 #缺陷标记 每次处理时都先将缺陷标记置零
        #  比卷积均值大 thr_g_r 则置为255
        gamma = cv.cvtColor(source, cv.COLOR_BGR2GRAY)
        rows = source.shape[0]
        cols = source.shape[1]
        br += 30
        #增强图像对比度
        print(type(gamma))
        for i in range(rows):
            for j in range(cols):
                power = br* pow(gamma.item(i,j),0.2)##获取像素点 并 乘方
                gamma.itemset((i,j),power)### 设置像素点
        #自适应阈值 进行二值化 thr_g_r 常数项 当 像素点比 平均值 大 thr_g_r 时 置为 255
        bi = cv.adaptiveThreshold(gamma, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY_INV, 25, thr_g_r)
        # 对二值化后图像进行形态学操作
        bi_1 = self.xingtai_demo(bi, k)
        # 轮廓发现 仅支持二值图像
        #ret,contours, hierarchy = cv.findContours(bi_1, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)  # opencv3 将ret 去掉
        contours, hierarchy = cv.findContours(bi_1, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)  # opencv4 将ret 去掉
        # 遍历所有轮廓
        defect_count_local = 0
        for i, contour in enumerate(contours):
            area = cv.contourArea(contour)
            para = cv.arcLength(contour, True)
            # 识别缺陷 缺陷面积下限 （轮廓面积小于该值则忽略）
            if area < the_cl or area > 500:
                continue
            # print('flaw area', area)
            index = float(para * para / (4 * area * np.pi))
            index = round(index,4)
            area = round(area,4)
            if index < 0.8: # 紧凑性系数 越接近圆形 越视为缺陷
                self.defect_flag = 1

            # 在原图上标记缺陷位置
            if self.defect_flag == 1:
                self.defect_count += 1
                defect_count_local += 1
                defect_info = '缺陷'+str(self.defect_count) +'\t紧凑系数：' + str(index) + '\n'
                defect_info += '\t缺陷面积：'+str(area) + '\n'
                #print(defect_info)
                self.defect_info_list.append(defect_info)
                x, y, w, h = cv.boundingRect(contour)
                cv.rectangle(source, (x, y), (x + w, y + h), (0, 0, 255), 2)
                moments = cv.moments(contour)
                if moments['m00']:
                    cx = moments['m10'] / moments['m00']
                    cy = moments['m01'] / moments['m00']
                else:
                    continue
                cv.circle(source, (np.int(cx), np.int(cy)), 4, (0, 0, 255), 1)
            else:
                defect_info = '未能检测出缺陷'
                self.defect_info_list.append(defect_info)
        return source

if __name__ == "__main__":
    app = App(tk.Tk(), "胶辊表面缺陷识别")



