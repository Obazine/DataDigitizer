from flask import Flask, request, redirect, url_for, render_template
import os
from matplotlib.pyplot import axes
from program import testFunc, testFunc2
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
axesValues = []
axesList = []

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
    axesInfo = request.data
    axesInfo = axesInfo.decode()
    axesList = axesInfo.strip('][').split(',')
    print(axesList)
    return render_template("index.html")

@app.route('/handle_data', methods =["GET", "POST"])
def handle_data():
    axesValues.append(request.form.get("minX"))
    axesValues.append(request.form.get("maxX"))
    axesValues.append(request.form.get("minY"))
    axesValues.append(request.form.get("maxY"))
    print(axesValues)
    return render_template("index.html")

@app.route('/get_point', methods=['GET', 'POST'])
def get_point():
    pointInfo = request.data.decode()
    print(pointInfo)
    calculatePointvalue(pointInfo)
    return render_template("index.html")

def calculatePointvalue(pointAxes):
    pointAxes = pointAxes.strip('[')
    pointAxes = pointAxes.strip(']')
    pointData = pointAxes.split(',')
    pointX = pointData[0]
    pointY = pointData[1]
    print(pointX)
    print(pointY)