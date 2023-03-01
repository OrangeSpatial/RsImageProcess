
import os

from cv2 import cv2
import numpy as np
from utils import Point, GetAreaOfPolyGon


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
    with open(path, "r") as f:
        data = f.readlines()
        f.close()
    return data, childImageName, suffix, overlap, h, w


# 更新点信息
def updatePoint(point, width, height, overlap, h, w):
        point.x = point.x + w * (width - overlap)
        point.y = point.y + h * (height - overlap)
        return point


# 读取

# 读取文件夹下文件
# 根路径
baseRoot = "/home/orange/MytestPace/"

# 处理标签文件夹
targetDir = baseRoot + "result/label"
# 分块结果文件夹
resultDir = baseRoot + "merge/label"

# 目标文件列表
list = os.listdir(targetDir)  # 列出文件夹下所有的目录与文件
# print(len(list))
# print("目标文件如下：")
# print(list)

# 分块大小
b_width = 1024
b_height = 1024
# 重叠大小，不足时黑色填充，第一行和第一列没有重叠
overlap = 128

# 循环处理
for i in range(0, len(list)):
    path = os.path.join(targetDir, list[i])
    data, childImageName, suffix, overlap, h, w = getInfoFromPath(path)
    for line in data:
        line = line.strip('\n')
        # print(line)
        items = line.split(" ")
        # print(items)
        name = items[0]
        left_top = Point(float(items[1]), float(items[2]))
        left_bottom = Point(float(items[3]), float(items[4]))
        right_bottom = Point(float(items[5]), float(items[6]))
        right_top = Point(float(items[7]), float(items[8]))
        print("---------------------------")
        print(left_top.x, left_top.y)

        new_left_top = updatePoint(left_top, b_width, b_height, overlap, h, w)
        new_left_bottom = updatePoint(left_bottom, b_width, b_height, overlap, h, w)
        new_right_bottom = updatePoint(right_bottom, b_width, b_height, overlap, h, w)
        new_right_top = updatePoint(right_top, b_width, b_height, overlap, h, w)

        print(new_right_top.x, new_right_top.y)
        print("---------------------------")

        with open(resultDir + "/" + childImageName +"."+suffix, "a") as f:
            f.write(
                name + " " + str(new_left_top.x) + " " + str(new_left_top.y) + " " + str(
                    new_left_bottom.x) + " " + str(new_left_bottom.y)
                + " " + str(new_right_bottom.x) + " " + str(new_right_bottom.y) + " " + str(
                    new_right_top.x) + " " + str(new_right_top.y) + " " + "\n")


