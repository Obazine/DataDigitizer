import cv2
import numpy as np
import csv
import re

def autoFind(colour, imagePath, datasetEntry, threshold):
    r = int(colour[1:3], 16)
    g = int(colour[3:5], 16)
    b = int(colour[5:7], 16)
    image = cv2.imread(imagePath)
    dimensions = image.shape
    containerX = 772.8
    containerY = 581.25
    resizeFactor = 1
    if(dimensions[0] > containerY or dimensions[1] > containerX):
        resizeFactorX = containerX / dimensions[1]
        resizeFactorY = containerY / dimensions[0]
        resizeFactor = min(resizeFactorX, resizeFactorY)
    lower = np.array([b-threshold,g-threshold,r-threshold])  
    upper = np.array([b+threshold,g+threshold,r+threshold]) 
    mask = cv2.inRange(image, lower, upper)  
    coords=cv2.findNonZero(mask)
    pointsArray = []
    for coord in coords:
        coord = re.sub(r'\[', '', re.sub(']', '', str(coord))).split(" ")
        coord = filter(None, coord)
        try:
            point = list(map(int, coord))
            pointsArray.append([round(float((point[0]*resizeFactor - datasetEntry["min-x-coord"])/(datasetEntry["max-x-coord"] - datasetEntry["min-x-coord"]) * (datasetEntry["max-x-val"] - datasetEntry["min-x-val"]) + datasetEntry["min-x-val"]), datasetEntry["dp-val"]), round(float((point[1]*resizeFactor - datasetEntry["min-y-coord"])/(datasetEntry["max-y-coord"] - datasetEntry["min-y-coord"]) * (datasetEntry["max-y-val"] - datasetEntry["min-y-val"]) + datasetEntry["min-y-val"]), datasetEntry["dp-val"])])
        except:
            break
    graphHeader = [datasetEntry["x-label"], datasetEntry["y-label"]]
    file = open('graph.csv', 'w', newline='')
    writer = csv.writer(file)
    writer.writerow(graphHeader)
    for i in range(0, len(pointsArray)):
        writer.writerow([pointsArray[i][0],pointsArray[i][1]])
    file.close()

