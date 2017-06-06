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
    return render_template("index2.html")

@app.route("/reprocess")
def reprocess():
    results = db.execQuery("select * from document where dataset='erudit' and id not in (select distinct documentid from meta)")
    for result in results:
        xmlDoc = cm.parseXML("C:/Users/Victor/Desktop" + result[2])
        erudit.saveAllData(xmlDoc)
    
    return render_template("index2.html")


if __name__ == "__main__":
    app.run(debug=True)
