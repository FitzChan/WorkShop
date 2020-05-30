#!/usr/bin/python
# -*- coding: UTF-8 -*-
# 1 读取摄像头函数
# 2 COM函数
# 3

import numpy as np
import cv2 as cv
import tkinter as tk
import PIL.Image, PIL.ImageTk
from tkinter import *
from tkinter import ttk ,scrolledtext,filedialog as fd,messagebox as mBox
import time
import glob
from os import path,makedirs,startfile,getcwd
from queue import Queue

class MyVideoCapture:  ## 读取视频 及 其高宽
    def __init__(self, canvas_width,canvas_height,video_source= 0,):
        # Open the video source
        self.vid = cv.VideoCapture(video_source,cv.CAP_DSHOW)
        self.vid.set(3, 2592)
        self.vid.set(4, 2048)
        '''if not self.vid.isOpened():
            raise ValueError("Unable to open video source", video_source)'''
        # Get video source width and height
        self.width =  canvas_width
        self.height = canvas_height
        # Release the video source when the object is destroyed
    def __del__(self):
        if self.vid.isOpened():
            self.vid.release()

    def get_frame(self):
        if self.vid.isOpened():
            ret, frame = self.vid.read()
            frame = cv.resize(frame, (self.width, self.height),interpolation=cv.INTER_NEAREST)# 采用最快的临近点差值
            if ret:
                 frame = cv.flip(frame, 1)
                 return (ret, cv.cvtColor(frame, cv.COLOR_BGR2RGB))

            else:
                 return (ret, None)
        else:
             ret = 2
             bg_img = cv.imread('D:/Defect Detection/BGimg.jpg')
             return (ret,bg_img)

class WidFun:
    def __init__(self):
        self.defect_count = 0# 缺陷计数
        self.defect_pic_count = 0## 循环播放缺陷图片用初始0
        self.defect_flag = 0
        self.defect_info_list =[]#用于存放带有缺陷信息str的list
        self.defect_src_list = []#用于存放带有缺陷的原图地址的list
        self.defect_dst_list = []#用于存放带有缺陷的dst地址的list
        self.pic_seq = 0
    #  设置默认的输入输出路径
    def defaultFileEntries(self,fileEntry,dstEntry,snapPathEntry):
        fileEntry.delete(0, tk.END)
        fileEntry.insert(0, 'D:/Defect Detection')
        dstEntry.delete(0, tk.END)
        dstEntry.insert(0, 'D:/Defect Detection/dst_directory')
        snapPathEntry.delete(0, tk.END)
        snapPathEntry.insert(0, 'D:/Defect Detection')


################### 第 1 页 用到方法################################################


    def create_folder(self,folder_time,folder_path,flag =0): #每次拍摄都创建一个文件夹用于保存图片####################
        folder_path_head = folder_path
        snapshot_folder_path = folder_path_head +'/'+ folder_time # 文件夹用时间来命名
        if flag ==0:
            makedirs(snapshot_folder_path)
        return snapshot_folder_path

    # 打开平台驱动程序  ######################################
    def start_infrared_program(self):
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

################### 第 2 页 用到方法################################################
    #获取 待处理图片 文件夹中文件的list 和 length

    def get_img_list(self,fileEntry):#!!!!!!!!!!!!!!!!1

        read_pic_add = str(fileEntry)
        print('read_pic_add',read_pic_add)
        glob_add = read_pic_add + '/*.jpg'#把addres 结尾是
        img_list = glob.glob(glob_add)
        #print(img_list)
        self.list_len = len(img_list)
        print('read list = ',img_list)
        return img_list,self.list_len

    # 处理照片
    def process_pic(self,value_Brightness,value_Threshold_constant,value_Convolution_kernel,value_Lower_defect_area,info_st,fileEntry,dstEntry,queue):
        #1 get params
        #queue = Queue()
        img_list,list_len = self.get_img_list(fileEntry=fileEntry)
        br = int(value_Brightness.get())  # 获取亮度值
        thr_g_r = int(value_Threshold_constant.get())
        k = int(value_Convolution_kernel.get())
        the_cl = int(value_Lower_defect_area.get())
        msg_flag = 0
        #2 创建dst folder
        folder_time = time.strftime("%d-%m-%Y-%H-%M-%S")
        dst_folder_add = self.create_dst_folder(dstEntry.get(),folder_time)
        self.dst_folder_address = dst_folder_add

        #3 get pic list and processing part
        for img_name  in img_list:
            #print('img name in process ',img_name)
            source = cv.imread(img_name)
            t1 = cv.getTickCount()
            dstPic = self.process(source, br, thr_g_r, k, the_cl)  # 算法处理

            t2 = cv.getTickCount()
            t0 = (t2 - t1)/cv.getTickFrequency()
            #print('处理时长'+ str(t0))
            if self.defect_flag == 1:# 当存在缺陷时 保存处理后的缺陷图片 并加入list 以备后续 对比时调用
                msg_flag = 1
                self.defect_src_list.append(img_name)
                self.savedstPic(dstPic,img_name,dst_folder_add)
        #4 处理过后 弹窗 和 显示 缺陷图片
        if msg_flag ==1:
            self.msgbox(self.defect_flag)
            self.defect_count = 0
        #self.put_defect_img(canvas,dst_folder_add)
        self.insert_info(info_st= info_st)
        return_list = [dst_folder_add, self.defect_src_list,self.defect_dst_list]
        queue.put(return_list)
    def put_defect_img(self,canvas,dst_folder_add):
        defect_img_list,defect_list_len = self.get_defect_img_list(dst_folder_add)
        img = cv.imread(defect_img_list[self.defect_pic_count])
        print('defect_img_list', defect_img_list)
        img_rgb = cv.cvtColor(img, cv.COLOR_BGR2RGB)
        self.defect_PIL =  PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(img_rgb))
        canvas.create_image(0,0, image=self.defect_PIL,anchor=tk.NW)
        if self.defect_pic_count < defect_list_len - 1:
            self.defect_pic_count += 1
        else:
            self.defect_pic_count = 0
        #self.canvas3.after(2000,self.put_defect_img(dst_folder_add))
    # 获得 待处理图片 路径d
    def getFileName(self,fileEntry,win):
        fDir = path.dirname(__file__)  ## 获取文件所在文件夹路径
        fName = fd.askdirectory(parent=win, initialdir=fDir) #获取图片路径
        fileEntry.config(state='enabled')
        fileEntry.delete(0, tk.END)
        fileEntry.insert(0, fName)
    #设置 输出图片 所在文件夹路径
    def setDstPath(self,dstEntry,win):
        fDir = path.dirname(__file__)  ## 获取文件所在文件夹路径
        dPath = fd.askdirectory(parent=win, initialdir='D:\Defect Detection\dst_directory') #设置输出路径
        #print(dPath)
        dstEntry.config(state='enabled')
        dstEntry.delete(0, tk.END)
        dstEntry.insert(0,dPath)

    def create_dst_folder(self,folder_path,folder_time,flag =0): #每次拍摄都创建一个文件夹用于保存dst图片
        #folder_path_head = self.dstEntry.get()
        folder_path_head =folder_path
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
        self.defect_dst_list.append(full_dst_name) # 将 缺陷识别 dst 放入 self.defect_dst_list 以备 queue.put
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
        defect_imgs_list = glob.glob(glob_add)
        list_len = len(defect_imgs_list)
        return defect_imgs_list,list_len
    def insert_info(self,info_st):
        for info in self.defect_info_list:
            info_st.insert(END,info)
    def write_defect_log(self):
        with open('defect info.txt','w') as f_obj:
            for info in self.defect_info_list:
                f_obj.write(info)

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
        return source

if __name__ == "__main__":
    pass



