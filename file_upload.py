# -*- coding: utf-8 -*-
import sys
sys.path.append("./static/py")
import os
import db
import json
import codecs
import cPickle as pickle
import numpy as np
import erudit_parser as erudit
import topic_model as tm
import common as cm
import constants as CONST
import oht
import re
import nltk

from flask import *
from lxml import etree


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = CONST.UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'

# Common variables
oht = oht.Wrapper()
db = db.Database()
aStopWord = []
results = db.execQuery("select lower(word) word, treetag from stopword where dataset=%s", ("adam2",))
for result in results:
    aStopWord.append(result[0].strip())
aStopWord = set(aStopWord)
tm = tm.TopicModel(stop_words=aStopWord)
# tm.loadModel()
# with open("./model/pkl/tm.pkl", "w+") as f:
#     pickle.dump(tm, f)
# tm = None
# with open("./model/pkl/tm.pkl", "r") as f:
#     tm = pickle.load(f)
strPath = "C:/Users/Victor/Desktop"

@app.route("/")
def index():
    saveStopWords()
    # prePreProcessTextToDisk()
    # tm.writeModelToDB()
    # inferTopicNames()
    # runTopicModel()
    # savePreProcessedList()
    # transformDocumentToModel(200)
    # saveTFDF()
    return render_template("index.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and cm.isSupportedFile(file.filename):
            strExt = file.filename.split(".")[-1].lower()
            strText = ""
            if strExt == "txt":
                strText = " ".join(strLine for strLine in file)
            
            strText = tm.removeStopWords(strText)

            # Check if this file has already been modeled
            strHash = cm.getSHA256(strText)

            aHash = db.execQuery("""select d.id, udt.dist, t.topicname from dochash d
inner join userdoctopic udt on udt.dochashid=d.id
inner join topic t on t.id=udt.topicid
where d.created > DATE_ADD(CURRENT_TIMESTAMP(), INTERVAL -1 DAY)
and d.hashkey=%s order by t.topicname""", (strHash,))

            if len(aHash) > 0:
                session["dochashid"] = aHash[0][0]
                session["topicdist"] = []
                session["topicdist"].append([0] * len(aHash))
                for result in aHash:
                    session["topicdist"][result[2]] = float(result[1])
            else:
                db.execUpdate("insert into dochash(hashkey) values(%s)", (strHash,))
                session["dochashid"] = db.execQuery("select id from dochash where hashkey=%s order by created desc limit 1", (strHash,))[0][0]
                strClean = tm.preProcessText(strText.decode("utf8"))
                session["topicdist"] = tm.transform(strClean).tolist()
                for topic_idx in np.array(session["topicdist"])[0].argsort():
                    db.execUpdate("""insert into userdoctopic(dochashid, topicid, dist) 
                    select d.id, t.id, %s from dochash d
                    left join topic t on t.topicname=%s
                    where d.created > DATE_ADD(CURRENT_TIMESTAMP(), INTERVAL -1 DAY)
                    and d.hashkey=%s order by d.created desc""", (session["topicdist"][0][topic_idx], topic_idx, strHash))
            
            session["keyterm"] = []
            session["searchterm"] = {}
            
            n = 0
            for topic_idx in np.array(session["topicdist"])[0].argsort()[::-1][:CONST.DS_MAXTERM]:
                if session["topicdist"][0][topic_idx] > CONST.DS_MINSIG:
                    term = {}
                    topic = db.execQuery("""select t.id, t.topicname, h.fr_heading, th.fr_thematicheading 
                    from topic t 
                    left join heading h on h.id=t.headingid
                    left join thematicheading th on th.id=h.thematicheadingid
                    where t.topicname=%s""", (str(topic_idx),))
                    term["id"] = topic[0][0]
                    term["name"] = topic[0][1]
                    term["dist"] = session["topicdist"][0][topic_idx]
                    term["heading"] = topic[0][2]
                    term["thematicheading"] = topic[0][3]
                    session["keyterm"].append(term)

                    if n < CONST.DS_MAXTERM:
                        session["searchterm"][topic[0][0]] = term
                        n += 1
    return redirect(url_for("index"))


@app.route("/analyzer")
def analyzer():
    search = getSearchResults(session["dochashid"])
    return render_template("analyzer.html"
        , search_result=search
        , search_term=session["searchterm"]
        , key_term=session["keyterm"])


def saveTFDF():
    tfdf = {}
    with open("./model/pkl/tfdf2.pkl", "r") as f:
        tfdf = pickle.load(f)
    
    for word in tfdf:
        db.execUpdate("insert into tfdf(word, freq, docfreq) values(%s, %s, %s)", (word, tfdf[word]["tf"], tfdf[word]["df"]))

def saveStopWords():
    aStopWord = []
    results = db.execQuery("select lower(word) word from stopword where dataset=%s", ("adam2",))
    for result in results:
        aStopWord.append(result[0].lower().strip())
    # aStopWord = set(aStopWord)

    with open("./model/pkl/stopword.pkl", "w+") as f:
        pickle.dump(aStopWord, f)

def inferTopicNames():
    results = db.execQuery("select id from topic")
    for result in results:
        aHeading = oht.getTopicHeadingRankList(result[0])
        aTop = { "value":0, "id":None, "col":[] }
        for key in aHeading:
            if aHeading[key] > aTop["value"]:
                aTop["value"] = aHeading[key]
                aTop["id"] = key
                aTop["col"] = []
            elif aHeading[key] == aTop["value"]:
                aTop["col"].append(key)
        strCol = ",".join(str(key) for key in aTop["col"])
        db.execUpdate("update topic set headingid=%s, infername=%s where id=%s", (aTop["id"], strCol, result[0]))


def getSearchResults( strDocHashID ):
    results = []
    aRankList = db.execQuery(""" 
select dt.documentid
, sum(udt.dist * ifnull(dt.dist, 0)) / sqrt( sum(udt.dist * udt.dist) * sum(dt.dist * dt.dist) ) cossim
from userdoctopic udt
left join topic t on t.id=udt.topicid
left join doctopic dt on dt.topicid=t.id
where udt.dochashid=%s
group by dt.documentid
order by sum(udt.dist * ifnull(dt.dist, 0)) / sqrt( sum(udt.dist * udt.dist) * sum(dt.dist * dt.dist) ) desc
limit 10;
    """, (strDocHashID,))

    for aDoc in aRankList:
        result = db.execQuery("""
    select d.id
    , t.titre
    , (select group_concat(concat(prenom
                                , CASE WHEN autreprenom != '' and autreprenom is not null 
                                    THEN concat(' ', autreprenom) ELSE '' END
                                , concat(' ', nomfamille)) separator ', ') 
        from auteur a where a.documentid=d.id 
        order by auteurpos) as auteur
    , m.titrerev
    , m.volume
    , m.nonumero
    , m.anonumero
    , m.editeur
    , m.annee
    , m.periode
    , m.ppage
    , m.dpage
    from document d
    left join meta m on m.documentid=d.id
    left join titre t on t.documentid=d.id
    where d.id=%s
    """, (aDoc[0],))
        resultlist = list(result[0])
        resultlist.append(aDoc[1])
        results.append(tuple(resultlist))
    
    search = []

    for result in results:
        doc = {}
        doc["id"] = result[0]
        doc["title"] = result[1]
        doc["author"] = result[2]
        
        doc["citation"] = result[3] + ", Vol. " + result[4]
        if result[5]:
            doc["citation"] += ", No. " + result[5]
        if result[6]:
            doc["citation"] += "." + result[6]
        doc["citation"] += ", " + result[1] + " (" + result[9] + " " + result[8] + ")"
        doc["citation"] += ", pp. " + result[10]
        if result[11]:
            doc["citation"] += "-" + result[11]

        doc["topiclist"] = []
        doc["cossim"] = result[12]
        aTopicDist = db.execQuery("""
        select t.topicname, t.id, d.dist, h.fr_heading, th.fr_thematicheading from doctopic d 
        left join topic t on t.id=d.topicid
        left join heading h on h.id=t.headingid
        left join thematicheading th on th.id=h.thematicheadingid
        where d.documentid=%s and d.dist > 0.1 
        order by d.dist desc limit 10""", (doc["id"],))

        for topic in aTopicDist:
            temp = {}
            temp["name"] = topic[0]
            temp["id"] = topic[1]
            temp["dist"] = topic[2]
            temp["heading"] = topic[3]
            temp["thematicheading"] = topic[4]
            doc["topiclist"].append(temp)
        
        doc["entitylist"] = []
        aEntity = db.execQuery("select entity, txt from entity where documentid=%s and (entitytype='nomorg' or entitytype='nompers')", (doc["id"],))

        for entity in aEntity:
            temp = {}
            temp["type"] = result[0]
            temp["name"] = result[1]
            doc["entitylist"].append(temp)

        search.append(doc)

    return search


def transformDocumentToModel(nSampleSize=100):
    results = db.execQuery("select distinct cleanpath from document where cleanpath is not null")
    
    n = 0
    for result in results:
        with codecs.open(result[0], encoding="utf-8") as json_file:
            aData = json.load(json_file)
        for key in aData:
            topic_dist = tm.transform(aData[key])
            db.execUpdate("delete from doctopic where documentid=%s;", (key,))
            for topic_idx, dist in enumerate(topic_dist[0]):
                db.execUpdate("""
                    insert into doctopic(documentid, topicid, dist) 
                    select %s, id, %s from topic where topicname=%s;"""
                    , (key, dist, str(topic_idx)) )

            db.execUpdate("update document set transformdt=CURRENT_TIMESTAMP where id=%s", (key,))
            n += 1
            if n == nSampleSize:
                    break
        if n == nSampleSize:
                    break


def savePreProcessedList():
    db.execUpdate("update document set cleanpath=null", ())
    aSavedFile = {}
    with open("./model/pkl/preprocess_list.pkl", "rb") as f:
        aSavedFile = pickle.load(f)

    for aFile in aSavedFile:
        db.execUpdate("update document set cleanpath=%s where id=%s", (aFile.values()[0],aFile.keys()[0]))
        

def runTopicModel(nSampleSize=1000):
    aDocument = []
    aDocList = []
    aSample = []
    dirPath = "./model/corps/boosted/"
    n = 0
    strText = u""
    for filename in os.listdir(dirPath):
        if filename.endswith(".txt"): 
            result = dirPath + filename
            with codecs.open(result, encoding="utf-8") as json_file:
                aData = json.load(json_file)
            for key in aData:
                n += 1
                aDocList.append(key)
                aDocument.append(aData[key])
                strText = aData[key]
                if n == nSampleSize:
                    break
        if n == nSampleSize:
            break

    tm.fitLDA(aDocument, aDocList)
    for i in range(1000):
        try:
            tm.processText(strText)
        except Exception, e:
            print str(e)
    # tm.writeModelToDB()
    # tm.saveModel()

def prePreProcessTextToDisk():
    with open("./model/pkl/stopword.pkl", "r") as f:
        tm.aStopWord = pickle.load(f)

    results = db.execQuery("""
        select max(cast(replace(replace(cleanpath,'./model/corps/', ''), '.txt', '') as UNSIGNED)) lastfile 
        from document""")
    if len(results) > 0:
        nDoc = int(results[0][0])
    else:
        nDoc = 0

    results = db.execQuery("select id, path from document where dataset='erudit' and cleanpath is null")
    aData = {}

    for result in results:
        xmlDoc = cm.parseXML(strPath + result[1])
        strText = erudit.getTextFromXML(result[0], xmlDoc)
        if strText == "":
            continue
        strCleanText = tm.preProcessText(strText)
        aData[str(result[0])] = strCleanText
        nDoc += 1
        
        if ((nDoc % 100) == 0) or (nDoc+1 == len(results)):
            strCleanPath = "./model/corps/" + str(nDoc) + ".txt"
            cm.saveUTF8ToDisk(strCleanPath, json.dumps(aData))
            for key in aData:
                db.execUpdate("update document set cleanpath=%s where id=%s", (strCleanPath, key))
            aData = {}


if __name__ == "__main__":
    sess.init_app(app)
    app.run(debug=True)
