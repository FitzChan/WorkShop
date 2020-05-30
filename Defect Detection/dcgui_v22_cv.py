#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 尝试debug 识别后的保存图片
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
#import schedule

class MyVideoCapture:  ## 读取视频 及 其高宽
    def __init__(self, video_source=0):
        # Open the video source
        self.vid = cv.VideoCapture(video_source)
        self.vid.set(3, 2592)
        self.vid.set(4, 2048)
        '''if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)'''
        # Get video source width and height
        self.width =  640
        self.height = 480
        # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

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

class App:
    def __init__(self, win, window_title,video_source = 0):
        self.win = win
        self.win.title(window_title)
        self.win.geometry('1120x630')
        self.win.resizable(0, 0) #窗口不可调节大小
        self.video_source = video_source
        # open video source
        self.vid = MyVideoCapture()
        self.pic_group_flag = 1 # 用于标记各组照片的组号
        self.pic_group_flag_pic_flag = 1 # 用于标记单组内的图片编号
        #self.read_flag = '' 读取文件用
        self.pic_sum = 0
        self.delay = 40  #视频刷新delay 1000/dely = 帧数
        self.pic_count = 0  #读取的原始图片
        self.defect_pic_count = 0 # 循环播放缺陷图片用初始0
        self.pic_seq = 0 # 上下键对比播放图片计数
        self.defect_count = 0  # 缺陷计数
        self.defect_src_list = [] # 存在缺陷的原图
        self.defect_info_list=[]
        self.COM = None
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
        self.create_widgets_3()  # 第三页 缺陷信息汇总页
        self.defaultFileEntries()
        self.receive_state_thread()
        #self.read_log_thread()  # 开启线程 监控log文件
        #self.put_defect_img()

        self.update_thread()
        self.win.mainloop()
    #创建实时显示  和 缺陷检测 分页
    def create_tab(self):
        tabControl = ttk.Notebook(self.win)  # 创建 TabControl

        self.tab_video = ttk.Frame(tabControl)  #创建分页
        tabControl.add(self.tab_video, text='实时显示')  # 在tab control中布置tab_video

        self.tab_process = ttk.Frame(tabControl)
        tabControl.add(self.tab_process, text='缺陷检测')

        self.tab_defect = ttk.Frame(tabControl)
        tabControl.add(self.tab_defect, text = '缺陷预览')

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
        l0 = tk.Label(self.tab_video, text='----- 设置 -----')
        l0.place(relx=0.05, rely=0.01)

        l1 = tk.Label(self.tab_video, text='逐帧拍摄间隔(毫秒)')
        l1.place(relx = 0.01 ,rely = 0.05)
        l2 = tk.Label(self.tab_video, text='自动拍摄次数')
        l2.place(relx=0.01, rely=0.1)
        l3 = tk.Label(self.tab_video, text = '自动拍摄间隔(分钟)')
        l3.place(relx = 0.01, rely = 0.15)
        '''
        l4 = tk.Label(self.tab_video, text = '每天定时拍照')
        l4.place(relx = 0.01, rely = 0.20)'''


        but_snap_path = ttk.Button(self.tab_video, text = '图片保存路径',command = self.setSnapPath)
        but_snap_path.place(relx = 0.01, rely = 0.23)

        snapPath = tk.StringVar()
        self.entryLen = 20
        self.snapPathEntry = ttk.Entry(self.tab_video, width=self.entryLen, textvariable=snapPath)
        self.snapPathEntry.place(relx=0.18, rely=0.23)


        self.timer_total_times = tk.IntVar()  # 自动拍摄总次数
        value_set1 = ttk.Combobox(self.tab_video, width=5, textvariable=self.timer_total_times)
        value_set1['values'] = (1, 2, 3, 4, 5)
        value_set1.current(0)
        value_set1.place(relx = 0.18 , rely = 0.10)

        self.pic_delay = tk.IntVar()  # 拍照时间间隔
        self.value_pic_delay = ttk.Combobox(self.tab_video, width=5, textvariable=self.pic_delay)
        self.value_pic_delay['values'] = (50, 100, 150, 200)
        self.value_pic_delay.current(0)
        self.value_pic_delay.place(relx=0.18, rely=0.05)

        self.timer_interval = tk.IntVar()  # 自动拍摄间隔
        value_set3 = ttk.Combobox(self.tab_video, width=5, textvariable=self.timer_interval)
        value_set3['values'] = (1, 2, 3, 4)
        value_set3.current(0)
        value_set3.place(relx=0.18, rely=0.15)

        but_open_com = tk.Button(self.tab_video,text = '打开串口', font = 'Symbol',fg = 'blue',bg = 'white',command = self.open_COM)
        but_open_com.place(relx = 0.06,rely = 0.35)

        but_get_pic = tk.Button(self.tab_video,text = '自动拍照' ,font = 'Symbol',fg = 'blue',bg = 'white',command = self.set_timer_thread)#auto_take_pic_thread
        but_get_pic.place(relx = 0.06 , rely = 0.45)

        but_start_motor_program = tk.Button(self.tab_video, text='启动红外', font='Symbol', fg='blue', bg='white',
                                command=self.start_motor_program)
        but_start_motor_program.place(relx=0.17, rely=0.45)

        but_platform_move = tk.Button(self.tab_video, text='平台移动', font='Symbol', fg='blue', bg='white',
                                command=self.slow_move)
        but_platform_move.place(relx=0.06, rely=0.55)

        but_platform_reset = tk.Button(self.tab_video, text='平台复位', font='Symbol', fg='blue', bg='white',
                                command=self.reset)
        but_platform_reset.place(relx=0.17, rely=0.55)

        but_click_move = tk.Button(self.tab_video, text='平台点动', font='Symbol', fg='blue', bg='white',
                                       command=self.click_move)
        but_click_move.place(relx=0.06, rely=0.65)

        self.click_move_pos = tk.IntVar()  # 自动拍摄次数
        combobox_click_move_pos = ttk.Combobox(self.tab_video, width=11, height = 3 ,textvariable=self.click_move_pos)
        combobox_click_move_pos['values'] = (0,500, 1000, 1500, 2000, 2400)
        combobox_click_move_pos.current(0)
        combobox_click_move_pos.place(relx=0.17, rely=0.65)

        # 截屏按钮
        self.btn_snapshot = tk.Button(self.tab_video, text="保存图片",width=28,fg = 'blue',bg = 'white', font = 'Symbol' ,command=self.creat_thread0)
        self.btn_snapshot.place(relx = 0.52 , rely = 0.9)
        # 视频画布
        self.canvas = tk.Canvas(self.tab_video, width=self.vid.width, height=self.vid.height,bg = 'grey' )
        self.canvas.place(relx = 0.37 , rely = 0.005)
#####################创建  第 2 页 的 按钮和标签####################################################
    def create_widgets_2(self):
        l0 = tk.Label(self.tab_process, text='       ---参数设置---')
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

        but_load_pic = tk.Button(self.tab_process,text = '进行缺陷识别', fg = 'blue',bg = 'white',font = 'Symbol',command = self.creat_thread_process_pic)
        but_load_pic.place(relx = 0.07 , rely = 0.32)
        # 用于显示图片的canvas
        self.canvas2 = tk.Canvas(self.tab_process, width=self.vid.width, height=self.vid.height,bg = 'grey')
        self.canvas2.place(relx=0.37, rely=0.005)
        #放置 label 和 commbox
        l_1 = [l0,l1, l2, l3, l4]
        l_2 = [value_set1, value_set2, value_set3, value_set4]
        step = 0.02
        for i in l_1:
            i.place(relx = 0.02 ,rely = 0.02 + step )
            step += 0.05
        step = 0.07
        for j in l_2:
            j.place(relx = 0.15 ,rely = 0.02 + step)
            step += 0.05
        '''# 输入输出路径 框架# pending
        mngFilesFrame = ttk.LabelFrame(self.tab_process, text=' Manage Files: ')
        mngFilesFrame.place(relx = 0.5 ,rely = 0.5)'''
        # 输入图片路径按钮
        srcbut = ttk.Button(self.tab_process, text="输入图片路径", command=self.getFileName)
        srcbut.place(relx=0.02, rely=0.6)
        # 输出图片路径按钮
        dstbut = ttk.Button(self.tab_process, text="输出图片路径", command=self.setDstPath)
        dstbut.place(relx=0.02, rely=0.7)
        #加载图片按钮
        loadbut = tk.Button(self.tab_process, text="加载图片", width = 28,bg = 'white',fg = 'blue',font = 'Symbol',command=self.put_img)
        loadbut.place(relx = 0.52 , rely = 0.9)
        # 读取路径Entry
        file = tk.StringVar()
        self.entryLen = 20
        self.fileEntry = ttk.Entry(self.tab_process, width=self.entryLen, textvariable=file)
        self.fileEntry.place(relx=0.15, rely=0.6)
        # 输出路径Entry
        dst = tk.StringVar()
        self.entryLen = 20
        self.dstEntry = ttk.Entry(self.tab_process, width=self.entryLen, textvariable=dst)
        self.dstEntry.place(relx=0.15, rely=0.7)
############################ 设置第 3 页 用到的 widgets###########################
    def create_widgets_3(self):
        self.canvas3 = tk.Canvas(self.tab_defect, width=self.vid.width, height=self.vid.height,bg = 'grey')
        self.canvas3.place(relx=0.37, rely=0.005)
        #加载图片按钮
        #loadbut_former = tk.Button(self.tab_defect, text="上一张", width = 12,bg = 'white',fg = 'blue',font = 'Symbol')
        #loadbut_former.place(relx = 0.49 , rely = 0.9)
        contrast_but = tk.Button(self.tab_defect, text="进行对比", width = 28,bg = 'white',fg = 'blue',font = 'Symbol',command = self.contrast)
        contrast_but.place(relx = 0.52 , rely = 0.9)

        label = tk.Label(self.tab_defect,text = '缺陷信息',fg = 'blue',font = 'Symbol 12')
        label.place(relx = 0.1,rely = 0.03)
        self.defect_info_st = scrolledtext.ScrolledText(self.tab_defect,width = 35 , height = 15,wrap=tk.WORD)
        self.defect_info_st.place(relx = 0.02 , rely = 0.10 )
        write_but = tk.Button(self.tab_defect, text="保存缺陷信息", width = 12,bg = 'white',fg = 'blue',font = 'Symbol',command = self.write_defect_log)
        write_but.place(relx = 0.06 , rely = 0.65)

    #  设置默认的输入输出路径
    def defaultFileEntries(self):
        self.fileEntry.delete(0, tk.END)
        self.fileEntry.insert(0, 'D:/Defect Detection')
        self.dstEntry.delete(0, tk.END)
        self.dstEntry.insert(0, 'D:/Defect Detection/dst_directory')
        self.snapPathEntry.delete(0, tk.END)
        self.snapPathEntry.insert(0, 'D:/Defect Detection')

    def start(self):
        pass
    #退出程序
    def quit(self):
        self.win.quit()
        self.win.destroy()
        exit()
################### 第 1 页 用到方法################################################
    #更新视频
    def update(self):
        ret,frame = self.vid.get_frame()
        if ret != 2:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0,0,image = self.photo,anchor = tk.NW)
            self.win.after(self.delay,self.update)
        if ret == 2:
            self.photo = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(frame))
            self.canvas.create_image(0, 0, image=self.photo, anchor=tk.NW)
    # 用于1次拍照
    def creat_thread0(self):
        runT = Thread(target=self.snapshot)
        runT.setDaemon(True)
        runT.start()
    # 用于多次拍照
    def auto_take_pic_thread(self):
        runT = Thread(target=self.auto_take_pic)
        runT.setDaemon(True)
        runT.start()
    #用于读取log
    '''
    def read_log_thread(self):
        runT = Thread(target=self.read_log)
        runT.setDaemon(True)
        runT.start()
        
    '''
    def open_COM(self):
        self.COM = serial.Serial('COM1', 9600, bytesize=8, stopbits=1, parity='N', timeout=0.5)
    def take_photo_new_thread(self):
        runT = Thread(target=self.take_photo_new)
        runT.setDaemon(True)
        runT.start()
    def update_thread(self):
        runT = Thread(target=self.update)
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


    #获取单张照片 并 记录照片时间 和 数量
    def create_folder(self,folder_time,flag =0): #每次拍摄都创建一个文件夹用于保存图片
        folder_path_head = self.snapPathEntry.get()
        self.snapshot_folder_path = folder_path_head +'/'+ folder_time # 文件夹用时间来命名
        if flag ==0:
            makedirs(self.snapshot_folder_path)

    def snapshot(self):
       # 拍摄一张图片
        snap_path_head = self.snapshot_folder_path
        self.pic_sum += 1 # 记录总计拍照次数
        current_position = self.get_platform_position()
        current_state = self.get_platform_state()
        if self.COM is not None:
            if current_position > 160 and current_position < 2401: #and self.platform_state == '04':
                print('第' + str(self.timer_times_count) + '次拍照')
                ret,frame = self.vid.get_frame()
                if ret:
                    pic_time = time.strftime("%d-%m-%Y-%H-%M-%S")
                    #group_flag = self.pic_group_flag
                    #pic_flag = self.pic_group_flag_pic_flag
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
                # group_flag = self.pic_group_flag
                # pic_flag = self.pic_group_flag_pic_flag
                snap_path = snap_path_head + '/' + 'L' + str(current_position) + '-' + pic_time + ".jpg"
                print(snap_path)
                frame = cv.cvtColor(frame, cv.COLOR_RGB2BGR)
                cv.imwrite(snap_path, frame)

    # 自动拍照
    def auto_take_pic(self):
        self.timer_times_count += 1
        if self.COM != None:
            self.slow_move()
            time.sleep(0.1)
            if self.platform_position == 0:
                self.slow_move()
                time.sleep(0.1)
            print('开始拍照')
            self.get_pic()
        else:
            print('开始脱离平台拍照')
            self.get_pic_in_test_mode()
    def get_pic(self):
        shot_flag = True
        new = 0
        old = 0
        pic_delay = self.pic_delay.get()/1000.0# tk.IntVar 要加上 .get()
        folder_time = time.strftime("%d-%m-%Y-%H-%M-%S")
        self.create_folder(folder_time)

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
    def get_pic_in_test_mode(self):
        if self.COM is None:
            pic_delay = self.pic_delay.get() / 1000.0  # tk.IntVar 要加上 .get()
            folder_time = time.strftime("%d-%m-%Y-%H-%M-%S")
            self.create_folder(folder_time)
            for i in range(10):
                self.snapshot()
                time.sleep(pic_delay)
    def start_timer(self):
        self.timer_times_count = 0 # 每次启动计时器都是从0开始
        interval = self.timer_interval.get()  #从gui中得到两次拍照间隔时长
        interval = int(interval)*60  # 间隔分钟  小时则改为 3600
        print('interval = ',interval,'s')
        for times in range(self.timer_total_times.get()):
            self.auto_take_pic()
            print('第', times + 1, '次拍照结束，总共拍照 ',self.timer_total_times.get(),'次')
            if times < self.timer_total_times.get() - 1:
                time.sleep(interval)
        mBox.showinfo(title='拍照结束', message='拍照结束')
        '''
        print('第一次拍照前',time.time())
        self.auto_take_pic() #先拍一次 在开始
        print('第一次拍照后',time.time())
        if self.timer_total_times.get() != 1:
            schedule.every(interval).minutes.do(self.auto_take_pic)#self.auto_take_pic
            print('schedule.every(interval).minutes.do(self.auto_take_pic)#self.auto_take_pic',time.time())
            while True:
                schedule.run_pending()
                time.sleep(1)
                if self.timer_times_count == int(self.timer_total_times.get()):
                    print('self.timer_times_count',self.timer_times_count)
                    print('self.timer_total_times.get()',self.timer_total_times.get())
                    print('if self.timer_times_count == (int(self.timer_total_times.get()) - 1):',time.time())
                    break
                else:
                    print('else:',time.time())
                    break
        print('Timer is over',time.time())
'''
    # 根据 log 进行拍照 (舍弃)
    '''    
    def  take_photo_new(self):
        pic_infos = self.log_info
        #print(pic_infos)
        if len(pic_infos) == 6:#判断已经读取到run_log.txt
            #print('log_info_get')
            pic_info_mode = int(pic_infos[0]) # 记录点击的按钮
            self.pic_info_speed =int(pic_infos[1]) # 记录运行速度
            self.pic_info_init_position = int(pic_infos[2]) # 记录本次点击时的起始位置
            self.pic_info_final_position = int(pic_infos[3])#记录本次点击时的终止位置
            pic_info_light_flag = int(pic_infos[4]) #判断开灯状态
            self.pic_info_init_time = cv.getTickCount()
            
            pic_number = self.pic_number_each_group.get()  # tk.IntVar 要加上 .get()
            group_number = self.pic_group_num.get()
            pic_delay = self.pic_delay.get() / 1000.0

            if pic_info_mode == 1 or pic_info_mode == 3:#当连续运行和停止时可以拍照
                if pic_info_light_flag ==1 :#当灯光亮起是可以拍照
                    folder_time = time.strftime("%d-%m-%Y-%H-%M-%S")
                    self.create_folder(folder_time)
                    for g in range(group_number):
                        for i in range(pic_number):
                            self.snapshot_new()
                            self.pic_group_flag_pic_flag += 1
                        self.pic_group_flag += 1  # 拍完一组后将组号+1
                        self.pic_group_flag_pic_flag = 1  # 拍完一组后将组内图片号 置为1
                        time.sleep(pic_delay)
                    self.pic_group_flag = 1  # 拍完全部后将组号置1

    # 为 自动拍照写的 拍照方法
    def snapshot_new(self):
       # Get a frame from the video source
        snap_path_head = self.snapshot_folder_path
        self.pic_sum += 1 # 记录总计拍照次数
        frame = self.vid.get_frame()
        if frame is not False:
            pic_time = time.strftime("%d-%m-%Y-%H-%M-%S")
            group_flag = self.pic_group_flag
            pic_flag = self.pic_group_flag_pic_flag
            pic_info_current_time = (cv.getTickCount() -self.pic_info_init_time)/cv.getTickFrequency()
            pic_info_current_position = int(self.pic_info_init_position + self.pic_info_speed * pic_info_current_time)
            print(pic_info_current_position)
            snap_path = snap_path_head +'/'+ 'L'+str(self.platform_position)+'-'+ pic_time + ".jpg"
            print(snap_path)
            cv.imwrite(snap_path, frame)
'''
    # 打开平台驱动程序
    def start_motor_program(self):
        Obj = 'C:\Program Files (x86)\CompactConnect\CompactConnect.exe'
       # C:/Program Files(x86)/CompactConnect/CompactConnect.exe
        if Obj and path.exists(Obj):  # 文件or 目录存在
            if path.isfile(Obj):
                import win32process
                try:  # 打开外部可执行程序
                    win32process.CreateProcess(Obj, '', None, None, 0, win32process.CREATE_NO_WINDOW, None, None,
                                               win32process.STARTUPINFO())
                except FileNotFoundError:
                    print('FileNotFoundError')
            else:
                startfile(str(Obj))  # 打开目录
        else:  # 不存在的目录
            print('不存在的目录')
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
    #发送状态请求
    def receive_state(self):  # 发送函数
        if self.COM != None:
            while True:
                self.state_read_flag.wait()
                if self.COM.is_open:
                    myinput = bytes([0X01, 0X03, 0X00, 0X00, 0X00, 0X02, 0XC4, 0X0B])
                    # x.write("\X01\X03\X00\X00\X00\X02\XC4\X0B".encode('gbk'))
                    self.COM.write(myinput)
                    time.sleep(0.05)
            #读取状态
                while self.COM.inWaiting() > 0:
                    myout = self.COM.read(9)   # 读取串口传过来的字节流，接收 9 个字节的数据
                    datas = ''.join(map(lambda x: ('/x' if len(hex(x)) >= 4 else '/x0') + hex(x)[2:], myout))  # 将数据转成十六进制的形式
                    #print('datas:', datas)  #datas: /x01/x03/x04/x00/x00/x00/x76/x7b/xd5
                    new_datas = datas.split("/x")  # 将字符串分割，拼接下标4和5部分的数据
                    #print('newdatas', new_datas) #newdatas ['', '01', '03', '04', '00', '00', '00', '76', '7b', 'd5']
                    if len(new_datas) == 10:
                        self.platform_position = int(new_datas[4], 16) * 256 + int(new_datas[5], 16)
                        self.platform_state = new_datas[6]  # 0 停止 2 复位 4 连续运行 8 点动运行
                    time.sleep(0.05)  #防止读取后无法 发送
                #print(self.platform_position)
          #print(self.platform_state,self.platform_position)
    def get_platform_position(self):
        if self.COM != None:
            position = self.platform_position
        else:
            r = random.randint(1,9999)
            position = r
        return position
    def get_platform_state(self):
        if self.COM != None:
            state = self.platform_state
        else:
            state = 'Test'
        return state
    #平台复位
    def reset(self):
        if self.COM != None:
            #self.lock.acquire()
            self.state_read_flag.clear()
            if self.COM.is_open:
                myinput = bytes([0X01, 0X05, 0X00, 0X00, 0XFF, 0X00, 0X8C, 0X3A])
                # 这是我要发送的命令，原本命令是：01 03 00 00 00 01 84 0A
                # x.write("\X01\X03\X00\X00\X00\X02\XC4\X0B".encode('gbk'))
                self.COM.write(myinput)
                time.sleep(0.1)
            self.state_read_flag.set()
            # self.timer_times_count += 1  #用于测试timer
            #self.lock.release()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法复位')

    #平台缓慢移动
    def slow_move(self):
        if self.COM != None:
            self.lock.acquire()
            #self.state_read_flag.clear()
            if self.COM.is_open:
                myinput = bytes([0X01, 0X05, 0X00, 0X01, 0XFF, 0X00, 0XDD, 0XFA])
                self.COM.write(myinput)
                time.sleep(0.05)
            #self.state_read_flag.set()
            self.lock.release()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法移动平台')
    def click_move(self): #点动
        if self.COM != None:
            self.state_read_flag.clear()
            self.lock.acquire()

            pos_get = self.click_move_pos.get()
            print(pos_get)

            pos_high8 = int(pos_get / 256) + 128
            pos_low8 = int(pos_get) % 256
            # print('位置 pos_high8',pos_high8,'tpye pos_high8',type(pos_high8))
            # print('位置 pos_high8', pos_low8, 'tpye pos_low8', type(pos_low8))
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
            #print('校验和计算完成', 'parity_high_8 =', parity_high_8, '   type', type(parity_high_8))
            #print('校验和计算完成', 'parity_low_8 =', parity_low_8, '   type', type(parity_low_8))
            if self.COM.is_open:
                myinput= bytes([0X01, 0X06, 0X00, 0X02, pos_high8, pos_low8,parity_high_8 ,parity_low_8])
                #print(myinput)
                self.COM.write(myinput)
                time.sleep(0.1)
            self.lock.release()
            self.state_read_flag.set()
        else:
            mBox.showinfo(title='串口未连接', message='串口未连接，无法移动平台')
    def setSnapPath(self):
        fDir = path.dirname(__file__)  ## 获取文件所在文件夹路径
        self.dPath = fd.askdirectory(parent=self.win, initialdir='D:/Defect Detection')  # 设置截图保存路径
        # print(self.dPath)
        self.snapPathEntry.config(state='enabled')
        self.snapPathEntry.delete(0, tk.END)
        self.snapPathEntry.insert(0, self.dPath)
################### 第 2 页 用到方法################################################
    #获取 待处理图片 文件夹中文件的list 和 length

    def get_img_list(self):
        read_pic_add = self.fileEntry.get()
        #print('read_pic_add',read_pic_add)
        glob_add = read_pic_add + '/*.jpg'
        img_list = glob.glob(glob_add)
        #print(img_list)
        list_len = len(img_list)
        return img_list,list_len
    # 用于处理图片图片
    def creat_thread_process_pic(self):
        img_list, self.list_len = self.get_img_list()  # 获取待处理图片 list 与 Length 防止在没加载图片
        self.runThread = Thread(target=self.process_pic)

        self.runThread.setDaemon(True)
        self.runThread.start()
    # 间隔播放图片
    def put_img(self):
        img_list,self.list_len = self.get_img_list()
        img = cv.imread(img_list[self.pic_count])
        img_RGB = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.img_PIL =  PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(img_RGB))
        self.canvas2.create_image(0,0, image=self.img_PIL,anchor=tk.NW)
        if self.pic_count < self.list_len - 1:
            self.pic_count += 1
        else:
            self.pic_count = 0
        self.canvas2.after(1000,self.put_img)#间隔一秒加载下一张图片
    # 处理照片
    def process_pic(self):
        #1 get params
        img_list,list_len = self.get_img_list()
        br = int(self.value_Brightness.get())  # 获取亮度值
        thr_g_r = int(self.value_Threshold_constant.get())
        k = int(self.value_Convolution_kernel.get())
        the_cl = int(self.value_Lower_defect_area.get())
        msg_flag = 0
        #2 创建dst folder
        folder_time = time.strftime("%d-%m-%Y-%H-%M-%S")
        dst_folder_add = self.create_dst_folder(folder_time)
        self.dst_folder_add = dst_folder_add
        #3 get pic list and processing part
        for img_name  in img_list:
            #self.fName = img_name
            #print('img name in process ',img_name)
            source = cv.imread(img_name)
            t1 = cv.getTickCount()
            dstPic = self.process(source, br, thr_g_r, k, the_cl)  # 算法处理
            t2 = cv.getTickCount()
            t0 = (t2 - t1)/cv.getTickFrequency()
            #print('处理时长'+ str(t0))
            if self.flag == 1:# 当存在缺陷是 保存处理后的缺陷图片 并加入list 以备后续 对比时调用
                msg_flag = 1
                self.defect_src_list.append(img_name)


                self.savedstPic(dstPic,img_name,dst_folder_add)
        #4 处理过后 弹窗 和 显示 缺陷图片
        if msg_flag ==1:
            self.msgbox(self.flag)
            self.defect_count = 0
        self.put_defect_img(dst_folder_add)
        self.insert_info()

    # 获得 待处理图片 路径
    def getFileName(self):
        fDir = path.dirname(__file__)  ## 获取文件所在文件夹路径
        self.fName = fd.askdirectory(parent=self.win, initialdir=fDir) #获取图片路径
        self.fileEntry.config(state='enabled')
        self.fileEntry.delete(0, tk.END)
        self.fileEntry.insert(0, self.fName)
    #设置 输出图片 所在文件夹路径
    def setDstPath(self):
        fDir = path.dirname(__file__)  ## 获取文件所在文件夹路径
        self.dPath = fd.askdirectory(parent=self.win, initialdir='D:\Defect Detection\dst_directory') #设置输出路径
        #print(self.dPath)
        self.dstEntry.config(state='enabled')
        self.dstEntry.delete(0, tk.END)
        self.dstEntry.insert(0, self.dPath)

    def create_dst_folder(self,folder_time,flag =0): #每次拍摄都创建一个文件夹用于保存dst图片
        folder_path_head = self.dstEntry.get()
        dst_folder_path = folder_path_head +'/'+ folder_time # 文件夹用时间来命名
        if flag ==0:
            makedirs(dst_folder_path )
        return dst_folder_path

    #保存处理过的图片
    def savedstPic(self,pic,pic_name,dst_add_dir):
        print('fName replaced before', pic_name)
        pic_name = pic_name.replace('\\','/')
        fName_tail = pic_name.split('/')[-1] # 取得文件名最后 L-time.jpg
        print('fName repalced after',fName_tail)
        full_dst_name = dst_add_dir+'/'+fName_tail

        print('full_dst_name',full_dst_name)
        cv.imwrite(full_dst_name,pic)
        #print(full_dst_name)
    #设置识别结果弹窗
    def msgbox(self,flag):
        if flag == 1:
            messages = '在 '+str(self.list_len)+ '张照片中共识别出 ' + str(self.defect_count) + ' 处缺陷'
            mBox.showinfo(title = '识别结果', message = messages)
        else:
            messages = '未发现缺陷 '
            mBox.showinfo(title ='识别结果', message = messages)



################### 第 3 页 用到方法################################################
    # 获取 处理后图片 文件夹中文件的list 和 length
    def get_defect_img_list(self,dst_folder_add):
        read_pic_add = dst_folder_add

        glob_add = read_pic_add + '/*.jpg'
        defect_list = glob.glob(glob_add)
        list_len = len(defect_list)
        return defect_list,list_len
    # 循环播放处理后的图片

    def put_defect_img(self,dst_folder_add):
        defect_img_list,defect_list_len = self.get_defect_img_list(dst_folder_add)
        img = cv.imread(defect_img_list[self.defect_pic_count])
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.defect_PIL =  PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(img_rgb))
        self.canvas3.create_image(0,0, image=self.defect_PIL,anchor=tk.NW)
        if self.defect_pic_count < defect_list_len - 1:
            self.defect_pic_count += 1
        else:
            self.defect_pic_count = 0
        #self.canvas3.after(2000,self.put_defect_img(dst_folder_add))



    def insert_info(self):
        for info in self.defect_info_list:
            self.defect_info_st.insert(END,info)
    def write_defect_log(self):
        with open('defect info.txt','w') as f_obj:
            for info in self.defect_info_list:
                f_obj.write(info)
    def contrast(self):
        self.contrast_win = tk.Toplevel(self.win)
        self.contrast_win.title('对比')
        self.contrast_win.geometry('1320x640')
        self.contrast_win.resizable(0, 0)

        self.canvas_src= tk.Canvas(self.contrast_win, width=640, height=480, bg='grey')
        self.canvas_src.place(relx=0.005, rely=0.08)

        self.canvas_dst= tk.Canvas(self.contrast_win, width=640, height=480, bg='grey')
        self.canvas_dst.place(relx=0.505, rely=0.08)

        last_but = tk.Button(self.contrast_win, text="上一张", width=12, bg='white', fg='blue', font='Symbol',
                              command=self.paging_last)
        last_but.place(relx=0.35, rely=0.9)

        next_but = tk.Button(self.contrast_win, text="下一张", width=12, bg='white', fg='blue', font='Symbol',
                              command=self.paging_next)
        next_but.place(relx=0.55, rely=0.9)
        self.dst_set()
        self.src_set()
        # 放置src
    def src_set(self):
        if self.defect_src_list:
            src = cv.imread(self.defect_src_list[self.pic_seq])
            src_rgb = cv.cvtColor(src, cv.COLOR_BGR2RGB)
            global src_PIL
            src_PIL = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(src_rgb))#image 需为全局变量
            self.canvas_src.create_image(0, 0, image=src_PIL, anchor=tk.NW)
        # 放置dst
    def dst_set(self):
        defect_img_list, defect_list_len = self.get_defect_img_list(self.dst_folder_add)
        dst = cv.imread(defect_img_list[self.pic_seq])
        dst_rgb = cv.cvtColor(dst, cv.COLOR_BGR2RGB)
        global dst_PIL
        dst_PIL = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(dst_rgb))
        self.canvas_dst.create_image(0, 0, image=dst_PIL, anchor=tk.NW)
    # 缺陷照片翻页 下一页
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
        self.flag = 0 #缺陷标记 每次处理时都先将缺陷标记置零
        #  比卷积均值大 thr_g_r 则置为255
        gamma = cv.cvtColor(source, cv.COLOR_BGR2GRAY)
        rows = source.shape[0]
        cols = source.shape[1]
        br += 30
        #增强图像对比度
        for i in range(rows):
            for j in range(cols):
                power = br* pow(gamma.item(i,j),0.2)##获取像素点 并 乘方
                gamma.itemset((i,j),power)### 设置像素点
                #gamma[i][j] = br * pow(gamma[i][j], 0.2) # 老方法
        #自适应阈值 进行二值化 thr_g_r 常数项 当 像素点比 平均值 大 thr_g_r 时 置为 255
        bi = cv.adaptiveThreshold(gamma, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY_INV, 25, thr_g_r)
        # 对二值化后图像进行形态学操作
        bi_1 = self.xingtai_demo(bi, k)
        # 轮廓发现
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
            if index < 1.75: # 紧凑性系数 越接近圆形 越视为缺陷
                self.flag = 1
            # 在原图上标记缺陷位置
            if self.flag == 1:
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
        return source

app = App(tk.Tk(), "胶辊表面缺陷识别")


