import cv2
import numpy as np
from matplotlib import pyplot as plt
'''
BINS : 横坐标上有几个分组
DIMS： 收集数据的参数数目 ：灰度值 1
RANGE： 灰度值范围 [0,256]

cv2.calHist([images],[channels],mask,[histSize],[ranges])
channels 灰度图像是 [0]，彩色图像 [0],[1],[2] 分别对应BGR
mask 掩膜：统计整幅图像的直方图 设为 None，某一部分时 需先制作掩膜图像
histSize = [256]
ranges = [0,256]
'''
'''
# 1 直方图计算
img = cv2.imread('D:/Study/cv_image/fairy.png',0)
# cv2.calcHist 是最快的
hist = cv2.calcHist([img],[0],None,[256],[0,256])
#plt.plot(hist,color = 'b')
#plt.show()
hist = np.bincount(img.ravel(),minlength=256) #一维直方图时使用，第二块
# hist = array([a1],[a2],...,[a256]) 共有 256个bin 每个bin 对应 这个灰度有几个像素
hist,bins = np.histogram(img.ravel(),256,[0,256])# img.ravel 将图像降维成一维数组 ，最慢
'''
# 2 绘制直方图

#  plt.hist(img.ravel(),256,[0,256])  在没有计算直方图的时候 直接 绘图

img = cv2.imread('D:/Study/cv_image/lena.jpg')
colors = ['b','g','r']

for i ,color in enumerate(colors):
    hist = cv2.calcHist([img],[i],None,[256],[0,256])
    plt.plot(hist,color= color) # 在已经计算了直方图后,直接hist 就可以
    plt.xlim([0,256])  #限制横轴参数范围
plt.show()

'''
# 3 使用掩膜
# 统计局部区域的直方图，构建掩膜：将要统计区域设置为白色，其余部分为黑色

#构建掩膜
img = cv2.imread('E:/lena.jpg',0)
mask = np.zeros(img.shape[:2],np.uint8)  # 创建一个和原图大小一样的 全是0的图像
mask[100:300,100:400] = 255 # 将要统计的区域设置为白色

masked_img = cv2.bitwise_and(img,img,mask=mask) #遮掩操作 仅保留需要统计处的局部区域
cv2.imshow('masked_img',masked_img)
#cv2.imshow('img',img)


hist_full = cv2.calcHist([img],[0],None,[256],[0,256]) #统计整幅图的hist
hist_mask = cv2.calcHist([img],[0],mask,[256],[0,256])
plt.subplot(221),plt.imshow(img,'gray'),plt.title('Original')
plt.xticks([]), plt.yticks([])
plt.subplot(222),plt.imshow(mask,'gray'),plt.title('mask')
plt.xticks([]), plt.yticks([])
plt.subplot(223),plt.imshow(masked_img,'gray'),plt.title('masked_img')
plt.xticks([]), plt.yticks([])
plt.subplot(224),plt.plot(hist_full),plt.plot(hist_mask),plt.title('hist')
plt.xlim([0,256])
'''
plt.show()
cv2.waitKey(0)
cv2.destroyAllWindows()
