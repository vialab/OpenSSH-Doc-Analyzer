import sys
sys.path.append("./static/py")

import os
import numpy as np
import base64
import re
import cStringIO
import imp
import pdf_text_extraction
import pdf_page_splitter
import ocr_pdf_with_imag_conversion_bounding_boxes
# import OCR_bounding_boxes_with_confidence
import convert_image_to_pdf
import pdf_merger
import pdf_text_extraction
import db
import erudit_parser as erudit
import common as cm
import constants as CONST
from werkzeug import secure_filename
from PIL import Image
from flask import *
from lxml import etree


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = CONST.UPLOAD_FOLDER

# Common variables
db = db.Database()


def allowed_file(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1] in CONST.ALLOWED_EXTENSIONS

@app.route("/")
def index():
    xmlDoc = cm.parseXML("C:/Users/Vialab-PC/Desktop")
    #   xmlData = erudit.getXPathElement(xmlDoc, "corps")
    #   strSchema = erudit.getXMLSchema(xmlData)
    
    xmlMeta = cm.getXPathElement(xmlDoc, "//erudit:admin", CONST.ERUDIT_NAMESPACES)
    root = xmlMeta.getroot()
    cm.removeNamespace(root, CONST.ERUDIT_NAMESPACES["erudit"])
    db.execProc("erudit_INSERT_metadata", ("1", etree.tostring(xmlMeta).encode("utf-8")))

    return render_template("index2.html")

@app.route("/return_file")
def return_file():
    return send_file("./file_processing/ocr_document.pdf", attachment_filename="ocr_document.pdf")

@app.route("/upload", methods=["GET", "POST"])
def upload_file():
    if request.method == "POST":
        file = request.files["file"]
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config["UPLOAD_FOLDER"], filename))

            #This strips the text out of an uploaded pdf
            #text = pdf_text_extraction.stripTextFromPDF("./uploads/"+filename)
            #print (text)

            #This splits the uploaded pdf into individual pages
            pdfSplitPages("./uploads/"+filename)

            #This converts all of the spilt pages to jpg cleaning up the file
            #processing folder as it goes it checks for hidden files and ignores them
            for filename2 in os.listdir("./file_processing/"):
                if not filename2.startswith("."):
                    convertPDFToJPG("./file_processing/"+filename2)




            #OCR the image files created and return the dictionary with all the info
            for filename3 in os.listdir("./file_processing/"):
                if not filename3.startswith("."):
                    #Extract the text
                    # textConfidence("./file_processing/"+filename3)
                    #Get the bounding boxes of the document
                    findBoundingBoxes("./file_processing/"+filename3)



            #Turn marked up image back to pdf

            for filename4 in os.listdir("./file_processing/"):
                if not filename4.startswith("."):
                    convertImageToPDF("./file_processing/"+filename4)


            #Merge into one pdf

            pdfMerger("./file_processing/")


    return "ooooooppppppssss"


#This gets the camera image
@app.route("/hook", methods=["POST"])
def get_image():
    image_b64 = request.values["imageBase64"]
    image_data = re.sub("^data:image/.+;base64,", "", image_b64).decode("base64")
    image_PIL = Image.open(cStringIO.StringIO(image_data))
    image_np = np.array(image_PIL)
    im = Image.fromarray(image_np)
    im.save(os.path.join(app.config["UPLOAD_FOLDER"],"test.png"))



    for filename in os.listdir("./uploads/"):
        if not filename3.startswith("."):
            findBoundingBoxes("./uploads/"+filename)

    #print "Image received: {}".format(image_np.shape)
    #return ""



if __name__ == "__main__":
    app.run(debug=True)
