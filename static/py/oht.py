# -*- coding: utf-8 -*-
import db
import codecs
import constants as CONST
import unicodecsv
from cStringIO import StringIO

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
        """ Return a heading object that initializes for a 
            given word in the dictionary"""
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
        results = self.db.execQuery("""
            select w.id 
            from word w 
            where w.headingid=%s""", (self.id,))
        words = []
        for result in results:
            word = Word(result[0])
            words.append(word)
        return words



    def Hypernym(self):
        """ Returns a list of heading objects that are parent 
            to current heading """
        nLen = len(self.atierindex)-1
        strIndex = ""
        for i in range(nLen):
            if i != 0:
                strIndex+="."
            strIndex+=self.atierindex[i]

        for i in range(7-nLen):
            strIndex+=".NA"

        results = self.db.execQuery("""
            select id 
            from heading 
            where tierindex=%s""", (strIndex,))
        headings = []
        for result in results:
            heading = Heading(result[0])
            headings.append(heading)

        return headings



    def Hyponym(self):
        """ Returns a list of heading objects that are sub 
            categories within the parent tier """
        results = self.db.execQuery("""
            select id 
            from heading 
            where tierindex=%s 
            and subcat is not null """,(self.tierindex,))
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
                results = self.db.execQuery("""
                    select id from word 
                    where word=%s""", (strWord,))
            else:
                results = self.db.execQuery("""
                    select id from word 
                    where word=%s and pos=%s""", (strWord,pos))
        
        if lang=="fr":
            if pos is None:
                results = self.db.execQuery("""
                    select id from word 
                    where fr_translation=%s""", (strWord,))
            else:
                results = self.db.execQuery("""
                    select id from word 
                    where fr_translation=%s and pos=%s""", (strWord,pos))
        
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
            left join (select topicid, sum(dist) total 
                from topicterm group by topicid) x on x.topicid=tt.topicid
            left join term w on w.id=tt.termid
            where tt.topicid=%s
            order by tt.dist desc, w.freq
            limit %s """, (strID, CONST.OHT_TOPDIST))

        for result in results:
            ngram_weight = 1
            strWord = result[0]
            strPOS = result[1]
            self.db.execUpdate("""
                insert into headingterm
                (word, pos, topicid, dist, normdist, freq) 
                values(%s, %s, %s, %s, %s, %s)"""
                , (strWord, strPOS, strID, result[2], result[3], result[4]))

            aWord = self.getWordList(strWord, pos=strPOS, lang="fr")
            if len(aWord) == 0:
                aGram = filter(bool, strWord.split(" "))
                if len(aGram) > 1:
                    # we got an n-gram so split it up and weight accordingly
                    ngram_weight = len(aGram)
                    aGramPOS = filter(bool, strPOS.split(" "))
                    for ngram, ngram_pos in zip(aGram, aGramPOS):
                        aWordGram = self.getWordList(ngram
                                                    , pos=ngram_pos
                                                    , lang="fr")
                        if len(aWordGram) > 0:
                            # concat results together
                            aWord = aWord + aWordGram
                if len(aWord) == 0:
                    # still nothing? skip it then
                    continue
            # since word collision can occur, save confidence level for each 
            # heading score also normalize based on topic weight and whether 
            # we had to split ngram or not
            fConf = ((1.0 / len(aWord)) * float(result[3])) / ngram_weight

            for word in aWord:
                if word.headingid in aHeading:
                    aHeading[word.headingid] += fConf
                else:
                    aHeading[word.headingid] = fConf

        return aHeading



    def sortHierarchy(self,line_list):
        """ Sort tree to ensure declarations come before references """
        has_error = True
        new_list = line_list

        while has_error:
            has_error = False
            parent_idx = len(new_list)-1
            # iterate through each node in desc. order
            while parent_idx > 0:
                can_decrement = True # no errors found
                node = new_list[parent_idx]
                parent_node = node.split(",")
                parent_name = parent_node[1].rstrip()
                first_idx = None

                if parent_node[2].rstrip() == "\"\"":
                    # we are root
                    first_idx = 0
                else:
                    # find first reference of this parent node
                    for idx, parent in enumerate(new_list):
                        node_parent = parent.split(",")
                        node_name = node_parent[2].rstrip()
                        if node_name == parent_name:
                            # found it
                            first_idx = idx
                            break

                if first_idx is not None:
                    # we were referenced
                    if parent_idx > first_idx:
                    # parent node appears after first reference                        
                        has_error = True
                        can_decrement = False # repeat process on current index
                        parent = new_list[parent_idx]
                        # delete parent node
                        del new_list[parent_idx]
                        # push parent node before first reference
                        new_list.insert(first_idx, parent)

                if can_decrement:
                    parent_idx -= 1

        return "".join(new_list)



    def getTierIndexChildren(self, root):
        """ Get all immediate sub categories and tier below without subs """
        csv = "\"heading_id\",\"name\",\"parent\",\"size\",\"keyword\"\n"
        parent_list = {}        
        line_list = []
        # if we are looking for the root
        if root=="root":
            new_line = "\"" + root + "\",\"" + root + "\",\"\",,\n"
            line_list.append(new_line)
            parent_list[root] = 1
            # include all three root categories, the mind
            new_line = "\"1.NA.NA.NA.NA.NA.NA.1\"\
                ,\"1.NA.NA.NA.NA.NA.NA.1\",\"root\",,\n"
            line_list.append(new_line)
            parent_list["1.NA.NA.NA.NA.NA.NA.1"] = 1
            # the earth
            new_line = "\"2.NA.NA.NA.NA.NA.NA.1\"\
                ,\"2.NA.NA.NA.NA.NA.NA.1\",\"root\",,\n"
            line_list.append(new_line)
            parent_list["2.NA.NA.NA.NA.NA.NA.1"] = 1
            # society
            new_line = "\"3.NA.NA.NA.NA.NA.NA.1\"\
                ,\"3.NA.NA.NA.NA.NA.NA.1\",\"root\",,\n"
            line_list.append(new_line)
            parent_list["3.NA.NA.NA.NA.NA.NA.1"] = 1
            # get tier index list
            aHeading = self.db.execQuery("""
            select tierindex, tiering from heading 
            where tierindex like %s 
            and id in (select distinct headingid from topic)
            group by tierindex, tiering""",('%.NA.NA.NA.NA.NA.NA',))
        else:
            # we are not root node
            tier = root.split(".")
            tier_index = ".".join(t for t in tier[:7])
            sub_tier = ".".join(t for t in tier[7:])
            # get immediate parent of this node
            parent_root, parent_sub = self.getParentTier(root)
            if parent_root == "":
                parent_tier = "root"
            else:
                parent_tier = parent_root + "." + parent_sub
            # append to csv the parent
            new_line = "\"" + parent_tier 
                + "\",\"" + parent_tier 
                + "\",\"\",,\n"        
            line_list.append(new_line)
            parent_list[parent_tier] = 1
            # now append to csv the node
            new_line = "\"" + root 
                + "\",\"" + root 
                + "\",\"" + parent_tier 
                + "\",,\n"
            line_list.append(new_line)
            parent_list[root] = 1
            
            if "sub" in sub_tier:
                # ensure we are of type sub.n
                if sub_tier.count(".") > 1:
                    sub_tier = sub_tier.rsplit(".", 1)[0]
                sub_tier += "%"
                # get nodes around this sub node
                aHeading = self.db.execQuery("""
                select tierindex
                , tiering
                from heading
                where tierindex=%s and tiering like %s 
                and id in (select distinct headingid from topic)
                group by tierindex, tiering
                """,(tier_index,sub_tier))
            else:
                # go up one node
                query_tier = ""
                na_found = False
                for idx, t in enumerate(tier[:7]):
                    if idx > 0:
                        query_tier += "."
                    if (not na_found and t == "NA") 
                            or (idx == 6 and not na_found):
                        query_tier += "%"
                        na_found = True
                        continue
                    query_tier += t
                # and search for anything around that node
                aHeading = self.db.execQuery("""
                select tierindex
                , tiering
                from heading
                where (tierindex=%s) 
                or (tierindex like %s 
                and tierindex != %s 
                and tiering not like %s) 
                and id in (select distinct headingid from topic)
                group by tierindex, tiering
                """,(tier_index, query_tier, tier_index, "sub%"))

        # for all the headings found
        for result in aHeading:
            tier_index = result[0] + "." + result[1]
            # make sure their parents exist in our CSV
            while tier_index not in parent_list:
                parent_tier, parent_sub = self.getParentTier(tier_index)
                parent_index = parent_tier + "." + parent_sub
                new_line = "\"" + tier_index 
                    + "\",\"" + tier_index 
                    + "\",\"" + parent_index 
                    + "\",,\n"
                line_list.append(new_line)
                parent_list[tier_index] = 1
                tier_index = parent_index
        
        csv += self.sortHierarchy(line_list) # sort references in our csv
        csv += self.getHeadingCSVList(parent_list) # now append all children

        return csv



    def getHeadingCSVList(self, parent_list):
        """ Convert array of headings into a CSV """
        csv = ""
        for key in parent_list:
            tier = key.split(".")
            tier_index = ".".join(t for t in tier[:7])
            root_tier = ".".join(t for t in tier[7:])
            # get all nodes for this heading
            aHeading = self.db.execQuery("""
            select id
            , heading
            , fr_heading
            , concat(tierindex,'.',tiering) parent
            from heading
            where tierindex=%s and tiering=%s
            """, (tier_index,root_tier))
            # append all nodes to csv
            for result in aHeading:
                csv += "\"" + str(result[0]) 
                    + "\",\"" + result[1] 
                    + "\",\"" + result[3] 
                    + "\",\"10\",\"1\"\n"
        return csv



    def getParentTier(self, root):
        """ Get parent tier of tier index """
        root_tier = root.split(".")

        if len(root_tier) == 10: # sub.n.n turns to sub.n
            tier = ".".join(t for t in root_tier[:7])
            sub_tier = root_tier[7] + "." + root_tier[8]
        elif len(root_tier) == 9: # sub.n turns to n
            tier = ".".join(t for t in root_tier[:7])
            sub_tier = root_tier[-1]
        else: # not sub cat - move tiers
            tier = ""
            start_na = False
            last_idx = 6
            # generate new tier index
            for idx, t in enumerate(root_tier[:7]):
                if idx > 0:
                    tier += "."
                # look for where NA's start
                if idx < len(root_tier)-1 and not start_na:
                    if root_tier[idx+1] == "NA":
                        if idx == 0: # we are root node
                            return "", ""
                        start_na = True
                        last_idx = idx
                # fill rest of tier index with NA if needed
                if start_na or idx == len(root_tier)-1:
                    tier += "NA"
                else:
                    # otherwise insert node
                    tier += t

            sub_tier = str(last_idx)
        return tier, sub_tier
