import numpy as np
import cv2 as cv
import matplotlib.pyplot as plt

#source = cv.imread('D:/crack.bmp')
source = cv.imread('D:/crack3.jpg')
#source = cv.resize(source,(576,432),interpolation=cv.INTER_AREA)
print(source.shape)
img = cv.imread('D:/crack3.jpg',0)

#img1 = np.power(img/float(np.max(img)), 0.3)
#cv.imshow('gamma_test',img1)
#cv.waitKey(0)
# 先画出原图的分布直方图

# 1 平滑实验

# 2 锐化实验

# 3 特征分类实验

# 形态学操作
class Detect:
    def __init__(self):
        self.defect_count = 0  # 缺陷计数
        self.defect_src_list = [] # 存在缺陷的原图
        self.defect_dst_list = []# 存在缺陷的dst图
        self.defect_info_list=[]


    def xingtai_demo(self,img, k):
        kernel_1 = np.ones((k, k), np.uint8)
        kernel_2 = np.ones((2, 2), np.uint8)
        kernel_3 = np.ones((10, 10), np.uint8)
        img_1 = cv.erode(img, kernel_2)
        dst = cv.morphologyEx(img_1, cv.MORPH_CLOSE, kernel_1)  # 闭操作 填充小的黑色区域
        src = cv.dilate(dst, kernel_3)
        return src


    def cal_hist(self,img):

        hist = cv.calcHist([img], [0], None, [256], [0, 256])
        plt.plot(hist,color = 'b')
        plt.show()

    def equalize_hist(self,img):
        equalize_hist = cv.equalizeHist(img)
        hist = cv.calcHist([equalize_hist], [0], None, [256], [0, 256])
        plt.plot(hist, color='b')
        plt.show()
        cv.imshow('equal',equalize_hist)
        cv.waitKey(0)
        cv.destroyAllWindows()



    def replaceZeroes(self,data):#用将图相中像素值为0的替换为非0的最小值
        min_nonzero = min(data[np.nonzero(data)])
        data[data == 0] = min_nonzero
        return data

    def SSR(self,src_img, sigma):#单尺度

        L_blur = cv.GaussianBlur(src_img, (0, 0), sigma)  # 对src进行高斯模糊
        img = self.replaceZeroes(src_img)
        L_blur = self.replaceZeroes(L_blur)

        #dst_Img = cv.log(img / 255.0) #对数变换
        dst_Img = cv.log(img )  # 对数变换 gai
        #dst_Lblur = cv.log(L_blur / 255.0)
        dst_Lblur = cv.log(L_blur)#gai
        #dst_IxL = cv.multiply(dst_Img, dst_Lblur)
        log_R = cv.subtract(dst_Img, dst_Lblur)

        dst_R = cv.normalize(log_R, None, 0, 255, cv.NORM_MINMAX)
        log_uint8 = cv.convertScaleAbs(dst_R)
        self.cal_hist(log_uint8)
        self.equalize_hist(log_uint8)
        cv.imshow("SSR",log_uint8)
        cv.waitKey(0)
        cv.destroyAllWindows()

    def MSR(self,img, scales): #scales = [15,101,301]
        weight = 1 / 3.0
        scales_size = len(scales)
        h, w = img.shape[:2]
        log_R = np.zeros((h, w), dtype=np.float32)
        #doubleI = img.convertTo(cv.CV_32FC3, 1.0, 1.0)

        for i in range(scales_size):
            img = self.replaceZeroes(img)
            L_blur = cv.GaussianBlur(img, (scales[i], scales[i]), 0)
            L_blur = self.replaceZeroes(L_blur)
            dst_Img = cv.log(img / 255.0)
            dst_Lblur = cv.log(L_blur / 255.0)
            dst_Ixl = cv.multiply(dst_Img, dst_Lblur)
            log_R += weight * cv.subtract(dst_Img, dst_Ixl)

        dst_R = cv.normalize(log_R, None, 0, 255, cv.NORM_MINMAX)
        log_uint8 = cv.convertScaleAbs(dst_R)
        cv.imshow("MSR", log_uint8)
        cv.waitKey(0)
        cv.destroyAllWindows()
        self.cal_hist(log_uint8)
        self.equalize_hist(log_uint8)


    def Lap_enhance(self,img):

        kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]])  # 定义卷积核
        imageEnhance = cv.filter2D(img, -1, kernel)  # 进行卷积运算
        cv.imshow('output', imageEnhance)

        cv.waitKey(0)  # 保持图像

#处理后，亮度br=20，灰度阈值上升thr_g_r=10,卷积核大小k=3,瑕疵值the_cl=100
detect = Detect()
#detect.cal_hist(img)# 计算原始图像hist
#detect.equalize_hist(img)#直方图均衡化
#detect.Lap_enhance(img)
scales = [15,101,301]
detect.MSR(img,scales)
#detect.roi(img)#测试裂纹区域ROI
#br, thr_g_r, k, the_cl)
#detect.process(source,20,10,3,50)
