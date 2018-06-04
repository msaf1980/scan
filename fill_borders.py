#!/usr/bin/python

import sys, os
from PIL import Image, ImageDraw

# Try to clean black borders of scanned image (usually black & white)
# !!!! wery alfa state, not tested on color or grayscale images

#xborder1 = 80
#yborder1 = 80

#xborder2 = 80
#yborder2 = 80

#threshold = 30
 
bw_threshold = 80

def rgb_to_grayscale(r, g, b):
    return (r * 299 + g * 587 + b * 114) // 1000

def fill_xborder_b2w(pix, x1, y1, x2, y2):
    xdec = 1 if x2 >= x1 else -1
    ydec = 1 if y2 >= y1 else -1
    changed = False
    #print("[%d:%d] [%d:%d]" % (x1, y1, x2, y2))
    x = x1
    try:        
        while x != x2:
            y = y1
            t = 0
            while y != y2 and t < threshold:
                #print("[%d:%d] = %s" % (x, y, str(pix[x, y])))
                if img.mode in ("P", "L"):
                    if pix[x, y] == 0:
                        pix[x, y] = 255
                        changed = True
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    elif threshold > 0:
                        if (ydec == 1 and y - y1 > threshold) or (ydec == -1 and y2 - y > threshold):
                            t += 1
                elif img.mode == "RGBA":
                    (r, g, b, a) = pix[x, y]
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255, a)
                        changed = True
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    elif threshold > 0:
                        if (ydec == 1 and y - y1 > threshold) or (ydec == -1 and y2 - y > threshold):
                            t += 1    
                else:
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255)
                        changed = True
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    elif threshold > 0:
                        if (ydec == 1 and y - y1 > threshold) or (ydec == -1 and y2 - y > threshold):
                            t += 1                
                y += ydec
            x += xdec
            #print("")
    except:
        print("[%d:%d] start [%d:%d] end [%d:%d]" % (x, y, x1, y1, x2, y2))
        raise
        
def fill_yborder_b2w(pix, x1, y1, x2, y2):
    xdec = 1 if x2 >= x1 else -1
    ydec = 1 if y2 >= y1 else -1
    changed = False
    #print("[%d:%d] [%d:%d]" % (x1, y1, x2, y2))
    y = y1
    try:        
        while y != y2:
            x = x1
            t = 0
            while x != x2 and t < threshold:
                #print("[%d:%d] = %s" % (x, y, str(pix[x, y])))
                if img.mode in ("P", "L"):
                    if pix[x, y] == 0:
                        pix[x, y] = 255
                        changed = True
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    elif (xdec == 1 and x - x1 > threshold) or (xdec == -1 and x2 - x > threshold):
                        t += 1
                elif img.mode == "RGBA":
                    (r, g, b, a) = pix[x, y]
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255, a)
                        changed = True
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    elif (xdec == 1 and x - x1 > threshold) or (xdec == -1 and x2 - x > threshold):
                        t += 1    
                else:
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255)
                        changed = True
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    elif (xdec == 1 and x - x1 > threshold) or (xdec == -1 and x2 - x > threshold):
                        t += 1                
                x += xdec
            y += ydec
            #print("")
    except:
        print("[%d:%d] start [%d:%d] end [%d:%d]" % (x, y, x1, y1, x2, y2))
        raise

if not len(sys.argv) in (6, 7):
    sys.stderr.write("use: %s image xborder1 yborder1 xborder2 yborder2 threshold\n")
    sys.exit(1)
        
filename = sys.argv[1]

xborder1 = int(sys.argv[2])
yborder1 = int(sys.argv[3])

xborder2 = int(sys.argv[4])
yborder2 = int(sys.argv[5])

img = Image.open(filename)
(width, height) = img.size

if len(sys.argv) == 7:
    threshold = int(sys.argv[6])

    pix = img.load()

    changed = fill_yborder_b2w(pix, 0, 0, xborder1, height)
    if fill_yborder_b2w(pix, width - 1, 0, width - xborder2, height): changes = True

    if fill_xborder_b2w(pix, xborder1 + 1, 0, width - xborder2, xborder1): changes = True
    if fill_xborder_b2w(pix, width - xborder2, height - 1, xborder1, height - yborder2): changes = True

else:
    changed = True
    if img.mode in ("P", "L"):
        bgcolor = 255
    elif img.mode == "RGBA":
        bgcolor = (255, 255, 255, 255)
    elif img.mode == "RGB":
        bgcolor = (255, 255, 255)
    
    draw = ImageDraw.Draw(img)
    #print("[%d:%d] [%d:%d]" % (0, 0, xborder1, height))
    draw.rectangle((0, 0, xborder1, height), fill=bgcolor)
    #print("[%d:%d] [%d:%d]" % (width - 1, 0, width - xborder2, height))
    draw.rectangle((width - 1, 0, width - xborder2, height), fill=bgcolor)
    #print("[%d:%d] [%d:%d]" % (xborder1 + 1, 0, width - xborder2, yborder1))
    draw.rectangle((xborder1 + 1, 0, width - xborder2, yborder1), fill=bgcolor)
    #print("[%d:%d] [%d:%d]" % (width - xborder2, height - 1, xborder1, height - yborder2))
    draw.rectangle((width - xborder2, height - 1, xborder1, height - yborder2), fill=bgcolor)

     
if changed:
    filename_back = filename + ".back"
    if os.path.isfile(filename_back):
        os.remove(filename_back)

    os.rename(filename, filename_back)
    img.save(filename)

    #filename_back = "_" + filename
    #img.save(filename_back)
