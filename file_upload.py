# -*- coding: utf-8 -*-
import sys
sys.path.append("./static/py")
import os
import db
import codecs
import simplejson as json
import cPickle as pickle
import numpy as np
import erudit_parser as erudit
import erudit_corpus as corpus
import topic_model as tm
import common as cm
import constants as CONST
import oht
import re
import nltk
import time
from sklearn.feature_extraction.text import CountVectorizer
from lz4.frame import compress, decompress
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
# tm.tfidf_vect.fit(tm.tf)
# with open("./model/pkl/tm.pkl", "w+") as f:
#     pickle.dump(tm, f)
tm = None
with open("./model/pkl/tm.pkl", "r") as f:
    tm = pickle.load(f)
strPath = "/Users/jayrsawal/Documents"

@app.route("/")
def index():
    countKeywords()
    # tm.tfidf_vect.fit(tm.tf)
    # tm.saveModel()
    # saveStopWords()
    # prePreProcessTextToDisk()
    # tm.writeModelToDB()
    # inferTopicNames()
    # runTopicModel()
    # savePreProcessedList()
    # transformDocumentToModel(5000)
    # saveTFDF()
    # oht.writeHierarchyToCSV()
    return render_template("index.html")

@app.route("/upload", methods=["GET","POST"])
def upload():
    if request.method == 'POST':
        file = request.files['file']
        if file and cm.isSupportedFile(file.filename):
            with open(file.filename, "r") as f:
                strText = f.read()
            if strText == "":
                return            
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
                    session["topicdist"][int(result[2])] = float(result[1])
            else:
                db.execUpdate("insert into dochash(hashkey) values(%s)", (strHash,))
                session["dochashid"] = db.execQuery("select id from dochash where hashkey=%s order by created desc limit 1", (strHash,))[0][0]
                strClean = tm.processText(strText.decode("utf8"), is_clean=False)
                session["topicdist"] = tm.transform(strClean).tolist()
                for rank,topic_idx in enumerate(np.array(session["topicdist"])[0].argsort()[::-1]):
                    db.execUpdate("""insert into userdoctopic(dochashid, topicid, dist, rank) 
                    select d.id, t.id, %s, %s from dochash d
                    left join topic t on t.topicname=%s 
                    where d.created > DATE_ADD(CURRENT_TIMESTAMP(), INTERVAL -1 DAY)
                    and d.hashkey=%s order by d.created desc"""
                    , (session["topicdist"][0][topic_idx], (rank+1), topic_idx, strHash))
            
            session["keyterm"] = []
            session["searchterm"] = {}
            
            n = 0
            for topic_idx in np.array(session["topicdist"])[0].argsort()[::-1][:CONST.DS_MAXTERM]:
                # if session["topicdist"][0][topic_idx] > CONST.DS_MINSIG:
                term = {}
                topic = db.execQuery("""select t.id
                , t.topicname
                , h.fr_heading
                , th.fr_thematicheading
                , concat(h.tierindex, case when h.tiering is not null then concat('.', h.tiering) else '' end)
                , t.headingid
                from topic t 
                left join heading h on h.id=t.headingid
                left join thematicheading th on th.id=h.thematicheadingid
                where t.topicname=%s""", (str(topic_idx),))
                term["id"] = topic[0][0]
                term["name"] = topic[0][1]
                term["dist"] = session["topicdist"][0][topic_idx]
                term["heading"] = topic[0][2]
                term["thematicheading"] = topic[0][3]
                term["tier_index"] = topic[0][4]
                term["heading_id"] = topic[0][5]
                session["keyterm"].append(term)

                if n < CONST.DS_MAXTERM and session["topicdist"][0][topic_idx] > 0.1:
                    session["searchterm"][topic[0][0]] = term
                    n += 1
    return redirect(url_for("index"))



@app.route("/search", methods=["POST"])
def search():
    content = request.get_json()
    aRankList = corpus.matchTopicList(content["data"], 10)
    search = getSearchMetaInfo(aRankList)
    return json.dumps(search)



@app.route("/explore")
@app.route("/explore/<heading_string>")
def explore( heading_string=None ):
    if heading_string is None:
        search_query = None
        search = db.execQuery("""
        select t.id
        , t.topicname
        , h.fr_heading
        , th.fr_thematicheading 
        from topic t 
        left join heading h on h.id=t.headingid
        left join thematicheading th on th.id=h.thematicheadingid
        """)
    else:
        heading_list = heading_string.split("+")
        session["explore_list"] = []
        for topic in heading_list:
            try:
                session["explore_list"].append(int(topic))
            except:
                continue
        search = getSearchResults()

        search_query = ",".join([str(topic) for topic in session["explore_list"]])
        name_list = db.execQuery("""
        select t.id
        , t.topicname
        , h.fr_heading
        , th.fr_thematicheading 
        from topic t 
        left join heading h on h.id=t.headingid
        left join thematicheading th on th.id=h.thematicheadingid
        where t.id in (""" + search_query + ")")
        search_query = " + ".join([name[2] for name in name_list])
    return render_template("explore.html"
        , search_query=search_query
        , search_result=search
    )



@app.route("/analyzer")
def analyzer():
    total_start = time.time()
    search = getSearchResults(session["dochashid"])
    total_end = time.time()
    print("Total Time: %s seconds" % (total_end-total_start))
    return render_template("analyzer.html"
        , search_result=search
        , search_term=session["searchterm"]
        , key_term=session["keyterm"])



@app.route("/oht")
@app.route("/oht/<tier_index>")
def oht_csv(tier_index=None):
    if tier_index is None:
        return Response(oht.csv(), mimetype="text/csv")
        
    if len(tier_index.split(".")) < 7 and tier_index != "root":
        abort(404)

    csv = oht.getTierIndexChildren(tier_index)
    return Response(csv, mimetype="text/csv")



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
    if " " not in aStopWord:
        aStopWord.append(u" ")
    # aStopWord = set(aStopWord)
    with open("./model/pkl/stopword.pkl", "w+") as f:
        pickle.dump(aStopWord, f)

def inferTopicNames():
    results = db.execQuery("select id from topic where headingid is null")
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


def getSearchResults( strDocHashID=None ):
    if strDocHashID is None:
        if session["explore_list"]:
            str_topic = ",".join([str(topic) for topic in session["explore_list"]])
            str_query = """
                select documentid
                , sum(dist / """ + str(len(session["explore_list"])) + """) cossim
                from doctopic
                where topicid in (
                """ + str_topic + """)
                group by documentid 
                order by sum(dist) desc
                limit 10"""

            aRankList = db.execQuery(str_query)
        else:
            redirect(url_for("index"))
    else:
        start = time.time()
        aRankList = corpus.match(strDocHashID, 10)
        end = time.time()
        print("Found 10 results in %s seconds" % (end-start))
    
    return getSearchMetaInfo(aRankList)

def getSearchMetaInfo(aRankList):
    results = []
    start = time.time()        
    for aDoc in aRankList:
        result = corpus.getDocumentInfo(aDoc[0])
        resultlist = list(result[0])
        # if strDocHashID is None:
        resultlist.append(aDoc[1])
        results.append(tuple(resultlist))
    end = time.time()
    print("Retrieved meta info in %s seconds" % (end-start))
    
    search = []
    start = time.time()
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
        # if strDocHashID is not None:
            # doc["cossim"] = corpus.calculateCosSim(strDocHashID, result[0])
        doc["cossim"] = result[12]
        aTopicDist = db.execQuery("""
        select t.topicname, t.id, d.dist, h.fr_heading, th.fr_thematicheading
            , concat(h.tierindex, case when h.tiering is not null then concat('.', h.tiering) else '' end)
            , t.headingid
        from doctopic d 
        left join topic t on t.id=d.topicid
        left join heading h on h.id=t.headingid
        left join thematicheading th on th.id=h.thematicheadingid
        where d.documentid=%s
        order by d.dist desc limit 10""", (doc["id"],))

        for topic in aTopicDist:
            temp = {}
            temp["name"] = topic[0]
            temp["id"] = topic[1]
            temp["dist"] = topic[2]
            temp["heading"] = topic[3]
            temp["thematicheading"] = topic[4]
            temp["tier_index"] = topic[5]
            temp["heading_id"] = topic[6]
            doc["topiclist"].append(temp)
        
        doc["entitylist"] = []
        aEntity = db.execQuery("""select entity, txt from entity where documentid=%s 
            and (entitytype='nomorg' or entitytype='nompers')""", (doc["id"],))

        for entity in aEntity:
            temp = {}
            temp["type"] = result[0]
            temp["name"] = result[1]
            doc["entitylist"].append(temp)

        search.append(doc)
    end = time.time()
    print("Calculated cosine similarity in %s seconds" % (end-start))
    return search


def transformDocumentToModel(nSampleSize=100):
    """ Save top 10 topics per document as well as a compressed version of all topic distributions
    - Run cosin sim on top 10 topics and then run cosin similarity on topic distribution """
    results = db.execQuery("select distinct cleanpath from document where cleanpath is not null")
    
    n = 0
    for result in results:
        with codecs.open(result[0], encoding="utf-8") as json_file:
            aData = json.load(json_file)
        for key in aData:
            topic_dist = tm.transform(aData[key])
            db.execUpdate("delete from doctopic where documentid=%s;", (key,))
            db.execUpdate("delete from doctopiclz where documentid=%s;", (key,))
            
            topic_str = ""
            for topic_idx, dist in enumerate(topic_dist[0]):
                if topic_idx > 0:
                    topic_str = topic_str + ","
                topic_str = topic_str + str(topic_idx) + "-" + str(dist)
            
            topic_hash = compress(topic_str)
            db.execUpdate("""
                insert into doctopiclz(documentid, topichash) 
                values(%s, %s)"""
                , (key, str(topic_hash).decode("latin1").encode("utf8")) )

            for topic_idx in topic_dist[0].argsort()[::-1][:CONST.DS_MAXTOPIC]:
                db.execUpdate("""
                    insert into doctopic(documentid, topicid, dist, rank) 
                    select %s, id, %s, %s from topic where topicname=%s;"""
                    , (key, topic_dist[0][topic_idx], rank, str(topic_idx)) )

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


def countKeywords():
    count_vect = CountVectorizer(max_df=CONST.TM_MAXDF, min_df=CONST.TM_MINDF
                                , max_features=CONST.TM_FEATURES, stop_words=aStopWord, token_pattern=r"(?<=\")(?:\\.|[^\"\\]){2,}(?=\")")

    dirPath = "./model/corps/"
    for filename in os.listdir(dirPath):
        if filename.endswith(".txt"): 
            result = dirPath + filename

            with codecs.open(result, encoding="utf-8") as json_file:
                aData = json.load(json_file)

            for key in aData:
                try:
                    tf = count_vect.fit_transform([aData[key]])
                except:
                    print key
                    continue
                keyword_list = []
                
                for word in count_vect.get_feature_names():
                    keyword = db.execQuery("""
                    select id from keyword where word=%s
                    """, (word,))
                    
                    if len(keyword) == 0:
                        db.execUpdate("""
                        insert into keyword(word) values(%s);
                        """, (word,))
                        keyword = db.execQuery("""
                        select id from keyword where word=%s
                        """, (word,))
                    keyword_list.append(keyword[0][0])

                num_words = sum([freq for freq in tf.data])
                for keyword_id, freq in zip(keyword_list, tf.data):
                    dist = freq/float(num_words)
                    db.execUpdate("""
                    insert into dockeyword(documentid, keywordid, freq, dist)
                    values(%s, %s, %s, %s)
                    """, (key, keyword_id, freq, dist))



if __name__ == "__main__":
    sess.init_app(app)
    app.run(debug=True)
