import cv2
import numpy as np
import os
import csv
import uuid

def GetAutoPoint(filename, datasetEntry):
    maxxcoord = 773
    maxycoord = 610
    img = cv2.imread(filename)
    dimensions = img.shape
    maxY = dimensions[0]
    maxX = dimensions[1]
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
    cv2.imwrite(os.path.join(os.environ.get("UPLOAD_FOLDER") , f"{uuid.uuid4().hex}.jpg"), img)
    #cv2.waitKey(0)
    #cv2.destroyAllWindows()
    xStartValue = (((x1/maxX) * maxxcoord) - datasetEntry["min-x-coord"])/(datasetEntry["max-x-coord"] - datasetEntry["min-x-coord"]) * (datasetEntry["max-x-val"] - datasetEntry["min-x-val"]) - datasetEntry["min-x-val"]
    yStartValue = (((y1/maxY) * maxycoord) - datasetEntry["min-y-coord"])/(datasetEntry["max-y-coord"] - datasetEntry["min-y-coord"]) * (datasetEntry["max-y-val"] - datasetEntry["min-y-val"]) - datasetEntry["min-y-val"]
    xEndValue = (((x2/maxX) * maxxcoord) - datasetEntry["min-x-coord"])/(datasetEntry["max-x-coord"] - datasetEntry["min-x-coord"]) * (datasetEntry["max-x-val"] - datasetEntry["min-x-val"]) - datasetEntry["min-x-val"]
    yEndValue = (((y2/maxY) * maxycoord) - datasetEntry["min-y-coord"])/(datasetEntry["max-y-coord"] - datasetEntry["min-y-coord"]) * (datasetEntry["max-y-val"] - datasetEntry["min-y-val"]) - datasetEntry["min-y-val"]
    gradient = (yEndValue-yStartValue)/(xEndValue-xStartValue)
    pointsArray = []
    for i in range(0,21):
        pointsArray.append([round((xStartValue + i * ((xEndValue - xStartValue)/20)),3), round((yStartValue + i * ((yEndValue - yStartValue)/20) * gradient),3)])
    graphHeader = ['X', 'Y']
    file = open('graph.csv', 'w', newline='')
    writer = csv.writer(file)
    writer.writerow(graphHeader)
    for i in range(0, len(pointsArray)):
        writer.writerow([pointsArray[i][0],pointsArray[i][1]])
    file.close()