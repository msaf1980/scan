#!/usr/bin/python

# Show images with identifical names from 2 dirs (for visual compare)
# Useful for verify image auto-processing results
# Install Qt5 and PIL (or Pillow)
# Use:
#   imgdir_diff.py [ sourcedir | startfile ] dir
#       if first argument is a dir or startfile not found, started from first file
#
#   For example, to compare Scan Tailor results with 2-pages splited images, use:
#       imgdir_diff.py [ sourcedir | startfile ] outdir
#
#   Hotkeys:
#       Ctrl+P  Prev
#       Ctrl+N  Next
#       Ctrl+R  Reload

import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from PIL import Image
from PIL.ImageQt import ImageQt

def strip_name(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def strip_sidename(filename):
    fname = os.path.splitext(os.path.basename(filename))[0]
    fname_l = fname.lower()
    if fname_l.endswith("_1l") or fname_l.endswith("_2r"): # 2-side scan tailor image
        return fname[0:-3]
    else:
        return fname

def img_mode(mode):
    if mode == "1":
        return "B&W"
    elif mode == "P":
        return "Color"
    elif mode == "L":
        return "Grayscale"
    else:
        return mode

        
class App(QWidget):
 
    def __init__(self, app, name1, name2):
        super().__init__()
        self.title = 'imgdir_diff'
        self.left = 50
        self.top = 50
        screen_resolution = app.desktop().screenGeometry()
        self.width = screen_resolution.width() - 100
        self.height = screen_resolution.height() - 200
        self.initUI(name1, name2)
        
    def initUI(self, name1, name2):
        self.setWindowTitle(self.title)
        self.load_dirs(name1, name2)

        self.img_label1 = QLabel(self)
        self.img_label1.setStyleSheet("border:1px solid rgb(0, 255, 0); border-radius: 2px")
        self.img_label1.setAlignment(Qt.AlignRight)
        self.status_label1 = QLabel(self)
        self.status_label1.setAlignment(Qt.AlignRight)
        
        self.img_label2 = QLabel(self)
        self.img_label2.setStyleSheet("border:1px solid rgb(0, 255, 0); border-radius: 2px")
        self.status_label2 = QLabel(self)

        self.prev_button = QPushButton("Prev")
        self.prev_button.clicked.connect(self.prev)
        shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut.activated.connect(self.prev)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next)
        shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut.activated.connect(self.next)
        
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload)
        shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut.activated.connect(self.reload)
        
        self.initUI_H()
        
        self.load()

    def initUI_H(self):
        self.setGeometry(self.left, self.top, self.width, self.height)
        self.iwidth = self.width // 2
        self.iheight = self.height

        layout = QVBoxLayout()
       
        hbox1 = QHBoxLayout()
        hbox2 = QHBoxLayout()
        

        hbox1.addWidget(self.img_label1)
        self.status_bar1 = QStatusBar()
        self.status_bar1.addWidget(self.status_label1, 1);
        hbox2.addWidget(self.status_bar1)
        
        hbox1.addWidget(self.img_label2)
        self.status_bar2 = QStatusBar()
        self.status_bar2.addWidget(self.status_label2, 1);
        hbox2.addWidget(self.status_bar2)
        
        layout.addLayout(hbox1)
        layout.addLayout(hbox2)
        
        hbox3 = QHBoxLayout() 
        hbox3.addWidget(self.prev_button)
        hbox3.addWidget(self.next_button)
        hbox3.addWidget(self.reload_button)
        
        layout.addLayout(hbox3)
        
        self.setLayout(layout)
        
        self.show()
        
    def set_enabled(self):
        if len(self.dirlist1) < 2:
            en_prev = False
            en_next = False
        elif self.i1 == 0:
            en_prev = False
            en_next = True
        elif self.i1 == len(self.dirlist1) - 1:
            en_prev = True
            if self.i2 == -1 and self.fname2 is None:
                en_next = False
            else:
                v = self.dirmap2.get(self.fname2)
                if v is None or len(v) < 2 or self.i2 >= len(v) - 1:
                    en_next = False
                else:
                    en_next = True
        else:
            en_prev = True
            en_next = True
        
        self.prev_button.setEnabled(en_prev)
        self.next_button.setEnabled(en_next)

    def prev(self):
        if self.i1 < 0:
            return
        elif not self.fname2 is None and self.i2 > 0:
            self.i2 -= 1
        else:
            self.i1 -= 1
            (self.fname2, self.i2) = self.find_map(self.dirlist1[self.i1], self.dirmap2)
            self.i2 = len(self.dirmap2[self.fname2]) - 1
            
        self.load()
        
    def next(self):
        if self.i1 >= len(self.dirlist1):
            return
        elif self.fname2 is None or self.i2 >= len(self.dirmap2[self.fname2]) - 1:
            if self.i1 == len(self.dirlist1) - 1:
                return
            self.i1 += 1
            (self.fname2, self.i2) = self.find_map(self.dirlist1[self.i1], self.dirmap2)
        else:
            self.i2 += 1
                        
        self.load()
        
    def reload(self):
        self.load_dirs(self.dirlist1[self.i1], self.dirname2)
        self.load()
    
    def display(self, img_label, status_label, filename, length, fileindx = -1):
        img = Image.open(filename)
        qim = ImageQt(img)

        aspect_w = float(img.size[0]) / self.iwidth
        aspect_h = float(img.size[1]) / self.iheight
        #print("%f %f" % (aspect_w, aspect_h))
        aspect = aspect_w if aspect_w > aspect_h else aspect_h
        
        pixmap = QPixmap.fromImage(qim).scaled(img.size[0] // aspect, img.size[1] // aspect, Qt.KeepAspectRatio,Qt.SmoothTransformation)
        img_label.setPixmap(pixmap)
        if fileindx < 0:
            status_label.setText("(%d) %s (%s %s [%d:%d])" % (length, filename, img_mode(img.mode), img.format, img.size[0], img.size[1]))
        else:
            status_label.setText("(%d:%d) %s (%s %s [%d:%d])" % (length, fileindx, filename, img_mode(img.mode), img.format, img.size[0], img.size[1]))
            
    def display_indx(self, img_label, status_label, dirlist, fileindx):
        if fileindx < 0 or len(dirlist) == 0:
            status_label.setText("(%d:%d)" % (len(dirlist), fileindx))
            img_label.clear()
        else:
            self.display(img_label, status_label, dirlist[fileindx], len(dirlist), fileindx)
            
    def display_map(self, img_label, status_label, length, dirmap, mapkey, mapindx):
        if dirmap is None or mapkey is None or mapindx < 0 or len(dirmap) == 0:
            status_label.setText("(%d): not found" % length)
            img_label.clear()
        else:
            self.display(img_label, status_label, dirmap[mapkey][mapindx], self.dirlen2, -1)
        

    def makemap_2(self, dirlist):
        self.dirmap2 = dict()
        self.j2 = -1
        self.fname2 = None
        for f in dirlist:
            fname = strip_sidename(f)
            v = self.dirmap2.get(fname)
            if v is None:
                v = []
                v.append(f)
                self.dirmap2[fname] = v
            else:
                v.append(f)
                
        #print(str(self.dirmap2))
            
    def find(self, dirlist, dirname, name):
        i = 0
        if dirname == name:
            return i

        #while n < len(dirlist):
        #    if dirlist[n] == name:
        #        i = n
        #        break
        #    n += 1

        g = 7
        a = 0
        b = len(dirlist)
        p = a
        while p < b:
            if dirlist[p] == name:
                return p;
            elif dirlist[p] > name:
                if p == a or p >= b - 1:
                    return 0
                elif g == 0:
                    # Next bin search iter
                    b = p
                    p = a + (b - a) // 2
                else: 
                    return 0
            else:
                if p == a and p == b - 1:
                    return 0
                elif g == 0:
                    # Next bin search iter
                    a = p
                    p = a + (b - a) // 2
                else:
                    a = p
                    p += 1
                    g -= 1
    
        return 0
        
    def find_map(self, filename, dirmap):
        if dirmap is None:
            return (None, -1)
        fname = strip_name(filename)
        fname_s = strip_sidename(fname)
        if fname != fname_s:
            raise ValueError("revert dir, 2-side image found: %s" % filename)

        v = dirmap.get(fname_s)
        if v is None or len(v) == 0:
            return (None, -1)
        else:
            if fname == fname_s:
                return (fname_s, 0)
    
    def load(self):
        self.set_enabled()
        self.display_indx(self.img_label1, self.status_label1, self.dirlist1, self.i1)
        self.display_map(self.img_label2, self.status_label2, self.dirlen2, self.dirmap2, self.fname2, self.i2)
    
    def load_dirs(self, name1, name2):
        (self.dirlist1, self.dirname1) = self.read_dir(name1)
        if len(self.dirlist1) == 0:
            raise ValueError("empthy dir: %s" % self.dirname1)
        self.dirlist1.sort()
        self.i1 = self.find(self.dirlist1, self.dirname1, name1)
        
        (dirlist2, self.dirname2) = self.read_dir(name2)
        self.dirlen2 = len(dirlist2)
        self.makemap_2(dirlist2)
        (self.fname2, self.i2) = self.find_map(self.dirlist1[self.i1], self.dirmap2)
        
    def read_dir(self, name):
        imgext = (".png", ".tif", ".tiff", ".jpg", ".jpeg")
        dirlist = list()
        filename = None
        if os.path.isfile(name):
            ext = os.path.splitext(name)[1]
            if ext in imgext:
                filename = name
            dirname = os.path.dirname(name)
        elif os.path.isdir(name):
            dirname = name
        else:
            raise ValueError("%s not a dir or file" % name)
        
        for file in os.listdir(dirname):
            fname = os.path.join(dirname, file)
            if not os.path.isfile(fname):
                continue
            ext = os.path.splitext(file)[1].lower()
            if ext in imgext:
                dirlist.append(fname)

        return (dirlist, dirname)

        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    if len(sys.argv) == 3:
        n1 = sys.argv[1]
        n2 = sys.argv[2]
        ex = App(app, n1, n2)
    else:
        sys.stderr.write("incorrect arguments, use:\n\t%s [ sourcedir | startfile ] dir\n" % sys.argv[0])
        sys.stderr.write("  if first argument is a dir or startfile not found, started from first file\n")
        sys.stderr.write("for example, to compare Scan Tailor results with 2-pages splited images, use:\n\t%s [ sourcedir | startfile ] outdir\n" % sys.argv[0])
        sys.exit(1)
    
    sys.exit(app.exec_())

    