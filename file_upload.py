#!/usr/bin/env python
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
import time
import urllib
import matplotlib.pyplot as plt
import pandas as pd
# import gzip
from nltk import word_tokenize
from lxml import etree, html
from flask import *
from lz4.frame import compress, decompress
from sklearn.feature_extraction.text import CountVectorizer
from pathlib2 import Path

app = Flask(__name__)
app.config["UPLOAD_FOLDER"] = CONST.UPLOAD_FOLDER
app.secret_key = 'super secret key'
app.config['SESSION_TYPE'] = 'filesystem'
app.session_interface = ps.PickleSessionInterface("./app_session")

# Common variables
oht_wrapper = oht.Wrapper()
db = db.Database()
aStopWord = []
results = db.execQuery(
    "select lower(word) word, treetag from stopword where dataset=%s", ("adam2",))
for result in results:
    aStopWord.append(result[0].strip())
aStopWord = set(aStopWord)
tm = tm.TopicModel(stop_words=aStopWord)
# tm.tfidf_vect.fit(tm.tf)
# print("gzipping")
# with gzip.open("./model/tm.gzip", 'wb') as f:
#     pickle.dump(tm, f, -1)
# print("done")
# with open("./model/tm.pkl", "w+") as f:
#     pickle.dump(tm, f)
# print("loading again")
tm = cm.load_zipped_pickle("./model/tm.gzip")
tm.loadModel()
# with open("./model/pkl/tm.pkl", "r") as f:
#     tm = pickle.load(f)
strPath = "/Users/jayrsawal/Documents"


@app.route("/")
def index():
    # results = db.execQuery("""select h.id, h.tierindex
    # from heading h
    # left join wordsize w on w.headingid = h.id
    # where h.pos='n' and h.subcat='' and w.pos_size is null;""")
    # n = 0
    # for result in results:
    #     pos = db.execQuery("""select h.id, sum(w.size) from heading h
    #     left join heading h2 on h2.tierindex=h.tierindex and h2.subcat=''
    #     left join wordsize w on w.headingid=h2.id
    #     where h.pos='n' and h.subcat='' and h.tierindex=%s
    #     group by h.id;""", (result[1],))
    #     db.execUpdate("update wordsize set pos_size=%s where headingid=%s", (pos[0][1],result[0]))
    #     n += 1
    #     if n % 1000 == 0:
    #         print(n)
    # saveParentHeadings()
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
    # oht_wrapper.writeHierarchyToCSV()
    # saveEntities()
    # getMap()
    # cleanAffiliations()
    # createMapJSON()
    # saveJournalCounts()
    return render_template("index.html")


@app.route("/journal")
def journal():
    return render_template("journal.html")


@app.route("/journal/analyzer")
def journal_analyzer():
    """ Web hook for main document analyzer page """
    # we have 4 options here
    # 0. Default - After uploading a file, go here to analyze
    # 2. Recover Document - Load a previously used document
    # 3. Recover Search - Load a previously used search query
    dochash_id = request.args.get("dochashid")

    if dochash_id is not None:
        recoverDocumentTfidf(dochash_id)

    total_start = time.time()
    search = getJournalSearchResults(session["tfidf"], 999)
    # results = db.execQuery("""
    #     select id
    #     , title
    #     from journal
    #     """)
    search = [row for row in search]
    search[0] = search[0] + (1,)

    # otherwise, our search will be done dynamically through client
    total_end = time.time()
    print("Total Time: %s seconds" % (total_end - total_start))
    return render_template("journal_analyzer.html", journal_list=search)


@app.route("/journal/documents")
def journal_view():
    """ Web hook for viewing the documents in a journal """
    journal_id = request.args.get("id")
    if journal_id is None:
        return redirect(url_for("index"))

    results = db.execQuery("""
        select documentid, 0
        from meta where journalid=%s""", (journal_id,))
    documents = getSearchMetaInfo(results, [])
    return render_template("journal_view.html", doc_list=documents)


@app.route("/document/keywords/<doc_id>", methods=["GET"])
def getKeywords(doc_id):
    """ Get a keyword list for a single document """
    results = db.execQuery("""select d.termid, d.word
    , d.tfidf, t.headingid
    from doctfidf d
    left join tfidf t on t.termid=d.termid
    where d.documentid=%s
    order by d.tfidf desc""", (doc_id,))
    used_terms = []
    keywords = []
    i = 0
    for topic in results:
        if topic[1] in used_terms:
            continue
        i += 1
        used_terms.append(topic[1])
        temp = {}
        temp["id"] = topic[0]
        temp["name"] = topic[1]
        temp["dist"] = topic[2]
        temp["heading_id"] = topic[3]
        temp["rank"] = i
        keywords.append(temp)
    return jsonify(keywords)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    """ Document upload web hook """
    if request.method == 'POST':
        file = request.files['file']
        # make sure upload is support file type
        if file and cm.isSupportedFile(file.filename):
            strText = file.read()
            if file.filename.split(".")[-1] == u"xml":
                xmlDoc = cm.parseXML(strText=strText)
                strText = erudit.getTextFromXML(None, xmlDoc)
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
                # transform to  model
                tfidf = tm.transformTfidf(strClean)
                session["tfidf"] = tfidf
                for idx in tfidf:
                    db.execUpdate("""
                    insert into userdoctfidf(dochashid, termid, tf, idf, tfidf)
                    values(%s, %s, %s, %s, %s);
                    """, (dochash_id, idx, tfidf[idx]["tf"], tfidf[idx]["idf"], tfidf[idx]["tfidf"]))
            # add data to session for later
            key_term = oht_wrapper.getTfidfHeadingList(tfidf)
            session["keyterm"] = key_term
            search_term = [term for term in key_term[:CONST.DS_MAXTOPIC]]
            session["searchterm"] = search_term
            session["tierindex"] = oht_wrapper.getTierIndexIntersection(
                search_term)
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

    term_list = []
    clean_list = []
    must_include = []
    if len(content["keyword_list"]) > 0:
        # get all keywords
        for k in content["keyword_list"]:
            # clean_word = re.sub('[^A-Za-z0-9]+', '', k["keyword"])
            clean_word = k["keyword"]
            clean_list.append(clean_word)
            term_list.append(k["term_id"])
            if k["heading_id"] == "null":
                k["heading_id"] = None
            if "search_id" not in content:
                db.execQuery("""insert into searchterm(searchid, keyword, weight, rank, headingid)
                values(%s, %s, %s, %s, %s); commit;""", (search_id, k["keyword"], k["weight"], k["order"], k["heading_id"]))
            if k["must_include"]:
                must_include.append(clean_word)
    # find matches in the corpus
    rank_list = corpus.matchKeyword(clean_list, 50, must_include)
    # attach meta info for display on the documents
    search = getSearchMetaInfo(rank_list, clean_list, must_include)
    return json.dumps(search)


@app.route("/searchkeyword", methods=["POST"])
def searchkeyword():
    """ Web hook for searching OHT for matching topics on keywords """
    content = request.get_json()
    search = oht_wrapper.getKeywords(content["data"])
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
    if (dochash_id is None and quick_search is None
            and search_id is None):
        return redirect(url_for("index"))

    total_start = time.time()
    search = None
    search_term = None
    key_term = None
    tier_index = None
    if quick_search is None and search_id is None:
        # if we are searching using a document - get results
        search_term = session["searchterm"]
        key_term = session["keyterm"]
        tier_index = session["tierindex"]
        clean_list = []
        # if len(search_term) > 0:
        #     # get all keywords
        #     for k in search_term:
        #         clean_list.append(k["name"])
        # search = getSearchResults(session["tfidf"], clean_list)
    # otherwise, our search will be done dynamically through client
    total_end = time.time()
    print("Total Time: %s seconds" % (total_end - total_start))
    return render_template("analyzer.html", search_result=search, search_term=search_term, key_term=key_term, tier_index=tier_index)


@app.route("/oht")
@app.route("/oht/<tier_index>")
def oht_csv(tier_index=None):
    """ Web hook for retrieving OHT tree based off tier index """
    if tier_index is None:
        return Response(oht_wrapper.csv(), mimetype="text/csv")

    csv = oht_wrapper.getTierIndexChildren(tier_index)
    return Response(csv, mimetype="text/csv")


@app.route("/oht/synset/<heading_id>")
def oht_synset(heading_id):
    """ Web hook for retrieving a word heading synset """
    if heading_id == "null":
        heading_id = 181456
    heading = oht.Heading(heading_id)
    words = heading.Synset()
    pos = heading.PartOfSpeech()
    response = {
        "id": heading_id,
        "name": heading.fr,
        "tier_index": heading.tierindex,
        "words": words,
        "pos": filterOHTHeadingList(pos)
    }
    return jsonify(response)


@app.route("/erudit/journal_count", methods=["POST"])
def erudit_journal():
    """ Get over-arching journal distribution based on search """
    content = request.get_json()
    clean_list = []
    must_include = []
    if len(content["keyword_list"]) > 0:
        # get all keywords
        for k in content["keyword_list"]:
            # clean_word = re.sub('[^A-Za-z0-9]+', '', k["keyword"])
            clean_word = k["keyword"]
            clean_list.append(clean_word)
            if k["must_include"]:
                must_include.append(clean_word)
    dist = corpus.getJournalCount(clean_list, must_include)
    return jsonify(dist)


@app.route("/oht/tier/<tier_index>")
def oht_tier(tier_index):
    return jsonify(oht_wrapper.getTierIndexTrio(tier_index))


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
    order by created desc
    limit 5
    """)
    doc_list = []
    for result in results:
        temp = {}
        temp["dochashid"] = result[0]
        temp["name"] = result[1]
        temp["date"] = result[2]
        doc_list.append(temp)
    # json markup
    history = {
        "searches": search_list, "documents": doc_list
    }
    return jsonify(history)


@app.route("/recoversearch/<search_id>")
def recoverSearch(search_id):
    """ Recover a set of search terms that was previously used by user """
    user_ip = request.environ["REMOTE_ADDR"]
    # get results and authenticate with ipaddress
    results = db.execQuery("""select st.headingid
    , st.keyword
    , st.weight
    , st.rank
    , concat(h.tierindex, '.', h.tiering)
    , h.heading
    , w.headingid
    , concat(h2.tierindex, '.', h2.tiering)
    , th.termid
    , ifnull(p.pos, 'n')
    , ifnull(p.posdesc, 'noun')
    from searchterm st
    left join search s on s.id=st.searchid
    left join heading h on h.id=st.headingid
    left join word w on w.fr_translation = st.keyword
    left join heading h2 on h2.id=w.headingid
    left join tfidf_heading th on th.wordid=w.id
    left join pos p on p.oht=w.pos
    where st.searchid=%s and s.ipaddr=%s
    order by st.rank""", (search_id, user_ip))
    data = oht_wrapper.aggregateByRelevance(results)
    # return json markup
    return jsonify(data)


def recoverDocumentTfidf(dochash_id, redirect=True):
    """ Recover a document that was uploaded by a user """
    # In order for this to happen, we need to populate
    # 1. session["tfidf"] - topic distribution
    # 2. session["keyterm"] - Topic heading id matches based off topicdist
    # 3. session["searchterm"] - filtered list of key terms
    session["dochashid"] = dochash_id
    aHash = db.execQuery("""
        select t.termid, t.word, udt.tf, udt.idf, udt.tfidf, t.headingid, h.tierindex
        from userdoctfidf udt
        left join tfidf t on t.termid=udt.termid
        left join heading h on h.id=t.headingid
        where udt.dochashid=%s and t.headingid is not null
        order by udt.tfidf desc
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
        tfidf[term_idx]["heading_id"] = result[5]
        tfidf[term_idx]["tier_index"] = result[6]
    session["tfidf"] = tfidf

    # get headings from oht
    key_term = oht_wrapper.getTfidfHeadingList(session["tfidf"])
    search_term = [term for term in key_term[:CONST.DS_MAXTOPIC]]
    session["keyterm"] = key_term
    session["searchterm"] = search_term
    session["tierindex"] = oht_wrapper.getTierIndexIntersection(search_term)
    # redirect to analyzer for display
    if redirect:
        return False
    else:
        return tfidf


def getSearchResults(tfidf, clean_list):
    """ Get a list of documents and return it's meta-info  """
    start = time.time()
    rank_list = match(tfidf, 100)
    end = time.time()
    print("Found 10 results in %s seconds" % (end - start))
    # return meta info
    return getSearchMetaInfo(rank_list, clean_list)


def match(tfidf, n=100):
    """ Find closest matching docs using tfidf score """
    terms = ",".join([str(term) for term in tfidf])
    return db.execQuery("""
        select documentid
        , sum(tfidf)
        from doctfidf
        where termid in (""" + terms + """)
        group by documentid
        order by sum(tfidf) desc
        limit %s
        """, (n,))


def getJournalSearchResults(tfidf, n=10):
    """ Like search results, but amalgamated by journal instead """
    terms = ",".join([str(term) for term in tfidf])
    rank_list = db.execQuery("""
        select m.journalid, j.title, j.logo from meta m
        left join (
			select documentid
			, sum(tfidf) score
			from doctfidf
			where termid in (""" + terms + """)
			group by documentid
			order by sum(tfidf) desc) x on x.documentid=m.documentid
        left join journal j on j.id=m.journalid
		group by m.journalid
        order by sum(x.score) desc
        limit %s;
        """, (n,))
    return rank_list


def getSearchMetaInfo(rank_list, keyword_list, must_include=[]):
    """ Get the meta info for a list of document ids """
    results = []
    start = time.time()
    # first get document info - author, title, etc.
    for aDoc in rank_list:
        r = corpus.getDocumentInfo(aDoc[0])
        resultlist = list(r[0])
        # if strDocHashID is None:
        resultlist.append(aDoc[1])
        results.append(resultlist)
    end = time.time()
    print("Retrieved meta info in %s seconds" % (end - start))
    # create the markup to return and also pull topic distribution for doc
    search = []
    start = time.time()
    for result in results:
        if len(result) < 13:
            continue
        doc = {}
        doc["id"] = result[0]
        doc["title"] = result[1]
        doc["author"] = result[2]
        cit_arr = []
        cit_arr.append(result[3])
        cit_arr.append(", Vol. ")
        cit_arr.append(result[4])
        if result[5]:
            cit_arr.append(", No. ")
            cit_arr.append(result[5])
        if result[6]:
            cit_arr.append(".")
            cit_arr.append(result[6])
        cit_arr.append(", ")
        cit_arr.append(result[1])
        cit_arr.append(" (")
        cit_arr.append(result[9])
        cit_arr.append(" ")
        cit_arr.append(result[8])
        cit_arr.append("), pp. ")
        cit_arr.append(result[10])
        if result[11]:
            cit_arr.append("-")
            cit_arr.append(result[11])
        doc["citation"] = "".join(cit_arr)
        doc["topiclist"] = []
        doc["keywordlist"] = []
        doc["cossim"] = result[12]
        # get document distributions
        aTopicDist = db.execQuery("""
        select d.termid, d.word, d.tfidf, t.headingid
        from doctfidf d
        left join tfidf t on t.termid=d.termid
        where d.documentid=%s""", (doc["id"],))
        aTopicDist = list(aTopicDist)
        aTopicDist.sort(key=lambda tup: tup[2], reverse=True)
        unused_terms = keyword_list[:]
        used_terms = []
        i = 0
        for topic in aTopicDist:
            if topic[1] in used_terms:
                continue
            else:
                used_terms.append(topic[1])
            i += 1
            temp = {}
            temp["id"] = topic[0]
            temp["name"] = topic[1]
            temp["dist"] = topic[2]

            hid = topic[3]
            if hid in oht_wrapper.heading:
                temp["heading"] = oht_wrapper.heading[hid]["heading"]
                temp["thematicheading"] = oht_wrapper.heading[hid]["thematicheading"]
                temp["tier_index"] = oht_wrapper.heading[hid]["tier"]
                temp["heading_id"] = hid
                temp["pos"] = oht_wrapper.heading[hid]["pos"]
                temp["posdesc"] = oht_wrapper.heading[hid]["posdesc"]
            else:
                temp["heading"] = topic[1]
                temp["thematicheading"] = None
                temp["tier_index"] = None
                temp["heading_id"] = None
                temp["pos"] = None
                temp["posdesc"] = None

            temp["is_keyword"] = None
            added = True
            if topic[1] in keyword_list:
                temp["is_keyword"] = 1
            if len(doc["topiclist"]) < CONST.DS_MAXTOPIC:
                doc["topiclist"].append(temp)
            else:
                if topic[1] in keyword_list:
                    temp["rank"] = i
                    doc["keywordlist"].append(temp)
                else:
                    added = False
            if added and temp["is_keyword"] == 1:
                unused_terms.remove(topic[1])
        if len(unused_terms) > 0:
            for term in unused_terms:
                temp = {}
                temp["name"] = term
                doc["keywordlist"].append(temp)
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
    print("Got document meta info in %s seconds" % (end - start))
    return search


def filterOHTWordList(words):
    """ Filter a list of words for client side use """
    heading_list = []
    for word in words:
        temp = {}
        temp["id"] = word["word"].id
        temp["name"] = word["word"].en
        temp["pos"] = word["word"].pos
        temp["heading_id"] = word["word"].headingid
        if word["enable"]:
            temp["enable"] = 1
        heading_list.append(temp)
    return heading_list


def filterOHTHeadingList(headings):
    """ Filter a list of words for client side use """
    heading_list = []
    for heading in headings:
        temp = {}
        temp["id"] = heading.id
        temp["name"] = heading.fr
        temp["pos"] = heading.pos
        temp["tier_index"] = heading.tierindex
        temp["size"] = heading.size
        heading_list.append(temp)
    return heading_list


############################## HELPER FUNCTIONS ##############################


def saveTFDF():
    tfdf = {}
    with open("./model/pkl/tfdf2.pkl", "r") as f:
        tfdf = pickle.load(f)

    for word in tfdf:
        db.execUpdate("insert into tfdf(word, freq, docfreq) values(%s, %s, %s)",
                      (word, tfdf[word]["tf"], tfdf[word]["df"]))


def saveStopWords():
    aStopWord = []
    results = db.execQuery(
        "select lower(word) word from stopword where dataset=%s", ("adam2",))
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
    results = db.execQuery(
        "select word, pos from tfidf where headingid is null")
    for result in results:
        aHeading = oht_wrapper.getTopicHeadingRankList(result[0])
        aTop = {"value": 0, "id": None, "col": []}
        for key in aHeading:
            if aHeading[key] > aTop["value"]:
                aTop["value"] = aHeading[key]
                aTop["id"] = key
                aTop["col"] = []
            elif aHeading[key] == aTop["value"]:
                aTop["col"].append(key)
        strCol = ",".join(str(key) for key in aTop["col"])
        db.execUpdate("update topic set headingid=%s, infername=%s where id=%s",
                      (aTop["id"], strCol, result[0]))


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
            db.execUpdate(
                "delete from doctopiclz where documentid=%s;", (key,))

            topic_str = ""
            for topic_idx, dist in enumerate(topic_dist[0]):
                if topic_idx > 0:
                    topic_str = topic_str + ","
                topic_str = topic_str + str(topic_idx) + "-" + str(dist)

            topic_hash = compress(topic_str)
            db.execUpdate("""
                insert into doctopiclz(documentid, topichash)
                values(%s, %s)""", (key, str(topic_hash).decode("latin1").encode("utf8")))

            for topic_idx in topic_dist[0].argsort()[::-1][:CONST.DS_MAXTOPIC]:
                db.execUpdate("""
                    insert into doctopic(documentid, topicid, dist, rank)
                    select %s, id, %s, %s from topic where topicname=%s;""", (key, topic_dist[0][topic_idx], rank, str(topic_idx)))

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
        db.execUpdate("update document set cleanpath=%s where id=%s",
                      (aFile.values()[0], aFile.keys()[0]))


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

        if ((nDoc % 100) == 0) or (nDoc + 1 == len(results)):
            strCleanPath = "./model/corps/" + str(nDoc) + ".txt"
            cm.saveUTF8ToDisk(strCleanPath, json.dumps(aData))
            for key in aData:
                db.execUpdate(
                    "update document set cleanpath=%s where id=%s", (strCleanPath, key))
            aData = {}


def countKeywords():
    count_vect = CountVectorizer(max_df=CONST.TM_MAXDF, min_df=CONST.TM_MINDF, max_features=CONST.TM_FEATURES,
                                 stop_words=aStopWord, token_pattern=r"(?<=\")(?:\\.|[^\"\\]){2,}(?=\")")

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
                    dist = freq / float(num_words)
                    db.execUpdate("""
                    insert into dockeyword(documentid, keywordid, freq, dist)
                    values(%s, %s, %s, %s)
                    """, (key, keyword_id, freq, dist))


def saveParentHeadings():
    headings = db.execQuery("""select h.id
        , h.pos
        , h.tierindex
        from heading h
        left join heading p on p.id=h.parentid
        where h.parentid is not null and h.parentid!=0
        and h.subcat='' and h.pos='n' and
        1=case when h.t2!=p.t2 and h.t3!='NA' then 1
            when h.t3!=p.t3 and h.t4!='NA' then 1
            when h.t4!=p.t4 and h.t5!='NA' then 1
            when h.t5!=p.t5 and h.t6!='NA' then 1
            when h.t6!=p.t6 and h.t7!='NA' then 1
            when p.t7!='NA' then 1
            else 0 end ;
    """)
    n = 0
    print "got %s headings ..." % len(headings)
    for heading in headings:
        n += 1
        if heading[1] == "n":
            p_tier, s_tier, parent_id = oht_wrapper.getParentTier(heading[2])
            db.execUpdate(
                "update heading set parentid=%s where id=%s", (parent_id, heading[0]))
        else:
            parent = db.execQuery("""select id from heading
            where tierindex=%s and pos='n' and subcat=''
            limit 1
            """, (heading[2],))
            if len(parent) > 0:
                db.execUpdate(
                    "update heading set parentid=%s where id=%s", (parent[0][0], heading[0]))
            else:
                # flat level with no words in it
                p_tier, s_tier, parent_id = oht_wrapper.getParentTier(
                    heading[2])

        if (n % 1000) == 0:
            print n


def saveEntities():
    n = 0
    results = db.execQuery(
        "select id, path from document where cleanpath is not null and id not in (select distinct documentid from entity)")
    for result in results:
        erudit.saveEntityData(
            result[0], "/Users/jayrsawal/Documents" + result[1])
        n += 1
        if (n % 1000) == 0:
            print n


def cleanAffiliations():
    results = db.execQuery("""select a.id, a.affiliation, a.lat, a.lng
        from affiliation a
        inner join (
        select lat, lng, count(*) c from affiliation group by lat, lng having count(*) > 1
        ) x on x.lat=a.lat and x.lng=a.lng
        order by a.lat, a.lng, length(a.affiliation);""")
    aff_group = []
    first = {}
    first["id"] = results[0][0]
    first["aff"] = results[0][1]
    first["lat"] = results[0][2]
    first["lng"] = results[0][3]

    for result in results[1:]:
        if result[2] == first["lat"] and result[3] == first["lng"]:
            db.execUpdate("""update author set affiliationid=%s, university=%s
                where affiliationid=%s
                """, (first["id"], first["aff"], result[0]))
            db.execUpdate("""delete from affiliation
                where id=%s
                """, (result[0],))
        else:
            first["id"] = result[0]
            first["aff"] = result[1]
            first["lat"] = result[2]
            first["lng"] = result[3]


def getMap():
    # results = db.execQuery("select distinct affiliation from author where affiliationid is null and affiliation like %s", ("%%universit%%",))
    results = db.execQuery(
        "select distinct university from author where university is not null and affiliationid is null;")
    n = 0
    for result in results:
        if n % 10 == 0:
            print n
        if n == 2450:
            break
        n += 1
        retry = 0
        while retry < 2:
            try:
                search = result[0].strip().encode("utf-8")
                strText = result[0].strip()
                if not strText.startswith("Universit"):
                    translate_char = u"!@#$%^&*()[]{};:,./<>?\|`~-=_+"
                    translate_table = dict((ord(char), u" ")
                                           for char in translate_char)
                    strText = strText.translate(
                        translate_table).replace("cours", "")
                    tokens = word_tokenize(
                        tm.removeStopWords(strText).encode("utf-8"))
                    search = ""
                    append = False
                    x = 0
                    for i, t in enumerate(tokens):
                        if x > 4:
                            break
                        if "universit" in t and append:
                            break
                        if "universit" in t and not append:
                            append = True
                            if i > 0:
                                search += tokens[i - 1] + " "
                        if append:
                            search += t + " "
                            x += 1
                search = search.strip()
                url = "https://maps.googleapis.com/maps/api/geocode/json?key=&address=" + \
                    urllib.quote(search)
                geo = json.loads(urllib.urlopen(url).read())
                if geo["status"] == "ZERO_RESULTS":
                    retry = 3
                    continue
                if geo["status"] == "OVER_QUERY_LIMIT":
                    time.sleep((retry + 1)**2)
                    raise ValueError("Blah")
                lat = geo["results"][0]["geometry"]["location"]["lat"]
                lng = geo["results"][0]["geometry"]["location"]["lng"]
                addr = geo["results"][0]["formatted_address"]
                types = " ".join(geo["results"][0]["types"])
                db.execUpdate("""insert into affiliation(affiliation, addr, lat, lng, loc)
                    values(%s, %s, %s, %s, %s);
                    """, (result[0], addr, lat, lng, types))
                aff = db.execQuery(
                    "select id from affiliation where affiliation=%s", (result[0],))
                db.execUpdate(
                    "update author set affiliationid=%s where university=%s", (aff[0][0], result[0]))
                time.sleep(0.1)
                retry = 2
            except:
                retry += 1


def createMapJSON():
    results = db.execQuery("""
        select m.documentid
        , m.journalid
        , m.titrerev
        , m.annee
        , m.periode
        , case when t.titre is null then t.surtitre else t.titre end titre
        , case when t.titre is null and t.surtitre is not null then null else t.surtitre end surtitre
        , concat(a.nomfamille, ', ', a.prenom) auteur
        , a.lat
        , a.lng
        , a.authorid
        , aa.affiliationid
        from meta m
        left join auteur a on a.documentid=m.documentid and a.auteurpos='au1'
        left join author aa on aa.id=a.authorid
        left join titre t on t.documentid=m.documentid
        where a.authorid is not null
        and aa.affiliationid is not null
        and a.documentid in (
            select documentid from auteur a
            left join author aa on aa.id=a.authorid
            where aa.affiliationid is not null
            group by documentid
            having count(*)  > 2
        );
        """)
    documents = []
    last_doc_id = results[0][0]
    for result in results:
        doc = {}
        doc["documentid"] = result[0]
        doc["journalid"] = result[1]
        doc["journal"] = result[2]
        doc["year"] = result[3]
        doc["period"] = result[4]
        doc["title"] = result[5]
        doc["subtitle"] = result[6]
        doc["author"] = result[7]
        doc["lat"] = result[8]
        doc["lng"] = result[9]
        doc["authorid"] = result[10]
        doc["entityid"] = result[11]
        documents.append(doc)
    strCleanPath = "./model/entities.json"
    entities = createEntityMapJSON()
    createEntityLinkData(documents)
    data = {
        "entities": entities, "documents": documents
    }
    cm.saveUTF8ToDisk(strCleanPath, json.dumps(data))


def createEntityMapJSON():
    entities = {}
    results = db.execQuery("""
        select id
        , affiliation
        , addr
        , lat
        , lng
        , loc
        from affiliation
        """)
    for result in results:
        entities[result[0]] = {}
        entities[result[0]]["entityid"] = result[0]
        entities[result[0]]["affiliation"] = result[1]
        entities[result[0]]["addr"] = result[2]
        entities[result[0]]["lat"] = result[3]
        entities[result[0]]["lng"] = result[4]
        entities[result[0]]["loc"] = result[5]
    return entities


def createEntityLinkData(documents):
    for doc in documents:
        links = []
        authors = db.execQuery("""
            select distinct aa.affiliationid
            , af.lat
            , af.lng
            from auteur a
            inner join author aa on a.authorid=aa.id
            inner join affiliation af on aa.affiliationid=af.id
            where a.documentid=%s
            and aa.affiliationid is not null
            """, (doc["documentid"],))
        for a in authors:
            author = {}
            author["affiliationid"] = a[0]
            author["lat"] = a[1]
            author["lng"] = a[2]
            links.append(author)
        if len(links) > 2:
            links = sortAuthorLinks(links)
        else:
            links = [link["affiliationid"] for link in links]
        doc["links"] = links


def sortAuthorLinks(links):
    link_stack = links
    sorted_links = []
    max_lat, min_lat, max_lng, min_lng = getMinMaxLatLng(links)
    # get only nodes existing in top right quadrant
    # but make sure we do not include max_lng to avoid duplicates
    q_maxlatlng = []
    added_list = []
    for i, link in enumerate(link_stack):
        if i not in added_list and link["lng"] >= max_lat["lng"] \
                and link["lat"] >= max_lng["lat"] \
                and (link != max_lng or max_lat == max_lng):
            q_maxlatlng.append(link)
            added_list.append(i)
    sorted_links += traverseQuadrant(q_maxlatlng, max_lat["lng"])
    # get only nodes existing in bottom right quadrant
    # but make sure we do not include min_lat to avoid duplicates
    q_maxlnglat = []
    for i, link in enumerate(link_stack):
        if i not in added_list and link["lat"] <= max_lng["lat"] \
                and link["lng"] <= min_lat["lng"] \
                and (link != min_lat or max_lng == min_lat):
            q_maxlnglat.append(link)
            added_list.append(i)
    sorted_links += traverseQuadrant(q_maxlnglat, max_lng["lat"])
    # get only nodes existing in bottom left quadrant
    # but make sure we do not include min_lng to avoid duplicates
    q_minlatlng = []
    for i, link in enumerate(link_stack):
        if i not in added_list and link["lng"] <= min_lat["lng"] \
                and link["lat"] <= min_lng["lat"] \
                and (link != min_lng or min_lng == min_lat):
            q_minlatlng.append(link)
            added_list.append(i)
    sorted_links += traverseQuadrant(q_minlatlng, min_lat["lng"])
    # get only nodes existing in bottom left quadrant
    # but make sure we do not include min_lng to avoid duplicates
    q_minlnglat = []
    for i, link in enumerate(link_stack):
        if i not in added_list and link["lat"] >= min_lng["lat"] \
                and link["lng"] <= max_lat["lng"] \
                and (link != max_lat or min_lng == max_lat):
            q_minlnglat.append(link)
            added_list.append(i)
    sorted_links += traverseQuadrant(q_minlnglat, min_lng["lat"])
    return [link["affiliationid"] for link in sorted_links]


def traverseQuadrant(quadrant, anchor):
    # traverse a quadrant in a line from anchor to max
    # return the ordered list
    ordered_list = []
    while len(quadrant) > 0:
        closest_distance = 999
        closest_index = 999
        for i, link in enumerate(quadrant):
            lat_diff = abs(link["lat"] - anchor)
            if lat_diff < closest_distance:
                closest_index = i
                closest_distance = lat_diff
        ordered_list.append(quadrant.pop(closest_index))
    return ordered_list


def getMinMaxLatLng(links):
    # get max and min lat lng values CLOCKWISE by pairwise values
    # this will give us quadrants
    max_lat = {"lat": -999, "lng": 999}
    min_lat = {"lat": 999, "lng": -999}
    max_lng = min_lat
    min_lng = max_lat
    for link in links:
        if link["lat"] >= max_lat["lat"]:
            if link["lat"] == max_lat["lat"]:
                if link["lng"] < max_lat["lng"]:
                    max_lat = link
            else:
                max_lat = link

        if link["lat"] <= min_lat["lat"]:
            if link["lat"] == min_lat["lat"]:
                if link["lng"] > min_lat["lng"]:
                    min_lat = link
            else:
                min_lat = link

        if link["lng"] >= max_lng["lng"]:
            if link["lng"] == max_lng["lng"]:
                if link["lat"] > max_lng["lat"]:
                    max_lng = link
            else:
                max_lng = link

        if link["lng"] <= min_lng["lng"]:
            if link["lng"] == min_lng["lng"]:
                if link["lat"] < min_lng["lat"]:
                    min_lng = link
            else:
                min_lng = link
    return max_lat, min_lat, max_lng, min_lng


def saveJournalCounts():
    results = db.execQuery("""
    select j.id, j.title, count(*) from journal j
    left join meta m on m.journalid=j.id
    group by j.id, j.title;
    """)
    journal = {}
    for result in results:
        journal[result[0]] = {}
        journal[result[0]]["title"] = result[1]
        journal[result[0]]["count"] = result[2]
    strCleanPath = "./model/journal.json"
    cm.saveUTF8ToDisk(strCleanPath, json.dumps(journal))


if __name__ == "__main__":
    sess.init_app(app)
    app.run(debug=True)
