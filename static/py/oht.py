# -*- coding: utf-8 -*-
import db
import constants as CONST

class Word(object):
    """ Word object that holds word and heading information """
    db = db.Database()
    
    def __init__(self, strID):
       """ Return a word object that initializes for a given word in the dictionary """
       word = self.db.execQuery(""" select w.id
                , w.headingid
                , w.word
                , w.fr_translation
                , w.pos
                from word w
                where w.id=%s """, (strID,))
       self.id = word[0][0]
       self.headingid = word[0][1]
       self.en = word[0][2]
       self.fr = word[0][3]
       self.pos = word[0][4]
       self.heading = Heading(self.headingid)

    def Synset(self):
        return self.heading.Synset()

    def Hypernym(self):
        return self.heading.Hypernym()

    def Hyponym(self):
        return self.heading.Hyponym()

class Heading(object):
    """ Heading object that allows traversal between headings"""
    db = db.Database()
    
    def __init__(self, strID):
        """Return a heading object that initializes for a given word in the dictionary"""
        heading = self.db.execQuery(""" select h.id
        , h.thematicheadingid
        , h.heading
        , h.fr_heading
        , th.thematicheading
        , th.fr_thematicheading
        , h.tierindex
        , h.subcat
        from heading h
        left join thematicheading th on th.id=h.thematicheadingid
        where h.id=%s """, (strID,))
        self.id = heading[0][0]
        self.thematicheadingid = heading[0][1]
        self.en = heading[0][2]
        self.fr = heading[0][3]
        self.thematicheading = heading[0][4]
        self.fr_thematicheading = heading[0][5]
        self.tierindex = heading[0][6]
        self.atierindex = heading[0][6].replace(".NA", "").split(".")
        self.subcat = heading[0][7]


    def Synset(self):
        """ Returns list of words categorized within current heading """
        results = self.db.execQuery(""" select w.id from word w where w.headingid=%s """, (self.id,))
        words = []
        for result in results:
            word = Word(result[0])
            words.append(word)
        return words


    def Hypernym(self):
        """ Returns a list of heading objects that are parent to current heading """
        nLen = len(self.atierindex)-1
        strIndex = ""
        for i in range(nLen):
            if i != 0:
                strIndex+="."
            strIndex+=self.atierindex[i]

        for i in range(7-nLen):
            strIndex+=".NA"

        results = self.db.execQuery( """ select id from heading where tierindex=%s """, (strIndex,))
        headings = []
        for result in results:
            heading = Heading(result[0])
            headings.append(heading)

        return headings

    def Hyponym(self):
        """ Returns a list of heading objects that are sub categories within the parent tier """
        results = self.db.execQuery( """ select id from heading where tierindex=%s and subcat is not null """,(self.tierindex,))
        headings = []
        for result in results:
            heading = Heading(result[0])
            headings.append(heading)

        return headings

class Wrapper(object):
    """ Wrapper functions to traverse OHT """
    wordList = []
    db = db.Database()
    ALLOWED_LANG = ["en", "fr"]

    def getWordList(self, strWord, pos=None, lang="en"):
        """ Returns a list of word objects that matches """
        if lang not in self.ALLOWED_LANG:
            raise Exception(lang + " is not a supported language")
        
        if lang=="en":
            if pos is None:
                results = self.db.execQuery("select id from word where word=%s", (strWord,))
            else:
                results = self.db.execQuery("select id from word where word=%s and pos=%s", (strWord,pos))
        
        if lang=="fr":
            if pos is None:
                results = self.db.execQuery("select id from word where fr_translation=%s", (strWord,))
            else:
                results = self.db.execQuery("select id from word where fr_translation=%s and pos=%s", (strWord,pos))
        
        words = []
        for result in results:
            word = Word(result[0])
            words.append(word)

        return words

    
    def getTopicHeadingRankList(self, strID):
        """ Get all headings with a rank for a single topic """
        aHeading = {}
        results = self.db.execQuery(""" select w.word
, w.oht
, tt.dist
, (tt.dist/x.total) normdist
, w.freq
from topicterm tt
left join (select topicid, sum(dist) total from topicterm group by topicid) x on x.topicid=tt.topicid
left join term w on w.id=tt.termid
where tt.topicid=%s
order by tt.dist desc, w.freq
limit %s """, (strID, CONST.OHT_TOPDIST))
        for result in results:
            ngram_weight = 1
            strWord = result[0]
            strPOS = result[1]
            self.db.execUpdate("insert into headingterm(word, pos, topicid, dist, normdist, freq) values(%s, %s, %s, %s, %s, %s)", (strWord, strPOS, strID, result[2], result[3], result[4]))
            aWord = self.getWordList(strWord, pos=strPOS, lang="fr")
            if len(aWord) == 0:
                aGram = filter(bool, strWord.split(" "))
                if len(aGram) > 1:
                    # we got an n-gram so split it up and weight accordingly
                    ngram_weight = len(aGram)
                    aGramPOS = filter(bool, strPOS.split(" "))
                    for ngram, ngram_pos in zip(aGram, aGramPOS):
                        aWordGram = self.getWordList(ngram, pos=ngram_pos, lang="fr")
                        if len(aWordGram) > 0:
                            # concat results together
                            aWord = aWord + aWordGram
                if len(aWord) == 0:
                    # still nothing? skip it then
                    continue
            # since word collision can occur, save confidence level for each heading score
            # also normalize based on topic weight and whether we had to split ngram or not
            fConf = ((1.0 / len(aWord)) * float(result[3])) / ngram_weight
            
            # aWordHeading = {}
            # for word in aWord:
            #     if word.headingid in aWordHeading:
            #         aWordHeading[word.headingid] += 1
            #     else:
            #         aWordHeading[word.headingid] = 1
            
            # norm_dist = float(result[3])
            # for key in aHeading:
            #     aHeading[key] *= (1-norm_dist)
            
            # for key in aWordHeading:
            #     if key in aHeading:
            #         aHeading[key] = ((aWordHeading[key]/ len(aWord)) * norm_dist) + aHeading[key]
            #     else:
            #         aHeading[key] = (aWordHeading[key]/ len(aWord)) * float(result[3])

            for word in aWord:
                if word.headingid in aHeading:
                    aHeading[word.headingid] += fConf
                else:
                    aHeading[word.headingid] = fConf

        return aHeading