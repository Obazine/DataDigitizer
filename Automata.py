import cv2
import numpy as np
import os

def GetAutoPoint(filename, dataset):
    img = cv2.imread(filename)
    dimensions = img.shape
    maxY = dimensions[0]
    maxX = dimensions[1]
    print(dimensions)
    #cv2.imshow('img.jpg',img)
    gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
    #cv2.imshow('gray.jpg',gray)

    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
    #cv2.imshow('hsv.jpg', hsv)

    h, s, v = cv2.split(hsv)
    ret,th = cv2.threshold(s,127,255, 0)
    #cv2.imshow('th.jpg', th)

    lines = cv2.HoughLinesP(th,1,np.pi/180,100,minLineLength=100,maxLineGap=10)

    x1,y1,x2,y2 = lines[0][0]
    cv2.line(img,(x1,y1),(x2,y2),(0,255,0),2)

    #cv2.imshow('HoughLines.jpg',img)
    cv2.imwrite(os.path.join('static/uploads/' , 'HoughLines.jpg'), img)

    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    percentXStart = (x1/maxX)
    percentYStart = (y1/maxY)
    percentXEnd = (x2/maxX)
    percentYEnd = (y2/maxY)
    return [percentXStart, percentYStart, percentXEnd, percentYEnd]