import os
import threading

import numpy as np
from cv2 import cv2 
import math

from osgeo import gdal
import pandas as pd


from labelClip import labelClip

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

    height, width = imgArray.shape

    # 转3波段
    # newImgArray = np.array([imgArray],imgArray,imgArray])
    newImgArray = np.expand_dims(imgArray, axis=2)
    newImgArray = np.concatenate((newImgArray, newImgArray, newImgArray), axis=-1)

    print(sum(sum(newImgArray[:,:,0] < 1))/(height*width))

    if black>1 and white >1:
        cv2.imwrite(outputFile, newImgArray)
    if sum(sum(newImgArray[:,:,0] < 1))/(height*width) < black and sum(sum(newImgArray[:,:,0] >=254))/(height*width) < white:
        # # img = cv2.imdecode(np.fromfile(path, np.uint8), -1)
        print("out=====>",fileName)
        cv2.imwrite(outputFile, newImgArray)

def write_tiff(output_file, array_data, rows, cols, counts, geo, proj):
    Driver = gdal.GetDriverByName("Gtiff")
    dataset = Driver.Create(output_file, cols, rows, 3, gdal.GDT_Byte)

    dataset.SetGeoTransform(geo)
    dataset.SetProjection(proj)

    # if counts == 1:
    #     array_data = np.array([array_data])

    for i in range(3):
        band = dataset.GetRasterBand(i + 1)
        band.WriteArray(array_data)  # 波段写入顺序调整可以改变图像颜色，思路i改为2-i

    del dataset

def cumulativehistogram(array_data, rows, cols, band_min, band_max, m_value):

    # 累计直方图统计
    # 逐波段统计最值
    gray_level = int(band_max - band_min + 1)
    # gray_array = np.zeros(gray_level)
    gray_array = np.ones(gray_level)

    counts = 0
    # 下面两个for循环时间复杂度高，当有千万级的数据运算会很慢****************
    # for row in range(rows):
    #     for col in range(cols):
    #         gray_array[int(array_data[row, col] - band_min)] += 1
    #         counts += 1
    # 改编上面的功能，代码如下**************
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


def singleBandimageClip(filePath, c_width, c_height, c_overlap, out8BitTiffPath, out8BitjpgPath,resultLabelDir):
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

    # 计算影像纬度及像元
    x_pixel_resolution = im_geotrans[1]  # 东西方向像素分辨率
    top_left_lat = im_geotrans[3]  # 左上角y坐标（纬度）
    # 按照分辨率改变切割大小
    
    # 地理坐标
    if x_pixel_resolution < 0.0001:
        img_resolution = math.cos(top_left_lat)*111000*x_pixel_resolution
    else: 
        img_resolution = x_pixel_resolution # 平面坐标

    if img_resolution <= 2:
        c_height = 2048
        c_width = 2048

    if bandsize != 1:
        print(fileName+"---此影像不是单波段影像！")
        return

    # ====== 标签切割 start===========
    isFinish = labelClip(txtFile, resultLabelDir, c_width, c_height, c_overlap)
    if not isFinish:
        print("影像名:"+filePath)
        return
    # ====== 标签结束 end===========

    # 设置空值为0
    im_data[im_data == 65536] = 0
    # 取出中心一半用于计算直方图压缩比例
    cumulativeArray = im_data[int(height/2)-int(height/4):int(height/2)+int(height/4),int(width/2)-int(width/4):int(width/2)+int(width/4)]
    band_max = np.max(cumulativeArray)
    band_min = np.min(cumulativeArray)
    m_value = int(np.mean(cumulativeArray))
    cutmin, cutmax = cumulativehistogram(cumulativeArray, cumulativeArray.shape[0],cumulativeArray.shape[1],band_min,band_max,m_value)
    if cutmax < cutmin:
        temp_cut = cutmin
        cutmin = cutmax
        cutmax = temp_cut

    compress_scale = (cutmax - cutmin) / 255

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
    num = 0
    for h in range(row_num):  # 从高度 可以分成几块！
        for w in range(col_num):
            num+=1
            print("正在切====================="+str(num))
            # 偏移量
            offset_x = w * (c_width - c_overlap)
            offset_y = h * (c_height - c_overlap)
            # 防止超出边界
            b_xsize = min(width - offset_x, c_width)
            b_ysize = min(height - offset_y, c_height)

            cutImgArray = dataset.ReadAsArray(offset_x, offset_y, b_xsize, b_ysize)

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
            compress_data = np.zeros((b_ysize, b_xsize), np.uint8)
            temp = np.array(cutImgArray)
            temp[temp > cutmax] = cutmax
            temp[temp < cutmin] = cutmin
            compress_data = (temp - cutmin) / compress_scale

            out8bitFile = out8BitTiffPath+"/" + fileName + "_" + str(c_overlap) + "_" + str(h) + "_" + str(w) + ".tiff"
            # compress_data = compress(cutImgArray, dst_transform,im_proj,b_ysize,b_xsize,bandsize,out8bitFile)
            write_tiff(out8bitFile, compress_data, b_ysize, b_xsize, 1, dst_transform, im_proj)

            dst_data = np.zeros((c_height, c_width), np.uint8)
            if b_xsize < c_width or b_ysize < c_height:
                dst_data[0:b_ysize, 0:b_xsize] = compress_data
            else:
                dst_data = compress_data

            # 转 jpg
            jpgFile = out8BitjpgPath + "/" + fileName + "_" + str(c_overlap) + "_" + str(h) + "_" + str(w) + ".jpg"
            tif2jpgdelNull(dst_data, jpgFile, 2, 2)

    print("此图总计可切："+str((h+1)*(w+1))+"张"+"，切割了"+str(num))
    del dataset
    

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
    suffix = ".img"
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
        singleBandimageClip(path, b_width, b_height, overlap, temp8BitDir, resultDir,resultLabelDir)

        # if (2 * i + 1) < len(newList):
        #     oddpath = os.path.join(targetDir, newList[2 * i + 1])
        #     print(oddpath)
        #     thread = threading.Thread(target=imageClip, args=(oddpath,temp16BitDir,b_width,b_height,overlap,temp8BitDir,resultDir), name="odd thread")
        #     thread.start()
        # if 2 * i < len(newList):
        #     path = os.path.join(targetDir, newList[2*i])
        #     imageClip(path, temp16BitDir, b_width, b_height, overlap, temp8BitDir, resultDir)


