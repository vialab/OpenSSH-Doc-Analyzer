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
import pickle_session as ps
import oht
import re
import nltk
import time
import matplotlib.pyplot as plt
from pathlib2 import Path
from sklearn.feature_extraction.text import CountVectorizer
from lz4.frame import compress, decompress
from flask import *
from lxml import etree


app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = CONST.UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.session_interface = ps.PickleSessionInterface("./app_session")

# Common variables
oht = oht.Wrapper()
db = db.Database()
aStopWord = []
results = db.execQuery("select lower(word) word, treetag from stopword where dataset=%s"
    , ("adam2",))
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
    # countKeywords()
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
    """ Document upload web hook """
    if request.method == 'POST':
        file = request.files['file']
        # make sure upload is support file type
        if file and cm.isSupportedFile(file.filename):
            with open(file.filename, "r") as f:
                strText = f.read()
            if strText == "":
                return
            # remove stopwords
            strText = tm.removeStopWords(strText)
            # hash the text and look for any matches in db
            strHash = cm.getSHA256(strText)
            aHash = db.execQuery("""
                select d.id, t.termid, t.word, udt.tf, udt.idf, udt.tfidf 
                from dochash d
                left join userdoctfidf udt on udt.dochashid=d.id
                left join tfidf t on t.id=udt.termid
                where d.hashkey=%s""", (strHash,))

            if len(aHash) > 1:
                # we have a match - recover it
                tfidf = recoverDocumentTfidf(aHash[0][0])
            else:
                # no match, save this to the db for future reference
                user_ip = request.environ["REMOTE_ADDR"]
                doc_name = file.filename
                db.execUpdate("""insert into dochash(ipaddr, hashkey, docname) 
                values(%s, %s, %s)""", (user_ip, strHash, doc_name))
                dochash_id = db.execQuery("""
                    select id from dochash where hashkey=%s 
                    order by created desc limit 1""", (strHash,))[0][0]
                session["dochashid"] = dochash_id
                # preprocess text
                strClean = tm.preProcessText(strText.decode("utf8"))
                # transform to topic model
                tfidf = tm.transformTfidf(strClean)
                session["tfidf"] = tfidf
                for idx in tfidf:
                    db.execUpdate("""
                    insert into userdoctfidf(dochashid, termid, tf, idf, tfidf)
                    values(%s, %s, %s, %s, %s);
                    """, (dochash_id, idx, tfidf[idx]["tf"], tfidf[idx]["idf"]
                            , tfidf[idx]["tfidf"]))

            # add data to session for later
            key_term = oht.getTfidfHeadingList(tfidf)
            session["keyterm"] = key_term
            session["searchterm"] = [term for term in key_term[:CONST.DS_MAXTOPIC]]
    return redirect(url_for("index"))



@app.route("/search", methods=["POST"])
def search():
    """ Web hook for document search """
    # accepts either a search_id, or a json list of headings/keywords
    content = request.get_json()
    user_ip = request.environ["REMOTE_ADDR"]
    search_id = None
    
    if "search_id" in content:
        search_id = content["search_id"]
    # if not a previous search, save this search to search history
    if search_id is None:
        # use session based queries
        cursor = db.beginSession()
        result = db.execSessionQuery(cursor, """
        insert into search(ipaddr)
        values(%s);
        """, (user_ip,))
        # get last inserted record in session
        result = db.execSessionQuery(cursor, """
        select last_insert_id();
        commit;
        """, close_cursor=True)
        search_id = result[0][0]

    aTopicList = []
    if len(content["heading_list"]) > 0:
        # get all heading ids
        for h in content["heading_list"]:
            aTopicList.append(h["heading_id"])
            if "search_id" not in content:
                db.execQuery("""insert into searchterm(searchid, headingid, weight, rank)
                values(%s, %s, %s, %s); commit;"""
                ,(search_id, h["heading_id"], h["weight"], h["order"]))

    aKeywordList = []
    if len(content["keyword_list"]) > 0:
        # get all keywords
        for k in content["keyword_list"]:
            aKeywordList.append(k["keyword"])
            if "search_id" not in content:
                db.execQuery("""insert into searchterm(searchid, keyword, weight, rank)
                values(%s, %s, %s, %s); commit;"""
                , (search_id, k["keyword"], k["weight"], k["order"]))

    # find matches in the corpus
    # currently, topics and keyword matches are found separately
    # concatenated and returned (will need to rework this)
    aRankList = corpus.matchHeadingList(content["heading_list"], 10)
    aRankList += corpus.matchKeyword(aKeywordList, 10)
    # attach meta info for display on the documents
    search = getSearchMetaInfo(aRankList)
    return json.dumps(search)


@app.route("/searchkeyword", methods=["POST"])
def searchkeyword():
    """ Web hook for searching OHT for matching topics on keywords """
    content = request.get_json()
    search = oht.getKeywords(content["data"])
    return json.dumps(search)


@app.route("/analyzer")
def analyzer():
    """ Web hook for main document analyzer page """
    # we have 4 options here
    # 0. Default - After uploading a file, go here to analyze
    # 1. Quick Search - single keyword document search
    # 2. Recover Document - Load a previously used document
    # 3. Recover Search - Load a previously used search query
    quick_search = request.args.get("quicksearch")
    dochash_id = request.args.get("dochashid")
    search_id = request.args.get("searchid")

    if dochash_id is not None:
        recoverDocumentTfidf(dochash_id)

    # nothing to load - return to home page
    if ("dochashid" not in session and quick_search is None 
            and search_id is None):
        return redirect(url_for("index"))
        
    total_start = time.time()
    search = None
    search_term = None
    key_term = None 
    if quick_search is None and search_id is None:
        # if we are searching using a document - get results
        search = getSearchResults(session["tfidf"])
        search_term = session["searchterm"]
        key_term = session["keyterm"]
    # otherwise, our search will be done dynamically through client
    total_end = time.time()
    print("Total Time: %s seconds" % (total_end-total_start))
    return render_template("analyzer.html"
        , search_result=search
        , search_term=search_term
        , key_term=key_term)


@app.route("/oht")
@app.route("/oht/<tier_index>")
def oht_csv(tier_index=None):
    """ Web hook for retrieving OHT tree based off tier index """
    if tier_index is None:
        return Response(oht.csv(), mimetype="text/csv")
        
    if len(tier_index.split(".")) < 7 and tier_index != "root":
        abort(404)

    csv = oht.getTierIndexChildren(tier_index)
    return Response(csv, mimetype="text/csv")


@app.route("/history")
def history():
    """ Web hook for retrieving search history on main page """
    user_ip = request.environ["REMOTE_ADDR"]
    # get search queries
    results = db.execQuery("""
    select id
    , DATE_FORMAT(created, '%%m/%%d/%%Y %%H:%%i')
    from search
    where ipaddr=%s
    order by created desc
    limit 5
    """, (user_ip,))
    search_list = []
    for result in results:
        temp = {}
        temp["search_id"] = result[0]
        temp["date"] = result[1]
        temp["terms"] = []
        # get terms used for this search
        term_list = db.execQuery("""select st.headingid
    , st.keyword
    , st.weight
    , st.rank 
    , concat(h.tierindex, '.', h.tiering)
    , h.heading
    from searchterm st
    left join search s on s.id=st.searchid
    left join heading h on h.id=st.headingid
    where st.searchid=%s 
    order by st.rank""", (result[0],))
        for term in term_list:
            t = {}
            if term[0] is not None:
                t["heading_id"] = term[0]
                t["tier_index"] = term[4]
                t["heading"] = term[5]
            else:
                t["keyword"] = term[1]
            t["weight"] = term[2]
            t["order"] = term[3]
            temp["terms"].append(t)
        search_list.append(temp)
    
    # get document queries
    results = db.execQuery("""
    select id, docname
    , DATE_FORMAT(created, '%%m/%%d/%%Y %%H:%%i')
    from dochash d
    where ipaddr=%s
    order by created desc
    limit 5
    """, (user_ip,))
    doc_list = []
    for result in results:
        temp = {}
        temp["dochashid"] = result[0]
        temp["name"] = result[1]
        temp["date"] = result[2]
        doc_list.append(temp)
    # json markup
    history = {
        "searches": search_list
        , "documents": doc_list
    }
    return jsonify(history)



@app.route("/recoversearch/<search_id>")
def recoverSearch(search_id):
    """ Recover a set of search terms that was previously used by user """
    search_term = []    
    user_ip = request.environ["REMOTE_ADDR"]

    # get results and authenticate with ipaddress
    term_list = db.execQuery("""select st.headingid
    , st.keyword
    , st.weight
    , st.rank 
    , concat(h.tierindex, '.', h.tiering)
    , h.heading
    from searchterm st
    left join search s on s.id=st.searchid
    left join heading h on h.id=st.headingid
    where st.searchid=%s and s.ipaddr=%s
    order by st.rank""", (search_id,user_ip))

    # correct ip address?
    if len(term_list) > 0:
        for term in term_list:
            t = {}
            if term[0] is not None:
                t["heading_id"] = term[0]
                t["tier_index"] = term[4]
                t["heading"] = term[5]
            else:
                t["keyword"] = term[1]
            t["weight"] = term[2]
            t["order"] = term[3]
            search_term.append(t)
    # return json markup
    return jsonify(search_term)


def recoverDocumentTfidf(dochash_id, redirect=True):
    """ Recover a document that was uploaded by a user """
    ## In order for this to happen, we need to populate
    # 1. session["tfidf"] - topic distribution
    # 2. session["keyterm"] - Topic heading id matches based off topicdist
    # 3. session["searchterm"] - filtered list of key terms
    session["dochashid"] = dochash_id
    aHash = db.execQuery("""
        select t.termid, t.word, udt.tf, udt.idf, udt.tfidf 
        from userdoctfidf udt 
        left join tfidf t on t.termid=udt.termid
        where udt.dochashid=%s
        limit 5""", (dochash_id,))

    # we have a match - recover it
    tfidf = {}
    for result in aHash:
        term_idx = int(result[0])
        tfidf[term_idx] = {}
        tfidf[term_idx]["term"] = result[1]
        tfidf[term_idx]["tf"] = result[2]
        tfidf[term_idx]["idf"] = result[3]
        tfidf[term_idx]["tfidf"] = result[4]
    session["tfidf"] = tfidf

    # get headings from oht
    keyterm = oht.getTfidfHeadingList(session["tfidf"])
    session["keyterm"] = keyterm
    session["searchterm"] = [term for term in keyterm[:CONST.DS_MAXTOPIC]]
    # redirect to analyzer for display
    if redirect:
        return False
    else:
        return tfidf



def getSearchResults( tfidf ):
    """ Get a list of documents and return it's meta-info  """
    start = time.time()
    aRankList = match(tfidf, 10)
    end = time.time()
    print("Found 10 results in %s seconds" % (end-start))
    # return meta info
    return getSearchMetaInfo(aRankList)



def match(tfidf, n=100):
    """ Find closest matching docs using tfidf score """
    terms = ",".join([str(term) for term in tfidf])
    return db.execQuery("""
        select documentid
        , sum(tfidf)
        from doctfidf
        where termid in (""" + terms + """)
        group by documentid
        order by sum(tfidf)
        limit %s
        """,(n,))



def getSearchMetaInfo(aRankList):
    """ Get the meta info for a list of document ids """
    results = []
    start = time.time()
    # first get document info - author, title, etc.
    for aDoc in aRankList:
        result = corpus.getDocumentInfo(aDoc[0])
        resultlist = list(result[0])
        # if strDocHashID is None:
        resultlist.append(aDoc[1])
        results.append(tuple(resultlist))
    end = time.time()
    print("Retrieved meta info in %s seconds" % (end-start))
    
    # create the markup to return and also pull topic distribution for doc
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
        doc["cossim"] = result[12]
        # get document distributions
        aTopicDist = db.execQuery("""
        select t.termid, d.word, d.tfidf, h.fr_heading, th.fr_thematicheading
            , concat(h.tierindex, case when h.tiering is not null 
                then concat('.', h.tiering) else '' end)
            , t.headingid
        from doctfidf d 
        left join tfidf t on t.termid=d.termid
        left join heading h on h.id=t.headingid
        left join thematicheading th on th.id=h.thematicheadingid
        where d.documentid=%s
        order by d.tfidf desc limit 10""", (doc["id"],))

        for topic in aTopicDist:
            temp = {}
            temp["id"] = topic[0]
            temp["name"] = topic[1]
            temp["dist"] = topic[2]
            temp["heading"] = topic[3]
            temp["thematicheading"] = topic[4]
            temp["tier_index"] = topic[5]
            temp["heading_id"] = topic[6]
            doc["topiclist"].append(temp)
        
        # pull any named entities saved for this document
        doc["entitylist"] = []
        # aEntity = db.execQuery("""select entity, txt from entity where documentid=%s 
        #     and (entitytype='nomorg' or entitytype='nompers')""", (doc["id"],))
        # for entity in aEntity:
        #     temp = {}
        #     temp["type"] = result[0]
        #     temp["name"] = result[1]
        #     doc["entitylist"].append(temp)
        search.append(doc)
    end = time.time()
    print("Got document meta info in %s seconds" % (end-start))
    return search




############################## HELPER FUNCTIONS ##############################


def saveTFDF():
    tfdf = {}
    with open("./model/pkl/tfdf2.pkl", "r") as f:
        tfdf = pickle.load(f)
    
    for word in tfdf:
        db.execUpdate("insert into tfdf(word, freq, docfreq) values(%s, %s, %s)"
            , (word, tfdf[word]["tf"], tfdf[word]["df"]))


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


def inferTopic(tfidf):
    # look up a list of words in OHT and place us somewhere
    for key in tfidf:
        word = tfidf[key]["word"]


def inferTopicNames():
    results = db.execQuery("select word, pos from tfidf where headingid is null")
    for result in results:
        aHeading = oht.getTfidfHeadingRankList(result[0])
        aTop = { "value":0, "id":None, "col":[] }
        for key in aHeading:
            if aHeading[key] > aTop["value"]:
                aTop["value"] = aHeading[key]
                aTop["id"] = key
                aTop["col"] = []
            elif aHeading[key] == aTop["value"]:
                aTop["col"].append(key)
        strCol = ",".join(str(key) for key in aTop["col"])
        db.execUpdate("update topic set headingid=%s, infername=%s where id=%s"
            , (aTop["id"], strCol, result[0]))


def transformDocumentToModel(nSampleSize=100):
    """ Save top 10 topics per document as well as a compressed version of 
    all topic distributions - Run cosin sim on top 10 topics and then run 
    cosin similarity on topic distribution """

    results = db.execQuery("""
        select distinct cleanpath from document 
        where cleanpath is not null
    """)
    
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

            db.execUpdate("""update document set 
                transformdt=CURRENT_TIMESTAMP where id=%s""", (key,))
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
        db.execUpdate("update document set cleanpath=%s where id=%s"
            , (aFile.values()[0],aFile.keys()[0]))
        

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
        select max(cast(replace(replace(cleanpath,'./model/corps/', '')
            , '.txt', '') as UNSIGNED)) lastfile 
        from document""")
    if len(results) > 0:
        nDoc = int(results[0][0])
    else:
        nDoc = 0

    results = db.execQuery("""
        select id, path from document 
        where dataset='erudit' and cleanpath is null""")
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
                db.execUpdate("update document set cleanpath=%s where id=%s"
                , (strCleanPath, key))
            aData = {}


def countKeywords():
    count_vect = CountVectorizer(max_df=CONST.TM_MAXDF, min_df=CONST.TM_MINDF
                    , max_features=CONST.TM_FEATURES, stop_words=aStopWord
                    , token_pattern=r"(?<=\")(?:\\.|[^\"\\]){2,}(?=\")")

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
