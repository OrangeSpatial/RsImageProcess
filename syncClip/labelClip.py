import os
import math
from geometry import Point, GetAreaOfPolyGon

def labelClip(filePath, outFilePath, b_width, b_height, img_overlap):
    fileName = os.path.basename(filePath).split('.')[0]
    if not os.path.isfile(filePath):
        print("此影像对应标签不存在！")
        return False
    with open(filePath, "r") as f:
        data = f.readlines()
        # print(data)
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
            # 多边形
            label_polygon = (left_top, left_bottom, right_bottom, right_top)
            # 面积
            label_polygon_area = GetAreaOfPolyGon(label_polygon)

            # 获取每个点在影像切割后对应行列值
            left_top_h, left_top_w = getWHByPoint(left_top, b_width, b_height, img_overlap)
            left_bottom_h, left_bottom_w = getWHByPoint(left_bottom, b_width, b_height, img_overlap)
            right_bottom_h, right_bottom_w = getWHByPoint(right_bottom, b_width, b_height, img_overlap)
            right_top_h, right_top_w = getWHByPoint(right_top, b_width, b_height, img_overlap)

            # 去重
            positions = {(left_top_h, left_top_w), (left_bottom_h, left_bottom_w), (right_bottom_h, right_bottom_w),
                         (right_top_h, right_top_w)}

            print("===============")
            print(left_top_h, left_top_w)
            print(left_bottom_h, left_bottom_w)
            print(right_bottom_h, right_bottom_w)
            print(right_top_h, right_top_w)

            print(positions)

            for item in positions:
                new_left_top = Point(left_top.x - item[1] * (b_width - img_overlap),
                                     left_top.y - item[0] * (b_height - img_overlap))
                new_left_bottom = Point(left_bottom.x - item[1] * (b_width - img_overlap),
                                        left_bottom.y - item[0] * (b_height - img_overlap))
                new_right_bottom = Point(right_bottom.x - item[1] * (b_width - img_overlap),
                                         right_bottom.y - item[0] * (b_height - img_overlap))
                new_right_top = Point(right_top.x - item[1] * (b_width - img_overlap),
                                      right_top.y - item[0] * (b_height - img_overlap))
                # 更新点使其在图片范围内
                new_left_top = updatePoint(new_left_top, b_width, b_height)
                new_left_bottom = updatePoint(new_left_bottom, b_width, b_height)
                new_right_bottom = updatePoint(new_right_bottom, b_width, b_height)
                new_right_top = updatePoint(new_right_top, b_width, b_height)

                new_polygon = (new_left_top, new_left_bottom, new_right_bottom, new_right_top)
                new_polygon_area = GetAreaOfPolyGon(new_polygon)

                if new_polygon_area / label_polygon_area < 0.3:
                    continue;
                else:
                    with open(outFilePath + "/" + fileName + "_" + str(img_overlap) + "_" + str(item[0]) + "_" + str(
                            item[1]) + ".txt", "a") as f:
                        f.write(
                            name + " " + str(new_left_top.x) + " " + str(new_left_top.y) + " " + str(
                                new_left_bottom.x) + " " + str(new_left_bottom.y)
                            + " " + str(new_right_bottom.x) + " " + str(new_right_bottom.y) + " " + str(
                                new_right_top.x) + " " + str(new_right_top.y) + " " + "\n")



# 更新点信息
def updatePoint(point, width, height):
    if 0 <= point.x <= width:
        if 0 <= point.y <= height:
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
        elif point.y > height:
            point.y = height
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
        else:
            point.y = 0
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
    elif point.x > width:
        point.x = width
        if 0 <= point.y <= height:
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
        elif point.y > height:
            point.y = height
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
        else:
            point.y = 0
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
    else:
        point.x = 0
        if 0 <= point.y <= height:
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
        elif point.y > height:
            point.y = height
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point
        else:
            point.y = 0
            point.x = round(point.x, 2)
            point.y = round(point.y, 2)
            return point


# 从0开始
def getWHByPoint(point, b_width, b_height, img_overlap):
    if point.x < b_width:
        if point.y < b_height:
            h = 0
            w = 0
        else:
            h = math.ceil((point.y - b_height) / (b_height - img_overlap))
            w = 0
    else:
        if point.y < b_height:
            h = 0
            w = math.ceil((point.x - b_width) / (b_width - img_overlap))
        else:
            h = math.ceil((point.y - b_height) / (b_height - img_overlap))
            w = math.ceil((point.x - b_width) / (b_width - img_overlap))
    return h, w

# if __name__ == "__main__":
#     # 读取

#     # 读取文件夹下文件
#     # 根路径

#     baseRoot = "/home/orange/MytestPace/"

#     # 处理标签文件夹
#     targetDir = baseRoot + "target/label"
#     # 分块结果文件夹
#     resultDir = baseRoot + "result/label"

#     # 目标文件列表
#     list = os.listdir(targetDir)  # 列出文件夹下所有的目录与文件
#     # print(len(list))
#     print("目标文件如下：")
#     print(list)

#     # 分块大小
#     b_width = 1024
#     b_height = 1024
#     # 重叠大小，不足时黑色填充，第一行和第一列没有重叠
#     overlap = 128

#     # 循环处理
#     for i in range(0, len(list)):
#         path = os.path.join(targetDir, list[i])
#         labelClip(path, resultDir, b_width, b_height, overlap)
