ERUDIT_NAMESPACES = {'erudit':'http://www.erudit.org/xsd/article'}
UPLOAD_FOLDER = "uploads/"
ALLOWED_EXTENSIONS = set(["txt", "pdf"])

# Document Search constants
DS_MINSIG = 0.05 # significance threshold for topic distribution (MAX 1.0)
DS_MAXTERM = 5 # number of prioritized terms

# Topic model constants
TM_TOPICS = 100
TM_FEATURES = 1000
TM_MAXDF = 1.0
TM_MINDF = 1
TM_PASSES = 20
TM_MAXITER = 5
TM_OFFSET = 50.
TM_RANDOM = 1
TM_ALPHA = .1
TM_L1RATIO = .5
TM_MINSIG = 0.1 # significance threshold for topic distribution (MAX 1.0)

# OHT constants
OHT_TOPDIST = 10 # number of words to get from topic term distribution

# Text Thresholds for text processing
TT_TITLE = 5