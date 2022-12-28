# Importing all the necessary packages
from flask import Flask, render_template, request, session, redirect, flash
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import numpy
import json
import cv2
import os


# taking the config.json file into the params variable
with open('app/templates/config.json', 'r') as c:
    params = json.load(c)["params"]

app = Flask(__name__)  # Flask App

basedir = os.path.abspath(os.path.dirname(
    __file__))  # Setting the Database Path

app.config['SQLALCHEMY_DATABASE_URI'] =\
    'sqlite:///' + \
    os.path.join(basedir, 'database.db')  # Setting the Database URI

db = SQLAlchemy(app)

app.secret_key = 'super-secret-key'


class Users(db.Model):  # Creating Users class for Users table
    sno = db.Column(db.Integer, primary_key=True)
    fname = db.Column(db.String(120), nullable=False)
    lname = db.Column(db.String(120), nullable=False)
    uname = db.Column(db.String(120), nullable=False)
    password = db.Column(db.String(120), nullable=False)


class Attendance(db.Model):  # Creating Attendance class for Attendance table
    sno = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


class Attendance2(db.Model):  # Creating Attendance2 class for Attendance2 table
    sno = db.Column(db.Integer, primary_key=True)
    uname = db.Column(db.String(120), nullable=False)
    date = db.Column(db.String(12), nullable=True)


@app.route("/")  # Homepage Route
def home():
    return render_template("index.html", params=params)


@app.route("/signup", methods=['GET', 'POST'])  # SignUp Page Route
def signup():
    if request.method == 'POST':
        fname = request.form.get('fname')
        lname = request.form.get('lname')
        uname = request.form.get('uname')
        password = request.form.get('password')

        if(fname == "" or lname == "" or uname == "" or password == ""):
            return render_template('failpage.html', params=params)

        if(Users.query.filter_by(uname=uname).first()):
            return render_template("wrongusername.html", params=params)

        else:
            insertion = Users(fname=fname, lname=lname,
                              uname=uname, password=password)
            db.session.add(insertion)
            db.session.commit()
            return render_template('successpage.html', params=params)

    return render_template('signup.html', params=params)


@app.route("/signin", methods=['GET', 'POST'])  # SignIn Page Route
def signin():

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('passwordd')
        if(Users.query.filter_by(uname=username, password=password).first() is not None):
            session['user'] = username
            return redirect('/user/' + username)
        else:
            return render_template("wrongcredits.html", params=params)

    return render_template("signin.html", params=params)


@app.route("/loginoption")  # Login Options Page Route
def loginoption():
    return render_template("loginoption.html", params=params)


# Admin's SignIn Page Route
@app.route("/signinadmin", methods=['GET', 'POST'])
def signinadmin():

    if request.method == 'POST':
        username_admin = request.form.get('usernameadmin')
        password_admin = request.form.get('passworddadmin')
        if(username_admin == params['admin_username'] and password_admin == params['admin_password']):
            session['user'] = username_admin
            return render_template("dashboardadmin.html", params=params)
        else:
            return render_template("wrongcreditsadmin.html", params=params)

    return render_template("signinadmin.html", params=params)


@app.route("/dashboardadmin")  # Admin's Dashboard Page Route
def dashboardadmin():
    return render_template("dashboardadmin.html", params=params)


@app.route("/signout")  # User's SignOut Page Route
def signout():
    session.pop('user')
    return redirect('/signedout')


@app.route("/signoutadmin")  # Admin's SignOut Page Route
def signoutadmin():
    session.pop('user')
    return redirect('/signedout')


# Face Registration Page Route
@app.route("/registerface", methods=['GET', 'POST'])
def registerface():
    if request.method == 'POST':

        username = request.form.get('uname')

        if(Users.query.filter_by(uname=username).first() is not None):

            # trained facial features .xml file
            train_file = 'app\\haarcascade_frontalface_default.xml'

            data = 'app\\Data'

            sub_data = username

            path = os.path.join(data, sub_data)
            if not os.path.isdir(path):
                os.mkdir(path)

            face = cv2.CascadeClassifier(train_file)
            cap = cv2.VideoCapture(0)

            d = 1
            while d < 101:
                (_, im) = cap.read()
                grayscale = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
                face_pictures = face.detectMultiScale(grayscale, 1.3, 4)
                for (x, y, w, h) in face_pictures:
                    cv2.rectangle(im, (x, y), (x + w, y + h), (0, 0, 255), 2)
                    cv2.putText(im, 'Collecting your Face Data.....', (x-10, y-10),
                                    cv2.FONT_HERSHEY_PLAIN, 1, (0, 0, 255), thickness=2)
                    faces = grayscale[y:y + h, x:x + w]
                    faces_resize = cv2.resize(faces, (130, 100))
                    cv2.imwrite('% s/% s.png' % (path, d), faces_resize)
                d = d + 1

                cv2.imshow('Creating Dataset', im)
                key = cv2.waitKey(10)
                if key == 27:
                    break
        else:
            return render_template("faceregisterwrongusername.html", params=params)
    return render_template("registerfaceform.html", params=params)


@app.route("/verifyface")  # Face Verification Page Route
def verifyface():

    # trained facial features .xml file
    train_file = 'app\\haarcascade_frontalface_default.xml'
    data = 'app\\Data'

    print('Face Recognition in Process.....')

    (img, lab, codeentity, code) = ([], [], {}, 0)
    for (subdirs, dirs, files) in os.walk(data):
        for subdir in dirs:
            codeentity[code] = subdir
            subjectpath = os.path.join(data, subdir)
            for filename in os.listdir(subjectpath):
                path = subjectpath + '/' + filename
                label = code
                img.append(cv2.imread(path, 0))
                lab.append(int(label))
            code = code + 1
    (w, h) = (130, 100)

    (img, lab) = [numpy.array(lis) for lis in [img, lab]]

    ml_model = cv2.face.LBPHFaceRecognizer_create()
    ml_model.train(img, lab)

    faces = cv2.CascadeClassifier(train_file)
    cap = cv2.VideoCapture(0)
    while True:
        (_, im) = cap.read()
        grayscale = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        faces_1 = faces.detectMultiScale(grayscale, 1.3, 5)
        for (x, y, w, h) in faces_1:
            cv2.rectangle(im, (x, y), (x + w, y + h), (64, 224, 208), 2)
            face_pictures = grayscale[y:y + h, x:x + w]
            faces_resize = cv2.resize(face_pictures, (w, h))

            pred = ml_model.predict(faces_resize)
            cv2.rectangle(im, (x, y), (x + w, y + h), (64, 224, 208), 2)

            identity_of_person = (codeentity[pred[0]])

            if(Attendance.query.filter_by(uname=identity_of_person).first() is None):
                insertion = Attendance(
                    uname=identity_of_person, date=datetime.now())
                insertion2 = Attendance2(
                    uname=identity_of_person, date=datetime.now())
                # Storing the attendees names into the Database
                db.session.add(insertion)
                db.session.add(insertion2)
                db.session.commit()

            if pred[1] < 500:

                cv2.putText(im, '% s - %.0f' % (codeentity[pred[0]], pred[1]), (x-10, y-10),
                            cv2.FONT_HERSHEY_PLAIN, 1, (64, 224, 208))
            else:
                cv2.putText(im, 'not recognized',
                            (x-10, y-10), cv2.FONT_HERSHEY_PLAIN, 1, (64, 224, 208))

        cv2.imshow('Recognizing Face', im)

        key = cv2.waitKey(10)
        if key == 27:
            break

    return render_template("dashboardadmin.html", params=params)


@app.route("/records")  # Attendance Records of people for the day Page Route
def records():
    data = Attendance.query.filter_by().all()
    return render_template("records.html", params=params, data=data)


# Deleting all records for the day Page Route
@app.route("/deleterecords", methods=['GET', 'POST'])
def deleterecords():
    data = Attendance.query.filter_by().all()
    for i in data:
        db.session.delete(i)
    db.session.commit()
    return render_template("records.html", params=params, data=data)


# Viewing each person's attendance records Page Route
@app.route("/user/<string:username_slug>")
def post_route(username_slug):
    details = Attendance2.query.filter_by(uname=username_slug).all()
    return render_template("userpage.html", params=params, details=details, name=username_slug)


@app.route("/sp")  # Successful Page Route
def sp():
    return render_template("successpage.html", params=params)


@app.route("/fp")  # Failure Page Route
def fp():
    return render_template("failpage.html", params=params)


@app.route("/wronguname")  # Wrong Username Page Route
def wronguname():
    return render_template("wrongusername.html", params=params)


@app.route("/wrongcredits")  # Wrong Login Credentials Page Route
def wrongcredits():
    return render_template("wrongcredits.html", params=params)


@app.route("/signedout")  # Signed Out Page Route
def signedout():
    return render_template("signedout.html", params=params)


# Wrong Username for Face Registration Page Route
@app.route("/faceregisterwrongusername")
def faceregisterwrongusername():
    return render_template("faceregisterwrongusername.html", params=params)
