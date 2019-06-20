import db
import constants as CONST
import math
import re
from scipy import spatial
from lz4.frame import compress, decompress

db = db.Database()

def matchKeyword(keyword_list, n=100, must_include=[]):
    """ Given a list of keywords, match results """
    if len(keyword_list) == 0:
        return []
    # put them for regex search
    keywords = " ".join(keyword_list)
    results = db.execQuery("""select d.documentid
        , sum(d.tfidf) score
        from doctfidf d
        where d.termid in (
            select termid
            from tfidf
            where match(word) against(%s in boolean mode)
        )
        group by d.documentid
        order by sum(d.tfidf) desc
        limit 100
        """, (keywords,))
    if len(must_include) > 0:
        # filter out results without our necessary keywords
        results = forceInclusion(results, must_include)
    return results


def getJournalCount(keyword_list, must_include):
    if len(keyword_list) == 0:
        return []
    results = matchKeyword(keyword_list, must_include=must_include)
    if len(results) == 0:
        return []
    docs = [result[0] for result in results]
    format_strings = ",".join(["%s"] * len(docs))
    results = db.execQuery("""select m.titrerev, ifnull(x.freq, 0) from meta m
        left join (
                select titrerev, count(*) freq from meta
                where documentid in (%s) group by titrerev
            ) x on x.titrerev=m.titrerev
        group by m.titrerev, x.freq
        order by m.titrerev;
        """ % format_strings, tuple(docs))
    freq = []
    for result in results:
        freq.append({ "name": result[0], "freq": result[1] })
    return freq


def forceInclusion(results, must_include):
    """ Filter matchKeyword results based on required keywords"""
    new_results = []
    for result in results:
        doc_tfidf = db.execQuery("""select word
        from doctfidf
        where documentid=%s""", (result[0],))
        unused_terms = must_include[:]
        for tfidf in doc_tfidf:
            if tfidf[0] in unused_terms:
                unused_terms.remove(tfidf[0])
        if len(unused_terms) == 0:
            new_results.append(result)
    return new_results


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
