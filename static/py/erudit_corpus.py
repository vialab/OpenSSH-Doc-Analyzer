import db
import constants as CONST
import math
import re
from scipy import spatial
from lz4.frame import compress, decompress

db = db.Database()

def matchHeadingList(search_id, heading_list, n=100):
    """ Match an array of selected topics to the corpus """
    if len(heading_list) == 0:
        return []
    for heading in heading_list:
        heading_id = heading["heading_id"]
        weight = heading["weight"]
        order = heading["order"]
        db.execUpdate("""
        insert into topicsearch(searchid, topicid, dist, rank)
        select %s
        , id
        , %s
        , %s
        from topic 
        where headingid=%s
        limit 1
        """, (search_id, weight, order, heading_id))

    # parametize our list to use in where in clause
    id_list = ",".join([int(heading["heading_id"]) for heading in heading_list])
    return db.execQuery("""
        select d.documentid, sum(d.tfidf)
        from tfidf t
        left join doctfidf d on d.termid=t.termid
        where t.headingid in (%s)
        group by d.documentid
        order by sum(d.tfidf) desc
        limit %s
        """, (id_list,n))


def matchKeyword(search_id, keyword_list, n=100):
    if len(keyword_list) == 0:
        return ()

    # clean list of special characters
    clean_list = []
    for word in keyword_list:
        clean_list.append(re.sub('[^A-Za-z0-9]+', '', word))
    
    keywords = "|".join(clean_list)
    return db.execQuery("""
        select d.documentid
        , sum(d.tfidf) score 
        from doctfidf d
        where d.term REGEXP %s
        group by d.documentid
        limit %s
        """, (keywords,n))



def getDocumentInfo(document_id):
    """ Get corpus document meta info """
    return db.execQuery("""
        select d.id
        , ifnull(t.titre, t.surtitre) titre
        , (select group_concat(concat(prenom
                ,   CASE  WHEN autreprenom != '' and autreprenom is not null 
                        THEN concat(' ', autreprenom) ELSE '' 
                    END
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
        """, (document_id,))



def calculateCosSim(dochash_id, document_id):
    """ Calculate cosine similarity between input and compressed corpus doc """
    user_topic = db.execQuery(""" select dist 
    from userdoctopic 
    where dochashid=%s 
    order by topicid""", (dochash_id,))

    user_topic = [float(topic[0]) for topic in user_topic]
    comp_topiclz = db.execQuery(""" select topichash 
    from doctopiclz 
    where documentid=%s limit 1""", (document_id,))

    comp_topic = decompress(comp_topiclz[0][0].decode("utf8").encode("latin1"))
    comp_topic = comp_topic.split(",")
    doc_topic = [float(dist.split("-")[1]) for dist in comp_topic]
    return 1-spatial.distance.cosine(user_topic, doc_topic)