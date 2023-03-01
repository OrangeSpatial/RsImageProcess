import os
import threading

import numpy as np
from cv2 import cv2 
import math

import pandas as pd
from osgeo import gdal

from labelClip import labelClip

def write_tiff(output_file, array_data, rows, cols, counts, geo, proj):
    Driver = gdal.GetDriverByName("Gtiff")
    dataset = Driver.Create(output_file, cols, rows, 3, gdal.GDT_Byte)

    dataset.SetGeoTransform(geo)
    dataset.SetProjection(proj)

    # if counts == 1:
    #     array_data = np.array([array_data])
    if counts > 3:
        for i in range(3):
            band = dataset.GetRasterBand(i + 1)
            if i == 0:
                band.WriteArray(array_data[3,:,:])
            else:
                band.WriteArray(array_data[i,:,:])  # 波段写入顺序调整可以改变图像颜色，思路i改为2-i
    elif counts == 3:
        for i in range(3):
            band = dataset.GetRasterBand(i + 1)
            band.WriteArray(array_data[i,:,:])  # 波段写入顺序调整可以改变图像颜色，思路i改为2-i

    del dataset

def tif2jpgdelNull(imgArray, outputFile, black, white):

    # if black > 1:
    #     black =1
    if black < 0:
        black = 0.1
    # if white >1:
    #     white = 1
    if white < 0:
        white = 0.1

    fileName = os.path.basename(outputFile).split('.')[0]
    print("开始==" + fileName)
    # img = cv2.imread(inputFile)

    channel, height, width = imgArray.shape

    # print(imgArray)

    # 转3波段
    # 转换为  height, width, channel
    newImgArray = imgArray[0:3,:,:]
    newImgArray = newImgArray.transpose(1, 2, 0)
    # newImgArray = np.transpose(imgArray,(1,2,0))

    print(sum(sum(newImgArray[:,:,0] < 1))/(height*width))

    if black>1 and white >1:
        cv2.imwrite(outputFile, newImgArray)

    if sum(sum(newImgArray[:,:,0] < 1))/(height*width) < black and sum(sum(newImgArray[:,:,0] >=254))/(height*width) < white:
        # # img = cv2.imdecode(np.fromfile(path, np.uint8), -1)
        print("out=====>",fileName)
        cv2.imwrite(outputFile, newImgArray)

def cumulativehistogram(array_data, rows, cols, band_min, band_max, m_value):

    # 累计直方图统计
    # 逐波段统计最值
    gray_level = int(band_max - band_min + 1)
    # gray_array = np.zeros(gray_level)
    gray_array = np.ones(gray_level)

    counts = 0
    b = array_data - band_min
    # b = np.maximum(b,0)
    c = np.array(b).reshape(1, -1)
    d = pd.DataFrame(c[0])[0].value_counts()
    for i in range(len(d.index)):
        gray_array[int(d.index[i])] = int(d.values[i])
    # print(gray_array)
    # gray_array[gray_level-1] *= 0.02 
    counts = rows * cols
    # 截至*****************************

    count_percent2 = counts * 0.02
    count_percent98 = counts * 0.98

    cutmax = 0
    cutmin = 0

    for i in range(1, gray_level):
        gray_array[i] += gray_array[i - 1]
        if (gray_array[i] >= count_percent2 and gray_array[i - 1] <= count_percent2):
            cutmin = i + band_min

        if (gray_array[i] >= count_percent98 and gray_array[i - 1] <= count_percent98):
            cutmax = i + band_min
    if cutmax == 0 and gray_level > 1:
        # cutmax = gray_level - 1
        cutmax = int((gray_level - 1)*0.8)
    if cutmin == 0 and gray_level >1:
        cutmin = m_value * 0.2
    return cutmin, cutmax


def multipleBandimageClip(filePath, c_width, c_height, c_overlap, out8BitTiffPath, out8BitjpgPath, resultLabelDir):
    fileName = os.path.basename(filePath).split('.')[0]
    labelPath = os.path.dirname(filePath)
    txtFile = labelPath +"/"+fileName+".txt"
    dataset = gdal.Open(filePath)  # 读取要切的原图
    print("open tif file succeed")
    width = dataset.RasterXSize  # 获取数据宽度
    height = dataset.RasterYSize  # 获取数据高度
    bandsize = dataset.RasterCount  # 获取数据波段数
    im_geotrans = dataset.GetGeoTransform()  # 获取仿射矩阵信息
    im_proj = dataset.GetProjection()  # 获取投影信息
    im_data = dataset.ReadAsArray()  # 获取数据
    dataType = dataset.GetRasterBand(1).DataType # 获取类型

    print ("dataType:====="+str(dataType))

    if bandsize < 3:
        print(fileName+"---此影像不是多波段影像！")
        return
    
    # 计算影像纬度及像元
    x_pixel_resolution = im_geotrans[1]  # 东西方向像素分辨率
    top_left_lat = im_geotrans[3]  # 左上角y坐标（纬度）
    # 按照分辨率改变切割大小
    if x_pixel_resolution < 0.0001:
        img_resolution = math.cos(top_left_lat)*111000*x_pixel_resolution # 地理坐标
    else: 
        img_resolution = x_pixel_resolution # 平面坐标

    if img_resolution <= 2:
        c_height = 2048
        c_width = 2048
    # ====== 标签切割 start===========
    labelClip(txtFile, resultLabelDir, c_width, c_height, c_overlap)
    # ====== 标签结束 end===========

    # ====== 影像切割 start===========

    # 设置空值为0
    im_data[im_data == 65536] = 0
    # 读取波段数据
    # 选取部分计算直方图
    band_data = []
    out_bands = []
    # cumulativeArray = dataset.ReadAsArray(int(width/2-width/4), int(height/2-height/4), int(width/2), int(height/2))
    cumulativeArray = im_data[:,int(height/2)-int(height/4):int(height/2)+int(height/4),int(width/2)-int(width/4):int(width/2)+int(width/4)]
    for i in range(bandsize):
        item = dataset.GetRasterBand(i+1)
        band_data.append(item)
        band_max = np.max(cumulativeArray[i,:,:])
        band_min = np.min(cumulativeArray[i,:,:])
        m_value = int(np.mean(cumulativeArray[i,:,:]))
        cutmin, cutmax = cumulativehistogram(cumulativeArray[i,:,:], cumulativeArray.shape[1],cumulativeArray.shape[2],band_min,band_max,m_value)
        out_bands.append((cutmin,cutmax))
    
    # 将影像外界像素值设为0
    # im_data[im_data == 65536] = 65536*0.002
    # 定义切图的起始点坐标
    offset_x = 0
    offset_y = 0
    # 定义切图的大小（矩形框）
    col_num = int(width / c_width)  # 宽度可以分成几块
    row_num = int(height / c_height)  # 高度可以分成几块
    if (width % c_width != 0):
        col_num += 1
    if (height % c_height != 0):
        row_num += 1

    print("行:%d   列:%d" % (row_num, col_num))
    for h in range(row_num):  # 从高度 可以分成几块！
        for w in range(col_num):
            # 偏移量
            offset_x = w * (c_width - c_overlap)
            offset_y = h * (c_height - c_overlap)
            # 防止超出边界
            b_xsize = min(width - offset_x, c_width)
            b_ysize = min(height - offset_y, c_height)

            # 获取原图的原点坐标信息
            # ori_transform = dataset.GetGeoTransform()
            # 读取原图仿射变换参数值
            top_left_x = im_geotrans[0]  # 左上角x坐标
            w_e_pixel_resolution = im_geotrans[1]  # 东西方向像素分辨率
            top_left_y = im_geotrans[3]  # 左上角y坐标
            n_s_pixel_resolution = im_geotrans[5]  # 南北方向像素分辨率

            # 根据反射变换参数计算新图的原点坐标
            top_left_x = top_left_x + offset_x * w_e_pixel_resolution
            top_left_y = top_left_y + offset_y * n_s_pixel_resolution

            # 将计算后的值组装为一个元组，以方便设置
            dst_transform = (
            top_left_x, im_geotrans[1], im_geotrans[2], top_left_y, im_geotrans[4], im_geotrans[5])

            # 压缩为8为bit
            # 压缩存储
            compress_data = np.zeros((bandsize, b_ysize,b_xsize), np.uint8)
            # 各波段截取
            for ite in range(bandsize):
                # 获取直方图信息
                new_cutmin, new_cutmax = out_bands[ite]
                # array_data = band_data[i].ReadAsArray(offset_x, offset_y, b_xsize, b_ysize)
                array_data = im_data[ite,offset_y:(offset_y+b_ysize), offset_x:(offset_x+b_xsize)]

                if new_cutmax < new_cutmin:
                    temp_cut = new_cutmin
                    new_cutmin = new_cutmax
                    new_cutmax = temp_cut
                compress_scale = (new_cutmax - new_cutmin) / 255
                # 压缩
                temp = np.array(array_data)
                temp[temp > new_cutmax] = new_cutmax
                temp[temp < new_cutmin] = new_cutmin
                compress_data[ite, :, :] = (temp - new_cutmin) / compress_scale
                out8bitFile = out8BitTiffPath+"/" + fileName + "_" + str(c_overlap) + "_" + str(h) + "_" + str(w) + ".tiff"
            write_tiff(out8bitFile, compress_data, b_ysize,b_xsize,bandsize, dst_transform, im_proj)

            # cutImgArray = dataset.ReadAsArray(offset_x, offset_y, b_xsize, b_ysize)

            # 补全不足
            dst_data = np.zeros((bandsize, c_height, c_width), np.uint8)
            if b_xsize < c_width or b_ysize < c_height:
                dst_data[:,0:b_ysize, 0:b_xsize] = compress_data
            else:
                dst_data = compress_data

            # 转 jpg
            jpgFile = out8BitjpgPath + "/" + fileName + "_" + str(c_overlap) + "_" + str(h) + "_" + str(w) + ".jpg"
            tif2jpgdelNull(dst_data, jpgFile, 1, 1)
    del dataset
    # ====== 影像切割 end===========
    

if __name__ == "__main__":
    # 读取文件夹下文件
    # 根路径
    baseRoot = "F:/imageClip/"
    # 处理影像文件夹
    targetDir = baseRoot + "imgSpace/img"
    # 转8位影像临时文件夹
    # temp16BitDir = baseRoot + "imgSpace/16bit"
    temp8BitDir = baseRoot + "imgSpace/8bit"
    # 分块结果文件夹
    resultDir = baseRoot + "imgSpace/result"
    resultLabelDir = baseRoot + "imgSpace/label"


    # 目标文件列表
    list = os.listdir(targetDir)  # 列出文件夹下所有的目录与文件

    newList = []
    #指定后缀
    suffix = ".tiff"
    for ofile in list:
        print(ofile)
        if os.path.splitext(ofile)[1] == suffix:
            newList.append(ofile)
    
    # print(len(list))
    print("目标文件如下：")
    print(newList)

    # 分块大小
    b_width = 1024
    b_height = 1024
    # 重叠大小，不足时黑色填充，第一行和第一列没有重叠
    overlap = 128

    # 循环处理
    for i in range(0, len(newList)):
        path = os.path.join(targetDir, newList[i])
        multipleBandimageClip(path, b_width, b_height, overlap, temp8BitDir, resultDir, resultLabelDir)

        # if (2 * i + 1) < len(newList):
        #     oddpath = os.path.join(targetDir, newList[2 * i + 1])
        #     print(oddpath)
        #     thread = threading.Thread(target=imageClip, args=(oddpath,temp16BitDir,b_width,b_height,overlap,temp8BitDir,resultDir), name="odd thread")
        #     thread.start()
        # if 2 * i < len(newList):
        #     path = os.path.join(targetDir, newList[2*i])
        #     imageClip(path, temp16BitDir, b_width, b_height, overlap, temp8BitDir, resultDir)


