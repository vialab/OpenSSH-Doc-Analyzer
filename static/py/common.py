# -*- coding: utf-8 -*-
import db
import numpy as np
import base64
import re
import cStringIO
import imp
import constants as CONST
import hashlib
import codecs
from lxml import etree, objectify
from PIL import Image

## Common helper functions used across the web app

def getSHA256(strText):
    """ Create a checksum for a file """
    hash_sha256 = hashlib.sha256(strText)
    return hash_sha256.hexdigest()


def getUTFStringFromXML(xmlDoc):
    """ Convert an XML to a UTF-8 encoded string
    This is how we insert stuff into the database"""
    if xmlDoc is None:
        return ""

    return etree.tostring(xmlDoc, encoding="UTF-8", xml_declaration=False)

def isSupportedFile(filename):
    """ Check if this file type is supported by the system """
    return "." in filename and \
           filename.rsplit(".", 1)[1] in CONST.ALLOWED_EXTENSIONS

def logError(e):
    """ Log a system error to the systemerror database table """
    newdb = db.Database()
    strError = "System Error %d:  %s" % (e.args[0], e.args[1])
    newdb.execProc("sp_systemerror", (strError,))

def removeNamespace(xmlData, namespace):
    """ Strip the namespaces found in an XML Element tree
    Erudit data comes has custom schema, strip it out
    so that we can validate with our own schemas """
    ns = u'{%s}' % namespace
    nsl = len(ns)
    for elem in xmlData.getiterator():
        if isinstance(elem.tag, basestring):
            if elem.tag.startswith(ns):
                elem.tag = elem.tag[nsl:]

def getXPathElement(xmlDoc, strXPath, aNamespaces=None):
    """ Get an element in the erudit namespace """    
    if aNamespaces is None:
        ndData = xmlDoc.xpath(strXPath)
    else:    
        ndData = xmlDoc.xpath(strXPath, namespaces=aNamespaces)
    
    if(len(ndData) > 0):
        xmlData = getElementTree(ndData[0])
    else:
        return None
    return xmlData

def getFullText(xmlData):
    """ Pull all text from an XML node without sub element mark-up """
    if xmlData.text:
        strData = xmlData.text
    else:
        strData = ''
    for ndChild in xmlData:
        if ndChild.tail is not None:
            strData += ndChild.tail
    return strData

def getElementTree(xmlData):
    """ Convert an XML Element to an Element Tree """    
    return etree.ElementTree(xmlData)

def parseXML(strPath):
    """ Parse an xml file """
    xmlDoc = etree.parse(strPath.strip())
    return xmlDoc

def parseXMLSchema(strSchemaPath):
    """ Parse an xsd schema file """
    xmlSchema_doc = etree.parse(strSchemaPath)
    return etree.XMLSchema(xmlSchema_doc)

def saveUTF8ToDisk(strPath, strText):
    """ Write file out to disk with UTF-8 encoding """
    with codecs.open(strPath, "w+", "utf-8") as f:
        f.write(strText)