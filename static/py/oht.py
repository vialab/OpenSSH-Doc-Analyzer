# -*- coding: utf-8 -*-
import db
import codecs
import constants as CONST
import unicodecsv
import cPickle as pickle
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
                , t.pos
                from word w
                left join tfidf t on t.wordid=w.id
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
        , h.pos
        , ifnull(p.size, 0)
        from heading h
        left join thematicheading th on th.id=h.thematicheadingid
        left join wordsize p on p.headingid=h.id
        where h.id=%s""", (strID,))
        self.id = heading[0][0]
        self.thematicheadingid = heading[0][1]
        self.en = heading[0][2]
        self.fr = heading[0][3]
        self.thematicheading = heading[0][4]
        self.fr_thematicheading = heading[0][5]
        self.tierindex = heading[0][6]
        self.atierindex = heading[0][6].replace(".NA", "").split(".")
        self.subcat = heading[0][7]
        self.pos = heading[0][8]
        self.size = heading[0][9]


    def PartOfSpeech(self):
        """ Returns all parts of speech for a given tier """
        results = self.db.execQuery("""select h.id, w.size
            from heading h
            left join wordsize w on w.headingid=h.id
            where h.tierindex=%s and h.subcat=''
            """, (self.tierindex,))
        pos_list = []
        for result in results:
            pos_list.append(Heading(result[0]))
        return pos_list


    def Synset(self):
        """ Returns list of words categorized within current heading """
        results = self.db.execQuery("""
            select w.fr_translation
                , w.headingid
				, case when w.en_docs > 0 or w.fr_docs > 0
					then concat('en',w.en_docs,'fr',w.fr_docs)
                    else null end
            from word w
            where w.headingid=%s
            group by w.id, w.fr_translation, w.headingid
            order by case when (w.en_docs+w.fr_docs) > 0 then 1 else 0 end desc
            , w.fr_translation;""", (self.id,))
        words = []
        for result in results:
            temp = {}
            temp["name"] = result[0]
            temp["heading_id"] = result[1]
            temp["enable"] = result[2]
            words.append(temp)
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
    child_count = {}
    synset_count = {}


    def __init__(self):
        self.db.execProc("sp_tfidf_cache")
        counts = self.db.execQuery("""select h.id, count(h2.id)
            from heading h
            left join heading h2 on h2.parentid=h.id and h2.pos='n' and h2.subcat=''
            left join wordsize w on w.headingid=h2.id
            where h.pos='n' and h.subcat='' and w.size > 0
            group by h.id;
        """)
        # synsets = self.db.execQuery("""select w.headingid
        #       , count(*)
        #   from word w
        #   left join tfidf wc on wc.wordid=w.id
        #   where w.headingid in (select distinct id from heading where subcat='')
        #     and wc.termid in (select termid from term_cache)
        #   group by w.headingid;
        # """, to_dict=True)
        # pos = self.db.execQuery("""select h.parentid
        #     , count(*)
        #   from word w
        #   left join tfidf wc on wc.wordid=w.id
        #   left join heading h on h.id=w.headingid
        #   where w.headingid in (select distinct id from heading where subcat='' and pos!='n')
        #     and wc.termid in (select termid from term_cache)
		# group by h.parentid;
        # """, to_dict=True)
        # preprocess and cache results for RT retrieval
        for count in counts:
            _heading_id = str(count[0])
            self.child_count[_heading_id] = count[1] # how many children
            # count how big their synset is
            # heading = Heading(count[0])
            # heading_count = 0
            # if _heading_id in synsets:
            #     heading_count = synsets[_heading_id][0]
            # if _heading_id in pos:
            #     heading_count += pos[_heading_id][0]

            # self.synset_count[_heading_id] = { "heading": heading_count, "children":0 }
            # # check if we have children to count
            # if count[1] == 0:
            #     continue
            # # get list of children
            # headings = self.getHeadingChildrenCSVList(heading_id=_heading_id, output_csv=False)
            # n = 0
            # # save total size of this branch
            # for h in headings:
            #     h_id = str(h[0])
            #     if h_id in synsets:
            #         n += synsets[h_id][0]
            #     if h_id in pos:
            #         n += pos[h_id][0]
            # self.synset_count[_heading_id]["children"] = n
        # # cached this because it made startup take ~5 mins
        # with open("./model/pkl/synset.pkl", "w+") as f:
        #     pickle.dump(self.synset_count, f)
        with open("./model/synset.pkl", "r") as f:
            self.synset_count = pickle.load(f)



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
        left join wordsize ws on ws.headingid=h.id
        where w.word like %s and h.id in (select headingid from tfidf_cache) and h.pos='n'
        and (ws.size > 0 or ws.pos_size > 0)
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


    def getTierIndexChildren(self, heading_id):
        """ Get all immediate sub categories and tier below without subs """
        csv = self.getCSVLine("heading_id","name","parent","size","keyword", "tier", "cat", "length", "set_size", "child_size")
        parent_list = {}
        line_list = []
        # get our tier index
        root = self.getTierIndex(heading_id)
        root_cat = root.split(".")[0]
        # if we are looking for the root
        if root=="root":
            # set "root" as top of hierarchy
            new_line = self.getCSVLine("root","root", tier="-1")
            line_list.append(new_line)
            parent_list["root"] = False
            # only need children so include all three root categories, the earth
            new_line = self.getCSVLine("181456","Le Monde","root", cat="1")
            line_list.append(new_line)
            parent_list["181456"] = True
            # the mind
            new_line = self.getCSVLine("295250","L'Esprit","root", cat="2")
            line_list.append(new_line)
            parent_list["295250"] = True
            # society
            new_line = self.getCSVLine("325638","Société","root", cat="3")
            line_list.append(new_line)
            parent_list["325638"] = True
        else:
            # we are not root node
            root_heading = Heading(heading_id)
            parent_tier, sub, parent_id = self.getParentTier(root)
            if parent_id == "root":
                heading_name = "root"
            else:
                h = self.db.execQuery("select fr_heading from heading where id=%s", (parent_id,))
                heading_name = h[0][0]
            # set our parent as the root
            new_line = self.getCSVLine(parent_id, heading_name, tier="-1")
            line_list.append(new_line)
            parent_list[parent_id] = False
            # then add in us
            new_line = self.getCSVLine(heading_id, root_heading.fr, parent_id, cat=root_cat)
            line_list.append(new_line)
            parent_list[heading_id] = True

        csv += self.sortHierarchy(line_list) # sort references in our csv
        if root != "root":
            csv += self.getHeadingChildrenCSVList(root, heading_id, parent_list) # now append all children
        return csv


    def getParentHeadingList(self, tier_index, parent_tier, child_tier):
        """ Based on a tierindex, get a list of headings for this tier """
        return self.db.execQuery("""
            select h.tierindex
            , h.tiering
            , case when h.t2='NA' then '1'
                when h.t3='NA' then '2'
                when h.t4='NA' then '3'
                when h.t5='NA' then '4'
                when h.t6='NA' then '5'
                when h.t7='NA' then '6'
                else 0 end
            , h.t1
            , h.heading
            from heading h
            where (h.tierindex=%s or h.tierindex like %s or (h.tierindex like %s))
            and h.pos='n' and h.subcat=''
            and h.id in (select distinct headingid from tfidf_cache)
            group by h.tierindex, h.tiering, case when h.t2='NA' then '1'
                when h.t3='NA' then '2'
                when h.t4='NA' then '3'
                when h.t5='NA' then '4'
                when h.t6='NA' then '5'
                when h.t7='NA' then '6'
                else 0 end
            , h.t1
            , h.heading
            """,(tier_index, parent_tier, child_tier))



    def getCSVLine(self, heading_id="", name="", parent="", size="", keyword="", tier="0", cat="0", length="", set_size="", child_size=""):
        """ Helper function to standardize creating CSV lines """
        if length == "":
            if heading_id in self.child_count:
                length = self.child_count[heading_id]
            else:
                length = "0"

        if (set_size == "" or child_size == "") and heading_id!="root":
            result = self.db.execQuery("select size, pos_size from wordsize where headingid=%s"
                , (heading_id,))
            set_size = result[0][1]
            child_size = result[0][0]

        new_line = "\"" + str(heading_id) \
            + "\",\"" + name \
            + "\",\"" + str(parent) \
            + "\",\"" + str(size) \
            + "\",\"" + str(keyword) \
            + "\",\"" + str(tier) \
            + "\",\"" + str(cat) \
            + "\",\"" + str(length) \
            + "\",\"" + str(set_size) \
            + "\",\"" + str(child_size) + "\"\n"
        return new_line


    def getHeadingChildrenCSVList(self, root=None, heading_id=None, parent_list={}, output_csv=True):
        """ Get our tier children and format them for CSV """
        if root is None:
            root = self.getTierIndex(heading_id)
        csv = ""
        query_tier = ""
        tier = root.split(".")
        found_na = False
        last_index = 1
        count = 0
        # get wild card for children query
        for i, t in enumerate(tier):
            if i > 0:
                query_tier += "."
            if found_na and count < 1:
                # redundant, but here to be able to wild card more tiers
                query_tier += "NA"
                count += 1
            elif t == "NA" and not found_na:
                found_na = True
                query_tier += "%"
                last_index = i+1
            else:
                query_tier += t

        headings = self.db.execQuery("""
            select h.id
            , h.fr_heading
            , h.t1
            , h.tierindex
            , case when h.t2='NA' then '1'
                when h.t3='NA' then '2'
                when h.t4='NA' then '3'
                when h.t5='NA' then '4'
                when h.t6='NA' then '5'
                when h.t7='NA' then '6'
                else 0 end
            , case when h.parentid=0 then 'root' else h.parentid end
            , ifnull(w.pos_size, 0)
            , ifnull(w.size, 0)
            from heading h
            left join wordsize w on w.headingid=h.id
            where h.tierindex like %s and h.pos='n' and h.subcat=''
            and h.parentid is not null
            and t""" + str(last_index) + "!= 'NA'", (query_tier,))

        if not output_csv:
            return headings

        for h in headings:
            h_id = str(h[0])
            if h_id in parent_list:
                continue
            if h[6] == 0 and h[7] == 0:
                continue
            parent_list[h_id] = True
            p_id = str(h[5])
            while p_id not in parent_list:
                p = self.db.execQuery("""select h.id
                        , h.heading
                        , h.t1
                        , h.tierindex
                        , case when h.t2='NA' then '1'
                            when h.t3='NA' then '2'
                            when h.t4='NA' then '3'
                            when h.t5='NA' then '4'
                            when h.t6='NA' then '5'
                            when h.t7='NA' then '6'
                            else 0 end
                        , case when h.parentid=0 then 'root' else h.parentid end
                    from heading h where h.id=%s and h.pos='n' and h.subcat=''
                    and h.parentid is not null""", (p_id,))
                if len(p) == 0 or str(p[0][0]) in parent_list:
                    p_id = heading_id
                    break
                p_id = str(p[0][5])
                parent_list[str(p[0][0])] = True
                csv += self.getCSVLine(str(p[0][0]), p[0][1], p_id, "10", "1", str(p[0][4]), p[0][2], set_size=h[6], child_size=h[7])
            csv += self.getCSVLine(str(h[0]), h[1], p_id, "10", "1", str(h[4]), h[2], set_size=h[6], child_size=h[7])
        return csv


    def getHeadingCSVList(self, parent_list):
        """ Convert array of headings into a CSV """
        csv = ""
        for key in parent_list:
            if not parent_list[key]:
                continue
            aParent = self.db.execQuery("""
            select tierindex, tiering
            from heading where id=%s
            """, (key,))
            tier_index = aParent[0][0]
            root_tier = aParent[0][1]
            # get all nodes for this heading
            aHeading = self.db.execQuery("""
            select h.id
            , h.heading
            , h.fr_heading
            , concat(h.tierindex,'.',h.tiering) parent
            , case when h.t2='NA' then '1'
                when h.t3='NA' then '2'
                when h.t4='NA' then '3'
                when h.t5='NA' then '4'
                when h.t6='NA' then '5'
                when h.t7='NA' then '6'
                else 0 end
            , h.tiering
            , h.t1
            from heading h
            where h.tierindex=%s and h.tiering=%s and h.pos='n' and h.subcat=''
            and h.id in (select distinct headingid from tfidf_cache)
            """, (tier_index,root_tier))
            # append all nodes to csv
            for result in aHeading:
                if str(result[0]) in parent_list:
                    continue
                try:
                    tier = int(result[4])
                    if "sub" in result[5]:
                        tier += 1
                except:
                    tier = 0
                h = self.db.execQuery("""
                select h.id
                from heading h
                where h.tierindex=%s and h.pos='n' and h.subcat=''
                and h.id in (select distinct headingid from tfidf_cache)
                limit 1
                """, (tier_index,))
                csv += self.getCSVLine(str(result[0]), result[1], str(h[0][0]), "10", "1", str(tier), result[6])
        return csv


    def getParentTier(self, root):
        """ Get parent tier of tier index """
        if root == "":
            return "root", "", "root"
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
                            return "", "", "root"
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
        and pos='n' and subcat=''
        """, (tier,))
        if len(results) == 0:
            return self.getParentTier(tier)
        else:
            parent_id = str(results[0][0])
            if parent_id == "":
                parent_id = "root"
        return tier, sub_tier, parent_id


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
            and pos='n' and subcat=''
            order by tiering, subcat
            limit 1""", (".".join(root_tier),sub_query))
            if len(results) > 0:
                return results[0][0] + "." + results[0][1]
        else:
            results = self.db.execQuery("""
            select tierindex, tiering
            from heading
            where tierindex = %s and tiering != ''
            and pos='n' and subcat=''
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
        """ Get term information associated with OHT """
        search_term = []
        for term in aTF:
            if term is None:
                continue
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
        top_index = "1.NA.NA.NA.NA.NA.NA"
        for term in search_term:
            if term is None or term["heading_id"] is None:
                continue
            key = term["heading_id"]
            if key in aHeading:
                aHeading[key] += 1
            else:
                aHeading[key] = 1

            if aHeading[key] > top_freq:
                top_freq = aHeading[key]
                top_heading = key
                if "sub" in term["tier_index"]:
                    top_index = self.getParentTier(term["tier_index"])[0]
                else:
                    top_index = term["tier_index"]
        return self.getTierIndexTrio(top_index)


    def getTierIndexTrio(self, root_tier):
        """ Given a tier index, also get its parent and immediate child """
        tier_index = {}
        tier_index["home"] = self.getHeadingId(root_tier)
        tier_index["parent"] = self.getParentTier(root_tier)[2]
        tier_index["child"] = self.getHeadingId(self.getFirstChildTier(root_tier))
        return tier_index


    def getClosestHeading(self, root_tier, heading_list):
        """ Given a list of headings, return the heading closest to given tier"""
        root = root_tier.split(".")[:7]
        top_score = -1.0
        top_heading = None
        for heading in heading_list:
            if heading["heading_id"] is None:
                continue
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
                    continue

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
                t["term_id"] = term[8]
                t["pos"] = term[9]
                t["posdesc"] = term[10]
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
            if term["heading_id"] is None:
                continue
            total_score = 0
            temp = [term]
            # loop through rest of terms
            for key in term_list:
                if term_list[key][0]["heading_id"] is None:
                    temp.append(term_list[key][0])
                    continue
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


    def getTierIndex(self, heading_id):
        results = self.db.execQuery("""
        select tierindex from heading
        where id=%s
        """, (heading_id,))
        if len(results) > 0:
            return results[0][0]
        return "root"

    def getHeadingId(self, tier_index):
        results = self.db.execQuery("""
        select id from heading
        where tierindex=%s
        and pos='n' and subcat=''
        """, (tier_index,))
        if len(results) > 0:
            return str(results[0][0])
        return "root"
