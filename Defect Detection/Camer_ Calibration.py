import numpy as np
import cv2
import glob

# 定义终止标准
criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER ,30,0.001)
#精确度（误差）满足epsilon停止 迭代次数超过max_iter停止
# 预定义目标点 # 获取标定板角点的位置
objp = np.zeros((4*5,3),np.float32)
objp[:,:2] = np.mgrid[0:5,0:4].T.reshape(-1,2)#将世界坐标系建在标定板上，所有点的Z坐标全部为0，所以只需要赋值x和y

#
objpoints = [] # 真实世界的3d points
imgpoints = [] #图片中的2d points
images = glob.glob('D:/Defect Detection/biaoding/*.jpg')
for fname in images:
    img = cv2.imread(fname)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)

    # 寻找棋盘角
    ret,corners = cv2.findChessboardCorners(gray,(5,4),None)

    # 如果找到，添加到目标点以及图像点
    if ret == True:
        objpoints.append(objp)

        corners2 = cv2.cornerSubPix(gray,corners,(11,11),(-1,-1),criteria)
        imgpoints.append(corners2)

        # 绘制点
        img = cv2.drawChessboardCorners(img,(5,4),corners2,ret)
        cv2.imshow('img',img)
        cv2.waitKey(500)
cv2.destroyAllWindows()

#       第二步 相机标定
# 返回摄像机矩阵mtx，畸变参数dist。旋转和平移向量等

ret,mtx,dist,rvecs,tvecs = cv2.calibrateCamera(objpoints,imgpoints,gray.shape[::-1],None,None)
np.savez('B.npz',mtx = mtx , dist = dist,rvecs = rvecs,tvecs = tvecs)
#      第三步 畸变校正
img = cv2.imread('D:/Defect Detection/biaoding/test.jpg')
h,w = img.shape[:2]
#优化相机矩阵
newcameramtx,roi = cv2.getOptimalNewCameraMatrix(mtx,dist,(w,h),1,(w,h))# 自由缩放系数 1

# 畸变校正 方法一
dst = cv2.undistort(img,mtx,dist,None,newcameramtx)
x,y,w,h = roi
dst = dst[y:y+h,x:x+w]
cv2.imshow('calibresult',dst)



# 畸变校正 方法二
mapx,mapy = cv2.initUndistortRectifyMap(mtx,dist,None,newcameramtx,(w,h),5)
dst = cv2.remap(img,mapx,mapy,cv2.INTER_LINEAR)

x,y,w,h = roi
dst = dst[y:y+h,x:x+w]
cv2.imshow('calresult',dst)

cv2.imshow('src',img)

cv2.waitKey(0)
cv2.destroyAllWindows()

# 反向投影误差
tot_error = 0

for i in range(len(objpoints)):
    imgpoints2,_ = cv2.projectPoints(objpoints[i],rvecs[i],tvecs[i],mtx,dist)
    error = cv2.norm(imgpoints[i],imgpoints2,cv2.NORM_L2)/len(imgpoints2)
    tot_error += error

print('total error',tot_error/len(objpoints))