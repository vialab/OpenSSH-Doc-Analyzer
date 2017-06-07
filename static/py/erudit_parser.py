import string
import constants as CONST
import common as cm
import nltk
import db
from lxml import etree, objectify
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.decomposition import NMF, LatentDirichletAllocation

db = db.Database()
## Parser for handling erudit XML data

# Based on our custom schemas in ./static/xml
# return the XML format type we detected using XSD validation
def getXMLSchema(xmlData):
    root = xmlData.getroot()
    cm.removeNamespace(root, CONST.ERUDIT_NAMESPACES["erudit"])

    xsd = cm.parseXMLSchema("./static/xml/para.xsd")
    if (xsd.validate(xmlData)):
        return "PARA"
    
    xsd = cm.parseXMLSchema("./static/xml/roc.xsd")
    if(xsd.validate(xmlData)):
        return "ROC"

    xsd = cm.parseXMLSchema("./static/xml/libre.xsd")
    if(xsd.validate(xmlData)):
        return "LIBRE"
    
    return "UNKNOWN"

# Strip the text from the corps element based on its schema
def getTextFromXML(strDocumentID, xmlData):
    root = xmlData.getroot()
    cm.removeNamespace(root, CONST.ERUDIT_NAMESPACES["erudit"])
    xmlCorps = cm.getXPathElement(xmlData, "//corps")
    strSchema = getXMLSchema(xmlCorps)

    if(strSchema == "PARA"):
        # well formed
        strText = " ".join(xmlCorps.xpath("//para//alinea//text()"))
    elif(strSchema == "ROC"):
        # everything should be seperated by paragraphs
        # need to handle for some anomalies first
        strText = getTextFromROC(strDocumentID, xmlCorps)
    else:
        # just a block of text, no need to handle anomalies
        strText = " ".join(xmlData.xpath("//corps//text()"))

    # if a bibliography exists in this text, delete it
    # assumption: bibliography always occurs in the end
    nEnd = strText.lower().find("bibliographie")
    if nEnd != -1:
        strText = strText[:nEnd]

    return strText


# ROC = ORC - text is split out by line in <alinea> elements
# May contain some anomalies that needs to be processed here
def getTextFromROC(strDocumentID, xmlCorps):
    metaData = db.execQuery("select d.path, m.titrerev from document d left join meta m on m.documentid = d.id where d.id=%s", (strDocumentID,))
    # handle anomalies if we have meta data
    if(metaData):
        strTitle = metaData[0][1]
        # strip out titles after occurence threshold has been met
        nTitles = 0
        for nd in xmlCorps.xpath("//alinea"):
            # don't touch this if it has children nodes
            if len(nd) or not nd.text:
                continue
            # check title occurence threshold
            if strTitle.lower() in nd.text.lower():
                if nTitles > CONST.TT_TITLE:
                    # past threshold, remove this node
                    nd.getparent().remove(nd)
                else:
                    nTitles += 1
    else:
        # we do not have meta data for this document        
        # let's try to receive the meta data to try again
        strMetaXML = cm.getUTFStringFromXML(xmlMeta)
        db.execProc("erudit_INSERT_metadata", (strDocumentID, strMetaXML))
        metaData = db.execQuery("select d.path, m.titrerev from document d left join meta m on m.documentid = d.id where d.id=%s", (strDocumentID,))
        
        if metaData:
            # we got something! let's do this again            
            # WARNING: "SAFE" RECURSION HAPPENING HERE
            return processTextFromROC(strDocumentID, xmlCorps)

    return " ".join(xmlCorps.xpath("//alinea//text()"))
        

# Save all the data we want from this XML Document
def saveAllData(strDocumentID, xmlDoc):
        root = xmlDoc.getroot()
        cm.removeNamespace(root, CONST.ERUDIT_NAMESPACES["erudit"])
        strXML = cm.getUTFStringFromXML(xmlDoc)

        xmlMeta = cm.getXPathElement(xmlDoc, "//admin")
        strMetaXML = cm.getUTFStringFromXML(xmlMeta)

        xmlBiblio = cm.getXPathElement(xmlDoc, "//partiesann")
        strBiblioXML = cm.getUTFStringFromXML(xmlBiblio)

        xmlLiminaire = cm.getXPathElement(xmlDoc, "//liminaire")
        strLiminaireXML = cm.getUTFStringFromXML(xmlLiminaire)

        xmlCorps = cm.getXPathElement(xmlDoc, "//corps")
        strCorpsXML = cm.getUTFStringFromXML(xmlCorps)
        db.execProc("erudit_INSERT", (strDocumentID, strXML, strMetaXML, strBiblioXML, strLiminaireXML, strCorpsXML))

# Save meta data section of the ERUDIT XML
# Assumes namespace has been stripped from XML
def saveMetaData(strDocumentID, xmlDoc):
    xmlMeta = cm.getXPathElement(xmlDoc, "//admin")
    strMetaXML = cm.getUTFStringFromXML(xmlMeta)
    db.execProc("erudit_INSERT_metadata", (strDocumentID, strMetaXML))

# Save bibliography section of the ERUDIT XML
# Assumes namespace has been stripped from XML
def saveBibliography(strDocumentID, xmlDoc):
    xmlBiblio = cm.getXPathElement(xmlDoc, "//partiesann")
    strBiblioXML = cm.getUTFStringFromXML(xmlBiblio)
    db.execProc("erudit_INSERT_biblio", (strDocumentID, strBiblioXML))

# Save key notes section of the ERUDIT XML
# Assumes namespace has been stripped from XML
def saveKeynote(strDocumentID, xmlDoc):
    xmlLiminaire = cm.getXPathElement(xmlDoc, "//liminaire")
    strLiminaireXML = cm.getUTFStringFromXML(xmlLiminaire)
    db.execProc("erudit_INSERT_liminaire", (strDocumentID, strLiminaireXML))

# Save corps section of the ERUDIT XML
# Assumes namespace has been stripped from XML
def saveCorpus(strDocumentID, xmlDoc):
    xmlCorps = cm.getXPathElement(xmlDoc, "//corps")
    strCorpsXML = cm.getUTFStringFromXML(xmlCorps)
    db.execProc("erudit_INSERT_corps", (strDocumentID, strCorpsXML))

# Save raw Erudit XML
def saveRawXML(strDocumentID, xmlDoc):
    strXML = cm.getUTFStringFromXML(xmlDoc)
    db.execUpdate("insert into raw_xml(documentid, rawxml) values(%s, %s)", (strDocumentID, strXML))

