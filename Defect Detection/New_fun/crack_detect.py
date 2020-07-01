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


    def process(self, source, br, thr_g_r, k, the_cl):
        self.defect_flag = 0  # 缺陷标记 每次处理时都先将缺陷标记置零
        #  比卷积均值大 thr_g_r 则置为255
        gamma = cv.cvtColor(source, cv.COLOR_BGR2GRAY)
        cv.imshow('RGB2GRAY',gamma)
        #gamma = self.adjust_gamma(gamma)
        #cv.imshow('gamma_adjust',gamma)
        gamma = cv.medianBlur(gamma,3)
        #gamma = cv.bilateralFilter(gamma,3,50,50)
        cv.imshow('blur',gamma)
        rows = source.shape[0]
        cols = source.shape[1]
        br += 30
        # 增强图像对比度
        print(type(gamma))
        gamma = cv.equalizeHist(gamma)
        cv.imshow('equal',gamma)
        #laplace = cv.Laplacian(gamma, cv.CV_8U, ksize=3)
        #cv.imshow('laplace', laplace)
        #scharr_x = cv.Scharr(gamma, cv.CV_8U, 1, 0)
        #cv.imshow('scharr_x', scharr_x)
        copy_gamma = gamma.copy()
        for i in range(rows):  # gamma矫正
            for j in range(cols):
                power = br * pow(gamma.item(i, j), 0.3)  ##获取像素点 并 乘方
                gamma.itemset((i, j), power)  ### 设置像素点
                # gamma[i][j] = br * pow(gamma[i][j], 0.2) # 老方法
        # 自适应阈值 进行二值化 thr_g_r 常数项 当 像素点比 平均值 大 thr_g_r 时 置为 255
        cv.imshow('gamma_add',gamma)
        #copy_gamma = np.power(img/float(np.max(copy_gamma)), 0.3)
        #cv.imshow('gamma_addcopy',copy_gamma)
        bi = cv.adaptiveThreshold(gamma, 255, cv.ADAPTIVE_THRESH_MEAN_C, cv.THRESH_BINARY_INV, 25, thr_g_r)
        #cv.imshow('bi',bi)
        # 对二值化后图像进行形态学操作
        bi_1 = self.xingtai_demo(bi, k)
       # cv.imshow('xintai',bi_1)
        # 轮廓发现 仅支持二值图像
        # ret,contours, hierarchy = cv.findContours(bi_1, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)  # opencv3 将ret 去掉
        #contours, hierarchy = cv.findContours(bi_1, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)  # opencv4 将ret 去掉
        contours, hierarchy = cv.findContours(bi, cv.RETR_EXTERNAL, cv.CHAIN_APPROX_SIMPLE)  # opencv4 将ret 去掉

        # 遍历所有轮廓
        defect_count_local = 0
        for i, contour in enumerate(contours):
            area = cv.contourArea(contour)
            para = cv.arcLength(contour, True)
            # 识别缺陷 缺陷面积下限 （轮廓面积小于该值则忽略）
            if area < the_cl or area > 1000:
                continue
            # print('flaw area', area)
            index = float(para * para / (4 * area * np.pi))
            index = round(index, 4)  # 保留4位小数
            area = round(area, 4)  # 保留4位小数
            xc, yc, wc, hc = cv.boundingRect(contour)
            ratio_hw = hc / wc
            if index < 1.2 and ratio_hw < 5:  # 紧凑性系数 越接近圆形 越视为缺陷
                self.defect_flag = 1  # 圆形异物缺陷缺陷
            if ratio_hw > 5 and index > 1.75:  # 高宽比，大于5越大则狭长
                self.defect_flag = 2
            # 在原图上标记缺陷位置
            if self.defect_flag == 1:
                self.defect_count += 1
                defect_count_local += 1
                defect_info_fo = '异物缺陷' + str(self.defect_count) + '\t紧凑系数：' + str(index) + '\n'
                defect_info_fo += '\t缺陷面积：' + str(area) + '\n'
                # print(defect_info)
                self.defect_info_list.append(defect_info_fo)
                x, y, w, h = cv.boundingRect(contour)
                if self.defect_flag == 1:
                    cv.rectangle(source, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    moments = cv.moments(contour)
                    if moments['m00']:
                        cx = moments['m10'] / moments['m00']
                        cy = moments['m01'] / moments['m00']
                    else:
                        continue
                    cv.circle(source, (np.int(cx), np.int(cy)), 4, (0, 0, 255), 1)
            elif self.defect_flag == 2:
                cv.rectangle(source, (xc, yc), (xc + wc, yc + hc), (0, 255, 0), 2)
                defect_info_crack = '裂纹缺陷' + str(self.defect_count) + '\t长宽比：' + str(ratio_hw) + '\n'
                defect_info_crack += '\t裂纹缺陷长度：' + str(hc)
                defect_info_crack += '\t裂纹缺陷宽度：' + str(wc) + '\n'
                # print(defect_info)
                self.defect_info_list.append(defect_info_crack)

            else:
                defect_info = '未能检测出缺陷'
        for info in self.defect_info_list:
            print(info)
        cv.imshow('dst',source)
        cv.waitKey(0)
        cv.destroyAllWindows()
        return source
    def roi(self,srcImg):
        roiImg = srcImg[20:120, 170:270]
        cv.imshow('roi',roiImg)
        cv.waitKey(0)
        cv.destroyAllWindows()

    def replaceZeroes(self,data):#用将图相中像素值为0的替换为非0的最小值
        min_nonzero = min(data[np.nonzero(data)])
        data[data == 0] = min_nonzero
        return data

    def SSR(self,src_img, size):#单尺度
        #L_blur = cv.GaussianBlur(src_img, (size, size), 0) #对src进行高斯模糊
        L_blur = cv.GaussianBlur(src_img, (0, 0), size)  # 对src进行高斯模糊
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
