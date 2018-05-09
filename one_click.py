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
    top=y-130
    botton=y-20
    if x<mid:
        print('Next jump right')
        left=x
        right=x+200
    else:
        print('Next jump left')
        left=0
        right=x
    region = img[top:botton, left:right].copy()
    cv2.rectangle(img, (left, botton), (right, top), (0, 255, 0), 4)
    edge_region_list=[]
    for idx in range(3):
        region_gray=cv2.cvtColor(region,cv2.COLOR_BGR2HSV)[:,:,idx]
        region_shape=region.shape
        region_gray=cv2.GaussianBlur(region_gray,(5,5),0)
        region_sobel=np.abs(cv2.Sobel(region_gray,cv2.CV_32F,0,1,ksize=3))
        region_sobel=np.uint8(region_sobel)
        region_sobel=cv2.threshold(region_sobel,12,255,cv2.THRESH_BINARY)[1]
        kernel=np.ones((3,3),np.uint8)
        region_sobel=cv2.dilate(region_sobel,kernel)
        region_sobel=cv2.erode(region_sobel,kernel)
        region_sobel = np.uint8(region_sobel)
        edge_region_list.append(region_sobel)
    region_sobel_final=np.bitwise_or(edge_region_list[0],edge_region_list[1])
    region_sobel_final=np.bitwise_or(region_sobel_final,edge_region_list[2])
    dis_x=-1
    dis_y=-1
    for i in range(region_sobel_final.shape[0]):
        for j in range(region_sobel_final.shape[1]):
            if region_sobel_final[i,j] == 255:
                dis_x=j
                dis_y=i
                break
        if dis_x>0:
            break
    tx=int(left+dis_x)
    ty=-1
    for i in range(dis_y, region_sobel_final.shape[0]):
        px=int((i-dis_y)*np.sqrt(3)+dis_x)
        if region_sobel_final[i, px]==255 or region_sobel_final[i,px-1]==255 or region_sobel_final[i,px+1]==255:
            continue
        else:
            ty=top+i-1
            break



    #ty=int(chess_y-np.abs(tx-chess_x)/np.sqrt(3))
    dis=np.abs(tx-chess_x)*2/np.sqrt(3)/scale
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


def update_data():
    global src_x, src_y, filename

    img = cv2.imread(filename)

    img = cv2.resize(img, (0, 0), fx=scale, fy=scale)

    img, src_x, src_y = search(img)

    calc_dis=findTarget(img,src_x,src_y)
    print('zyk calc distance is',calc_dis)
    return img


fig = plt.figure()
index = 0

pull_screenshot()
img = update_data()

update = True
im = plt.imshow(img, animated=True)


def updatefig(*args):
    global update

    if update:
        time.sleep(1.5)
        pull_screenshot()
        im.set_array(update_data())
        update = False
    return im,


def onClick(event):
    global update
    global src_x, src_y

    dst_x, dst_y = event.xdata, event.ydata

    distance = (dst_x - src_x) ** 2 + (dst_y - src_y) ** 2
    distance = (distance ** 0.5) / scale
    print('distance = ', distance)
    jump(distance)
    update = True


fig.canvas.mpl_connect('button_press_event', onClick)
ani = animation.FuncAnimation(fig, updatefig, interval=5, blit=True)
plt.show()
