from flask import Flask, request, redirect, url_for, render_template
import os
from matplotlib.pyplot import axes
from program import testFunc, testFunc2
from werkzeug.utils import secure_filename

app = Flask(__name__)

UPLOAD_FOLDER = 'static/uploads/'
app.secret_key = "secret key"
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def array(list):
    string = ""
    for x in list:
        string+= x
    return string

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
