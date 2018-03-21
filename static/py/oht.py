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
            select w.id, wc.id
            from word w
            left join word_cache wc on wc.wordid=w.id
            where w.headingid=%s
            order by wc.id desc""", (self.id,))
        words = []
        for result in results:
            if result[1]:
                bEnable = True
            else:
                bEnable = False
            word = { "word":Word(result[0]), "enable": bEnable }
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
            where tierindex=%s and tiering not like 'sub%%'
            and id in (select distinct headingid from tfidf_cache)
            """, (strIndex,))
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
            where tierindex=%s and tiering not like 'sub%%'
            and id in (select distinct headingid from tfidf_cache)
            """,(self.tierindex,))
        headings = []
        for result in results:
            heading = Heading(result[0])
            headings.append(heading)
        return headings


    def Cohyponym(self):
        """ Returns a list of heading objects that are adjacent
            to the current heading """
        results = self.db.execQuery("""
            select id
            from heading
            where tierindex=%s and id != %s
            and id in (select distinct headingid from tfidf_cache)
            """, (self.tierindex,self.id))
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

    def __init__(self):
        self.db.execProc("sp_tfidf_cache")

    def getKeywords(self, keyword, n=10):
        """ Returns a list of headings that have a matching keyword """
        return self.db.execQuery("""
        select distinct h.id
            , h.heading
            , h.fr_heading
            , th.fr_thematicheading
            , concat(h.tierindex, case when h.tiering is not null then concat('.', h.tiering) else '' end)
        from word w
        left join heading h on h.id=w.headingid
        left join thematicheading th on th.id=h.thematicheadingid
        where w.word like %s and h.id in (select headingid from tfidf_cache)
        limit %s
        """, ("%" + keyword + "%", n))

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
                    pass
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
        csv = self.getCSVLine("heading_id","name","parent","size","keyword", "tier")
        parent_list = {}        
        line_list = []
        # set "root" as top of hierarchy
        new_line = self.getCSVLine("root","root", tier="-1")
        line_list.append(new_line)
        parent_list["root"] = False
        # if we are looking for the root
        if root=="root":
            # include all three root categories, the mind
            new_line = self.getCSVLine("1.NA.NA.NA.NA.NA.NA","1.NA.NA.NA.NA.NA.NA","root")
            line_list.append(new_line)
            parent_list["1.NA.NA.NA.NA.NA.NA"] = True
            # the earth
            new_line = self.getCSVLine("2.NA.NA.NA.NA.NA.NA","2.NA.NA.NA.NA.NA.NA","root")
            line_list.append(new_line)
            parent_list["2.NA.NA.NA.NA.NA.NA"] = True
            # society
            new_line = self.getCSVLine("3.NA.NA.NA.NA.NA.NA","3.NA.NA.NA.NA.NA.NA","root")
            line_list.append(new_line)
            parent_list["3.NA.NA.NA.NA.NA.NA"] = True
            # get tier index list
            aHeading = self.db.execQuery("""
            select tierindex
            , tiering 
            case when t2='NA' then '1'
                    when t3='NA' then '2'
                    when t4='NA' then '3'
                    when t5='NA' then '4'
                    when t6='NA' then '5'
                    when t7='NA' then '6'
                    else 0 end
            from heading 
            where tierindex like %s 
            and id in (select distinct headingid from tfidf_cache)
            group by tierindex, tiering, case when t2='NA' then '1'
                    when t3='NA' then '2'
                    when t4='NA' then '3'
                    when t5='NA' then '4'
                    when t6='NA' then '5'
                    when t7='NA' then '6'
                    else 0 end""",('%.NA.NA.NA.NA.NA.NA',))
        else:
            # we are not root node
            tier = root.split(".")
            tier_index = ".".join(t for t in tier[:7])
            parent_tier, sub = self.getParentTier(tier_index)
            sub_tier = ".".join(t for t in tier[7:])

            # get all related headings (parent, sibling, children)
            child_tier = ""
            na_found = False
            for idx, t in enumerate(tier[:7]):
                if idx > 0:
                    child_tier += "."
                if (not na_found and t == "NA"):
                    child_tier += "%"
                    na_found = True
                    continue
                child_tier += t
            if parent_tier == "":
                aHeading = self.db.execQuery("""
                select tierindex
                , tiering
                , case when t2='NA' then '1'
                    when t3='NA' then '2'
                    when t4='NA' then '3'
                    when t5='NA' then '4'
                    when t6='NA' then '5'
                    when t7='NA' then '6'
                    else 0 end
                from heading
                where (tierindex=%s or tierindex like %s or (tierindex like %s))
                and id in (select distinct headingid from tfidf_cache)
                group by tierindex, tiering, case when t2='NA' then '1'
                    when t3='NA' then '2'
                    when t4='NA' then '3'
                    when t5='NA' then '4'
                    when t6='NA' then '5'
                    when t7='NA' then '6'
                    else 0 end
                """,(tier_index, "%.NA.NA.NA.NA.NA.NA", child_tier))
            else:
                aHeading = self.db.execQuery("""
                select tierindex
                , tiering
                , case when t2='NA' then '1'
                    when t3='NA' then '2'
                    when t4='NA' then '3'
                    when t5='NA' then '4'
                    when t6='NA' then '5'
                    when t7='NA' then '6'
                    else 0 end
                from heading
                where (tierindex=%s or tierindex=%s or (tierindex like %s))
                and id in (select distinct headingid from tfidf_cache)
                group by tierindex, tiering, case when t2='NA' then '1'
                    when t3='NA' then '2'
                    when t4='NA' then '3'
                    when t5='NA' then '4'
                    when t6='NA' then '5'
                    when t7='NA' then '6'
                    else 0 end
                """,(tier_index, parent_tier, child_tier))

        # for all the headings found
        for result in aHeading:
            tier_index = result[0]+'.'+result[1]
            # make sure their parents exist in our CSV
            while tier_index not in parent_list:
                parent_tier, sub = self.getParentTier(tier_index)
                if parent_tier == "":                
                    parent_tier = "root"
                if sub != "":
                    parent_tier = parent_tier + "." + sub
                tier = -1
                for t in parent_tier.split("."):
                    if t == "NA":
                        break
                    tier += 1                    
                new_line = self.getCSVLine(tier_index, tier_index, parent_tier, tier=str(tier))
                line_list.append(new_line)
                parent_list[tier_index] = True
                tier_index = parent_tier
    
        csv += self.sortHierarchy(line_list) # sort references in our csv
        csv += self.getHeadingCSVList(parent_list) # now append all children
        return csv


    def getCSVLine(self, heading_id="", name="", parent="", size="", keyword="", tier="0"):
        """ Helper function to standardize creating CSV lines """
        new_line = "\"" + heading_id \
            + "\",\"" + name \
            + "\",\"" + parent \
            + "\",\"" + size \
            + "\",\"" + keyword \
            + "\",\"" + tier + "\"\n"
        return new_line


    def getHeadingCSVList(self, parent_list):
        """ Convert array of headings into a CSV """
        csv = ""
        for key in parent_list:
            if not parent_list[key]:
                continue
            tier = key.split(".")
            tier_index = ".".join(t for t in tier[:7])
            root_tier = ".".join(t for t in tier[7:])
            # get all nodes for this heading
            aHeading = self.db.execQuery("""
            select id
            , heading
            , fr_heading
            , concat(tierindex,'.',tiering) parent
            , case when t2='NA' then '1'
                when t3='NA' then '2'
                when t4='NA' then '3'
                when t5='NA' then '4'
                when t6='NA' then '5'
                when t7='NA' then '6'
                else 0 end
            from heading
            where tierindex=%s and tiering=%s
            and id in (select distinct headingid from tfidf_cache)
            """, (tier_index,root_tier))
            # append all nodes to csv
            for result in aHeading:
                csv += self.getCSVLine(str(result[0]), result[1], result[3], "10", "1", result[4])
        return csv

    

    def getParentTier(self, root):
        """ Get parent tier of tier index """
        if root == "":
            return "root", ""
        root_tier = root.split(".")
        if len(root_tier) > 9: # sub.n.i turns to n
            tier = ".".join(t for t in root_tier[:7])
            sub_tier = root_tier[8]
        else: # not sub cat - move tiers
            tier = ""
            sub_tier = ""            
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
                if start_na or idx+1 == len(root_tier)-1:
                    tier += "NA"
                else:
                    # otherwise insert node
                    tier += t
        # recurse until we find closest tier we actually use
        results = self.db.execQuery("""
        select id from heading
        where tierindex=%s
        and id in (select id from tfidf_cache)
        """, (tier,))
        if len(results) == 0:
            return self.getParentTier(tier)
        return tier, sub_tier


    def getFirstChildTier(self, root):
        """ Get child tier of current tier index """
        root_tier = root.split(".")[:7]
        sub_tier = root.split(".")[7:]

        if len(sub_tier) > 1:
            # no children beyond this point
            return ""
        elif len(sub_tier) == 1:
            # check for sub.sub children
            sub_query = "sub." + sub_tier[0] + ".%"
            results = self.db.execQuery("""
            select tierindex, tiering
            from heading
            where tierindex = %s and tiering like %s
            and id in (select id from tfidf_cache)
            order by tiering, subcat
            limit 1""", (".".join(root_tier),sub_query))
            if len(results) > 0:
                return results[0][0] + "." + results[0][1]
        else:
            results = self.db.execQuery("""
            select tierindex, tiering
            from heading
            where tierindex = %s and tiering != ''
            and id in (select id from tfidf_cache)
            order by tiering, subcat
            limit 1""", (root,))
            if len(results) > 0:
                return results[0][0] + "." + results[0][1]

        # go down one root tier level
        tier = ""
        start_na = False
        last_index = 1
        if root_tier[-1] != "NA":
            # we are already at the deepest level
            return ".".join(root_tier)
        elif root == "root": 
            return "1.NA.NA.NA.NA.NA.NA"
        else:
            # we need to build a tier for search query
            for idx, t in enumerate(root_tier):
                if idx > 0:
                    tier += "."
                # look for where NA's first start
                if root_tier[idx] == "NA" and not start_na:
                    # found first NA so make it wild card
                    start_na = True
                    tier += "%"
                    last_index = idx+1
                else:
                    # otherwise insert node
                    tier += t
        t = "t"+str(last_index)
        results = self.db.execQuery("""
        select tierindex, tiering
        from heading
        where tierindex like %s
        and """ + t +  """!= 'NA'
        order by cast(""" + t + """ as UNSIGNED)
        limit 1""", (tier,))
        if len(results) > 0:
            return results[0][0] + "." + results[0][1]
        else:
            return ""


    def getTfidfHeadingList(self, aTF):
        search_term = []
        for term in aTF:
            aWord = {}
            heading = self.db.execQuery("""select t.termid
            , t.word
            , h.fr_heading
            , th.fr_thematicheading
            , concat(h.tierindex, case when h.tiering is not null 
                then concat('.', h.tiering) else '' end)
            , t.headingid
            from tfidf t 
            left join heading h on h.id=t.headingid
            left join thematicheading th on th.id=h.thematicheadingid
            where t.termid=%s""", (term,))
            aWord["id"] = heading[0][0]
            aWord["name"] = heading[0][1]
            aWord["dist"] = aTF[term]["tfidf"]
            aWord["heading"] = heading[0][2]
            aWord["thematicheading"] = heading[0][3]
            aWord["tier_index"] = heading[0][4]
            aWord["heading_id"] = heading[0][5]
            search_term.append(aWord)
        return search_term


    def getTierIndexIntersection(self, search_term):
        """ Given a list of headings, return closest common tier """
        aHeading = {}
        top_freq = 0
        top_tier = ""
        for term in search_term:
            key = term["heading_id"]
            if key in aHeading:
                aHeading[key] += 1
            else:
                aHeading[key] = 1
            
            if aHeading[key] > top_freq:
                top_freq = aHeading[key]
                top_heading = key
                top_index = term["tier_index"]
        return self.getTierIndexTrio(top_index)

    
    def getTierIndexTrio(self, root_tier):
        """ Given a tier index, also get its parent and immediate child """
        tier_index = {}
        tier_index["home"] = root_tier
        tier_index["parent"] = self.getParentTier(root_tier)
        tier_index["child"] = self.getFirstChildTier(root_tier)
        return tier_index

    
    def getClosestHeading(self, root_tier, heading_list):
        """ Given a list of headings, return the heading closest to given tier"""
        root = root_tier.split(".")[:7]
        top_score = -1.0
        top_heading = None
        for heading in heading_list:
            heading_score = 0.0
            tier = heading["tier_index"].split(".")[:7]
            # calculate score, cascading tiers (e.g. point per matching tier)
            for x, y in zip(root, tier):
                if x == "NA" and y == "NA":
                    # we are done here
                    break
                if x == "NA" or y == "NA":
                    # penalize for being broader/narrower (top-bottom = -1)
                    heading_score -= 0.2
                
                if x != y:
                    # give partial marks proportional to difference
                    ix = float(x)
                    iy = float(y)
                    heading_score += 1-abs(((ix-iy)/max(ix,iy)))
                    break
                heading_score += 1
            # use this heading if better score
            if heading_score > top_score:
                top_heading = heading
                top_score = heading_score
        return top_heading, top_score


    def aggregateByRelevance(self, results):
        """ Based off a list of indistinct search terms, 
            return most tightly related distinct set """
        term_list = {}    
        if len(results) > 0:
            for term in results:
                t = {}
                if term[0] is not None:
                    t["heading_id"] = term[0]
                    t["tier_index"] = term[4]
                    t["heading"] = term[5]
                    t["word"] = term[5]
                else:
                    t["word"] = term[1]
                    t["keyword"] = term[1]
                    t["heading_id"] = term[6]
                    t["tier_index"] = term[7]
                t["weight"] = term[2]
                t["order"] = term[3]
                # save duplicates to an array
                if t["word"] not in term_list:
                    term_list[t["word"]] = [t]
                else:
                    term_list[t["word"]].append(t)

        # only use most relevant headings and compare correlation
        search_list = []
        base_word = next(iter(term_list))
        best_score = -1 # first one always wins incase of tie
        # correlation will be based off the first keyword    
        for term in term_list[base_word]:
            total_score = 0
            temp = [term]
            # loop through rest of terms
            for key in term_list:
                if key == base_word:                
                    continue
                heading, score = self.getClosestHeading(term["tier_index"], term_list[key])
                temp.append(heading)
                total_score += score
            # use this set of unique search terms if better correlation
            if total_score > best_score:
                best_score = total_score
                search_list = temp

        return {
            "content": search_list,
            "tier_index": self.getTierIndexIntersection(search_list)
        }
                