#!/usr/bin/env python
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
import scipy
import operator
from sklearn.externals import joblib
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer, HashingVectorizer, TfidfTransformer
from sklearn.decomposition import NMF, LatentDirichletAllocation

# os.environ["JAVAHOME"] = "C:/Program Files (x86)/Java/jre1.8.0_121/bin/java.exe"
os.environ["TAGDIR"] = "./treetagger/"

class TopicModel(object):
    """ Class for handling all topic modeling functions """
    db = db.Database()
    tagger = treetaggerwrapper.TreeTagger(TAGLANG="fr")
    # ner = nltk.tag.stanford.StanfordNERTagger("C:/stanford-ner/classifiers/english.all.3class.distsim.crf.ser.gz", "C:/stanford-ner/stanford-ner.jar", encoding="utf-8")
    # TDIF NMF
    nmf = NMF(n_components=CONST.TM_TOPICS, random_state=CONST.TM_RANDOM,
            alpha=CONST.TM_ALPHA, l1_ratio=CONST.TM_L1RATIO)
    # LDA VARIABLES
    lda_path = "/model/"
    lda = LatentDirichletAllocation(n_topics=CONST.TM_TOPICS, max_iter=CONST.TM_MAXITER,
                                    learning_method='online',
                                    learning_offset=CONST.TM_OFFSET,
                                    random_state=CONST.TM_RANDOM)
    aDocList = []
    aStopWord = []
    tfidf_vect = None
    count_vect = None
    is_loaded = False
    tfidf = None
    tf = None

    def __init__(self, stop_words=None):
        for word in stop_words:
            self.aStopWord.append(word.strip())

        self.count_vect = CountVectorizer(max_df=CONST.TM_MAXDF, min_df=CONST.TM_MINDF
                                        , max_features=CONST.TM_FEATURES, stop_words=self.aStopWord)
                                        # , token_pattern=r"(?<=\")(?:\\.|[^\"\\]){2,}(?=\")")
        self.tfidf_vect = TfidfTransformer()


    def preProcessText(self, strText, quote=False):
        """ Remove stopwords and punctuation, and also lemmatize the text. """
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
        aCleanWordList = []
        for word in aWordList:
            strPOS = word[1].lower().replace(u":", u"")

            if "pun" in strPOS or "sent" in strPOS or "@" in word[2]:
                continue
            # lemmatized word can have multiple versions
            aLemma = word[2].lower().replace(u"'", "").split(u"|")

            for lemma in aLemma:
                # make sure individual lemma is not a stop word
                if lemma not in self.aStopWord and lemma[0] != u"_" and len(lemma) > 1:
                    aCleanWordList.append([lemma, strPOS])
        if quote:
            return " ".join("\""+word[0]+"_"+word[1]+"\"" for word in aCleanWordList)
        else:
            return " ".join(word[0]+"_"+word[1] for word in aCleanWordList)

    def processText(self, strRawText, is_clean=True):
        """ Run TFIDF transformation on text and extract and boost
        1-gram, bi-gram, and tri-gram unique descriptors """
        strText = strRawText
        if not is_clean:
            strText = self.preProcessText(strRawText, quote=True)

        doc_tf = self.count_vect.transform([strText])
        doc_tfidf = self.tfidf_vect.transform(doc_tf)

        aVocab = self.count_vect.vocabulary_
        aDescriptor = {}
        for idx, freq in enumerate(doc_tf.data):
            word = u""
            tfidf = 0.0
            # get the english word
            for key, value in aVocab.iteritems():
                if value == doc_tf.indices[idx]:
                    word = key
                    break
            # get the tfidf score
            for key, value in np.ndenumerate(doc_tfidf.indices):
                if value == doc_tf.indices[idx]:
                    tfidf = doc_tfidf.data[key]

            aDescriptor[word] = { "freq":freq, "score":tfidf }

        aDescriptor = self.getSignificantDescriptors(aDescriptor)
        aDescriptor = self.formNGrams(strText, aDescriptor)
        aDescriptor = self.boostNounDescriptors(aDescriptor)
        return self.generateTextFreqMap(aDescriptor)

    def getSignificantDescriptors(self, aDescriptor):
        """ Return only the descriptors that have a score above the relative mean """
        aPD = np.array([aDescriptor[word]["score"] for word in aDescriptor])
        fStd = np.std(aPD)
        fM = np.mean(aPD)

        aRelevant = {}
        for word in aDescriptor:
            if len(aRelevant) != 0:
                if aDescriptor[word]["score"] < fM or abs(aDescriptor[word]["score"] - fM) <= (fStd * CONST.TT_DEVIATION):
                    # exclude any word with tfidf score below mean tfidf score of doc
                    continue
            aRelevant[word] = aDescriptor[word]

        return aRelevant

    def formNGrams(self, strText, aDescriptor):
        """ Given unique descriptors, get relevant bi and tri-grams with frequency """
        aBiGram = {}
        aTriGram = {}
        aWord = strText.split(u" ")

        for idx in range(len(aWord)):
            if aWord[idx] not in aDescriptor:
                # only care about ngrams with descriptors
                continue
            if aDescriptor[aWord[idx]]["freq"] <= CONST.TT_MINFREQ:
                # can not justify descriptor exists in ngram due to min frequency
                continue
            # get possible bi-grams
            if len(aWord) > idx+1:
                strBiGram = aWord[idx] + u" " + aWord[idx+1]
                if strBiGram in aBiGram:
                    aBiGram[strBiGram]["freq"] += 1
                else:
                    aBiGram[strBiGram] = { "freq":1, "score":0.0 }
            if idx > 0:
                strBiGram = aWord[idx-1] + u" " + aWord[idx]
                if strBiGram in aBiGram:
                    aBiGram[strBiGram]["freq"] += 1
                else:
                    aBiGram[strBiGram] = { "freq":1, "score":0.0 }
            # get possible tri-grams
            if len(aWord) > idx+2:
                strTriGram = aWord[idx] + u" " + aWord[idx+1] + u" " + aWord[idx+2]
                if strTriGram in aTriGram:
                    aTriGram[strTriGram]["freq"] += 1
                else:
                    aTriGram[strTriGram] = { "freq":1, "score":0.0 }
            if len(aWord) > idx+1 and idx > 0:
                strTriGram = aWord[idx-1] + u" " + aWord[idx] + u" " + aWord[idx+1]
                if strTriGram in aTriGram:
                    aTriGram[strTriGram]["freq"] += 1
                else:
                    aTriGram[strTriGram] = { "freq":1, "score":0.0 }
            if idx > 1:
                strTriGram = aWord[idx-2] + u" " + aWord[idx-1] + u" " + aWord[idx]
                if strTriGram in aTriGram:
                    aTriGram[strTriGram]["freq"] += 1
                else:
                    aTriGram[strTriGram] = { "freq":1, "score":0.0 }

        # combine tri-grams with bi-grams
        aSigNGram = self.replaceNGramDescriptor(aTriGram, aBiGram)
        # combine descriptors with the n-grams
        aSigNGram = self.replaceNGramDescriptor(aSigNGram, aDescriptor)
        return aSigNGram

    def replaceNGramDescriptor(self, aNGram, aDescriptor):
        """ Return ngrams that have atleast TT_NGRAMSIG percent freq in relation
        to average freq of descriptors within the ngram """
        aSigNGram = dict(aDescriptor)
        for ngram in aNGram:
            nTF = aNGram[ngram]["freq"]
            nDF = 0
            fDesc = 0.0
            fDScore = 0
            tfidf = 0.0

            aSigDesc = {}
            for descriptor in aDescriptor:
                if descriptor in ngram and aDescriptor[descriptor]["freq"] > CONST.TT_MINFREQ:
                    nDF += aDescriptor[descriptor]["freq"]
                    fDesc += 1.0
                    tfidf += aDescriptor[descriptor]["score"]
                    aSigDesc[descriptor] = aDescriptor[descriptor]

            # prefer bi-grams over tri-grams with 1 frequency
            if fDesc < 1:
                continue

            fRelFreq = nTF/(nDF/fDesc)
            if fRelFreq > CONST.TT_NGRAMSIG:
                # average the tfidf score of descriptors involved
                aNGram[ngram]["score"] = (tfidf / fDesc)
                aSigNGram[ngram] = aNGram[ngram]
                # replace original descriptors
                for descriptor in aSigDesc:
                    if descriptor in aSigNGram:
                        del aSigNGram[descriptor]

        return aSigNGram

    def boostNounDescriptors(self, aDescriptor):
        """ Boost noun frequency by a factor of CONST.NOUN_BOOST
        and then smooth by fitting on logarithmic scale """
        aBoosted = {}
        for descriptor in aDescriptor:
            if any(tag in descriptor for tag in CONST.NOUN_TAG):
                aBoosted[descriptor] = { "freq":(aDescriptor[descriptor]["freq"] * CONST.NOUN_BOOST) }
            else:
                aBoosted[descriptor] = { "freq":aDescriptor[descriptor]["freq"] }

        # aSorted = sorted(aBoosted.items(), key=operator.itemgetter(1))
        # size = len(aSorted)
        # x_axis = scipy.arange(1, size+1)
        # y_axis = [word[1] for word in aSorted]
        # i = self.interpolateIntoLog(x_axis, y_axis)
        # aLabel = list([word[0] for word in aSorted])
        # aLog = [int(round(i(x))) for x in x_axis]

        # aBoosted = {}
        # for descriptor, y in zip(aLabel, aLog):
        #     aBoosted[descriptor] = { "freq":y }

        return aBoosted

    def interpolateIntoLog(self, x, y):
        logx = np.log10(x)
        logy = np.log10(y)
        lin_interp = scipy.interpolate.interp1d(logx, logy, kind='cubic')
        log_interp = lambda z: np.power(10.0, lin_interp(np.log10(z)))
        return log_interp

    def generateTextFreqMap(self, aDescriptor):
        """ Return string of descriptors repeated by its frequency """
        strText = ""
        for word in aDescriptor:
            for i in range(aDescriptor[word]["freq"]):
                strText += "\"" + word + "\" "
        return strText

    def removeStopWords(self, strText):
        """ Stop word removal from string"""
        aStopWordSet = set(self.aStopWord)
        aWord = strText.split(" ")
        strCleanText = " ".join(word.lower() for word in aWord if word.lower() not in aStopWordSet)
        return strCleanText

    def fitLDA(self, aDocument, _aDocList):
        """ Topic model an array of documents using Latent Dirichlet Association """
        self.aDoclist = _aDocList
        self.tf = self.count_vect.fit_transform(aDocument)
        self.tfidf = self.tfidf_vect.fit(self.tf)
        self.lda.fit(self.tf)

    def transform(self, strText):
        """ Fit a body of text to our topic model """
        tf = self.count_vect.transform([strText])
        return self.lda.transform(tf)

    def transformTfidf(self, strText):
        """ Fit a body of text to our tfidf vect """
        tf = self.count_vect.transform([strText])
        tfidf = self.tfidf.transform(tf)
        vocab = self.count_vect.get_feature_names()
        # extract data into dict
        tfidf_list = {}
        for tf_idx, x in enumerate(tf.indices):
            tfidf_list[x] = {}
            tfidf_list[x]["term"] = vocab[x]
            tfidf_list[x]["tf"] = tf.data[tf_idx]

        for idf_idx, x in enumerate(tfidf.indices):
            tfidf_list[x]["idf"] = tfidf.data[idf_idx]
            tfidf_list[x]["tfidf"] = tfidf_list[x]["tf"] * tfidf_list[x]["idf"]

        return tfidf_list

    def printTopWords(self, model, feature_names, n_top_words):
        """ Print the top N words from each topic in a model """
        for topic_idx, topic in enumerate(model.exp_dirichlet_component_):
            print("Topic #%d:" % topic_idx)
            print(" ".join([feature_names[i] + "*" + str(topic[i])
                                for i in topic.argsort()[:-n_top_words - 1:-1]]))

    def saveModel(self):
        """ Pickle the model variables """
        joblib.dump(self.count_vect, "./model/pkl/vectorizer.pkl")
        joblib.dump(self.lda, "./model/pkl/lda.pkl")
        joblib.dump(self.tfidf, "./model/pkl/tfidf.pkl")
        joblib.dump(self.tf, "./model/pkl/tf.pkl")
        joblib.dump(self.tfidf_vect, "./model/pkl/tfidf_vect.pkl")

        aConfig = {}
        aConfig["doclist"] = self.aDocList

        joblib.dump(aConfig, "./model/pkl/config.pkl")

    def loadModel(self):
        """ Load the model variables """
        if not self.is_loaded:
            gc.disable()
            self.is_loaded = True
            self.count_vect = joblib.load("./model/pkl/vectorizer.pkl")
            self.tfidf = joblib.load("./model/pkl/tfidf.pkl")
            self.tfidf_vect = joblib.load("./model/pkl/tfidf_vect.pkl")
            self.tf = joblib.load("./model/pkl/tf.pkl")
            self.lda = joblib.load("./model/pkl/lda.pkl")
            self.aStopWord = joblib.load("./model/pkl/stopword.pkl")
            aConfig = joblib.load("./model/pkl/config.pkl")
            self.aDocList = self.aDocList
            gc.enable()

    def writeModelToDB(self, aDocument=None):
        """ Write all topics, features, and distributions to database """
        aFeatureNames = self.count_vect.get_feature_names()
        tf_sum = self.tf.sum(axis=0).A1 # sum term frequencies for each doc

        # # save terms with tf and idf
        for term in self.count_vect.vocabulary_:
            aTerm = filter(bool, term.split(" "))
            no_pos = ""
            pos = ""
            # check if bi-gram or tri-gram
            if len(aTerm) > 1:
                for idx, word in enumerate(aTerm):
                    term_pos = filter(bool,word.split("_"))
                    if len(term_pos) < 2:
                        term_pos.append("")
                    no_pos = no_pos + term_pos[0]
                    pos = pos + term_pos[1]
                    if idx != len(aTerm)-1:
                        no_pos = no_pos + " "
                        pos = pos + " "
                no_pos = no_pos.strip()
                pos = pos.strip()
            else:
                term_pos = filter(bool,term.split("_"))
                if len(term_pos) < 2:
                    term_pos.append("")
                no_pos = term_pos[0]
                pos = term_pos[1]

            idx = self.count_vect.vocabulary_[term]
            self.db.execUpdate("""insert into term(wordpos, word, pos, freq, docfreq) values(%s, %s, %s, %s, %s)"""
            , (term, no_pos, pos, tf_sum[idx], self.tfidf.idf_[idx]))

        # save topics and their term distributions
        for topic_idx, topic in enumerate(self.lda.components_):
            self.db.execUpdate("insert into topic(topicname) values(%s)", (topic_idx,))
            for key, value in self.count_vect.vocabulary_.iteritems():
                self.db.execUpdate("""insert into topicterm(topicid, termid, dist)
                select topic.id, term.id, %s from topic
                left join term on term.wordpos=%s collate utf8mb4_bin
                where topic.topicname=%s
                """, (topic[value], key.encode("utf-8"), topic_idx))
