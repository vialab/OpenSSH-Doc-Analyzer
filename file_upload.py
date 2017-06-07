import sys
sys.path.append("./static/py")

import os
import db
import erudit_parser as erudit
import topic_model as tm
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
    # results = db.execQuery("select id, path from document where id=%s limit 10", (166519,))
    results = db.execQuery("select id, path from document where dataset='erudit' limit 10")
    strPath = "C:/Users/Victor/Desktop"
    aDocument = []
    for result in results:
        xmlDoc = cm.parseXML(strPath + result[1])
        strText = erudit.getTextFromXML(result[0], xmlDoc)
        aTag = tm.preProcessText(strText, "adam")
        aDocument.append(" ".join(word[2] for word in aTag))

    tm.fitNMF(aDocument)
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
