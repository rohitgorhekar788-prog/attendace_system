
import os, csv, base64, io
from datetime import datetime
from functools import wraps
from pathlib import Path

import cv2
import numpy as np
from PIL import Image
from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_from_directory
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
IMAGES_DIR = BASE_DIR / "images"
UPLOAD_DIR = BASE_DIR / "uploads"
MODEL_DIR = BASE_DIR / "models"
UPLOAD_DIR.mkdir(exist_ok=True)
MODEL_DIR.mkdir(exist_ok=True)

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "face-attendance-change-this-secret")

DB_CONFIG = {
    "host": os.getenv("DB_HOST", "localhost"),
    "user": os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASSWORD", "aadnya2901"),
    "database": os.getenv("DB_NAME", "systemface attendance"),
}

def db():
    return mysql.connector.connect(**DB_CONFIG)

def init_db():
    conn = db()
    cur = conn.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS register (
        fname VARCHAR(50), lname VARCHAR(50), contact VARCHAR(20),
        email VARCHAR(100) PRIMARY KEY, securityQ VARCHAR(100),
        securityA VARCHAR(100), password VARCHAR(100)
    )""")
    cur.execute("""CREATE TABLE IF NOT EXISTS student (
        Dep VARCHAR(50), Course VARCHAR(50), Year VARCHAR(30), Sem VARCHAR(30),
        ID VARCHAR(50) PRIMARY KEY, Name VARCHAR(100), Div VARCHAR(20),
        `Roll No` VARCHAR(30), Gender VARCHAR(20), DOB VARCHAR(30),
        Email VARCHAR(100), `Phone No` VARCHAR(30), Address VARCHAR(255),
        Teacher VARCHAR(100), `Photo Sample` VARCHAR(10)
    )""")
    conn.commit()
    cur.close(); conn.close()

def login_required(f):
    @wraps(f)
    def wrapped(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return wrapped

def slot_now():
    t = datetime.now().strftime("%H:%M")
    slots = [
        ("10:00","11:00","10:00 AM - 11:00 AM"),
        ("11:00","12:00","11:00 AM - 12:00 PM"),
        ("12:00","13:00","12:00 PM - 01:00 PM"),
        ("13:00","14:00","Lunch Break (01:00 PM - 02:00 PM)"),
        ("14:00","15:00","02:00 PM - 03:00 PM"),
        ("15:00","16:00","03:00 PM - 04:00 PM"),
        ("16:00","17:00","04:00 PM - 05:00 PM"),
    ]
    for a,b,label in slots:
        if a <= t < b: return label
    return "Off Hours"

def recognize_frame(frame, test_mode=False):
    cascade = cv2.CascadeClassifier(str(BASE_DIR/"haarcascade_frontalface_default.xml"))
    model_path = MODEL_DIR/"classifier.xml"
    if not model_path.exists():
        model_path = BASE_DIR/"classifier.xml"
    if not model_path.exists():
        return frame, []
    clf = cv2.face.LBPHFaceRecognizer_create()
    clf.read(str(model_path))
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = cascade.detectMultiScale(gray, 1.1, 10)
    found=[]
    conn=None
    cache={}
    if not test_mode:
        try: conn=db()
        except Exception: conn=None
    for x,y,w,h in faces:
        sid,predict=clf.predict(gray[y:y+h,x:x+w])
        confidence=int(100*(1-predict/300))
        if confidence > 77:
            info={"id":str(sid),"name":f"User_{sid}","roll":"TEST","dep":"DEMO"}
            if not test_mode and conn:
                cur=conn.cursor()
                cur.execute("SELECT ID,Name,`Roll No`,Dep FROM student WHERE ID=%s",(str(sid),))
                row=cur.fetchone(); cur.close()
                if row: info={"id":str(row[0]),"name":row[1],"roll":row[2],"dep":row[3]}
            found.append(info)
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,255,0),2)
            cv2.putText(frame,f"Student ID: {info['id']}",(x,y-75),cv2.FONT_HERSHEY_COMPLEX,.6,(255,255,255),2)
            cv2.putText(frame,f"Roll: {info['roll']}",(x,y-50),cv2.FONT_HERSHEY_COMPLEX,.6,(255,255,255),2)
            cv2.putText(frame,f"Name: {info['name']}",(x,y-25),cv2.FONT_HERSHEY_COMPLEX,.6,(255,255,255),2)
        else:
            cv2.rectangle(frame,(x,y),(x+w,y+h),(0,0,255),2)
            cv2.putText(frame,"Unknown",(x,y-10),cv2.FONT_HERSHEY_COMPLEX,.6,(0,0,255),2)
    if conn: conn.close()
    return frame, found

@app.route("/")
def index():
    if "user" not in session: return redirect(url_for("login"))
    return render_template("index.html", slot=slot_now())

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method=="POST":
        email=request.form.get("email","").strip()
        password=request.form.get("password","")
        try:
            conn=db(); cur=conn.cursor()
            cur.execute("SELECT * FROM register WHERE email=%s AND password=%s",(email,password))
            row=cur.fetchone(); cur.close(); conn.close()
            if row:
                session["user"]=email
                return redirect(url_for("index"))
            flash("Invalid Email or Password!","error")
        except Exception as e:
            flash(f"Database error: {e}","error")
    return render_template("login.html")

@app.route("/register", methods=["GET","POST"])
def register():
    if request.method=="POST":
        vals=[request.form.get(k,"").strip() for k in ["fname","lname","contact","email","securityQ","securityA","password"]]
        if not all(vals): flash("All fields are required!","error")
        else:
            try:
                conn=db(); cur=conn.cursor()
                cur.execute("SELECT email FROM register WHERE email=%s",(vals[3],))
                if cur.fetchone(): flash("User with this Email already exists!","error")
                else:
                    cur.execute("INSERT INTO register VALUES(%s,%s,%s,%s,%s,%s,%s)",vals)
                    conn.commit(); flash("Registered Successfully!","success"); return redirect(url_for("login"))
                cur.close(); conn.close()
            except Exception as e: flash(f"Database error: {e}","error")
    return render_template("register.html")

@app.route("/logout")
def logout():
    session.clear(); return redirect(url_for("login"))

@app.route("/forgot", methods=["GET","POST"])
def forgot():
    if request.method=="POST":
        email=request.form.get("email",""); q=request.form.get("securityQ",""); a=request.form.get("securityA",""); p=request.form.get("new_password","")
        try:
            conn=db(); cur=conn.cursor()
            cur.execute("SELECT email FROM register WHERE email=%s AND securityQ=%s AND securityA=%s",(email,q,a))
            if not cur.fetchone(): flash("Wrong Security Question or Answer!","error")
            else:
                cur.execute("UPDATE register SET password=%s WHERE email=%s",(p,email)); conn.commit(); flash("Your password has been reset! Please login.","success"); return redirect(url_for("login"))
            cur.close(); conn.close()
        except Exception as e: flash(f"Database error: {e}","error")
    return render_template("forgot.html")

@app.route("/students")
@login_required
def students():
    search=request.args.get("search","").strip()
    by=request.args.get("by","Roll No")
    conn=db(); cur=conn.cursor()
    if search and by in ("Roll No","Phone No"):
        col="`Roll No`" if by=="Roll No" else "`Phone No`"
        cur.execute(f"SELECT * FROM student WHERE {col} LIKE %s",(f"%{search}%",))
    else: cur.execute("SELECT * FROM student")
    rows=cur.fetchall(); cur.close(); conn.close()
    return render_template("students.html", rows=rows, form=None, search=search, by=by)

@app.route("/students/save", methods=["POST"])
@login_required
def student_save():
    f=request.form
    vals=[f.get(k,"").strip() for k in ["dep","course","year","sem","id","name","div","roll","gender","dob","email","phone","address","teacher","photo"]]
    try:
        conn=db(); cur=conn.cursor()
        cur.execute("SELECT ID FROM student WHERE ID=%s",(vals[4],))
        if cur.fetchone():
            cur.execute("""UPDATE student SET Dep=%s,Course=%s,Year=%s,Sem=%s,Name=%s,Div=%s,`Roll No`=%s,Gender=%s,DOB=%s,Email=%s,`Phone No`=%s,Address=%s,Teacher=%s,`Photo Sample`=%s WHERE ID=%s""",
                        (vals[0],vals[1],vals[2],vals[3],vals[5],vals[6],vals[7],vals[8],vals[9],vals[10],vals[11],vals[12],vals[13],vals[14],vals[4]))
            msg="Student details successfully updated"
        else:
            cur.execute("INSERT INTO student VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)",vals)
            msg="Student details has been added successfully"
        conn.commit(); cur.close(); conn.close(); flash(msg,"success")
    except Exception as e: flash(f"Error: {e}","error")
    return redirect(url_for("students"))

@app.route("/students/delete/<student_id>", methods=["POST"])
@login_required
def student_delete(student_id):
    try:
        conn=db(); cur=conn.cursor(); cur.execute("DELETE FROM student WHERE ID=%s",(student_id,)); conn.commit(); cur.close(); conn.close(); flash("Student deleted successfully","success")
    except Exception as e: flash(f"Error: {e}","error")
    return redirect(url_for("students"))

@app.route("/students/capture", methods=["POST"])
@login_required
def capture():
    sid=request.form.get("student_id","").strip()
    image=request.files.get("image")
    if not sid or not image: return jsonify(ok=False,message="Student ID and photo are required"),400
    try:
        n=len(list(DATA_DIR.glob(f"user.{sid}.*.jpg")))+1
        img=Image.open(image.stream).convert("RGB")
        img.save(DATA_DIR/f"user.{sid}.{n}.jpg")
        return jsonify(ok=True,message=f"Photo sample {n} saved")
    except Exception as e: return jsonify(ok=False,message=str(e)),500

@app.route("/train", methods=["GET","POST"])
@login_required
def train():
    if request.method=="POST":
        try:
            faces=[]; ids=[]
            for p in DATA_DIR.glob("user.*.*.jpg"):
                parts=p.stem.split(".")
                if len(parts)>=3:
                    img=Image.open(p).convert("L")
                    faces.append(np.array(img,"uint8")); ids.append(int(parts[1]))
            if not faces: raise ValueError("No face samples found in data folder.")
            recognizer=cv2.face.LBPHFaceRecognizer_create(); recognizer.train(faces,np.array(ids)); recognizer.write(str(MODEL_DIR/"classifier.xml"))
            shutil_copy=str(MODEL_DIR/"classifier.xml")
            flash("Training data set completed","success")
        except Exception as e: flash(f"Training error: {e}","error")
    return render_template("train.html")

@app.route("/recognition")
@login_required
def recognition():
    return render_template("recognition.html", slot=slot_now())

@app.route("/api/recognize", methods=["POST"])
@login_required
def api_recognize():
    data=request.json.get("image","") if request.is_json else ""
    if not data: return jsonify(ok=False,message="No image"),400
    try:
        raw=base64.b64decode(data.split(",",1)[-1])
        arr=np.frombuffer(raw,np.uint8); frame=cv2.imdecode(arr,cv2.IMREAD_COLOR)
        if frame is None: raise ValueError("Invalid image")
        out,found=recognize_frame(frame,False)
        ok,enc=cv2.imencode(".jpg",out)
        result=base64.b64encode(enc).decode()
        return jsonify(ok=True,image="data:image/jpeg;base64,"+result,students=found,slot=slot_now())
    except Exception as e: return jsonify(ok=False,message=str(e)),500

@app.route("/api/attendance", methods=["POST"])
@login_required
def save_attendance():
    ids={str(x) for x in request.json.get("ids",[])}
    slot=slot_now()
    if slot=="Off Hours" or slot.startswith("Lunch Break"):
        return jsonify(ok=False,message=f"Attendance is not active: {slot}"),400
    try:
        conn=db(); cur=conn.cursor()
        cur.execute("SELECT ID,`Roll No`,Name,Dep FROM student ORDER BY CAST(`Roll No` AS UNSIGNED)")
        students=cur.fetchall(); cur.close(); conn.close()
        csvpath=BASE_DIR/"rohit.csv"
        exists=csvpath.exists() and csvpath.stat().st_size>0
        with open(csvpath,"a",newline="",encoding="utf-8") as f:
            w=csv.writer(f)
            if not exists: w.writerow(["ID","Roll No","Name","Department","Lecture","Time","Date","Status"])
            now=datetime.now()
            for s in students:
                sid=str(s[0]); status="Present" if sid in ids else "Absent"
                w.writerow([s[0],s[1],s[2],s[3],slot,now.strftime("%H:%M:%S") if status=="Present" else "--:--:--",now.strftime("%d/%m/%Y"),status])
        return jsonify(ok=True,message="Attendance saved successfully")
    except Exception as e: return jsonify(ok=False,message=str(e)),500

@app.route("/attendance")
@login_required
def attendance():
    rows=[]
    p=BASE_DIR/"rohit.csv"
    if p.exists():
        with open(p,newline="",encoding="utf-8") as f: rows=list(csv.reader(f))[1:]
    return render_template("attendance.html",rows=rows)

@app.route("/photos")
@login_required
def photos():
    pics=sorted([p.name for p in DATA_DIR.glob("*.jpg")])
    return render_template("photos.html",pics=pics)

@app.route("/data/<path:name>")
@login_required
def data_file(name): return send_from_directory(DATA_DIR,name)

@app.route("/developer")
@login_required
def developer(): return render_template("developer.html")

@app.route("/help")
@login_required
def help_page(): return render_template("help.html")

@app.route("/exit")
def exit_app():
    session.clear(); return redirect(url_for("login"))

if __name__=="__main__":
    try: init_db()
    except Exception as e: print("Database initialization warning:",e)
    app.run(host="127.0.0.1",port=int(os.getenv("PORT","5000")),debug=True)
