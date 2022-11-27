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
from passlib.hash import pbkdf2_sha256
from autoextract import autoFind

load_dotenv()

def create_app():
    app = Flask(__name__)
    s3 = boto3.client('s3',
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
    )
    BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME")
    client = MongoClient(os.environ.get("MONGODB_URI"))
    app.db = client.datadigitizer
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
    app.secret_key = "secret key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

    #The initial root that is directed to when the app starts. If a user is not logged on, then email and dataset-name is set to "temp". 
    #If both are still temp when user starts new image, previous data will be deleted on the database.
    @app.route('/')
    def home():
        #DatabaseReset()
        if not session.get("email"):
            session["email"] = "temp"
        if not session.get("dataset-name"):
            session["dataset-name"] = "temp"
        dataset_list = app.db.datasets.find({"user-id": session["email"]})
        dataset_name_list = []
        for dataset in dataset_list:
            dataset_name_list.append(dataset["dataset-name"])
        print(dataset_name_list)
        return render_template("index.html", filename=session.get("image-path"), email=session.get("email"), dataset_list=dataset_name_list, dataset_name=session["dataset-name"])

    #Directs user to the help page
    @app.route('/help')
    def help():
        return render_template("help.html")

    #The function is called when user tries to upload new image
    #All temp data is deleted from the dataset and local storage is also cleared
    #A unique filename is generated so that it can be stored in the databse
    #Current image is downloaded to the uploads folder so that the html file can display the newly uploaded image
    @app.route('/upload_image', methods=['POST'])
    def upload_image(): 
        if session.get("image-name") and session["dataset-name"] == "temp":
            s3.delete_object(Bucket=BUCKET_NAME, Key=session["image-name"])
            app.db.datasets.delete_many({"filename": session["image-name"]})
            os.remove(os.path.join(app.config['UPLOAD_FOLDER'], session["image-name"]))
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
                if session.get("dataset-name") == "temp":
                    app.db.datasets.insert_one({"user-id": session["email"], "dataset-name": session["dataset-name"], "filename": filename, "min-x-coord": None, "max-x-coord": None, "min-y-coord": None, "max-y-coord": None, "min-x-val": None, "max-x-val": None, "min-y-val": None, "max-y-val": None, "X": [], "Y": []})
                else:
                    app.db.datasets.update_one({"user-id": session["email"], "dataset-name": session["dataset-name"]}, {"$set" : {"filename" : filename}})
                session["image-name"] = filename
        return redirect(url_for("home"))

    #Modifies the src route to image on html file
    @app.route('/display/<filename>')
    def display_image(filename):
        return redirect(url_for('static', filename='uploads/' + filename), code=301)

    #Called when user clicks axes calibration
    #Mouse click coordinates are stored in an array, and these values are stored in a collection on the database
    @app.route('/axes_calibration', methods=['GET', 'POST'])
    def axes_calibration():
        axesInfo = request.data.decode()
        axesInfo = re.sub(r'\[', '', re.sub(']', '', axesInfo)).split(',')
        app.db.datasets.update_one({"user-id": session["email"], "filename": session["image-name"]}, {"$set": { "min-x-coord": int(axesInfo[0]), "max-x-coord": int(axesInfo[2]), "min-y-coord": int(axesInfo[5]), "max-y-coord": int(axesInfo[7])}})
        return redirect(url_for("home"))

    #Called after axes calibration
    #Axes values are stored in an array from a form input and is stored in another collection on the database
    @app.route('/data_calibration', methods =["GET", "POST"])
    def data_calibration():
        app.db.datasets.update_one({"filename": session["image-name"]},{"$set": { "min-x-val": int(request.form.get("minX")), "max-x-val": int(request.form.get("maxX")), "min-y-val": int(request.form.get("minY")), "max-y-val": int(request.form.get("maxY"))} })
        return redirect(url_for("home"))

    #Called everytime user clicks on screen after set up
    #Each point is stored as a record in a database
    @app.route('/get_point', methods=['GET', 'POST'])
    def get_point():
        pointInfo = request.data.decode()
        tempArray = CalculatePointvalue(pointInfo)
        app.db.datasets.update_one({"filename": session["image-name"]}, {"$push": {"X": tempArray[0]}})
        app.db.datasets.update_one({"filename": session["image-name"]}, {"$push": {"Y": tempArray[1]}})
        return redirect(url_for("home"))

    #Called when user clicks export databse, ExportTOCSV function is called and sends path to the site
    @app.route('/download')
    def download_file():
        ExportToCSV()
        path = "graph.csv"
        return send_file(path, as_attachment = True)

    #Email and password is obtained from a form input
    #If an image is already present, the user-id is changed from temp to the user's email
    #Session email is updated and user is redirected to home
    @app.route('/login', methods=['GET', 'POST'])
    def login():
        if request.method =="POST":
            email = request.form.get("email")
            password = request.form.get("password")

            user = app.db.users.find_one({"user-id": email})
            if user is None:
                flash("Incorrect e-mail or password.")
            elif pbkdf2_sha256.verify(password, user["password"]):
                session["email"] = email
                if(session.get("image-name")):
                    app.db.datasets.update_one({"filename": session["image-name"]}, { "$set": { "user-id": email }})
                return redirect(url_for("home"))
            else:
                flash("Incorrect e-mail or password.")
        return render_template("login.html")

    #Similar to login, just adds the user information into a collection in the database
    @app.route('/signup', methods=['GET', 'POST'])
    def signup():
        if request.method == "POST":
            email = request.form.get("email")
            password = pbkdf2_sha256.hash(request.form.get("password"))
            if app.db.users.count_documents({"user-id": email}):
                flash("Error: This account already exists")
            else:
                app.db.users.insert_one({"user-id": email, "password": password})
                session["email"] = email
                if(session.get("image-name")):
                    app.db.datasets.update_one({"filename": session["image-name"]}, { "$set": { "user-id": email }})
                return redirect(url_for("home"))
        return render_template("signup.html")

    #Clears session data for the user
    @app.route('/signout')
    def signout():
        session.clear()
        return redirect(url_for("home"))

    #A form input gets the user's dataset name
    #If an image already exists, the dataset name is changed from temp to the name specified by the user
    @app.route('/create_dataset', methods=['GET', 'POST'])
    def create_dataset():
        datasetname = request.form.get("datasetName")
        if app.db.datasets.count_documents({"dataset-name": datasetname}):
            print("a database with the same name already exists")
        else:
            if session["email"] == "temp":
                s3.delete_object(Bucket=BUCKET_NAME, Key=session["image-name"])
            session["dataset-name"] = datasetname
            app.db.datasets.insert_one({"user-id": session["email"], "dataset-name": session["dataset-name"], "filename": None, "min-x-coord": None, "max-x-coord": None, "min-y-coord": None, "max-y-coord": None, "min-x-val": None, "max-x-val": None, "min-y-val": None, "max-y-val": None, "X": [], "Y": []})
            session["image-name"] = None
        return redirect(url_for("home"))

    @app.route('/select_dataset', methods=['GET', 'POST'])
    def select_dataset():
        datasetname = request.form.get("dataset")
        session["dataset-name"] = str(datasetname)
        selectedDataset = app.db.datasets.find_one({"dataset-name": session["dataset-name"]})
        if selectedDataset["filename"] is not None:
            s3.download_file(Bucket=BUCKET_NAME, Key=selectedDataset["filename"], Filename=os.path.join(app.config['UPLOAD_FOLDER'], selectedDataset["filename"]))
            session["image-name"] = selectedDataset["filename"]
        return redirect(url_for("home"))

    @app.route('/delete_dataset', methods=['GET', 'POST'])
    def delete_dataset():
        datasetname = request.form.get("dataset")
        deleteDataset = app.db.datasets.find_one({"user-id": session["email"], "dataset-name": str(datasetname)})
        s3.delete_object(Bucket=BUCKET_NAME, Key=deleteDataset["filename"])
        app.db.datasets.delete_one({"user-id": session["email"], "dataset-name": str(datasetname)})
        if app.db.datasets.count_documents({"user-id": session["email"]}):
            tempdataset = app.db.datasets.find_one({"user-id": session["email"]})
            session["dataset-name"] = tempdataset["dataset-name"]
            session["image-name"] = tempdataset["filename"]
        else:
            session["dataset-name"] = "temp"
        return redirect(url_for("home"))

    @app.route('/auto_extract', methods=['GET', 'POST'])
    def auto_extract():
        linecolour = request.form.get("graph-colour")
        file = app.db.datasets.find_one({"filename": session["image-name"]})
        if file["min-x-val"] is not None:
            autoFind(linecolour, os.path.join(app.config['UPLOAD_FOLDER'], session["image-name"]), file)
            path = "graph.csv"
            return send_file(path, as_attachment = True)
        else:
            return redirect(url_for("home"))

    #Function used to get the real data value of a point selected by the user, returns the xy values as array
    #Fields are filtered using the unique-session-id and dataset-name
    def CalculatePointvalue(pointAxes: str):
        datasetEntry = app.db.datasets.find_one({"filename": session["image-name"]})
        pointData = pointAxes.strip('][').split(',')
        pointX = int(pointData[0])
        pointY = int(pointData[1])
        calculatedXValue = round((pointX - datasetEntry["min-x-coord"])/(datasetEntry["max-x-coord"] - datasetEntry["min-x-coord"]) * (datasetEntry["max-x-val"] - datasetEntry["min-x-val"]) + datasetEntry["min-x-val"], 3)
        calculatedYValue = round((pointY - datasetEntry["min-y-coord"])/(datasetEntry["max-y-coord"] - datasetEntry["min-y-coord"]) * (datasetEntry["max-y-val"] - datasetEntry["min-y-val"]) + datasetEntry["min-y-val"], 3)
        tempArray = [calculatedXValue, calculatedYValue]
        return(tempArray)
    
    #Function to create a CSV file with all the xy points
    def ExportToCSV():
        graphHeader = ['X', 'Y']
        file = open('graph.csv', 'w', newline='')
        writer = csv.writer(file)
        writer.writerow(graphHeader)
        graphData = app.db.datasets.find_one({"filename": session["image-name"]})
        for i in range(0, len(graphData["X"])):
            writer.writerow([graphData["X"][i],graphData["Y"][i]])
        file.close()

    def DatabaseReset():
        session.clear()
        app.db.datasets.delete_many({})
        app.db.users.delete_many({})

    return app
    