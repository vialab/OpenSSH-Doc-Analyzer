import db
import constants as CONST
import math
from scipy import spatial
from lz4.frame import compress, decompress

db = db.Database()

def matchTopicList(topic_list, n=100):
    """ Match an array of selected topics to the corpus """
    cursor = db.beginSession()
    result = db.execSessionQuery(cursor, """
    insert into search(querytype) values('topic');
    """)
    result = db.execSessionQuery(cursor, """
    select last_insert_id();
    """)
    search_id = result[0][0]

    for topic in topic_list:
        heading_id = topic["heading_id"]
        weight = topic["weight"]
        order = topic["order"]
        db.execSessionQuery(cursor, """ 
        insert into topicsearch(searchid, topicid, dist, rank)
        select %s
        , id
        , %s
        , %s
        from topic 
        where headingid=%s
        limit 1
        """, (search_id, weight, order, heading_id))
    
    return db.execProc("sp_searchtopic", (
        search_id
        , len(topic_list)
        , CONST.DS_PENALTY
        , n
    ))



def match(dochash_id, n=100):
    """ Find closest matching docs using ranked weighted penalty distance """
    return db.execProc("sp_searchdoc", (
        dochash_id        
        , CONST.DS_MAXTOPIC
        , CONST.DS_PENALTY
        , n
    ))
    


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