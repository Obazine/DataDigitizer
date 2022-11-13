from flask import Flask, request, redirect, url_for, render_template
import os
from matplotlib.pyplot import axes
from program import testFunc, testFunc2
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
axesValues = []
axesList = []
RealDataValues = []

@app.route('/')
def home():
    return render_template("index.html")

@app.route('/', methods=['POST'])
def upload_image():
    file = request.files['file']
    filename = secure_filename(file.filename)
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    return render_template('index.html', filename=filename)

@app.route('/display/<filename>')
def display_image(filename):
    return redirect(url_for('static', filename='uploads/' + filename), code=301)

@app.route('/get-coordinates', methods=['GET', 'POST'])
def thisRoute():
    global axesList
    axesInfo = request.data.decode()
    axesList = re.sub(']', '', axesInfo)
    axesList = re.sub(r'\[', '', axesList).split(',')
    return render_template("index.html")

@app.route('/handle_data', methods =["GET", "POST"])
def handle_data():
    global axesValues
    axesValues.append(request.form.get("minX"))
    axesValues.append(request.form.get("maxX"))
    axesValues.append(request.form.get("minY"))
    axesValues.append(request.form.get("maxY"))
    return render_template("index.html")

@app.route('/get_point', methods=['GET', 'POST'])
def get_point():
    global RealDataValues
    pointInfo = request.data.decode()
    print(pointInfo)
    RealDataValues.append(calculatePointvalue(pointInfo))
    print(RealDataValues)
    return render_template("index.html")

def calculatePointvalue(pointAxes):
    pointData = pointAxes.strip('][').split(',')
    pointX = int(pointData[0])
    pointY = int(pointData[1])
    calculatedXValue = round((pointX - int(axesList[0]))/(int(axesList[2]) - int(axesList[0])) * (int(axesValues[1]) - int(axesValues[0])) - int(axesValues[0]), 3)
    calculatedYValue = round((pointY - int(axesList[5]))/(int(axesList[7]) - int(axesList[5])) * (int(axesValues[3]) - int(axesValues[2])) - int(axesValues[2]), 3)
    tempArray = [calculatedXValue, calculatedYValue]
    return tempArray