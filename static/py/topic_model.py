import db
import constants as CONST
import common as cm
import treetaggerwrapper
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation

db = db.Database()
tagger = treetaggerwrapper.TreeTagger(TAGLANG="fr")

# Strip the text of stop words
# default is the external set of stop words
def preProcessText(strText, dataset="external"):
    aStopWord = []
    # This tokenizes, pos tags, and lemmatizes all our words
    aWordList = treetaggerwrapper.make_tags(tagger.tag_text(strText), exclude_nottags=True)
    # Now create stop word array (also without punctuation to match)
    results = db.execQuery("select word from stopword where dataset=%s", (dataset,))
    for result in results:
        aStopWord.append(result[0].lower())
    
    # For performance, turn our stop word list to a set
    aStopWord = set(aStopWord)
    # Remove all stop words (based on lemmatized words) and punctuation
    aCleanWordList = [word 
        for word in aWordList 
            if word[2].lower() not in aStopWord 
                and "PUN" not in word[1] 
                and "SENT" not in word[1]
                and "@" not in word[2]
                and len(word[2]) > 1
    ]
    
    return aCleanWordList


# Segment a single document text into an array
# This will be used for single document topic modeling
def segmentDocument(strText):
    aTag = preProcessText(strText, "adam")
    
    aDocument = []
    nTerms = len(aTag)
    nDocLen = nTerms / CONST.TM_TOPICS
    nStart = 0
    nEnd = nDocLen
    # break down single document into segments
    while (nEnd < nTerms):
        aDocument.append(" ".join(tag[2] for tag in aTag[nStart:nEnd]))
        nStart += nDocLen
        nEnd += nDocLen
    
    return aDocument


# Topic model an array of documents using Non-negative Matrix Factorization (TFIDF)
def fitNMF(aDocument):
    tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2,
                                   max_features=CONST.TM_FEATURES)
    tfidf = tfidf_vectorizer.fit_transform(aDocument)
    
    nmf = NMF(n_components=CONST.TM_TOPICS, random_state=1,
          alpha=.1, l1_ratio=.5).fit(tfidf)
    
    tfidf_feature_names = tfidf_vectorizer.get_feature_names()
    print_top_words(nmf, tfidf_feature_names, 20)


# Topic model an array of documents using Latent Dirichlet Association
def fitLDA(aDocument):
    tf_vectorizer = CountVectorizer(max_df=0.95, min_df=2,
                                    max_features=CONST.TM_FEATURES)
    
    tf = tf_vectorizer.fit_transform(aDocument)

    lda = LatentDirichletAllocation(n_topics=CONST.TM_TOPICS, max_iter=5,
                                learning_method='online',
                                learning_offset=50.,
                                random_state=0)
    lda.fit(tf)

    tf_feature_names = tf_vectorizer.get_feature_names()
    print_top_words(lda, tf_feature_names, 20)


# Print the top N words from each topic in a model
def print_top_words(model, feature_names, n_top_words):
    for topic_idx, topic in enumerate(model.components_):
        print("Topic #%d:" % topic_idx)
        print(" ".join([feature_names[i]
                        for i in topic.argsort()[:-n_top_words - 1:-1]]))