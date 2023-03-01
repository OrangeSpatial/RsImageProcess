import os
import threading
from typing import Dict

from cv2 import cv2
import numpy as np
# from utils import copy8bitTo

# 补全
def copy8bitTo(im_data, new_width, new_height):
    # 判读数组维数,获取图像信息
    if len(im_data.shape) == 2:
        height, width = im_data.shape
        dst_image = np.zeros((new_height, new_width), np.uint8)
        dst_image[0:height, 0:width] = im_data
    else:
        height, width, channel = im_data.shape
        # dst_image = np.zeros((new_height, new_width, channel), np.uint8)
        dst_image = np.zeros((new_height, new_width, channel), np.uint8)
        dst_image[0:height, 0:width, :] = im_data
    return np.uint8(dst_image)

def getInfoFromPath(childFilePath):
    fileName = os.path.basename(childFilePath).split('.')
    prefix = fileName[0]
    suffix = fileName[1]
    # print(fileName)
    # 获取重叠度，行列号
    fileInfo = prefix.split("_")
    overlap = int(fileInfo[-3])
    h = int(fileInfo[-2])
    w = int(fileInfo[-1])
    tempStr = "_" + str(overlap) + "_" + str(h) + "_" + str(w)
    childImageName = prefix.replace(tempStr, "")

    img = cv2.imdecode(np.fromfile(childFilePath, np.uint8), -1)
    if (img is None):
        print("this is nonetype")
    return img, childImageName, suffix, overlap, h, w

def getAllImgByTile(rootPath):
    list = os.listdir(rootPath)
    imgDict = {}
    for i in range(len(list)):
        path = os.path.join(rootPath, list[i])
        # q1_128_0_5.jpg
        fileName = os.path.basename(path).split('.')
        prefix = fileName[0]
        fileInfo = prefix.split("_")
        overlap = int(fileInfo[-3])
        h = int(fileInfo[-2])
        w = int(fileInfo[-1])
        tempStr = "_" + str(overlap) + "_" + str(h) + "_" + str(w)
        childImageName = prefix.replace(tempStr, "")
        # if imgDict.has_key(childImageName):
        if imgDict.__contains__(childImageName):
            imgDict[childImageName].append(path)
        else:
            imgDict[childImageName] = [path]

    return imgDict

def merge(dic, item):
    print(threading.current_thread().name, item)
    temp_imageName = ""
    temp_w = 0
    temp_h = 0
    temp_img_w = 0
    temp_img_h = 0

    childImgCounts = 0

    for imgPath in dic[item]:
        childImgCounts+=1
        print("正在合并第"+str(childImgCounts)+"张:")
        print(imgPath)
        img, childImageName, suffix, overlap, h, w = getInfoFromPath(imgPath)
        # 判读数组维数,获取图像信息
        if len(img.shape) == 2:
            img_height, img_width = img.shape
        else:
            img_height, img_width, img_channel = img.shape

        if temp_imageName == "":
            # dst_image = img
            dst_image = np.zeros(img.shape, np.uint8)
            # cv2.imencode('.' + suffix, dst_image)[1].tofile(
            #     resultDir + "/" + childImageName + "." + suffix)
            temp_imageName = childImageName

    
        if temp_w < w:
            temp_w = w
        if temp_h < h:
            temp_h = h

        if temp_img_w < img_width:
            temp_img_w = img_width
        if temp_img_h < img_height:
            temp_img_h = img_height

        extend_height = temp_h * (temp_img_h - overlap) + temp_img_h
        extend_width = temp_img_w + temp_w * (temp_img_w - overlap)

        dst_image = copy8bitTo(dst_image, extend_width, extend_height)
        # cv2.imencode('.' + suffix, dst_image)[1].tofile(
        #     resultDir + "/" + childImageName + "." + suffix)
        if h == 0:
            if w == 0:
                dst_image[img_height * h:img_height * h + img_height,
                img_width * w:img_width * w + img_width] = img[
                                                           0:img_height,
                                                           0:img_width]
            else:
                dst_image[0:img_height,
                (img_width + (img_width - overlap) * (w - 1)):(img_width + (img_width - overlap) * w)] = img[
                                                                                                         0:img_height,
                                                                                                         overlap:img_width]
        else:
            if w == 0:
                dst_image[
                img_height + (img_height - overlap) * (h - 1):img_height + (img_height - overlap) * h,
                0:img_width] = img[
                               overlap:img_height,
                               0:img_width]
            else:
                dst_image[
                img_height + (img_height - overlap) * (h - 1):img_height + (img_height - overlap) * h,
                (img_width + (img_width - overlap) * (w - 1)):(img_width + (img_width - overlap) * w)] = img[
                                                                                                         overlap:img_height,
                                                                                                         overlap:img_width]
    cv2.imencode('.' + suffix, dst_image)[1].tofile(
        resultDir + "/" + childImageName + "." + suffix)



if __name__ == '__main__':

    # 读取文件夹下文件
    # 根路径
    baseRoot = "F:/imageClip/"
    # 处理影像文件夹
    targetDir = baseRoot + "imgSpace/result"

    # 结果文件夹
    resultDir = baseRoot + "imgSpace/merge"

    dic = getAllImgByTile(targetDir)

    keyList = list(dic.keys())

    print(keyList)
    if len(keyList) > 0:
        for i in range(len(keyList)):
            # if (2 * i + 1) < len(keyList):
            #     odd = keyList[2*i+1]
            #     thread = threading.Thread(target=merge, args=(dic, odd), name="odd thread")
            #     thread.start()
            # if 2*i < len(keyList):
            #     merge(dic, keyList[2*i])
            print(keyList[i]+"开始处理。。。")
            merge(dic, keyList[i])
