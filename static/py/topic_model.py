# -*- coding: utf-8 -*-
import db
import constants as CONST
import common as cm
import treetaggerwrapper
import re
import os
import nltk
import codecs
import json
import time
import numpy as np
import gc
from eli5.sklearn import InvertableHashingVectorizer
from sklearn.externals import joblib
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, HashingVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation

os.environ["JAVAHOME"] = "C:/Program Files (x86)/Java/jre1.8.0_121/bin/java.exe"

class TopicModel(object):
    """ Class for handling all topic modeling functions """
    db = db.Database()
    tagger = treetaggerwrapper.TreeTagger(TAGLANG="fr")
    ner = nltk.tag.stanford.StanfordNERTagger("C:/stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz", "C:/stanford-ner/stanford-ner.jar", encoding="utf-8")
    
    # TDIF NMF
    tfidf_vectorizer = TfidfVectorizer(max_df=CONST.TM_MAXDF, min_df=CONST.TM_MINDF, max_features=CONST.TM_FEATURES)
    nmf = NMF(n_components=CONST.TM_TOPICS, random_state=CONST.TM_RANDOM,
            alpha=CONST.TM_ALPHA, l1_ratio=CONST.TM_L1RATIO)
    # LDA VARIABLES
    lda_path = "/model/"
    lda = LatentDirichletAllocation(n_topics=CONST.TM_TOPICS, max_iter=CONST.TM_MAXITER,
                                    learning_method='online',
                                    learning_offset=CONST.TM_OFFSET,
                                    random_state=CONST.TM_RANDOM)
    aDocList = []
    aStopWord = None
    vectorizer = None
    is_stateless = False
    is_loaded = False
    
    def __init__(self, stateless=False, stop_words=None):
        self.is_stateless = stateless
        self.aStopWord = stop_words
        if stateless:
            self.vectorizer = HashingVectorizer(n_features=CONST.TM_FEATURES, non_negative=True)
        else:
            self.vectorizer = CountVectorizer(max_df=CONST.TM_MAXDF, min_df=CONST.TM_MINDF, 
                                    max_features=CONST.TM_FEATURES, stop_words=self.aStopWord)
    # Strip the text of stop words
    # default is the external set of stop words
    def preProcessText(self, strText, dataset="adam2"):
        """ Strip the text of stop words """
        aStopWord = []
        # Always add spaces after apostrophe
        strText = strText.replace(u"\u2019", u" ")
        # Kill underscores, and other characters we don't care about
        translate_char = u"!@#$%^&*()[]{};:,./<>?\|`~-=_+"
        translate_table = dict((ord(char), u" ") for char in translate_char)
        strText = strText.translate(translate_table)
        # This tokenizes, pos tags, and lemmatizes all our words
        aWordList = treetaggerwrapper.make_tags(self.tagger.tag_text(strText), exclude_nottags=True)

        # Remove all stop words (based on lemmatized words) and punctuation
        # also make sure pos is lower case and without colons
        aCleanWordList = [word
            for word in aWordList 
                if "pun" not in word[1].lower()
                    and "sent" not in word[1].lower()
                    and "@" not in word[2]
                    and len(word[2]) > 1
        ]
        strCleanText = " ".join(word[2].lower()+"_"+word[1].lower() for word in aTag if word[2] != "")
        strCleanText = strCleanText.replace(u":", u"")
        strCleanText = re.sub(u"[|]", u"", strCleanText)
        strCleanText = strCleanText.replace(u"lale_proper", u"")
        strCleanText = strCleanText.replace(u"foifois_proper", u"")
        return strCleanText.lower()


    def saveCleanedTextToDisk(self, strPath, strText):
        with codecs.open(strPath, "w+", "utf-8") as f:
            f.write(strText)

    def removeStopWords(self, strText):
        """ Stop word removal from string"""
        aStopWordSet = set(self.aStopWord)
        aWord = strText.split(" ")
        strCleanText = " ".join(word.lower() for word in aWord if word.split("_")[0].lower() not in aStopWordSet and word[0] != "_")
        return strCleanText

    def fitNMF(self, aDocument):
        """ Topic model an array of documents using Non-negative Matrix Factorization (TFIDF) """        
        tfidf = self.tfidf_vectorizer.fit_transform(aDocument)

        self.nmf.fit(tfidf)

        tfidf_feature_names = self.tfidf_vectorizer.get_feature_names()
        print_top_words(self.nmf, tfidf_feature_names, 20)


    def fitLDA(self, aDocument, _aDocList):
        """ Topic model an array of documents using Latent Dirichlet Association """
        self.aDoclist = _aDocList
        tf = self.vectorizer.fit_transform(aDocument)
        if self.is_stateless:
            self.lda.partial_fit(tf)            
        else:
            self.lda.fit(tf)

    def transform(self, strText):
        """ Fit a body of text to our topic model """
        tf = self.vectorizer.transform([strText])
        return self.lda.transform(tf)

    def getFeatureNames(self, aDocument=None):
        """ Get a complete list of features in all topics for our model """
        if self.is_stateless and aDocument==None:
            raise SyntaxError("Missing sample document required for dehashing feature names")
        
        if self.is_stateless:
            ihash_vectorizer = InvertableHashingVectorizer(self.vectorizer)
            ihash_vectorizer.fit(aDocument)
            aNames = ihash_vectorizer.get_feature_names()

            with codecs.open("test.txt", "w+", "utf-8") as f:
                f.write("{")
                for idx, name in enumerate(aNames):
                    f.write("\"" + str(idx) + "\":\"")                    
                    f.write(" ".join(word["name"] for word in name ) + "\"")
                    if idx < len(aNames) - 1:
                        f.write(",\n")
                f.write("}")

            return [word[0]["name"] if "name" in word[0] else word[0] for word in aNames]
        else:
            return self.vectorizer.get_feature_names()

    def printTopWords(self, model, feature_names, n_top_words):
        """ Print the top N words from each topic in a model """
        for topic_idx, topic in enumerate(model.exp_dirichlet_component_):
            print("Topic #%d:" % topic_idx)
            print(" ".join([feature_names[i] + "*" + str(topic[i])
                                for i in topic.argsort()[:-n_top_words - 1:-1]]))

    def saveModel(self):
        """ Pickle the model variables """
        joblib.dump(self.vectorizer, "./model/pkl/vectorizer.pkl")
        joblib.dump(self.lda, "./model/pkl/lda.pkl")

        aConfig = {}
        aConfig["is_stateless"] = self.is_stateless
        aConfig["doclist"] = self.aDocList

        joblib.dump(aConfig, "./model/pkl/config.pkl")

    def loadModel(self):
        """ Load the model variables """
        if not self.is_loaded:
            gc.disable()
            self.is_loaded = True
            self.vectorizer = joblib.load("./model/pkl/vectorizer.pkl")
            self.lda = joblib.load("./model/pkl/lda.pkl")
            self.aStopWord = joblib.load("./model/pkl/stopword.pkl")
            aConfig = joblib.load("./model/pkl/config.pkl")
            self.is_stateless = aConfig["is_stateless"]
            self.aDocList = self.aDocList
            gc.enable()

    def writeModelToDB(self, aDocument=None):
        """ Write all topics, features, and distributions to database """
        aFeatureNames = self.getFeatureNames(aDocument)
        
        for term in self.vectorizer.vocabulary_:
            aTerm = filter(bool,term.split("_"))
            if len(aTerm) < 2:
                aTerm.append("")
            self.db.execUpdate("insert into term(wordpos, word, pos, freq) values(%s, %s, %s, %s)", (term, aTerm[0], aTerm[1], self.vectorizer.vocabulary_[term]))

        for topic_idx, topic in enumerate(self.lda.components_):
            self.db.execUpdate("insert into topic(topicname) values(%s)", (topic_idx,))
            for i in topic.argsort(): 
                self.db.execUpdate("insert into topicterm(topicid, termid, dist) select topic.id, term.id, %s from topic left join term on term.wordpos=%s where topic.topicname=%s", (topic[i], aFeatureNames[i].encode("utf-8"), topic_idx))