from flask import Flask, request, redirect, url_for, render_template, send_file
from werkzeug.utils import secure_filename
import re
import os
from pymongo import MongoClient
import csv
from dotenv import load_dotenv
import glob

load_dotenv()

def create_app():
    app = Flask(__name__)
    client = MongoClient(os.environ.get("MONGODB_URI"))
    app.db = client.datadigitizer
    UPLOAD_FOLDER = 'static/uploads/'
    app.secret_key = "secret key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route('/')
    def home():
        return render_template("index.html")

    @app.route('/', methods=['POST'])
    def upload_image(): 
        files = glob.glob('static/uploads/*')
        for f in files:
            os.remove(f)
        file = request.files['file']
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
        app.db.axescoords.delete_many({})
        app.db.axesvalues.delete_many({})
        app.db.realdatavalues.delete_many({})
        return render_template('index.html', filename=filename)

    @app.route('/display/<filename>')
    def display_image(filename):
        return redirect(url_for('static', filename='uploads/' + filename), code=301)

    @app.route('/axes_calibration', methods=['GET', 'POST'])
    def axes_calibration():
        axesInfo = request.data.decode()
        axesInfo = re.sub(r'\[', '', re.sub(']', '', axesInfo)).split(',')
        app.db.axescoords.insert_one({"min-x-coord": int(axesInfo[0]), "max-x-coord": int(axesInfo[2]), "min-y-coord": int(axesInfo[5]), "max-y-coord": int(axesInfo[7])})
        return render_template("index.html")

    @app.route('/data_calibration', methods =["GET", "POST"])
    def data_calibration():
        app.db.axesvalues.insert_one({"min-x": int(request.form.get("minX")), "max-x": int(request.form.get("maxX")), "min-y": int(request.form.get("minY")), "max-y": int(request.form.get("maxY"))})
        return render_template("index.html")

    @app.route('/get_point', methods=['GET', 'POST'])
    def get_point():
        pointInfo = request.data.decode()
        tempArray = CalculatePointvalue(pointInfo)
        app.db.realdatavalues.insert_one({"X": tempArray[0], "Y": tempArray[1]})
        return render_template("index.html")

    @app.route('/download')
    def download_file():
        ExportToCSV()
        path = "graph.csv"
        return send_file(path, as_attachment = True)

    def CalculatePointvalue(pointAxes: str):
        axesCoordEntry = app.db.axescoords.find_one({})
        axesValueEntry = app.db.axesvalues.find_one({})
        pointData = pointAxes.strip('][').split(',')
        pointX = int(pointData[0])
        pointY = int(pointData[1])
        calculatedXValue = round((pointX - axesCoordEntry["min-x-coord"])/(axesCoordEntry["max-x-coord"] - axesCoordEntry["min-x-coord"]) * (axesValueEntry["max-x"] - axesValueEntry["min-x"]) - axesValueEntry["min-x"], 3)
        calculatedYValue = round((pointY - axesCoordEntry["min-y-coord"])/(axesCoordEntry["max-y-coord"] - axesCoordEntry["min-y-coord"]) * (axesValueEntry["max-y"] - axesValueEntry["min-y"]) - axesValueEntry["min-y"], 3)
        tempArray = [calculatedXValue, calculatedYValue]
        return(tempArray)

    def ExportToCSV():
        graphHeader = ['X', 'Y']
        file = open('graph.csv', 'w', newline='')
        writer = csv.writer(file)
        writer.writerow(graphHeader)
        for graphData in app.db.realdatavalues.find({}):
            writer.writerow([graphData["X"],graphData["Y"]])
        file.close()

    return app
    