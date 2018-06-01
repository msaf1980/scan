#!/usr/bin/python

import sys, os
from PIL import Image

# Split image by 2 parts

def usage():
    sys.stderr.write("use: %s img [v | h] for split image vertically or horizontaly\n\tby default auto-split by largest dimension\n")
    sys.exit(1)

horizontal = None    
if len(sys.argv) == 3:
    if sys.argv[2] == "v":
        horizontal = False
    elif sys.argv[2] == "h":
        horizontal = True
    else:
        usage()
        
filename = sys.argv[1]

img = Image.open(filename)
(width, height) = img.size
if horizontal is None:
    if width >= height:
        horizontal = True
    else:
        horizontal = False

if horizontal:
    if width % 2 == 0:
        wsize = width // 2
    else:
        wsize = width // 2 + 1
    hsize = height
    box1 = (0, 0, wsize, height)
    box2 = (wsize, 0, width, height)
else:
    if height % 2 == 0:
        hsize = height // 2
    else:
        hsize = height // 2 + 1
    wsize = width
    box1 = (0, 0, width, hsize)
    box2 = (0, hsize, width, height)
        
(name, ext) = os.path.splitext(filename)
if horizontal:
    name1 = name + "_L" + ext
    name2 = name + "_R" + ext
else:
    name1 = name + "_1" + ext
    name2 = name + "_2" + ext

#print("split " + filename + " %d:%d by %d:%d" % (width, height, wsize, hsize))    
print(name1 + " " + str(box1))
im = img.crop(box1)
im.save(name1)
im = img.crop(box2)
print(name2 + " " + str(box2))
im.save(name2)
