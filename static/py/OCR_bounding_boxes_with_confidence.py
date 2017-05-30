from PIL import Image, ImageDraw
import pytesseract
from textstat.textstat import textstat

# This converts the 0-100 confidence level from the OCR into an opacity
# scale from 0-255. I limit the top range to 165 so you can see the word still
def opacityConversion(confidence):
    OldMax = 100
    OldMin = 0
    NewMin = 200
    NewMax = 0

    OldRange = (OldMax - OldMin)
    if OldRange == 0:
        NewValue = NewMin
    else:
        NewRange = (NewMax - NewMin)
        NewValue = (((confidence - OldMin) * NewRange) / OldRange) + NewMin
        return NewValue

# def textConfidence(fname):
    # with PyTessBaseAPI() as api:
    #     #for image in images:
    #         api.SetImageFile(fname)
    #         text = api.GetUTF8Text()
    #         #print api.AllWordConfidences()
    #         print textstat.flesch_kincaid_grade(text)

    #         print  textstat.flesch_reading_ease(text)

    #         print ("90-100 : Very Easy")
    #         print ("80-89 : Easy")
    #         print ("70-79 : Fairly Easy")
    #         print ("60-69 : Standard")
    #         print ("50-59 : Fairly Difficult")
    #         print ("30-49 : Difficult")
    #         print ("0-29 : Very Confusing")


#Find the orientation
# def orientation(fname):
#     with PyTessBaseAPI(psm=PSM.AUTO_OSD) as api:
#         image = Image.open(fname)
#         api.SetImage(image)
#         api.Recognize()

#         it = api.AnalyseLayout()
#         orientation, direction, order, deskew_angle = it.Orientation()
#         print "Orientation: {:d}".format(orientation)
#         print "WritingDirection: {:d}".format(direction)
#         print "TextlineOrder: {:d}".format(order)
#         print "Deskew angle: {:.4f}".format(deskew_angle)

#Find the bounding boxes

def findBoundingBoxes(fname):
    # This opens the converted pdf as an image file
    image = Image.open(fname)
    #This converts the original image to RGBA to allow for alpha channel
    #composits (This allows for transparency in PIL)
    img = image.convert("RGBA")
    #This creates a new transparent image to composite with teh original
    tmp = Image.new('RGBA', img.size, (0,0,0,0))
    #This creates the drawing object for the overlay
    draw = ImageDraw.Draw(tmp)

    with TessBaseAPI() as api:
        api.SetImage(image)

        # Interate over lines using OCR
        #boxes = api.GetComponentImages(RIL.TEXTLINE, True)

        # Iterate over words using OCR
        boxes = api.GetComponentImages(RIL.WORD, True)
        #print 'Found {} textline image components.'.format(len(boxes))
        for i, (im, box, _, _) in enumerate(boxes):
            # im is a PIL image object
            # box is a dict with x, y, w and h keys
            api.SetRectangle(box['x'], box['y'], box['w'], box['h'])
            ocrResult = api.GetUTF8Text()

            conf = api.MeanTextConf()

            #scale the confidence to the opacity
            opacity = opacityConversion(conf)

            #draw = ImageDraw.Draw(image)
            draw.rectangle(((box['x'],box['y']),((box['x']+box['w']),(box['y']+box['h']))), fill=(244, 167, 66,opacity))

    # This creates a composit image with the original image and the transparent overlay
    img = Image.alpha_composite(img, tmp)
    # This saves the new image
    img.save(fname)

            #print (u"Box[{0}]: x={x}, y={y}, w={w}, h={h}, "
                   #"confidence: {1}, text: {2}").format(i, conf, ocrResult, **box)
