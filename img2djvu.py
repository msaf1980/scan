#!/usr/bin/env python

# Multithreaded script for compose multipage djvu document from induvidual images or singlepage djvu's
### Inspired by script pdf-trim-to-djvu.sh (http://gist.github.com/315791)
### PUBLIC DOMAIN
## Python 3.5 or greater is required
#
# Use ImageMagic and DJVU Libre
# For extract pages from PDF used Ghostscript
# Add to path, if not. For Windows
# set PATH=d:\utils\graph\imagemagick;C:\Program Files (x86)\DjVuLibre;c:\Program Files (x86)\gs\gs9.19\bin;%PATH%
# python img2djvu.py -i d:\scan -c png -f d:\scan.djvu

import sys, os, glob, subprocess, re, optparse
import shlex
import tempfile, shutil
from distutils import spawn
from time import sleep
import traceback
import threading
import queue

running = True

def exit_error(msg):
    if msg:
        sys.stderr.write(msg)
    sys.exit(1)
    
def basename_noext(filename):
    return os.path.splitext(os.path.basename(filename))[0]

def is_djvu(filename):
    filename, file_extension = os.path.splitext(filename)
    if file_extension.lower() in (".djv", ".djvu"):
        return True
    else:
        return False

def workers_init(WorkerClass, jobs):
    workers = []
    queue_in = queue.Queue()
    queue_out = queue.Queue()
    for _ in range(jobs):
        worker = WorkerClass(queue_in, queue_out)
        worker.start()
        workers.append(worker)
    return(workers, queue_in, queue_out)

        
# Return stdout
def call_out(cmd_args):
    proc = subprocess.Popen(cmd_args, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    output = proc.communicate()
    #print(output)
    #print(proc.returncode)
    if proc.returncode > 0:
        print(output)
        raise ValueError
    elif output[0] is None:
        raise ValueError
    return output[0]

    
### Ghostscript extract
def pdf_extract(inf, gs_out, out_dir):
    cmd_args = [ gs, "-q", "-dBATCH", "-dNOPAUSE", "-r{:d}".format(dpi) ]
    cmd_args.append("-sDEVICE={:s}".format(gs_out))
    cmd_args.append("-sOutputFile={:s}".format(os.path.join(out_dir, "%05d.png")))
    cmd_args.append(inf)
    subprocess.check_call(cmd_args)
    print("GS {:s}".format(basename_noext(inf)))


# Convert images, extracted with Ghostscript
#def convert(in_dir, convert)
#    for conv in convert:
#        c = conv.split("=")
        #mono=2-10,15 256=1

    
### General coders functions

def colorcoder(inf, outf):
    if usecodjvu < 1:
        c44coder(inf, outf)
    else:
        codjvucoder(inf, outf)

### Subcoders functions

### Black and white
def cjb2coder(inf, outf):
  subprocess.check_call([ cjb2, cjb2opt, "-dpi", str(dpi), inf, outf ])
  print("B {:s}".format(basename_noext(inf)))

def minidjvucoder(inf_list, outf):
    cmd    = "{:s} -d {:d} -p {:d} {:s}".format(minidjvu, dpi, usemini, minidjvuopt)
    cmd_args = shlex.split(cmd)
    cmd_args.extend(inf_list)
    cmd_args.append(outf)
    subprocess.check_call(cmd_args)
    return("M:{%d} {:s} - {:s}".format(len(inf_list), basename_noext(inf_list[0]), basename_noext(inf_list[-1])))

### Color
def cpaldjvucoder(inf, outf):
    cmd    = "{:s} -dpi {:d} {:s}".format(cpaldjvu, dpi, cpaldjvuopt)
    cmd_args = shlex.split(cmd)
    cmd_args.append(inf)
    cmd_args.append(outf)
    subprocess.check_call(cmd_args)
    print("F {:s}".format(basename_noext(inf)))

def c44coder(inf, outf):
    cmd    = "{:s} -dpi {:d} {:s}".format(c44, dpi, c44opt)
    cmd_args = shlex.split(cmd)
    cmd_args.append(inf)
    cmd_args.append(outf)
    subprocess.check_call(cmd_args)
    print("C {:s}".format(basename_noext(inf)))

# Layer separation and "forced segmentation" coder
def codjvucoder(inf, outf):
    # image parameters
    of, oext = os.path.splitext(outf)
    format = "%[fx:ceil(w/{:d})]x%[fx:ceil(h/{:d})]".format(usecodjvu, usecodjvu)
    try:
        newsize = call_out([ identify, '-format', format, inf ]) + "!"
    except ValueError:
        #print format
        exit_error("can't identify {:s}\n".format(inf))
    # separate layers from Scan Tailor
    subprocess.check_call([ convert,  inf, "-threshold", "1", of + "-fore.pbm" ], shell=True)
    cmd_args = [ convert, inf, "-fill", "white", "-opaque", "black" ]
    cmd_args.extend(shlex.split(usepro))
    cmd_args.extend([ "-resize", newsize, of + "-back.ppm" ])
    subprocess.check_call(cmd_args, shell=True)
    # make BG44 chunk
    subprocess.check_call([ c44, c44opt, "-dpi", str(dpi), of + "-back.ppm ", of + "-back.djvu" ])
    subprocess.check_call([ djvuextract, of + "-back.djvu", "BG44=" + of + "-bg44.cnk" ])
    # make Sjbz chunk
    cjb2coder(of + "-fore.pbm", of + "-sjbz.djvu")
    subprocess.check_call([ djvuextract, of + "-sjbz.djvu", "Sjbz=" + of + "-sjbz.cnk" ])
      #if dv < 3523:
    # make FG44 chunk from background (!)
    subprocess.check_call([ convert, "-size", newsize, "-depth", "8", "xc:black", of + "-fore.pgm" ], shell=True)
    subprocess.check_call([ c44, "-dpi", str(dpi), "-slice", "120", of + "-fore.pgm", of + "-fore.djvu" ])
    subprocess.check_call([ djvuextract, of + "-fore.djvu", "BG44=" + of + "-fg44.cnk" ])
    # make compound DjVu
    subprocess.check_call([ djvumake, outf, "INFO=,,{:d}".format(dpi), "Sjbz=" + of + "-sjbz.cnk", "FG44=" + of + "-fg44.cnk".format(of), "BG44=" + of + "-bg44.cnk" ])
    os.remove(of + "-bg44.cnk")
    os.remove(of + "-fg44.cnk")
    os.remove(of + "-fore.djvu")
    os.remove(of + "-fore.pbm")
    os.remove(of + "-fore.pgm")    
    os.remove(of + "-back.ppm")
    os.remove(of + "-back.djvu")
    os.remove(of + "-sjbz.djvu")
    os.remove(of + "-sjbz.cnk")

      #else
    # use new ability of djvumake to create FGbz chunk on the fly
    #subprocess.check_call([ djvumake, outf, "INFO=,,{:d}".format(dpi), "Sjbz=sjbz.cnk", "FGbz=\"#black\"", "BG44=bg44.cnk" ])
    
    print("L {:s}", os.path.splitext(os.path.basename(inf)))

# Run OCR
def ocr(djvu):
    if useocr:
        print("Starting OCR")
        subprocess.check_call([ ocrodjvu, "--engine", ocrengine, "--language", ocrlanguage, "--jobs", str(jobs), "--in-place", "--on-error=resume",  djvu ])

def nomini_process(f):
    global running
    inf = os.path.join(in_dir, f)
    if is_djvu(inf):
        return inf
    else:
        of = os.path.join(tmp_dir, f)
        of_pnm = of + ".pnm"
        of_djvu = of + ".djvu"
        
        if os.path.exists(of_djvu):
            return (inf, of_djvu, None)
        try:
            if not os.path.exists(of_pnm):
                subprocess.check_call([ convert, inf, of_pnm ], shell=True)
        
            if int(call_out([ identify, "-format", "%z", of_pnm ])) > 1:
                if treshold > 0:
                    colors = int(call_out([ identify, "-format", "%k", of_pnm ]))
                    if colors < treshold:
                        cpaldjvucoder(of_pnm, of_djvu)
                    else:
                        colorcoder(of_pnm, of_djvu)
                else:
                    colorcoder(of_pnm, of_djvu)
            else:
                cjb2coder(of_pnm, of_djvu)
            return (inf, of_djvu, None)
        except ValueError:
            running = False
            return (inf, None, "not identify %s: %s\n" % (inf, traceback.format_exc()))
        except KeyboardInterrupt:
            running = False
            if os.path.exists(of_djvu):
                sleep(1)
                os.remove(of_djvu)
            if os.path.exists(of_pnm):
                sleep(1)
                os.remove(of_pnm)
            return (inf, None, "inperrupted process %s\n%s" % (f, traceback.format_exc()))
        except Exception:
            if os.path.exists(of_djvu):
                os.remove(of_djvu)
            return (inf, None, "failed process %s\n%s" % (f, traceback.format_exc()))
        finally:
            if os.path.exists(of_pnm):
                os.remove(of_pnm)

class NoMiniProcess(threading.Thread):
    def __init__(self, queue_in, queue_out):
        threading.Thread.__init__(self)
        self._queue_in = queue_in
        self._queue_out = queue_out

    def run(self):
        global running
        while running:
            f = self._queue_in.get()
            if f == 'quit' or not running:
                break
            out = nomini_process(f)
            if out[1] is None:
                running = False
            self._queue_out.put(out)
            
### General coder and bundler
# convert all pages to pnm: convert
# determine color depth of each page
# if depth <= 1, compress with cjb2 or minidjvu
# if depth > 1 and treshold > 0, count number of unique colors
# if unique colors < 129, compress with cpaldjvu
# if unique colors >= 129, compress with c44 or codjvu
# display progress symbols (B or M for Bitonal, C for TrueColor, L for codjvu layers, F for Palette)
# create bundled DjVu file
def nomini(out_djvu, no_merge):
    global running
    files = [ f for f in os.listdir(in_dir) if os.path.isfile(os.path.join(in_dir, f)) and os.path.splitext(f)[-1].lower() in extensions ]
    files.sort()
    pgcount = len(files)
    if pgcount == 0:
        exit_error("input files not found")
    sys.stdout.write("processing {:d} files\n".format(pgcount))
    pg = 0
    djvus = [ ]
    if jobs >  1:
        res = 0
        (workers, queue_in, queue_out) = workers_init(NoMiniProcess, jobs)
        for f in files:
            if running: queue_in.put(f)
            try:
                (inf, djvu, err) = queue_out.get(False, timeout=0.5)
                if djvu is None:
                    running = False
                    res  = 1
                    sys.stderr.write("%s not converted: %s\n" % err)
                else:
                    djvus.append(djvu)
                    pg += 1
            except queue.Empty:
                pass
            except Exception as e:
                sys.stderr.write("%s\n" % traceback.format_exc())
                running = False
                res = 1

       	for worker in workers:
            queue_in.put('quit')
        for worker in workers:
            worker.join()
            
        try:
            while True:
                (inf, djvu, err) = queue_out.get(False)
                if djvu is None:
                    res  = 1
                    sys.stderr.write("%s not converted: %s\n" % err)
                else:
                    djvus.append(djvu)
                    pg += 1
                    if pg % 10 == 0:
                        sys.stdout.write("processed {:d} files\n".format(pg))
                        sys.stdout.flush()
        except queue.Empty:
            pass
            
        if res == 0:
            sys.stdout.write("processed {:d} files\n".format(pg))
            sys.stdout.flush()
        else:
            sys.exit(res)
    else:
        for f in files:
            (f, djvu, err) = nomini_process(f)
            if djvu is None:
                sys.stderr.write(err)
                sys.exit(1)
            djvus.append(djvu)
            pg += 1
            if pg % 10 == 0:
                    sys.stdout.write("processed {:d} files\n".format(pg))
                    
        sys.stdout.write("processed {:d} files\n".format(pg))
        
    if no_merge:
        return
        
    djvus.sort()
    cmd_args = [ djvm, "-c",  out_djvu ]
    cmd_args.extend(djvus)
    subprocess.check_call(cmd_args)
    print("merged {:s}".format(out_djvu))
    ocr(out_djvu)

### Minidjvu-based coder and bundler
# Similar to previous, but instead of cjb2 minidjvu called every time when black and white sequence interrupted with color image, or when sequence ends on black and white file
# Works with sequences, therefore visually less verbose, minidjvu is also slower than cjb2
def mini(out_djvu, no_merge):
    exit_error("minidjvu  not relised yet")


def main():
    global useocr
    
    global ags
    global age
    global identify
    global convert    
    global c44
    global c44opt
    global cjb2
    global cjb2opt
    global cpaldjvu
    global cpaldjvuopt
    global minidjvu
    global minidjvuopt
    global djvuextract
    global djvumake
    global ocrodjvu
    global djvm
    global gs
    
    global ag
    global dpi
    global ocrengine
    global jobs
    global usecodjvu
    global usemini
    global ocrlanguage
    global usepro
    global treshold
    global verbose
    global out_dir
    global tmp_dir
    global in_dir
    global out_djvu
    global extensions
    
    global runnnig

    parser = optparse.OptionParser(usage='Usage: %prog [options]')
    
    #sys.stderr.write(" -a <0|1|2> aggressivity: 0 is not aggressive, 1 is aggressive, 2 is very aggressive [default: {:d}]\n".format(agdefault))    
    parser.add_option('-a', dest='ag', action='store', type="int", default=0,\
                             help='<0|1|2> aggressivity: 0 is not aggressive, 1 is aggressive, 2 is very aggressive')
    #sys.stderr.write(" -d <int>   resolution in DPI [default: {:d}]\n".format(dpidefault))
    parser.add_option('-d', dest='dpi', action='store', type="int", default=300,\
                             help='resolution in DPI')
    #sys.stderr.write(" -e <ocrengine>    [default: {:s}]\n".format(ocrenginedefault))
    parser.add_option('-e', dest='ocrengine', action='store',\
                             help='use OCR engine (supported by ocrodjvu) with this name')
    #sys.stderr.write(" -r <lang>   if not empty, use OCR engine with given language [default: {:s}]\n".format(ocrlanguagedefault))
    parser.add_option('-r', dest='ocrlanguage', action='store',\
                             help='if not empty, use OCR engine with given language')                             
    #sys.stderr.write(" -j <jobs>   number of jobs [default: {:d}]\n".format(jobs))
    parser.add_option('-j', dest='jobs', action='store', type="int", default=1,\
                             help='number of jobs (1 disabled multiprocessing')
    #sys.stderr.write(" -l <int>    [default: {:d}]\n".format(codefault))
    parser.add_option('-l', dest='usecodjvu', action='store', type="int", default=0,\
                             help='if not 0, will use forced segmentation (with <int> downsampling)')
    #sys.stderr.write(" -m <int>   if not 0, will use minidjvu (with <int> dictionary size) instead of cjb2 [default: {:d}]\n".format(midefault))
    parser.add_option('-m', dest='usemini', action='store', type="int", default=0,\
                             help='if not 0, will use minidjvu (with <int> dictionary size) instead of cjb2')
    #sys.stderr.write(" -p <color_options>   process color layer with given ImageMagick options [default: {:d}]\n".format(prodefault))
    parser.add_option('-p', dest='usepro', action='store', default="-contrast -blur 0x1",\
                             help='process color layer with given ImageMagick options')
    #sys.stderr.write(" -t <int>   if not 0, will use cpaldjvu for all images with number of colors less than <int> [default: {:d}]\n".format(trdefault))
    parser.add_option('-t', dest='treshold', action='store', type="int", default=129,\
                             help='if not 0, will use cpaldjvu for all images with number of colors less than <int>')
    #sys.stderr.write(" -v <0|1>   if not 0, minidjvu run will be verbose [default: {:d}]\n".format(verbminidefault))                             
    parser.add_option('-v', dest='verbose', action='store_true', default=False,\
                             help='verbose' )
    parser.add_option('-o', dest='out_dir', action='store', default = None,\
                             help='use output dir (by default used input dir')
    parser.add_option('-f', dest='out_djvu', action='store', default=None,\
                             help='output DJVU file name (by default merged.djvu')                             
    parser.add_option('-i', dest='in_dir',  default = None,\
                             help='input dir or pdf file')
    parser.add_option('-k', dest='keep', action='store_true', default=False,\
                             help='keep pages, extracted from pdf' )                             
    parser.add_option('-c', dest='extensions',  action = "append", default = None,\
                             help='input file extensions (by default used tif')
    parser.add_option('-g', dest='gs_out',  action = "store", default = 'png16m',\
                             help='Ghost script output device (for pdf extract) (by default used png16m. Also avaliable png256, pngalpha, pnggray, pngmono')
    #parser.add_option('--convert', dest='gs_convert',  action = "append", default = None,\
    #                         help='convert pages, extracted from pdf, like mono=2-10,15 gray=16 256=all')
    parser.add_option('-n', dest='no_merge',  action = "store_true", default=False,\
                             help='do not merge djvu pages to final djvu document')
                             
    (opts, args) = parser.parse_args()
    
    ag = opts.ag
    dpi = opts.dpi
    ocrengine = opts.ocrengine
    ocrlanguage = opts.ocrlanguage
    jobs = opts.jobs
    usecodjvu = opts.usecodjvu
    usemini = opts.usemini
    usepro = opts.usepro
    treshold = opts.treshold
    verbose = opts.verbose
    out_dir = opts.out_dir
    in_dir = opts.in_dir
    out_djvu = opts.out_djvu
    no_merge = opts.no_merge
    pdf = None
    keep = opts.keep
    gs_out=opts.gs_out
    #gs_convert = opts.gs_convert
    #print gs_convert
    if not opts.extensions:
        extensions = [ '.tif' ]
    else:
        extensions = [ "." + ext for ext in opts.extensions ]

    identify = "identify"
    convert = "convert"
    djvuextract = "djvuextract"
    djvumake = "djvumake"
    ocrodjvu = "ocrodjvu"
    djvm = "djvm"
    minidjvu = "minidjvu"
    cpaldjvu = "cpaldjvu"
    cjb2 = "cjb2"
    c44 = "c44"
    gs="gswin32c"
    
    #mono_opt="-threshold 30% -type bilevel"
    #color256_opt="-colors 256"
    #gray_opt="-colorspace Gray -gamma 1.0 -normalize -level 27%,76%"
    
    ### Checks
    if in_dir is None:
        exit_error("input dir is required\n")
    if not os.path.isdir(in_dir):
        filename, file_extension = os.path.splitext(in_dir)
        if file_extension.lower() == ".pdf":
            pdf = in_dir
            in_dir = os.path.dirname(in_dir)
            extensions = [ '.png' ]
            if not spawn.find_executable(gs):
                exit_error("Ghostscript not in path\n")
            if not out_djvu:
                out_djvu = filename + ".djvu"
        else:
            exit_error("{:s} not a dir or pdf file\n".format(in_dir))
    if not out_dir:
        out_dir = in_dir
    elif not os.path.isdir(out_dir):
        exit_error("{:s} not a dir\n".format(out_dir))
    if not out_djvu:
        out_djvu = os.path.join(out_dir, "merged.djvu")
        
    if not spawn.find_executable("cpaldjvu"):
        exit_error("DjVu Libre not in path\n")

    #dv=`cpaldjvu 2>&1| sed -e '2,$d' -e 's/^.*-\([1-9.]*\)$/\1/' -e 's/\.//g'`
    
    if not spawn.find_executable(identify):
        exit_error("ImageMagick not in path\n")

    if not ocrengine or not ocrlanguage:
        useocr=False
        if ocrengine or ocrlanguage:
            exit_error("For OCR, both OCR options (-e and -r) should be specified\n")
    else:
        if not spawn.find_executable("ocrodjvu"):
            exit_error("ocrodjvu not in path\n")
        useocr=True
    
    if usemini > 0 and not spawn.find_executable(minidjvu):
        exit_error("For -m option, minidjvu is required.\n")
        
    ### Aggressivity options
    if ag == 0:
        ags="<"
        age=">"
        c44opt=""
        cjb2opt=""
        cpaldjvuopt="-bgwhite"
        minidjvuopt=""
    elif ag == 1:
        ags="<<"
        age=">>"
        c44opt="-slice 74+13+10"
        cjb2opt="-clean"
        cpaldjvuopt=""
        minidjvuopt="--clean"
    elif ag == 2:
        ags="<<<"
        age=">>>"
        c44opt="-slice 76+15"
        cjb2opt="-lossy"
        cpaldjvuopt=""
        minidjvuopt="--lossy --aggression 200"
    else:
        exit_error("Aggressivity has only three possible values: 0, 1, or 2.\n\n")


    if verbose:
        minidjvu += " -v"
        cpaldjvu += " -verbose"
    
    ### START!
    if pdf:
        tmp_dir = tempfile.mkdtemp(dir=out_dir)
        pdf_extract(pdf, gs_out, tmp_dir)
        in_dir = tmp_dir
        #if not gs_convert:
        #    convert(tmp_dir, gs_convert)
    else:
        tmp_dir = out_dir
        
    if usemini < 1:
        nomini(out_djvu, no_merge)
    else:
        mini(out_djvu, no_merge)
    
    if pdf and tmp_dir != out_dir and not keep:
        shutil.rmtree(tmp_dir)
        
if __name__ == "__main__":
    main()
    