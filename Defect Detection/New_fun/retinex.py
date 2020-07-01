import numpy as np
import cv2
import time
import matplotlib.pyplot as plt

# https://blog.csdn.net/ajianyingxiaoqinghan/article/details/71435098 retinex 理论
img = cv2.imread('D:/crack3.jpg')
img_gray = cv2.imread('D:/crack3.jpg',0)
config = {'sigma_list':[15, 80, 200],'G' : 5.0,'b': 25.0,'alpha': 125.0,'beta':46.0,'low_clip':0.01,'high_clip':0.99}


def cal_hist(img):
    hist = cv2.calcHist([img], [0], None, [256], [0, 256])
    plt.plot(hist, color='b')
    plt.show()


def equalize_hist(img):
    equalize_hist = cv2.equalizeHist(img)
    hist = cv2.calcHist([equalize_hist], [0], None, [256], [0, 256])
    plt.plot(hist, color='b')
    plt.show()
    cv2.imshow('equal', equalize_hist)
    cv2.waitKey(0)
    cv2.destroyAllWindows()
def retinex_2_gray(retinex_img):
    retinex_img_int8 = np.uint8(retinex_img)
    retinex_img_gray = cv2.cvtColor(retinex_img_int8,cv2.COLOR_BGR2GRAY)
    return  retinex_img_gray
def retinex_show(retinex_img_gray,window_name):
    cv2.imshow(window_name,retinex_img_gray)
    cv2.waitKey(0)
    cv2.destroyAllWindows()

def singleScaleRetinex(img, sigma):
    img = np.float64(img)
    #retinex = np.log10(img) - np.log10(cv2.GaussianBlur(img, (0, 0), sigma))
    logI = cv2.log(img)
    logGI = cv2.log(cv2.cv2.GaussianBlur(img, (0, 0), sigma))
    retinex = cv2.subtract(logI,logGI)
    return retinex
    #return retinex

def singleScaleRetinex_with_return(img, sigma):
    print(img[1:5,1:5])
    img = np.float64(img)
    print(img[1:5, 1:5])
    #retinex = np.log10(img) - np.log10(cv2.GaussianBlur(img, (0, 0), sigma))
    logI = cv2.log(img)
    logGI = cv2.log(cv2.cv2.GaussianBlur(img, (0, 0), sigma))
    retinex = cv2.subtract(logI,logGI)

    m = np.argmax(retinex)
    r, c = divmod(m, retinex.shape[1])
    # print ('max',np.argmax(r))
    # print(r, c)
    print(retinex.dtype)
    print(retinex.shape)

    #img_retinex = np.uint8(retinex)
    print(retinex[10:30, 10:30])
    retinex_return = np.exp(retinex)
    print('aMSRCR dtype', retinex_return .dtype)
    print(retinex_return[10:30,10:30])
    dst_R = cv2.normalize(retinex_return, None, 0, 255, cv2.NORM_MINMAX)
    log_uint8 = cv2.convertScaleAbs(dst_R)
    print(retinex_return[10:20,10:20])
    return log_uint8
    #return retinex

# single_SR = singleScaleRetinex_with_return(img_gray,80)
# cv2.imshow('ssr_return',single_SR)

def multiScaleRetinex(img, sigma_list):#'sigma_list':[15, 80, 200] 改变的是高斯模糊里的sigma
    retinex = np.zeros_like(img)  #创建全零形状与原图相同的矩阵
    for sigma in sigma_list:#对每个高斯sigam值进行SSR，再进行叠加
        retinex += singleScaleRetinex(img, sigma)

    retinex = retinex / len(sigma_list)#叠加后除以sigma个数
    #print(retinex.dtype)
    #img_retinex = np.uint8(retinex)
    #retinex = cv2.cvtColor(retinex,cv2.COLOR_BGR2BGRA)
    return retinex

def multiScaleRetinex_with_return(img, sigma_list):#'sigma_list':[15, 80, 200] 改变的是高斯模糊里的sigma
    img = np.float64(img)
    retinex = np.zeros_like(img)  #创建全零形状与原图相同的矩阵
    for sigma in sigma_list:#对每个高斯sigam值进行SSR，再进行叠加
        retinex += singleScaleRetinex(img, sigma)

    retinex = retinex / len(sigma_list)#叠加后除以sigma个数
    #print(retinex.dtype)
    #img_retinex = np.uint8(retinex)
    #retinex = cv2.cvtColor(retinex,cv2.COLOR_BGR2BGRA)
    retinex_return = np.exp(retinex)
    dst_R = cv2.normalize(retinex_return, None, 0, 255, cv2.NORM_MINMAX)
    log_uint8 = cv2.convertScaleAbs(dst_R)
    print(retinex_return[10:20,10:20])
    return log_uint8
multi_SR = multiScaleRetinex_with_return(img,config['sigma_list'])
cv2.imshow('msr',multi_SR)
multi_SR_gray = cv2.cvtColor(multi_SR,cv2.COLOR_BGR2GRAY)
cv2.imshow('msr_gray',multi_SR_gray)
#multi_SR = np.uint8(multi_SR)
#v2.imshow('multi_SR',multi_SR)
#cal_hist(multi_SR)
#MSR = multiScaleRetinex(img_gray,config['sigma_list'])
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

        low_val = unique[0] / 100.0#最小值 0 ？
        high_val = unique[-1] / 100.0#最大值 255？
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

if __name__ == '__main__' :
    # print('amsrcr processing......')
    # t1 = time.time()
    # img_amsrcr = automatedMSRCR(
    #     img,
    #     config['sigma_list']
    # )
    # t2 = time.time()
    # print(t2 - t1)
    # cv2.imshow('autoMSRCR retinex', img_amsrcr)
    # cal_hist(img_amsrcr)
    # equalize_hist(img_amsrcr)


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
