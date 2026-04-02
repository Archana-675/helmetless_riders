import cv2
import pandas as pd
from datetime import datetime
from flask import Flask, render_template, request, redirect, session, send_from_directory
from utils.helmet_detector import detect_helmet
from utils.plate_detector import detect_plate
from utils.ocr_reader import read_plate
import threading
import os

app = Flask(__name__)
app.secret_key = "traffic_secret_key"

# Ensure folders exist
os.makedirs("violations", exist_ok=True)
os.makedirs("database", exist_ok=True)

# ----------------------------- 
# ADMIN LOGIN
# -----------------------------
ADMIN_USER = "admin"
ADMIN_PASS = "1234"


@app.route("/", methods=["GET", "POST"])
def login():
    error = ""

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        if username == ADMIN_USER and password == ADMIN_PASS:
            session["admin"] = True
            return redirect("/dashboard")
        else:
            error = "Invalid Username or Password"

    return render_template("login.html", error=error)


# -----------------------------
# DASHBOARD
# -----------------------------
@app.route("/dashboard")
def dashboard():

    if "admin" not in session:
        return redirect("/")

    try:
        df = pd.read_csv("database/fines.csv")
        data = df.values.tolist()
        total = len(df)
        
        # Calculate properly 
        if "Violation" in df.columns:
            nohelmet = len(df[df["Violation"] == "No Helmet"])
            helmet = total - nohelmet
        else:
            nohelmet = total
            helmet = 0
    except:
        data = []
        total = 0
        nohelmet = 0
        helmet = 0

    return render_template(
        "dashboard.html",
        data=data,
        total=total,
        helmet=helmet,
        nohelmet=nohelmet
    )


# -----------------------------
# SHOW IMAGES IN DASHBOARD
# -----------------------------
@app.route('/violations/<path:filename>')
def show_image(filename):
    return send_from_directory('violations', filename)


# -----------------------------
# LOGOUT
# -----------------------------
@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/")


# -----------------------------
# DETECTION SYSTEM
# -----------------------------
def run_detection():

    # Note: Replace 0 with a video file like 'traffic.mp4' or an IP camera URL if needed
    camera_source = 0 

    cap = cv2.VideoCapture(camera_source)

    if not cap.isOpened():
        print("Camera not connected. Using fallback or please check source.")
        return

    while True:

        ret, frame = cap.read()

        if not ret:
            print("Frame not received")
            break

        detections = detect_helmet(frame)

        for x1, y1, x2, y2, label in detections:

            if label == "no_helmet":

                cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 0, 255), 2)

                plates = detect_plate(frame)

                for px1, py1, px2, py2, plate_img in plates:

                    number = read_plate(plate_img)

                    cv2.rectangle(frame, (px1, py1), (px2, py2), (255, 0, 0), 2)

                    cv2.putText(
                        frame,
                        number,
                        (px1, py1 - 10),
                        cv2.FONT_HERSHEY_SIMPLEX,
                        0.8,
                        (255, 0, 0),
                        2
                    )

                    time = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

                    # Save image correctly
                    img_name = f"{number}_{time}.jpg"
                    img_full_path = f"violations/{img_name}"

                    cv2.imwrite(img_full_path, frame)

                    # Path for dashboard
                    img_path = f"/violations/{img_name}"

                    data = [[number, time, "No Helmet", img_path]]

                    df = pd.DataFrame(
                        data,
                        columns=[
                            "Vehicle Number",
                            "Time",
                            "Violation",
                            "Image"
                        ]
                    )

                    df.to_csv(
                        "database/fines.csv",
                        mode="a",
                        header=not os.path.exists("database/fines.csv"),
                        index=False
                    )

        cv2.imshow("Smart Traffic Monitoring", frame)

        if cv2.waitKey(1) & 0xFF == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


# -----------------------------
# START SYSTEM
# -----------------------------
if __name__ == "__main__":

    # Run detection in background
    t = threading.Thread(target=run_detection)
    t.daemon = True
    t.start()

    # Run Flask app
    app.run(debug=True);