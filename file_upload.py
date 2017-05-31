import sys
sys.path.append("./static/py")

import os
import db
import erudit_parser as erudit
import common as cm
import constants as CONST

from flask import *
from lxml import etree


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = CONST.UPLOAD_FOLDER

# Common variables
db = db.Database()

@app.route("/")
def index():
    xmlDoc = cm.parseXML("C:/Users/Vialab-PC/Desktop")
    #   xmlData = erudit.4getXPathElement(xmlDoc, "corps")
    #   strSchema = erudit.getXMLSchema(xmlData)
    
    xmlMeta = cm.getXPathElement(xmlDoc, "//erudit:admin", CONST.ERUDIT_NAMESPACES)
    root = xmlMeta.getroot()
    cm.removeNamespace(root, CONST.ERUDIT_NAMESPACES["erudit"])
    db.execProc("erudit_INSERT_metadata", ("1", etree.tostring(xmlMeta).encode("utf-8")))

    return render_template("index2.html")


if __name__ == "__main__":
    app.run(debug=True)
