# -------------------------------------------------------------------------------
# Name:        多边形面积计算
# -------------------------------------------------------------------------------
import math

class Point():
    def __init__(self, x, y):
        self.x = x
        self.y = y


class Line():
    def __init__(self, point1, point2):
        self.point1 = point1
        self.point2 = point2


class Square():
    def __init__(self, left_top, length):
        self.left_top = left_top
        self.length = length

class Rectangle():
    def __init__(self, left_top, width, height):
        self.left_top = left_top
        self.width = width
        self.height = height


def GetAreaOfPolyGon(points):
    '''计算多边形面积值
    points:多边形的点集，每个点为Point类型
    返回：多边形面积'''
    area = 0
    if (len(points) < 3):
        raise Exception("至少需要3个点才有面积")
    p1 = points[0]
    for i in range(1, len(points) - 1):
        p2 = points[1]
        p3 = points[2]
        # 计算向量
        vecp1p2 = Point(p2.x - p1.x, p2.y - p1.y)
        vecp2p3 = Point(p3.x - p2.x, p3.y - p2.y)
        # 判断顺时针还是逆时针，顺时针面积为正，逆时针面积为负
        vecMult = vecp1p2.x * vecp2p3.y - vecp1p2.y * vecp2p3.x

        sign = 0
        if (vecMult > 0):
            sign = 1
        elif (vecMult < 0):
            sign = -1

        triArea = GetAreaOfTriangle(p1, p2, p3) * sign
        area += triArea

    return abs(area)


def GetAreaOfTriangle(p1, p2, p3):
    '''计算三角形面积'''
    area = 0
    p1p2 = GetLineLength(p1, p2)
    p2p3 = GetLineLength(p2, p3)
    p3p1 = GetLineLength(p3, p1)
    s = (p1p2 + p2p3 + p3p1) / 2
    area = s * (s - p1p2) * (s - p2p3) * (s - p3p1)
    area = math.sqrt(area)
    return area


def GetLineLength(p1, p2):
    '''计算边长'''
    length = math.pow((p1.x - p2.x), 2) + math.pow((p1.y - p2.y), 2)
    length = math.sqrt(length)
    return length


def isInPolygon(points, rectangle):
    count = 0
    for point in points:
        if rectangle.left_top.x <= point.x <= rectangle.left_top.x + rectangle.width and rectangle.left_top.y <= point.y <= rectangle.left_top.y - rectangle.height:
            count = count + 1
    return count == len(points)