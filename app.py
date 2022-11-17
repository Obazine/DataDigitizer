from flask import Flask, request, redirect, url_for, render_template, send_file, session, flash
from werkzeug.utils import secure_filename
import re
import os
from pymongo import MongoClient
import csv
from dotenv import load_dotenv
import uuid
import boto3
import glob

load_dotenv()

def create_app():
    app = Flask(__name__)
    s3 = boto3.client('s3',
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    BUCKET_NAME = "datadigitizer-images"
    client = MongoClient(os.environ.get("MONGODB_URI"))
    app.db = client.datadigitizer
    UPLOAD_FOLDER = 'static/uploads/'
    app.secret_key = "secret key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    @app.route('/')
    def home():
        if not session.get("email"):
            session["email"] = None
        session["unique-session-id"] = uuid.uuid4().hex
        return render_template("index.html", filename=session.get("filename"), email=session.get("email"))

    @app.route('/help')
    def help():
        return render_template("help.html")

    @app.route('/upload_image', methods=['POST'])
    def upload_image(): 
        app.db.axescoords.delete_many({"user-id": None, "unique-session-id": session["unique-session-id"]})
        app.db.images.delete_many({"user-id": None, "unique-session-id": session["unique-session-id"]})
        app.db.axesvalues.delete_many({"user-id": None, "unique-session-id": session["unique-session-id"]})
        app.db.realdatavalues.delete_many({"user-id": None, "unique-session-id": session["unique-session-id"],})
        files = glob.glob('static/uploads/*')
        for f in files:
            os.remove(f)
        if request.method == 'POST':
            img = request.files['file']
        if img:
                filename = secure_filename(img.filename)
                filename = uuid.uuid4().hex
                img.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                s3.upload_file(
                    Bucket = BUCKET_NAME,
                    Filename=os.path.join(app.config['UPLOAD_FOLDER'], filename),
                    Key=filename
                )
                app.db.images.insert_one({"user-id": session["email"], "unique-session-id": session["unique-session-id"], "filename": filename})
                session["filename"] = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                #s3.download_file(Bucket=BUCKET_NAME, Key=filename, Filename=os.path.join(app.config['UPLOAD_FOLDER'], filename))
        return render_template('index.html', filename=session.get("filename"), email=session.get("email"))

    @app.route('/display/<filename>')
    def display_image(filename):
        return redirect(url_for('static', filename='uploads/' + filename), code=301)

    @app.route('/axes_calibration', methods=['GET', 'POST'])
    def axes_calibration():
        axesInfo = request.data.decode()
        axesInfo = re.sub(r'\[', '', re.sub(']', '', axesInfo)).split(',')
        app.db.axescoords.insert_one({"user-id": session["email"], "unique-session-id": session["unique-session-id"], "min-x-coord": int(axesInfo[0]), "max-x-coord": int(axesInfo[2]), "min-y-coord": int(axesInfo[5]), "max-y-coord": int(axesInfo[7])})
        return render_template("index.html")

    @app.route('/data_calibration', methods =["GET", "POST"])
    def data_calibration():
        app.db.axesvalues.insert_one({"user-id": session["email"], "unique-session-id": session["unique-session-id"], "min-x": int(request.form.get("minX")), "max-x": int(request.form.get("maxX")), "min-y": int(request.form.get("minY")), "max-y": int(request.form.get("maxY"))})
        return render_template("index.html")

    @app.route('/get_point', methods=['GET', 'POST'])
    def get_point():
        pointInfo = request.data.decode()
        tempArray = CalculatePointvalue(pointInfo)
        app.db.realdatavalues.insert_one({"user-id": session["email"], "unique-session-id": session["unique-session-id"], "X": tempArray[0], "Y": tempArray[1]})
        return render_template("index.html")

    @app.route('/download')
    def download_file():
        ExportToCSV()
        path = "graph.csv"
        return send_file(path, as_attachment = True)

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method =="POST":
            email = request.form.get("email")
            password = request.form.get("password")

            user = app.db.users.find_one({"email": email})
            print(user)
            if user["password"] == password:
                session["email"] = email
                return redirect(url_for("home"))
            flash("Incorrect e-mail or password.")
        return render_template("login.html")

    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == "POST":
            email = request.form.get("email")
            password = request.form.get("password")
            if app.db.users.count_documents({"email": email}):
                print("Error: You are already in the database")
            else:
                app.db.users.insert_one({"user-id": email, "password": password})
                flash("Successfully signed up.")
                return redirect(url_for("login"))
        return render_template("signup.html")

    @app.route('/signout')
    def signout():
        session.clear()
        return redirect(url_for("home"))

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
    