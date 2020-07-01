import numpy as np
import cv2
import time
import matplotlib.pyplot as plt
import math

# https://blog.csdn.net/ajianyingxiaoqinghan/article/details/71435098 retinex 理论
img = cv2.imread('D:/crack3.jpg',0)
config = {'sigma_list':[15, 80, 200],'G' : 5.0,'b': 25.0,'alpha': 125.0,'beta':46.0,'low_clip':0.01,'high_clip':0.99}
cv2.imshow('src',img)
def cal_hist(img):
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    plt.plot(hist, color='b')
    plt.show()
#cal_hist(img)


def equalize_hist(img):
    equalize_hist = cv2.equalizeHist(img)
    hist = cv2.calcHist([equalize_hist], [0], None, [256], [0, 256])
    plt.plot(hist, color='b')
    plt.show()
    cv2.imshow('equal', equalize_hist)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    return equalize_hist


def gamma(img,gamma):
    gamma_dst = img.copy()
    rows = img.shape[0]
    cols = img.shape[1]
    invGamma = 1.0 / gamma
    pixel_max = np.max(img)
    pixel_min = np.min(img)
    table = np.array([((i / (pixel_max - pixel_min)) ** invGamma) * 255 for i in np.arange(0, 256)]).astype("uint8") #gamma 映射表
    for i in range(rows):  # gamma矫正
        for j in range(cols):
            power =(pixel_max - pixel_min) * pow(img.item(i, j)/(pixel_max - pixel_min), invGamma)  ##获取像素点 并 乘方
            gamma_dst.itemset((i, j), power)  ### 设置像素点
    cv2.imshow('gamma_adjust',gamma_dst)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cal_hist(gamma_dst)
# mean = np.mean(img)
# gamma_val = math.log10(0.5)/math.log10(mean/255)
# print(gamma_val)
#gamma(img,0.5)
def gamma2(img,gamma):
    gamma_table = [np.power(x / 255.0, gamma) * 255.0 for x in range(256)]  # 建立映射表
    gamma_table = np.round(np.array(gamma_table)).astype(np.uint8)  # 颜色值为整数
    gamma_dst =  cv2.LUT(img, gamma_table)
    cv2.imshow('gamma_adjust',gamma_dst)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
    cal_hist(gamma_dst)
    return  gamma_dst
#gama_dst = gamma2(img,1.4)


def retinex_2_gray(retinex_img):
    retinex_img_int8 = np.uint8(retinex_img)
    retinex_img_gray = cv2.cvtColor(retinex_img_int8,cv2.COLOR_BGR2GRAY)
    return  retinex_img_gray
def retinex_show(retinex_img_gray,window_name):
    cv2.imshow(window_name,retinex_img_gray)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def singleScaleRetinex(img, sigma):
    retinex = np.log10(img) - np.log10(cv2.GaussianBlur(img, (0, 0), sigma))
    print(retinex.dtype)
    print(retinex.shape)
    print(retinex[110,110])
    return retinex

def multiScaleRetinex(img, sigma_list):#'sigma_list':[15, 80, 200] 改变的是高斯模糊里的sigma
    retinex = np.zeros_like(img)  #创建全零形状与原图相同的矩阵
    for sigma in sigma_list:#对每个高斯sigam值进行SSR，再进行叠加
        retinex += singleScaleRetinex(img, sigma)

    retinex = retinex / len(sigma_list)#叠加后除以sigma个数
    #print(retinex.dtype)
    #img_retinex = np.uint8(retinex)
    #retinex = cv2.cvtColor(retinex,cv2.COLOR_BGR2BGRA)
    return retinex

# 在前面的增强过程中，图像可能会因为增加了噪声，而使得图像的局部细节色彩失真，不能显现出物体的真正颜色，整体视觉效果变差。
# 针对这一点不足，MSRCR在MSR的基础上，加入了色彩恢复因子C来调节由于图像局部区域对比度增强而导致颜色失真的缺陷。
#对多尺度MSR结果做了色彩平衡，归一化，增益和偏差线性加权

def colorRestoration(img, alpha, beta):#beta 增益常数 alpha 受控制的非线性强度
    img_sum = np.sum(img, axis=2, keepdims=True)

    color_restoration = beta * (np.log10(alpha * img) - np.log10(img_sum))

    return color_restoration


def simplestColorBalance(img, low_clip, high_clip):
    total = img.shape[0] * img.shape[1]
    for i in range(img.shape[2]):
        unique, counts = np.unique(img[:, :, i], return_counts=True)
        current = 0
        for u, c in zip(unique, counts):
            if float(current) / total < low_clip:
                low_val = u
            if float(current) / total < high_clip:
                high_val = u
            current += c

        img[:, :, i] = np.maximum(np.minimum(img[:, :, i], high_val), low_val)

    return img

# {'sigma_list':[15, 80, 200],'G' : 5.0,'b': 25.0,'alpha': 125.0,'beta':46.0,'low_clip':0.01,'high_clip':0.99}
def MSRCR(img, sigma_list, G, b, alpha, beta, low_clip, high_clip):#带颜色恢复的MSR方法
    img = np.float64(img) + 1.0

    img_retinex = multiScaleRetinex(img, sigma_list)

    img_color = colorRestoration(img, alpha, beta)
    img_msrcr = G * (img_retinex * img_color + b)

    for i in range(img_msrcr.shape[2]):
        img_msrcr[:, :, i] = (img_msrcr[:, :, i] - np.min(img_msrcr[:, :, i])) / \
                             (np.max(img_msrcr[:, :, i]) - np.min(img_msrcr[:, :, i])) * \
                             255

    img_msrcr = np.uint8(np.minimum(np.maximum(img_msrcr, 0), 255))
    img_msrcr = simplestColorBalance(img_msrcr, low_clip, high_clip)

    return img_msrcr


def automatedMSRCR(img, sigma_list):
    img = np.float64(img) + 1.0

    img_retinex = multiScaleRetinex(img, sigma_list)

    for i in range(img_retinex.shape[2]):#对每个通道进行循环
        unique, count = np.unique(np.int32(img_retinex[:, :, i] * 100), return_counts=True) #返回不带重复值的数组，返回的新矩阵对应于原矩阵中元素在原矩阵中相应的出现次数。
        for u, c in zip(unique, count):
            if u == 0:  #判断 0 出现的次数
                zero_count = c
                break


        low_val = unique[0] / 100.0#最小值 low val -0.44    -0.91   -1.38
        print('low val',low_val)
        high_val = unique[-1] / 100.0#最大值 high val 0.12  0.15   0.21
        print('high val',high_val)
        for u, c in zip(unique, count):
            if u < 0 and c < zero_count * 0.1:
                low_val = u / 100.0
            if u > 0 and c < zero_count * 0.1:
                high_val = u / 100.0
                break

        img_retinex[:, :, i] = np.maximum(np.minimum(img_retinex[:, :, i], high_val), low_val)

        img_retinex[:, :, i] = (img_retinex[:, :, i] - np.min(img_retinex[:, :, i])) / \
                               (np.max(img_retinex[:, :, i]) - np.min(img_retinex[:, :, i])) \
                               * 255

    img_retinex = np.uint8(img_retinex)
    print('aMSRCR dtype',img_retinex.dtype)
    gray_img_retinex = cv2.cvtColor(img_retinex,cv2.COLOR_BGR2GRAY)
    return gray_img_retinex


def MSRCP(img, sigma_list, low_clip, high_clip):
    img = np.float64(img) + 1.0

    intensity = np.sum(img, axis=2) / img.shape[2]

    retinex = multiScaleRetinex(intensity, sigma_list)

    intensity = np.expand_dims(intensity, 2)
    retinex = np.expand_dims(retinex, 2)

    intensity1 = simplestColorBalance(retinex, low_clip, high_clip)

    intensity1 = (intensity1 - np.min(intensity1)) / \
                 (np.max(intensity1) - np.min(intensity1)) * \
                 255.0 + 1.0

    img_msrcp = np.zeros_like(img)

    for y in range(img_msrcp.shape[0]):
        for x in range(img_msrcp.shape[1]):
            B = np.max(img[y, x])
            A = np.minimum(256.0 / B, intensity1[y, x, 0] / intensity[y, x, 0])
            img_msrcp[y, x, 0] = A * img[y, x, 0]
            img_msrcp[y, x, 1] = A * img[y, x, 1]
            img_msrcp[y, x, 2] = A * img[y, x, 2]

    img_msrcp = np.uint8(img_msrcp - 1.0)

    return img_msrcp


def custom_lapalian_demo(img):
    #kernel = np.array([[0,1,0],[1,-4,1],[0,1,0]])  #拉普拉斯算子默认为 4 领域算子
    kernel = np.array([[1,1,1],[1,-8,1],[1,1,1]])   #拉普拉斯 8领域算子
    dst = cv2.filter2D(img,cv2.CV_32F,kernel=kernel)
    lpls = cv2.convertScaleAbs(dst)# 转回uint8
    cv2.imshow('custom lapalian',lpls)
    return lpls
def high_up_filter(img,kernel=3,k=1):
    blur = cv2.GaussianBlur(img,(kernel,kernel),-1)
    gmask = cv2.subtract(img,blur)
    dst = cv2.add(img,k*gmask)
    return dst
#lpls = custom_lapalian_demo(gama_dst)
#cal_hist(lpls)
highup = high_up_filter(img,3,3)
cv2.imshow('high up',highup)
cv2.waitKey(0)
cv2.destroyAllWindows()
lpls = custom_lapalian_demo(highup)
# cal_hist(lpls)

# hist = equalize_hist(img)
# lpls = custom_lapalian_demo(hist)


# print('msrcr processing......')
# img_msrcr = MSRCR(
#     img,
#     config['sigma_list'],
#     config['G'],
#     config['b'],
#     config['alpha'],
#     config['beta'],
#     config['low_clip'],
#     config['high_clip']
# )
# cv2.imshow('MSRCR retinex', img_msrcr)
# cv2.imwrite("MSRCR_retinex.tif", img_msrcr);

def unevenLightCompensate(gray, blockSize):
    #gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    average = np.mean(img)

    rows_new = int(np.ceil(gray.shape[0] / blockSize))
    cols_new = int(np.ceil(gray.shape[1] / blockSize))

    blockImage = np.zeros((rows_new, cols_new), dtype=np.float32)
    for r in range(rows_new):
        for c in range(cols_new):
            rowmin = r * blockSize
            rowmax = (r + 1) * blockSize
            if (rowmax > gray.shape[0]):
                rowmax = gray.shape[0]
            colmin = c * blockSize
            colmax = (c + 1) * blockSize
            if (colmax > gray.shape[1]):
                colmax = gray.shape[1]

            imageROI = gray[rowmin:rowmax, colmin:colmax]
            temaver = np.mean(imageROI)
            blockImage[r, c] = temaver

    blockImage = blockImage - average
    blockImage2 = cv2.resize(blockImage, (gray.shape[1], gray.shape[0]), interpolation=cv2.INTER_CUBIC)
    gray2 = gray.astype(np.float32)
    dst = gray2 - blockImage2
    dst = dst.astype(np.uint8)
    dst = cv2.GaussianBlur(dst, (3, 3), 0)
    dst = cv2.cvtColor(dst, cv2.COLOR_GRAY2BGR)

    return dst





if __name__ == '__main__' :
    '''
    print('amsrcr processing......')
    t1 = time.time()
    img_amsrcr = automatedMSRCR(
        img,
        config['sigma_list']
    )
    t2 = time.time()
    print(t2 - t1)
    cv2.imshow('autoMSRCR retinex', img_amsrcr)
    cal_hist(img_amsrcr)
    equalize_hist(img_amsrcr)
    '''
    delight = unevenLightCompensate(img,16)
    cv2.imshow('delight',delight)
    delight_lps = custom_lapalian_demo(delight)
    cv2.imshow('delight_lps',delight_lps)
    #cv2.imwrite('AutomatedMSRCR_retinex.tif', img_amsrcr)
    #
    # print('msrcp processing......')
    # img_msrcp = MSRCP(
    #     img,
    #     config['sigma_list'],
    #     config['low_clip'],
    #     config['high_clip']
    # )
    #
    # shape = img.shape
    # cv2.imshow('Image', img)
    #
    # cv2.imshow('MSRCP', img_msrcp)
    # cv2.imwrite('MSRCP.tif', img_msrcp)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
