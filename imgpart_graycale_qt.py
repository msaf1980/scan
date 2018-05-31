#!/usr/bin/python

# Converted selected regions to grayscale, black & white or white
# Useful for clean scan processing results
# Install Qt5 and PIL (or Pillow)
# Hotkeys:
#   Select:
#        Ctrl+D     Del selected regions
#        Ctrl+E     Reset all regions
#        Ctrl+A     Select All
#   Process:
#        Ctrl+G     Process selected regions to Grayscale
#        Ctrl+B     Process selected regions to Black and White
#        Ctrl+W     Process selected regions to White
#
#   Mouse Right Button click display selected pixel info
        
import sys
import os
from PyQt5.QtWidgets import *
from PyQt5.QtGui import QIcon, QPixmap, QKeySequence
from PyQt5.QtCore import Qt, QSize, QRect, QPoint
from PIL import Image
from PIL.ImageQt import ImageQt

bw_threshold = 80

def rgb_to_grayscale(r, g, b):
    return (r * 299 + g * 587 + b * 114) // 1000

def pixel_info(img, x, y):
    pix = img.getpixel((x, y))
    s = str(pix)
    if img.mode in ("RGB", "RGBA"):
        gray = rgb_to_grayscale(pix[0], pix[1], pix[2])
        s += ", as gray %d" % gray
    return s

def img_mode(mode):
    if mode == "1":
        return "B&W"
    elif mode == "P":
        return "Color"
    elif mode == "L":
        return "Grayscale"
    else:
        return mode

        
class Range:
    def __init__(self, rband, aratio):
        self.rband = rband
        (self.x1, self.y1, self.x2, self.y2) = self.rband.geometry().getCoords()
        if self.x1 < 0:
            self.x1 = 0
        else:
            self.x1 = int(self.x1 * aratio)
        if self.y1 < 0:
            self.y1 = 0
        else:
            self.y1 = int(self.y1 * aratio)
        self.x2 = int(self.x2 * aratio)
        self.y2 = int(self.y2 * aratio)
        
        self.s = "%d:%d %d:%d" % (self.x1, self.y1, self.x2, self.y2)
        
    def __cmp__(self, other):
        if self.s == other.s:
            return 0
        elif self.s < other.s:
            return -1
        else:
            return 1

        
class QListWidgetRange(QListWidget):
    def __init__(self, parent = None):
        QListWidget.__init__(self, parent)
        self.s_ranges = list()
        
    def addItem(self, r):
        self.s_ranges.append(r)
        item = QListWidgetItem(r.s)
        super(QListWidgetRange, self).addItem(item)
        self.parent().enable_s_rect_button()
        
    def removeSelectedItems(self):
        if len(self.s_ranges) == 0:
            return
        model = self.model()
        for selectedItem in self.selectedItems():
            qIndex = self.indexFromItem(selectedItem)
            rs = model.data(qIndex)
            #print("removing : %s" % model.data(qIndex))
            model.removeRow(qIndex.row())    
            n = 0
            while n < len(self.s_ranges):
                if self.s_ranges[n].s == rs:
                    #print("removing : %d" % n)
                    self.s_ranges[n].rband.hide()
                    del self.s_ranges[n]
                    break
                n += 1
        
        if len(self.s_ranges) == 0:
            self.parent().enable_s_rect_button(False)
                
    def clear(self):
        super(QListWidgetRange, self).clear()
        n = 0
        if len(self.s_ranges) > 0:
            while n < len(self.s_ranges):
                #print("removing : %d" % n)
                self.s_ranges[n].rband.hide()
                n += 1
        
            self.s_ranges = list()
            
        self.parent().enable_s_rect_button(False)
        
        
class QLabelRect(QLabel):
    def __init__(self, parent = None):
        QLabel.__init__(self, parent)
        self.setStyleSheet("border:1px solid rgb(0, 255, 0); border-radius: 2px")
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.origin = None

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.origin = QPoint(event.pos())
            self.rubberBand.setGeometry(QRect(self.origin, QSize()))
            self.rubberBand.show()

    def mouseMoveEvent(self, event):
        if not self.origin.isNull():
            self.rubberBand.setGeometry(QRect(self.origin, event.pos()).normalized())
     
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            if not self.origin is None:
                #(x1, y1, x2, y2) = self.rubberBand.geometry().getCoords()
                #if x1 < 0:
                #    x1 = 0
                #else:
                #    x1 = int(x1 * self.parentWidget().aspect)
                #if y1 < 0:
                #    y1 = 0
                #else:
                #    y1 = int(y1 * self.parentWidget().aspect)
                #x2 = int(x2 * self.parentWidget().aspect)
                #y2 = int(y2 * self.parentWidget().aspect)
                #print("%d:%d %d:%d %f" % (x1, y1, x2, y2, self.parent().aspect))
                
                r = Range(self.rubberBand, self.parent().aspect)
                self.parent().list_srect.addItem(r)
                #print("%d %d:%d %f" % (r.x1, r.y1, r.x2, r.y2, self.parent().aspect))
                
                self.origin = None
                #self.rubberBand.hide()
                self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        elif not self.parent() is None:
            self.parent().display_pixel(event.pos().x() * self.parent().aspect, event.pos().y() * self.parent().aspect)
                
    def select_all(self):
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        self.rubberBand.setGeometry(0, 0, self.parent().img_label.width(), self.parent().img_label.height())
        self.rubberBand.show()
        r = Range(self.rubberBand, self.parent().aspect)
        self.parent().list_srect.addItem(r)
        
        self.origin = None
        self.rubberBand = QRubberBand(QRubberBand.Rectangle, self)
        
  
class App(QWidget):
 
    def __init__(self, app, filename = None):
        super().__init__()
        self.title = 'imgpart_graycale'
        self.left = 50
        self.top = 50
        screen_resolution = app.desktop().screenGeometry()
        self.width = screen_resolution.width() - 100
        self.height = screen_resolution.height() - 200
        
        self.img = None
        self.img_process = None
        self.aspect = 1.0
        
        self.changed = False

        if filename is None:
            self.index = -1
            self.dirlist = list()
        else:
            self.index = self.read_dir(filename)
        
        self.initUI(filename)
    
    def read_dir(self, name):
        imgext = ("bmp", ".png", ".tif", ".tiff", ".jpg", ".jpeg")
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
            
        self.dirlist = list()
        n = 0
        i = -1
        for file in os.listdir(dirname):
            fname = os.path.join(dirname, file)
            ext = os.path.splitext(file)[1]
            if os.path.isfile(fname) and ext in imgext:
                self.dirlist.append(fname)
                if fname == filename:
                    i = n
                n += 1
        #print("%d %d %s" % (i, n, filename)) 
        if len(self.dirlist) > 0 and i == -1:
            return 0
        else:
            return i
    
    def open(self, filename = None):
        if not filename is None:
            self.filename = filename
        elif self.filename is None:
            return
        self.img = Image.open(self.filename)
       
        self.set_changed(False)

        (width, height) = self.img.size
        
        self.display()
        
        self.rect = list()
        self.setWindowTitle(self.title + " " + self.filename)
        
        self.status_bar.showMessage("%s %s [%d:%d] %s" % (img_mode(self.img.mode), self.img.format, self.img.size[0], self.img.size[1], self.filename))
        
        self.enable_s_rect_button(False)
        
        self.check_prev_next()
        
    def display(self):
        qim = ImageQt(self.img)
        
        s_width = self.img_label.width()
        s_height = self.img_label.height()

        #print("%s / %s" % (self.img.size[0], s_width))
        #print("%s / %s" % (self.img.size[1], s_height))
        aspect_w = float(self.img.size[0]) / s_width
        aspect_h = float(self.img.size[1]) / s_height
        #print("%f %f" % (aspect_w, aspect_h))
        self.aspect = aspect_w if aspect_w > aspect_h else aspect_h
        
        pixmap = QPixmap.fromImage(qim).scaled(self.img.size[0] // self.aspect, self.img.size[1] // self.aspect, Qt.KeepAspectRatio,Qt.SmoothTransformation)
        self.img_label.setPixmap(pixmap)

    def display_pixel(self, x, y):
        if self.img is None or x >= self.img.size[0] or y >= self.img.size[1]:
            self.status_bar2.showMessage("")
        else:
            self.status_bar2.showMessage("[%d:%d] = %s" % (x, y, pixel_info(self.img, x, y)))
    
    def check_prev_next(self):
        #print("%d %d" % (self.index, len(self.dirlist)))
        if self.index == -1:
            self.prev_button.setEnabled(False)
            self.next_button.setEnabled(False)
            return
        if self.index == 0:
            self.prev_button.setEnabled(False)
        else:
            self.prev_button.setEnabled(True)
        if self.index >= len(self.dirlist) - 1:
            self.next_button.setEnabled(False)
        else:
            self.next_button.setEnabled(True)
        
    def enable_s_rect_button(self, e = True):
    
        self.del_button.setEnabled(e)
        self.reset_button.setEnabled(e)
        if self.img is None or not self.img.mode in ("RGB", "RGBA", "P") or len(self.list_srect.s_ranges) == 0:
            gs = False
        else:
            gs = e
        self.process_gs_button.setEnabled(gs)
        if self.img is None or self.img.mode == "1" or len(self.list_srect.s_ranges) == 0:
            bw = False
        else:
            bw = e
        self.process_bw_button.setEnabled(bw)
        
        self.process_w_button.setEnabled(e)

    def set_changed(self, e = True):
        self.changed = e
        self.save_button.setEnabled(e)
        
    def delete_s_ranges(self):
        self.list_srect.removeSelectedItems()
        
    def reset_s_ranges(self):
        self.list_srect.clear()
    
    def select_all(self):
        self.reset_s_ranges()
        self.img_label.select_all()
        
    
    def prev(self):
        if self.index > 0:
            self.index -= 1
            self.reset_s_ranges()
            self.open(self.dirlist[self.index])
        self.check_prev_next()
        
    def next(self):
        if self.index < len(self.dirlist) - 1:
            self.index += 1
            self.reset_s_ranges()
            self.open(self.dirlist[self.index])
        self.check_prev_next()
        
    def process_grayscale(self):
        if not self.img.mode in ("RGB", "RGBA", "P") or len(self.list_srect.s_ranges) == 0:
            self.list_srect.clear()
            return
        self.set_changed()
        n = 0
        pix = self.img.load()
        (width, height) = self.img.size
        while n < len(self.list_srect.s_ranges):
            #print("removing : %d" % n)
            #print(self.list_srect.s_ranges[n].s)
            y = self.list_srect.s_ranges[n].y1
            while y <= self.list_srect.s_ranges[n].y2 and y < height:
                x = self.list_srect.s_ranges[n].x1
                while x <= self.list_srect.s_ranges[n].x2 and x < width:
                    if self.img.mode == "P":
                        #r = (pix[x, y] >> 5) * 32
                        #g = ((pix[x, y] & 28) >> 2) * 32
                        #b = (pix[x, y] & 3) * 64      
                        
                        #r = (pix[x, y] >> 5) * 255 // 7
                        #g = ((pix[x, y] >> 2) & 0x07) * 255 // 7
                        #b = (pix[x, y] & 0x03) * 255 // 3
                        
                        r = pix[x, y]
                        g = pix[x, y]
                        b = pix[x, y]
                    else:
                        (r, g, b) = pix[x, y]
                    #gray = int((r + g + b) / 3)
                    #gray = int(0.2989 * r + 0.5870 * g + 0.1140 * b)
                    gray = (r * 299 + g * 587 + b * 114) // 1000
                    if self.img.mode == "P":
                        pix[x, y] = gray
                    else:
                        pix[x, y] = (gray, gray, gray)
                    x += 1
                y += 1
            n += 1
            
        self.display()
        self.list_srect.clear()
        return
        
    def process_bw(self):
        global bw_threshold
        if not self.img.mode in ("RGB", "RGBA", "P", "L") or len(self.list_srect.s_ranges) == 0:
            self.list_srect.clear()
            return
        self.set_changed()    
        n = 0
        bw_threshold = self.bw_threshold_edit.value()
        print(bw_threshold)
        pix = self.img.load()
        (width, height) = self.img.size
        while n < len(self.list_srect.s_ranges):
            #print("removing : %d" % n)
            #print(self.list_srect.s_ranges[n].s)
            y = self.list_srect.s_ranges[n].y1
            while y <= self.list_srect.s_ranges[n].y2 and y < height:
                x = self.list_srect.s_ranges[n].x1
                while x <= self.list_srect.s_ranges[n].x2 and x < width:
                    if self.img.mode in ("L", "P"):
                        if pix[x, y] >= bw_threshold:
                            pix[x, y] = 255
                        else:
                            pix[x, y] = 0
                    elif self.img.mode == "RGBA":
                        (r, g, b, a) = pix[x, y]
                        bw = rgb_to_grayscale(r, b, b)
                        if bw >= bw_threshold:
                            bw = 255
                        else:
                            bw = 0
                        pix[x, y] = (bw, bw, bw, a)
                    else:
                        (r, g, b) = pix[x, y]
                        bw = rgb_to_grayscale(r, b, b)
                        if bw >= bw_threshold:
                            bw = 255
                        else:
                            bw = 0
                        pix[x, y] = (bw, bw, bw)
                    x += 1
                y += 1
            n += 1
            
        self.display()
        self.list_srect.clear()
        return
        
    def process_w(self):
        if not self.img.mode in ("RGB", "RGBA", "P", "L", "1") and len(self.list_srect.s_ranges) == 0:
            self.list_srect.clear()
            return
        self.set_changed()    
        n = 0
        pix = self.img.load()
        (width, height) = self.img.size
        while n < len(self.list_srect.s_ranges):
            #print("removing : %d" % n)
            #print(self.list_srect.s_ranges[n].s)
            y = self.list_srect.s_ranges[n].y1
            while y <= self.list_srect.s_ranges[n].y2 and y < height:
                x = self.list_srect.s_ranges[n].x1
                while x <= self.list_srect.s_ranges[n].x2 and x < width:
                    if self.img.mode in ("1", "P", "L"):
                        pix[x, y] = 255
                    elif self.img.mode == "RGBA":
                        (r, g, b, a) = pix[x, y]
                        pix[x, y] = (255, 255, 255, a)
                    else:
                        pix[x, y] = (255, 255, 255)
                    x += 1
                y += 1
            n += 1
            
        self.display()
        self.list_srect.clear()
        return
        
    def save(self):
        if not self.changed:
            return
        filename_back = self.filename + ".back"
        if os.path.isfile(filename_back):
            os.remove(filename_back)
        os.rename(self.filename, filename_back)
        
        self.img.save(self.filename)

        #if self.img.format == "PNG":
            # Convert to 8-bit color
        #    self.img.convert('P', palette=Image.ADAPTIVE, colors=255).save(self.filename, optimize=True)
        #else:
            #if self.img.mode <> "RGB":
            #    self.img.convert(self.img.mode).save(self.filename)
            #else:
                # Save as 24-bit RGB
                #self.img.save(self.filename)
            
        self.set_changed(False)
    
    def reload(self):
        self.read_dir(self.filename)
        self.reset_s_ranges()
        self.open()
        
    def initUI(self, filename):
        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)
        
        layout = QHBoxLayout()
       
        vbox1 = QVBoxLayout()
        
        # Create widget
        self.img_label = QLabelRect(self)
        self.img_label.resize(self.width - 100, self.height)
        #self.img_label.width = self.width() - 100
        #self.img_label.height = self.height()

        self.img_label.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        layout.addWidget(self.img_label)
        
        vbox2 = QVBoxLayout()
        
        self.list_srect = QListWidgetRange()
        vbox2.addWidget(self.list_srect)
        
        hbox2_2 = QHBoxLayout()
        
        self.del_button = QPushButton("Del")
        self.del_button.clicked.connect(self.delete_s_ranges)
        shortcut = QShortcut(QKeySequence("Ctrl+D"), self)
        shortcut.activated.connect(self.delete_s_ranges)
        hbox2_2.addWidget(self.del_button)
        
        self.reset_button = QPushButton("Reset")
        self.reset_button.clicked.connect(self.reset_s_ranges)
        shortcut = QShortcut(QKeySequence("Ctrl+E"), self)
        shortcut.activated.connect(self.reset_s_ranges)        
        hbox2_2.addWidget(self.reset_button)
        self.select_all_button = QPushButton("Select All")
        self.select_all_button.clicked.connect(self.select_all)
        shortcut = QShortcut(QKeySequence("Ctrl+A"), self)
        shortcut.activated.connect(self.select_all) 
        hbox2_2.addWidget(self.select_all_button)
        self.process_gs_button = QPushButton("Process Gs")
        self.process_gs_button.clicked.connect(self.process_grayscale)
        shortcut = QShortcut(QKeySequence("Ctrl+G"), self)
        shortcut.activated.connect(self.process_grayscale)
        hbox2_2.addWidget(self.process_gs_button)
        self.process_bw_button = QPushButton("Process BW")
        self.process_bw_button.clicked.connect(self.process_bw)
        shortcut = QShortcut(QKeySequence("Ctrl+B"), self)
        shortcut.activated.connect(self.process_bw)
        hbox2_2.addWidget(self.process_bw_button)
        self.process_w_button = QPushButton("Process W")
        self.process_w_button.clicked.connect(self.process_w)
        shortcut = QShortcut(QKeySequence("Ctrl+W"), self)
        shortcut.activated.connect(self.process_w)
        hbox2_2.addWidget(self.process_w_button)
        vbox2.addLayout(hbox2_2)

        self.enable_s_rect_button(False)
        
        hbox2_3 = QHBoxLayout() 
        
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save)
        shortcut = QShortcut(QKeySequence("Ctrl+S"), self)
        shortcut.activated.connect(self.save)
        hbox2_3.addWidget(self.save_button)
        
        self.reload_button = QPushButton("Reload")
        self.reload_button.clicked.connect(self.reload)
        shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        shortcut.activated.connect(self.reload)
        hbox2_3.addWidget(self.reload_button)

        bw_threshold_label = QLabel("BW threshold")
        bw_threshold_label.setMaximumWidth(100)
        hbox2_3.addWidget(bw_threshold_label)
        self.bw_threshold_edit = QSpinBox()
        self.bw_threshold_edit.setMaximumWidth(100)
        self.bw_threshold_edit.setMinimum(0)
        self.bw_threshold_edit.setMaximum(255)
        self.bw_threshold_edit.setSingleStep(1)
        self.bw_threshold_edit.setValue(80)
        hbox2_3.addWidget(self.bw_threshold_edit)
        
        vbox2.addLayout(hbox2_3)
        
        hbox2_4 = QHBoxLayout() 
        
        self.prev_button = QPushButton("Prev")
        self.prev_button.clicked.connect(self.prev)
        shortcut = QShortcut(QKeySequence("Ctrl+P"), self)
        shortcut.activated.connect(self.prev)
        hbox2_4.addWidget(self.prev_button)
        
        self.next_button = QPushButton("Next")
        self.next_button.clicked.connect(self.next)
        shortcut = QShortcut(QKeySequence("Ctrl+N"), self)
        shortcut.activated.connect(self.next)
        hbox2_4.addWidget(self.next_button)
        
        vbox2.addLayout(hbox2_4)
        
        hbox2_5 = QHBoxLayout() 
        
        self.status_bar = QStatusBar()
        hbox2_5.addWidget(self.status_bar)
        
        self.status_bar2 = QStatusBar()
        hbox2_5.addWidget(self.status_bar2)
        
        vbox2.addLayout(hbox2_5)
        
        self.set_changed(False)
        
        layout.addLayout(vbox2)
        
        #cmd_layout = QGridLayout()
        
        #layout.addWidget(cmd_layout, 1, 1)
        
        self.setLayout(layout)
        
        if self.index >= 0:
            self.open(self.dirlist[self.index])

        self.show()

        
if __name__ == '__main__':
    app = QApplication(sys.argv)
    if len(sys.argv) == 2:
        f = sys.argv[1]
        ex = App(app, f)
    #elif len(sys.argv) == 1:
    #    f = None
    else:
        sys.stderr.write("incorrect arguments, use:\n\t%s [ sourcedir | startfile ]\n" % sys.argv[0])
        sys.exit(1)
    
    sys.exit(app.exec_())
