import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import math
import time
import os
import cv2
import datetime

scale = 0.25
template = cv2.imread('character.png')
template = cv2.resize(template, (0, 0), fx=scale, fy=scale)
template_size = template.shape[:2]
filename = 'autojump.png'
cv2.namedWindow('calc_Pos')
cv2.namedWindow('sobel')
def search(img):
    result = cv2.matchTemplate(img, template, cv2.TM_SQDIFF)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

    cv2.rectangle(img, (min_loc[0], min_loc[1]), (min_loc[0] + template_size[1], min_loc[1] + template_size[0]),
                  (255, 0, 0), 4)

    return img, min_loc[0] + template_size[1] / 2, min_loc[1] + template_size[0]

def findTarget(img, chess_x,chess_y):
    mid=img.shape[1]/2
    x=int(chess_x)
    y=int(chess_y)
    top=y-150
    botton=y
    if x<mid:
        print('Next jump right')
        left=x+25
        right=x+200
    else:
        print('Next jump left')
        left=0
        right=x-25
    region = img[top:botton, left:right].copy()
    # cv2.rectangle(img, (left, botton), (right, top), (0, 255, 0), 4)
    edge_region_list=[]
    for idx in range(3):
        region_gray=cv2.cvtColor(region,cv2.COLOR_BGR2HSV)[:,:,idx]
        region_shape=region.shape
        #region_gray=cv2.GaussianBlur(region_gray,(3,3),0)
        region_sobel=np.abs(cv2.Sobel(region_gray,cv2.CV_32F,0,1,ksize=3))
        region_sobel=np.uint8(region_sobel)
        region_sobel=cv2.threshold(region_sobel,60,255,cv2.THRESH_BINARY)[1]
        kernel=np.ones((3,3),np.uint8)
        region_sobel=cv2.dilate(region_sobel,kernel)
        region_sobel=cv2.erode(region_sobel,kernel)
        region_sobel = np.uint8(region_sobel)
        edge_region_list.append(region_sobel)
    region_sobel_final=np.bitwise_or(edge_region_list[0],edge_region_list[1])
    region_sobel_final=np.bitwise_or(region_sobel_final,edge_region_list[2])

    cv2.imshow('sobel', region_sobel_final)
    cv2.waitKey(1)
    #find most top point
    top_x=-1
    top_y=-1
    for i in range(region_sobel_final.shape[0]):
        for j in range(region_sobel_final.shape[1]):
            if region_sobel_final[i,j] == 255:
                if top_x<0:
                    top_x=left+j+3
                    top_y=top+i
                    break
        if top_x>0:
            break
    # if end_dis_x<0:
    #     end_dis_x=start_dis_x
    tx=top_x
    #find most left or most right point
    if x<mid:
        #should find the most right point
        start_dis_y=-1
        for i in range(region_sobel_final.shape[1]):
            for j in range(region_sobel_final.shape[0]):
                if region_sobel_final[j, region_sobel_final.shape[1]-i-1]==255:
                    start_dis_y=j
                    break
            if start_dis_y>0:
                break
        ty=top+start_dis_y-5
    else:
        #should find most left point
        left_x = -1
        left_y=-1
        test_num=-1
        for i in range(region_sobel_final.shape[1]):
            for j in range(region_sobel_final.shape[0]):
                if region_sobel_final[j, i] == 255:
                    left_y=top+j
                    left_x=left+i
                    break
            if left_y > 0:
                break
        #ty = top + start_dis_y-23
        ty=int(top_y+np.abs(left_x-top_x)*0.3)

    # ty=-1
    # for i in range(dis_y, region_sobel_final.shape[0]):
    #     px=int((i-dis_y)*np.sqrt(3)+dis_x)
    #     if px<region_sobel_final.shape[1] and (region_sobel_final[i, px]==255 or region_sobel_final[i,px-1]==255 or (px+1<region_sobel_final.shape[1] and region_sobel_final[i,px+1])==255):
    #         continue
    #     else:
    #         ty=top+i-1
    #         break
    #ty=int(chess_y-np.abs(tx-chess_x)/np.sqrt(3))
    # dis=np.abs(tx-chess_x)*2/np.sqrt(3)/scale
    dis = (tx-chess_x)**2+(ty-chess_y)**2
    dis=dis**0.5/scale
    cv2.circle(img,(tx,ty),2,(0,255,0),2)
    return dis

def pull_screenshot():
    global filename
    filename = datetime.datetime.now().strftime("%H%M%S") + '.png'
    #os.system('mv autojump.png {}'.format(filename))
    cmd = 'adb shell screencap -p /sdcard/'+filename
    os.system(cmd)
    #time.sleep(1.5)
    cmd = 'adb pull /sdcard/'+filename + ' .'
    os.system(cmd)
    cmd='adb shell rm /sdcard/'+filename
    os.system(cmd)


def jump(distance):
    press_time = distance * 1.35
    press_time = int(press_time)
    cmd = 'adb shell input swipe 320 410 320 410 ' + str(press_time)
    print(cmd)
    os.system(cmd)


while(1):
    pull_screenshot()
    img = cv2.imread(filename)
    img = cv2.resize(img, (0, 0), fx=scale, fy=scale)
    img, src_x, src_y = search(img)
    calc_dis=findTarget(img,src_x,src_y)
    cv2.imshow('calc_Pos', img)
    cv2.waitKey(1)
    print('zyk calc distance is',calc_dis)
    jump(calc_dis)
    cmd='rm '+filename
    os.system(cmd)
    time.sleep(calc_dis*2/1000)