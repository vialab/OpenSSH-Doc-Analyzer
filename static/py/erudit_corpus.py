import db
import constants as CONST
import math
from scipy import spatial
from lz4.frame import compress, decompress

db = db.Database()

def match(dochash_id, n=100):
    # Find closest matching documents using ranked weighted penalty distance
    sqrt_dist = math.sqrt(CONST.DS_MAXTOPIC)
    max_dist = CONST.DS_MAXTOPIC-1
    sqrt_max = math.sqrt(max_dist)
    return db.execQuery(""" 
        select dt.documentid
        , sum(case when udt.topicid is null 
            then %s*(case when dt.rank=%s then %s else sqrt(dt.rank) end) * %s 
            else (abs(udt.rank-dt.rank)/%s) * %s * ( (%s - sqrt(udt.rank)) 
                + (%s - (case when dt.rank = %s then sqrt(%s) else sqrt(dt.rank) end)) )
            end) cossim
        from doctopic dt
        left join (
                select * from userdoctopic where dochashid=%s order by rank limit %s
            ) udt on dt.topicid=udt.topicid
        where 
        -- look only at docs with atleast one matching topic
        dt.documentid in (
            select distinct documentid 
            from doctopic
            where topicid in (
                select topicid
                from userdoctopic
                where dochashid=%s
            )
        )
        group by dt.documentid
        -- ranked weighted penalty distance calculation
        order by sum(case when udt.topicid is null 
            then %s*(case when dt.rank=%s then %s else sqrt(dt.rank) end) * %s 
            else (abs(udt.rank-dt.rank)/%s) * %s * ( (%s - sqrt(udt.rank)) 
                + (%s - (case when dt.rank = %s then sqrt(%s) else sqrt(dt.rank) end)) )
        end)
        limit %s
        """, (  sqrt_dist
                ,CONST.DS_MAXTOPIC
                ,sqrt_max
                ,CONST.DS_PENALTY
                ,CONST.DS_MAXTOPIC
                ,max_dist
                ,sqrt_dist
                ,sqrt_dist
                ,CONST.DS_MAXTOPIC
                ,sqrt_max
                ,dochash_id
                ,CONST.DS_MAXTOPIC
                ,dochash_id
                ,sqrt_dist
                ,CONST.DS_MAXTOPIC
                ,sqrt_max
                ,CONST.DS_PENALTY
                ,CONST.DS_MAXTOPIC
                ,max_dist
                ,sqrt_dist
                ,sqrt_dist
                ,CONST.DS_MAXTOPIC
                ,sqrt_max
                ,n
    ))

def getDocumentInfo(document_id):
    return db.execQuery("""
        select d.id
        , ifnull(t.titre, t.surtitre) titre
        , (select group_concat(concat(prenom
                                    , CASE WHEN autreprenom != '' and autreprenom is not null 
                                        THEN concat(' ', autreprenom) ELSE '' END
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
    user_topic = db.execQuery(""" select dist from userdoctopic where dochashid=%s order by topicid""", (dochash_id,))
    user_topic = [float(topic[0]) for topic in user_topic]
    comp_topiclz = db.execQuery(""" select topichash from doctopiclz where documentid=%s limit 1""", (document_id,))
    comp_topic = decompress(comp_topiclz[0][0].decode("utf8").encode("latin1"))
    comp_topic = comp_topic.split(",")
    doc_topic = [float(dist.split("-")[1]) for dist in comp_topic]
    return 1-spatial.distance.cosine(user_topic, doc_topic)