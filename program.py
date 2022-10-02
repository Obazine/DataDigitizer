import cv2 as cv
import numpy as np
from matplotlib import pyplot as plt

img = cv.imread(r"C:\Users\Lian\Downloads\pict1_graph.C.png",0)
img = cv.medianBlur(img,5)
th3 = cv.adaptiveThreshold(img,255,cv.ADAPTIVE_THRESH_GAUSSIAN_C,\
            cv.THRESH_BINARY,11,2)
image = th3
plt.imshow(image,'gray')
plt.xticks([]),plt.yticks([])
plt.show()
