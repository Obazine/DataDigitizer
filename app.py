from flask import Flask, request, redirect, url_for, render_template
import os
from matplotlib.pyplot import axes
from VirtualGraph import VGraph
from werkzeug.utils import secure_filename
import re

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
vGraph = VGraph()

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

@app.route('/axes_calibration', methods=['GET', 'POST'])
def axes_calibration():
    axesInfo = request.data.decode()
    axesInfo = re.sub(r'\[', '', re.sub(']', '', axesInfo)).split(',')
    vGraph.SetAxesList(axesInfo)
    return render_template("index.html")

@app.route('/data_calibration', methods =["GET", "POST"])
def data_calibration():
    vGraph.AddAxesValue(request.form.get("minX"))
    vGraph.AddAxesValue(request.form.get("maxX"))
    vGraph.AddAxesValue(request.form.get("minY"))
    vGraph.AddAxesValue(request.form.get("maxY"))
    return render_template("index.html")

@app.route('/get_point', methods=['GET', 'POST'])
def get_point():
    pointInfo = request.data.decode()
    vGraph.CalculatePointvalue(pointInfo)
    print(vGraph)
    return render_template("index.html")
