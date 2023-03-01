
# -*- coding: utf-8 -*-
"""
@author: orange
"""

from cv2 import cv2
import os
import imgaug as ia
from imgaug import augmenters as iaa


# 增广方式
# seq = iaa.SomeOf(2, [
seq = iaa.Sequential([
    iaa.Affine(rotate=45),
    # iaa.Affine(rotate=(-10, 10)),
    # iaa.GaussianBlur(sigma=(0, 0.05)), # blur images with a sigma of 0 to 3.0,
    iaa.Fliplr(1.0),
    iaa.Flipud(1.0),
    # iaa.Affine(scale=(0.15, 0.3)),
], random_order=False)

def aug(inputImagePath, imputLabelPath, outputImagePath,outputLabelPath):
    # 读取标签列表txt文件
    files = os.listdir(imputLabelPath)

    # 每张图片增广次数
    m = 1
    
    for file in files:
        if not os.path.isdir(file):
            print(file)
            # 获取图像
            srcImg = cv2.imread(inputImagePath + "\\" + file.split(".")[0] + ".jpg")
            # 应该都是 500*500
            height, width, channels = srcImg.shape

            # 获取一张图片的所有标注信息
            srcTxt = open(imputLabelPath + "\\" +file)
            iter_f = iter(srcTxt)

            bbs = []
            label_objects = []
            # 遍历每个框
            for line in iter_f:
                row = line.split(" ")
                print(row)
                classIdx = row[0]
                label_objects.append(classIdx)

                leftTopX = float(row[1])
                leftTopY = float(row[2])
                leftBottomX = float(row[3])
                leftBottomY = float(row[4])
                rightBottomX = float(row[5])
                rightBottomY = float(row[6])
                rightTopX = float(row[7])
                rightTopY = float(row[8])

                # 取外接矩形进行増广
                Xmin = min(leftTopX, leftBottomX, rightBottomX, rightTopX)
                Xmax = max(leftTopX, leftBottomX, rightBottomX, rightTopX)
                Ymin = min(leftTopY, leftBottomY, rightBottomY, rightTopY)
                Ymax = max(leftTopY, leftBottomY, rightBottomY, rightTopY)

                bb = ia.BoundingBox(x1=Xmin, y1=Ymin, x2=Xmax, y2=Ymax);
                bbs.append(bb)

            # 总共增广 m 次
            for j in range(m):
                bbsi = ia.BoundingBoxesOnImage(bbs, shape=srcImg.shape)
                seq_det = seq.to_deterministic()  # 保持坐标和图像同步

                images = [srcImg]
                images_aug = seq_det.augment_images(images)

                baseName = file.split(".")[0] + "_aug_" + str(j)
                outputName = baseName + ".jpg"
                # 保存图片
                cv2.imwrite(outputImagePath + "\\" + outputName, images_aug[0])

                bbs_aug = seq_det.augment_bounding_boxes(bbsi)
                # 保存对应的标注框信息
                newTxt = open(outputLabelPath + "\\" + baseName + ".txt", "w")
                for i in range(len(bbs_aug.bounding_boxes)):

                    name = label_objects[i]
                    after = bbs_aug.bounding_boxes[i]
                    leftTopX = after.x1
                    leftTopY = after.y1
                    leftBottomX = after.x1
                    leftBottomY = after.y2
                    rightBottomX = after.x2
                    rightBottomY = after.y2
                    rightTopX = after.x2
                    rightTopY = after.y1

                    # TODO: 增广过后，太小的检测框 就不添加 标注信息了
                    info = name + " " + str(leftTopX) + " " + str(leftTopY) + " " + str(leftBottomX) + " " + str(leftBottomY)\
                        + " " + str(rightBottomX) + " " + str(rightBottomY) + " " + str(rightTopX) + " " + str(rightTopY) + " " + "\n"
                    newTxt.write(info)

                newTxt.close()
        srcTxt.close()