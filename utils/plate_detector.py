
from ultralytics import YOLO

model = YOLO("models/license_plate.pt")

def detect_plate(frame):

    results = model(frame)

    plates = []

    for r in results:
        for box in r.boxes:

            x1,y1,x2,y2 = map(int, box.xyxy[0])
            plate = frame[y1:y2, x1:x2]

            plates.append((x1,y1,x2,y2,plate))

    return plates
