import constants as CONST
import common as cm
from lxml import etree, objectify

## XML parser for handling erudit XML data
## Handles basic XML parsing and XML schema validation

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