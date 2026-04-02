
import easyocr

reader = easyocr.Reader(['en'])

def read_plate(img):

    results = reader.readtext(img)

    for res in results:
        return res[1]

    return "Unknown"
