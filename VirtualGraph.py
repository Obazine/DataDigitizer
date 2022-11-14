import cv2 as cv2
import numpy as np
from matplotlib import pyplot as plt

class VGraph:
    def __init__(self,):
        self.__axesValues = []
        self.__axesList = []
        self.__realDataValues = []

    def __str__(self):
        return f"Min-x :{self.__axesList[0]}, Max-x :{self.__axesList[1]}, Min-y: {self.__axesList[2]}, Max-Y: {self.__axesList[3]}, \n ({self.__realDataValues})"

    def Reset(self):
        self.__axesValues = []
        self.__axesList = []
        self.__realDataValues = []

    def SetAxesList(self, inputList):
        self.__axesList = [int(item) for item in inputList]

    def AddAxesValue(self, axesValue: str):
        self.__axesValues.append(int(axesValue))

    def CalculatePointvalue(self, pointAxes: str):
        pointData = pointAxes.strip('][').split(',')
        pointX = int(pointData[0])
        pointY = int(pointData[1])
        calculatedXValue = round((pointX - self.__axesList[0])/(self.__axesList[2] - self.__axesList[0]) * (self.__axesValues[1] - self.__axesValues[0]) - self.__axesValues[0], 3)
        calculatedYValue = round((pointY - self.__axesList[5])/(self.__axesList[7] - self.__axesList[5]) * (self.__axesValues[3] - self.__axesValues[2]) - self.__axesValues[2], 3)
        tempArray = [calculatedXValue, calculatedYValue]
        self.__realDataValues.append(tempArray)