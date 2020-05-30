import numpy as np
import cv2 as cv
src = cv.imread('D:/crack3.jpg',0)
M = src.shape[0]
N = src.shape[1]
Fd = 0.8
FD = -1*Fd
Fe = 128 #中间灰度
Xmax = 255
P = np.zeros(src.shape,np.float32)
for i in range(M):
    for j in range(N):

        power = pow(1+(Xmax - src.item(i, j))/Fe, FD)  ##获取像素点 并 乘方
        P.itemset((i, j), power)  ### 设置像素点
        #print(P[i,j])
        #P[i,j] = int((1+(Xmax-src[i,j])/Fe)**Fd)
#模糊增强
for i in range(M):
    for j in range(N):
        if P.item(i,j) <= 0.5:
            power = int(pow(2*P.item(i, j), 2))
            P.itemset((i,j),power)

        else:
            power = int(pow(1-2*P.item(i, j), 2))
            P.itemset((i, j), power)
print(P[100,20])
P.astype(np.uint8)
print(P.dtype)
cv.imshow('P',P)
cv.imshow('src',src)
cv.waitKey(0)
cv.destroyAllWindows()