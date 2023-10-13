from flask import Flask, request, redirect, url_for, render_template, send_file, session, flash
from werkzeug.utils import secure_filename
import re
import os
from pymongo import MongoClient
import csv
from dotenv import load_dotenv
import uuid
import boto3
from botocore.client import Config
from passlib.hash import pbkdf2_sha256
from autoextract import autoFind
import glob   
from flask_mail import Mail, Message
import jwt
from time import time
from threading import Thread

load_dotenv()

def create_app():
    app = Flask(__name__)
    s3 = boto3.client('s3',
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version='s3v4'),
        region_name='eu-west-2'
    )
    BUCKET_NAME = os.environ.get("AWS_BUCKET_NAME")
    client = MongoClient(os.environ.get("MONGODB_URI"))
    app.db = client.datadigitizer
    UPLOAD_FOLDER = os.environ.get("UPLOAD_FOLDER")
    app.secret_key = "secret key"
    app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
    app.config['MAIL_SERVER']='smtp.gmail.com'
    app.config['MAIL_PORT'] = 465
    app.config['MAIL_USERNAME'] = os.environ.get("MAIL_USERNAME")
    app.config['MAIL_PASSWORD'] = os.environ.get("APP_PASSWORD")
    app.config['MAIL_USE_TLS'] = False
    app.config['MAIL_USE_SSL'] = True
    mail = Mail(app)

    #The initial root that is directed to when the app starts. If a user is not logged on, then email and dataset-name is set to "temp". 
    #If both are still temp when user starts new image, previous data will be deleted on the database.
    @app.route('/')
    def home():
        #DatabaseReset()
        
        axescallibrated = False
        if not session.get("email"):
            session["email"] = "temp"
        if not session.get("dataset-name"):
            session["dataset-name"] = "temp"
        if session.get("image-name"):
            filename = create_presigned_url(BUCKET_NAME, session["image-name"])
            dataset = app.db.datasets.find_one({"filename": session["image-name"]})
            if dataset["max-y-val"] is not None:
                axescallibrated = True
        else:
            filename=''
        dataset_list = app.db.datasets.find({"user-id": session["email"]})
        dataset_name_list = []
        for dataset in dataset_list:
            if dataset["dataset-name"] != "temp":
                dataset_name_list.append(dataset["dataset-name"])
        print(dataset_name_list)
        return render_template("index.html", filename=filename, email=session.get("email"), dataset_list=dataset_name_list, dataset_name=session["dataset-name"], axescallibrated=axescallibrated, title="Home")

    #Directs user to the help page
    @app.route('/help')
    def help():
        return render_template("help.html", email=session.get("email"),  title="Help")

    #The function is called when user tries to upload new image
    #All temp data is deleted from the dataset and local storage is also cleared
    #A unique filename is generated so that it can be stored in the databse
    #Current image is downloaded to the uploads folder so that the html file can display the newly uploaded image
    @app.route('/upload_image', methods=['POST'])
    def upload_image(): 
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
                if session.get("image-name") and (session["dataset-name"] == "temp"):
                    s3.delete_object(Bucket=BUCKET_NAME, Key=session["image-name"])
                    app.db.datasets.delete_many({"filename": session["image-name"]})
                    app.db.datasets.insert_one({"user-id": session["email"], "dataset-name": session["dataset-name"], "filename": filename, "x-label": "X", "y-label": "Y", "dp-val": 3, "min-x-coord": None, "max-x-coord": None, "min-y-coord": None, "max-y-coord": None, "min-x-val": None, "max-x-val": None, "min-y-val": None, "max-y-val": None, "X": [], "Y": []})
                if not session.get("image-name"):
                    app.db.datasets.insert_one({"user-id": session["email"], "dataset-name": session["dataset-name"], "filename": filename, "x-label": "X", "y-label": "Y", "dp-val": 3, "min-x-coord": None, "max-x-coord": None, "min-y-coord": None, "max-y-coord": None, "min-x-val": None, "max-x-val": None, "min-y-val": None, "max-y-val": None, "X": [], "Y": []})
                app.db.datasets.update_one({"user-id": session["email"], "dataset-name": session["dataset-name"]}, {"$set": { "filename": filename }})
                session["image-name"] = filename
                files = glob.glob('static/uploads/*')
                for f in files:
                    os.remove(f)
        return redirect(url_for("home"))

    #Called when user clicks axes calibration
    #Mouse click coordinates are stored in an array, and these values are stored in a collection on the database
    @app.route('/axes_calibration', methods=['GET', 'POST'])
    def axes_calibration():
        axes_info = request.data.decode()
        axes_info = re.sub(r'\[', '', re.sub(']', '', axes_info)).split(',')
        app.db.datasets.update_one({"user-id": session["email"], "filename": session["image-name"]}, {"$set": { "min-x-coord": float(axes_info[0]), "max-x-coord": float(axes_info[2]), "min-y-coord": float(axes_info[5]), "max-y-coord": float(axes_info[7])}})
        return redirect(url_for("home"))

    #Called after axes calibration
    #Axes values are stored in an array from a form input and is stored in another collection on the database
    @app.route('/data_calibration', methods =["GET", "POST"])
    def data_calibration():
        app.db.datasets.update_one({"filename": session["image-name"]},{"$set": { "min-x-val": float(request.form.get("minX")), "max-x-val": float(request.form.get("maxX")), "min-y-val": float(request.form.get("minY")), "max-y-val": float(request.form.get("maxY"))} })
        return redirect(url_for("home"))

    #Called everytime user clicks on screen after set up
    #Each point is stored as a record in a database
    @app.route('/get_point', methods=['GET', 'POST'])
    def get_point():
        point_info = request.data.decode()
        temp_array = CalculatePointvalue(point_info)
        app.db.datasets.update_one({"filename": session["image-name"]}, {"$push": {"X": temp_array[0]}})
        app.db.datasets.update_one({"filename": session["image-name"]}, {"$push": {"Y": temp_array[1]}})
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
        return render_template("login.html", email=session.get("email"),  title="Login")

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
        return render_template("signup.html", email=session.get("email"),  title="Sign Up")

    @app.route('/password_reset', methods=['GET', 'POST'])
    def password_reset():
        if request.method == "POST":
            email = request.form.get("email")
            user = app.db.users.find_one({"user-id": email})
            if user is None:
                flash("This e-mail does not exist.")
            else:
                send_mail(email)
                flash("An email has been sent to you with instructions on how to reset your password.")
        return render_template("reset.html", email=session.get("email"),  title="Password Reset")

    @app.route('/password_reset_verified/<token>', methods=['GET', 'POST'])
    def password_reset_verified(token):
        user = verify_reset_token(token)
        if request.method == "POST":
            password = request.form.get("password")
            password_confirmed = request.form.get("password-confirmed")
            if password != password_confirmed:
                flash("Passwords do not match.")
            else:
                password = pbkdf2_sha256.hash(password)
                app.db.users.update_one({"user-id": user}, {"$set": {"password": password}})
                flash("Your password has been updated.")
                return redirect(url_for("login"))
        return render_template("reset_verified.html", email=session.get("email"),  title="Password Reset")

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
        user = session.get("email")
        if app.db.datasets.find_one({"user-id": session["email"], "dataset-name": datasetname}):
            print("a database with the same name already exists")
        else:
            if session["email"] == "temp":
                s3.delete_object(Bucket=BUCKET_NAME, Key=session["image-name"])
            session["dataset-name"] = datasetname
            app.db.datasets.insert_one({"user-id": session["email"], "dataset-name": session["dataset-name"], "filename": None, "x-label": "X", "y-label": "Y", "dp-val": 3, "min-x-coord": None, "max-x-coord": None, "min-y-coord": None, "max-y-coord": None, "min-x-val": None, "max-x-val": None, "min-y-val": None, "max-y-val": None, "X": [], "Y": []})
            session["image-name"] = None
        return redirect(url_for("home"))

    #Called when user clicks on select dataset
    #Obtains the dataset to be selected from a form input.
    #Changes the session variables to current dataset
    @app.route('/select_dataset', methods=['GET', 'POST'])
    def select_dataset():
        datasetname = request.form.get("dataset")
        session["dataset-name"] = str(datasetname)
        selectedDataset = app.db.datasets.find_one({"user-id": session["email"], "dataset-name": session["dataset-name"]})
        if selectedDataset["filename"] is not None:
            session["image-name"] = selectedDataset["filename"]
        return redirect(url_for("home"))

    #Called when user clicks on delete dataset
    #Obtains the dataset to be deleted from a form input.
    #Deletes the dataset from the database and deletes the image from S3
    @app.route('/delete_dataset', methods=['GET', 'POST'])
    def delete_dataset():
        datasetname = request.form.get("dataset")
        deleteDataset = app.db.datasets.find_one({"user-id": session["email"], "dataset-name": str(datasetname)})
        if(session.get("image-name") != None):
            s3.delete_object(Bucket=BUCKET_NAME, Key=deleteDataset["filename"])
        app.db.datasets.delete_one({"user-id": session["email"], "dataset-name": str(datasetname)})
        if app.db.datasets.count_documents({"user-id": session["email"]}):
            tempdataset = app.db.datasets.find_one({"user-id": session["email"]})
            session["dataset-name"] = tempdataset["dataset-name"]
            session["image-name"] = tempdataset["filename"]
        else:
            session["dataset-name"] = "temp"
            session["image-name"] = None
        return redirect(url_for("home"))

    #Route to customize the axes labels and allows user to select the number of decimal points on data
    @app.route('/axes_label', methods=['GET', 'POST'])
    def axes_label():
        xlabel = request.form.get("x-axis")
        ylabel = request.form.get("y-axis")
        dpVal = int(request.form.get("dp-value"))
        app.db.datasets.update_one({"filename": session["image-name"]}, { "$set": { "x-label": xlabel, "y-label": ylabel, "dp-val": dpVal }})
        return redirect(url_for("home"))

    #Route to allow the user to select the colour matching the graph. The image is downlaoded from the image database and so the python function can take it as a parameter.
    @app.route('/auto_extract', methods=['GET', 'POST'])
    def auto_extract():
        linecolour = request.form.get("graph-colour")
        threshold = request.form.get("threshold")
        file = app.db.datasets.find_one({"filename": session["image-name"]})
        s3.download_file(Bucket=BUCKET_NAME, Key=file["filename"], Filename=os.path.join(app.config['UPLOAD_FOLDER'], file["filename"]))
        if file["min-x-val"] is not None:
            autoFind(linecolour, os.path.join(app.config['UPLOAD_FOLDER'], session["image-name"]), file, int(threshold))
            path = "graph.csv"
            return send_file(path, as_attachment = True)
        else:
            return redirect(url_for("home"))

    #Help routes 
    @app.route('/quickstart')
    def quickstart():
        return render_template("tutorials/quickstart.html", email=session.get("email"),  title="Quickstart")
    
    @app.route('/axes_help')
    def axes_help():
        return render_template("tutorials/axes.html", email=session.get("email"),  title="Axes Help")

    @app.route('/measurements_help')
    def measurements_help():
        return render_template("tutorials/measurements.html", email=session.get("email"),  title="Measurements Help")

    @app.route('/dataset_help')
    def dataset_help():
        return render_template("tutorials/datasets.html", email=session.get("email"),  title="Dataset Help")

    #Function used to get the real data value of a point selected by the user, returns the xy values as array
    #Fields are filtered using the unique-session-id and dataset-name
    def CalculatePointvalue(pointAxes: str):
        datasetEntry = app.db.datasets.find_one({"filename": session["image-name"]})
        pointData = pointAxes.strip('][').split(',')
        pointX = int(pointData[0])
        pointY = int(pointData[1])
        calculatedXValue = round((pointX - datasetEntry["min-x-coord"])/(datasetEntry["max-x-coord"] - datasetEntry["min-x-coord"]) * (datasetEntry["max-x-val"] - datasetEntry["min-x-val"]) + datasetEntry["min-x-val"], datasetEntry["dp-val"])
        calculatedYValue = round((pointY - datasetEntry["min-y-coord"])/(datasetEntry["max-y-coord"] - datasetEntry["min-y-coord"]) * (datasetEntry["max-y-val"] - datasetEntry["min-y-val"]) + datasetEntry["min-y-val"], datasetEntry["dp-val"])
        tempArray = [calculatedXValue, calculatedYValue]
        return(tempArray)
    
    #Function to create a CSV file with all the xy points
    def ExportToCSV():
        dataset = app.db.datasets.find_one({"filename": session["image-name"]})
        graphHeader = [dataset["x-label"], dataset["y-label"]]
        file = open('graph.csv', 'w', newline='')
        writer = csv.writer(file)
        writer.writerow(graphHeader)
        graphData = app.db.datasets.find_one({"filename": session["image-name"]})
        for i in range(0, len(graphData["X"])):
            writer.writerow([graphData["X"][i],graphData["Y"][i]])
        file.close()

    #Function to obtain a temporary link to the graph image from the database so that it can be displayed on the webpage.
    #Created using the AWS S3 API
    def create_presigned_url(bucket_name, object_name, expiration=3600):
        response = s3.generate_presigned_url('get_object', Params={'Bucket': BUCKET_NAME, 'Key': session["image-name"]}, ExpiresIn = expiration)
        return response

    #Function to reset database and session variables to test the program
    def DatabaseReset():
        session.clear()
        app.db.datasets.delete_many({})
        app.db.users.delete_many({})

    #The two functions below define the email properties to send an email to the user for account creation and password reset.
    #Thread is used to send the email in the background so the user does not have to wait for the email to be sent.
    def send_confirmation_email(user):
        msg = Message()
        msg.subject = "Account Creation Confirmation"
        msg.sender = os.environ.get('MAIL_USERNAME')
        msg.recipients = [user]
        msg.body = "This is a confirmation email to confirm that you have created an account with DataDigitizer. If you did not create an account with Grapher, please ignore this email."
        Thread(target=send_async_email, args=(app, msg)).start()
        return "Sent"

    def send_mail(user):
        token = get_reset_token(user)
        msg = Message()
        msg.subject = "Flask App Password Reset"
        msg.sender = os.environ.get('MAIL_USERNAME')
        msg.recipients = [user]
        msg.html = render_template('reset_email.html', token=token, user=user)
        Thread(target=send_async_email, args=(app, msg)).start()
        return "Sent"

    def send_async_email(app, msg):
        with app.app_context():
            mail.send(msg)

    #JWT is created so it can be attached to the password reset email
    def get_reset_token(user, expires_sec=1800):
        return jwt.encode({'reset_password': user, 'exp': time() + expires_sec}, key = app.config['SECRET_KEY'])

    #Function used to match the JWT to the user on a database so the password for the respective user can be reset
    def verify_reset_token(token):
        try:
            user = jwt.decode(token, key = app.config['SECRET_KEY'])['reset_password']
            print(id)
        except Exception as e:
            print(e)
            return
        return user

    return app
    