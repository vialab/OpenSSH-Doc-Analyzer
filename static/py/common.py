import db
import numpy as np
import base64
import re
import cStringIO
import imp
from lxml import etree, objectify
from PIL import Image

## Common helper functions used across the web app

# Check if this file type is supported by the system
def isSupportedFile(filename):
    return "." in filename and \
           filename.rsplit(".", 1)[1] in CONST.ALLOWED_EXTENSIONS


# Log a system error to the systemerror database table
def logError(e):
    newdb = db.Database()
    strError = "System Error %d:  %s" % (e.args[0], e.args[1])
    newdb.execProc("sp_systemerror", (strError,))


# Strip the namespaces found in an XML Element tree
# Erudit data comes has custom schema, strip it out
# so that we can validate with our own schemas
def removeNamespace(xmlData, namespace):
    ns = u'{%s}' % namespace
    nsl = len(ns)
    for elem in xmlData.getiterator():
        if elem.tag.startswith(ns):
            elem.tag = elem.tag[nsl:]


# Get an element in the erudit namespace
def getXPathElement(xmlDoc, strXPath, aNamespaces=None):
    if aNamespaces is None:
        ndData = xmlDoc.xpath(strXPath)
    else:    
        ndData = xmlDoc.xpath(strXPath, namespaces=aNamespaces)
    
    xmlData = getElementTree(ndData[0])
    return xmlData


# Pull all text from an XML node without sub element mark-up
def getFullText(xmlData):
    if xmlData.text:
        strData = xmlData.text
    else:
        strData = ''
    for ndChild in xmlData:
        if ndChild.tail is not None:
            strData += ndChild.tail
    return strData


# Convert an XML Element to an Element Tree
def getElementTree(xmlData):
    return etree.ElementTree(xmlData)


# Parse an xml file
def parseXML(strPath):
    xmlDoc = etree.parse(strPath)
    return xmlDoc


# Parse an xsd schema file
def parseXMLSchema(strSchemaPath):
    xmlSchema_doc = etree.parse(strSchemaPath)
    return etree.XMLSchema(xmlSchema_doc)