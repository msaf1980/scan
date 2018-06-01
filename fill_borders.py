#!/usr/bin/python

import sys, os
from PIL import Image

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
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    else:
                        t += 1
                elif img.mode == "RGBA":
                    (r, g, b, a) = pix[x, y]
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255, a)
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    else:
                        t += 1    
                else:
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255)
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    else:
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
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    else:
                        t += 1
                elif img.mode == "RGBA":
                    (r, g, b, a) = pix[x, y]
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255, a)
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    else:
                        t += 1    
                else:
                    bw = rgb_to_grayscale(r, b, b)
                    if bw < bw_threshold:
                        pix[x, y] = (255, 255, 255)
                        #print("[%d:%d] => %s" % (x, y, str(pix[x, y])))
                    else:
                        t += 1                
                x += xdec
            y += ydec
            #print("")
    except:
        print("[%d:%d] start [%d:%d] end [%d:%d]" % (x, y, x1, y1, x2, y2))
        raise

if len(sys.argv) != 7:
    sys.stderr.write("use: %s image xborder1 yborder1 xborder2 yborder2 threshold\n")
    sys.exit(1)
        
filename = sys.argv[1]

xborder1 = int(sys.argv[2])
yborder1 = int(sys.argv[3])

xborder2 = int(sys.argv[4])
yborder2 = int(sys.argv[5])

threshold = int(sys.argv[6])

img = Image.open(filename)

(width, height) = img.size
pix = img.load()

fill_yborder_b2w(pix, 0, 0, xborder1, height)
fill_yborder_b2w(pix, width - 1, 0, width - xborder2, height)

fill_xborder_b2w(pix, xborder1 + 1, 0, width - xborder2, xborder1)
fill_xborder_b2w(pix, width - xborder2, height - 1, xborder1, height - yborder2)

filename_back = filename + ".back"
if os.path.isfile(filename_back):
    os.remove(filename_back)

os.rename(filename, filename_back)
img.save(filename)

#filename_back = "_" + filename
#img.save(filename_back)
