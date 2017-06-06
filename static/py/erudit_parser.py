import constants as CONST
import common as cm
import nltk
from lxml import etree, objectify

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

