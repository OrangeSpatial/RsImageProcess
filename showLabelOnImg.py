from cv2 import cv2
import numpy as np
import math

from PIL import Image, ImageFont, ImageDraw


def paint_chinese_opencv(im,chinese,position,fontsize,color):#opencv输出中文
    img_PIL = Image.fromarray(cv2.cvtColor(im,cv2.COLOR_BGR2RGB))# 图像从OpenCV格式转换成PIL格式
    font = ImageFont.truetype('simhei.ttf',fontsize,encoding="utf-8")
    #color = (255,0,0) # 字体颜色
    #position = (100,100)# 文字输出位置
    draw = ImageDraw.Draw(img_PIL)
    draw.text(position,chinese,font=font,fill=color)# PIL图片上打印汉字 # 参数1：打印坐标，参数2：文本，参数3：字体颜色，参数4：字体
    img = cv2.cvtColor(np.asarray(img_PIL),cv2.COLOR_RGB2BGR)# PIL图片转cv2 图片
    return img

filePath = "F:/imageClip/imgSpace/result/q_128_2_0.jpg"
labelPath = "F:/imageClip/imgSpace/label/q_128_2_0.txt"
img = cv2.imdecode(np.fromfile(filePath, np.uint8), -1)
# shape返回的是一个tuple元组，第一个元素表示图像的高度，第二个表示图像的宽度，第三个表示像素的通道数。
# size = img.shape
# print(size)  # (1728, 3072, 3)

with open(labelPath, "r") as f:
    data = f.readlines()
    for line in data:
        line = line.strip('\n')
        # print(line)
        items = line.split(" ")
        name = items[0]

        # 多边形
        show_pts = np.array([[float(items[1]), float(items[2])], [float(items[3]), float(items[4])], [float(items[5]), float(items[6])], [float(items[7]), float(items[8])]],
                       np.int32)
        pts = show_pts.reshape(-1, 1, 2)
        cv2.polylines(img, [pts], isClosed=True, color=(0, 0, 255), thickness=15)

        # 文字
        # font = cv2.FONT_HERSHEY_SIMPLEX
        # cv2.putText(img, name, (math.ceil(float(items[1])), math.ceil(float(items[2]))), font, 2, (255, 255, 0), 2, cv2.LINE_AA)

        # img = paint_chinese_opencv(img, name, (math.ceil(float(items[1]))+2, math.ceil(float(items[2]))+3), 20, (255, 0, 0))
cv2.namedWindow("show", 0)
cv2.imshow("show", img)
if cv2.waitKey(0) & 0xFF == ord('q'):
    cv2.destroyAllWindows()


# cv2.imencode('.jpg', img)[1].tofile("/home/orange/MytestPace/show/0.jpg")

