import cv2
import matplotlib.pyplot as plt
import numpy as np
########     四个不同的滤波器    #########
img = cv2.imread('D:/crack3.jpg',0)

# 均值滤波
img_mean = cv2.blur(img, (3,3))

# 高斯滤波
img_Guassian = cv2.GaussianBlur(img,(3,3),0)

# 中值滤波
img_median = cv2.medianBlur(img, 3)

# 双边滤波
img_bilater = cv2.bilateralFilter(img,3,1000,1000)
#邻域直径9，两个 75 分别是空间高斯函数标准差，灰度值相似性高斯函数标准差


# CV2.fastNlMeansDenoising（非局部平均去噪）

img_fastNlMean = cv2.fastNlMeansDenoising(img,None,3,3,5)
# 展示不同的图片
titles = ['srcImg','mean', 'Gaussian', 'median', 'bilateral','img_fastNlMean']
imgs = [img, img_mean, img_Guassian, img_median, img_bilater,img_fastNlMean]

for i in range(len(titles)):
    cv2.imshow(titles[i],imgs[i])
#     plt.subplot(2,3,i+1)#注意，这和matlab中类似，没有0，数组下标从1开始
#     plt.imshow(imgs[i])
#     plt.title(titles[i])
# plt.show()
cv2.waitKey(0)
cv2.destroyAllWindows()