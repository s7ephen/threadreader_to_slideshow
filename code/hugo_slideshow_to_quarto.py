#!/usr/bin/env python2
#   (note-to-self: runtime is run_s7dev)
#   NOTE: you also have to: apt-get install python-lxml python-requests
#               Or the program will crash in inexplicable places like
#               loading ConfigParser or using time() for some reason 
#   ---- 
#   The Purpose of this tool is run AFTER threadreader_to_slideshow.py and generate a Quarto (.qmd)
#   It will then use the input and output directories of threadreader_to_slideshow.py to merely generate
#   a _index.qmd file alongside the _index.md file created by threadreader_to_slideshow.py
#
#   To quickly finish this, this tool copied all the code from threadreader_to_slideshow.py
#   So there is lots of unnecessary code for our purpose.
#   
#   HOWEVER this tool will still:
#   - Use the .ini file 
#   - Use the same input and output directories of the .INI
#
#   This tool WILL NOT:
#   - Download any of the files that threadreader_to_slideshow.py woudldve already downloaded
#   - Create any directories
#  
#   This tool SHOULD ONLY generate _index.qmd files inside directories created by threadreader_to_slideshow.py
try:
    import os
    import shutil # for file copying
    from lxml import html
    import sys
    import time
    import requests
    import json
    import subprocess
    import hashlib
    import ConfigParser
    import re
    from string import Template
except:
    print("\n\n*** Not all necessary modules are installed. *** ")

global IMGEXTS, OCREXT, TESSEXE, CONFIG, CONFIG_FNAME, TESTRUN, OUTPUT_DIR
CONFIG_FNAME = 'threadreader_to_slideshow.ini'
IMGEXTS = [".png", ".jpeg", ".tif", ".jpg"]

class SlideDeck():
    """
        This class was necessary to:
        generate (using Templates) the markdown files for a reveal-hugo presentation
        using the contents of directories found in a threadreader_downloader directory.

        We are using Python's str.Template because it is built-in and we dont require
        the features from fancier Templating libraries.

        This class was reluctantly necessary because we have to handle cases where there
        are sections of the document that can have N-number of subsections, so we couldn't just
        a single static template. (I tried templates of templates but it was basically turning
        into a unreadable mess, so I just did the class for ease of readibility later.)

        Basic USAGE:
            deck = SlideDeck()
            deck.add_slidedeck_header()
            deck.add_single_image_slide(".asdfasdfasdf","50%","50%","50%")
            deck.add_header_text("A SLIDE YAY")
            deck.add_slide_divider() 
            deck._add_image_to_multi_image("./asdfasdfasdf")
            deck._add_image_to_multi_image("./aasdfasdiuo8sdf", "45%")
            deck._add_image_to_multi_image("./asdfasdasdliua38asdaxczzzzzfasdf", "65%","75%")
            deck.add_multi_image_slide()
            print deck            
    """
    def __init__(self):
        self.Deck = ""  # when intialized we start with a blank document, we'll be appending to it using templates.
        self.multi_imgs = [] # will be an array of dicts with info about each image to be embedded.
        self.DIV_RSTACK=Template('''
<section>
<div class="r-stack">
 $imgs
</div>
</section>''')
        self.IMG_SECTION=Template('''
<img
    class="fragment"
    src="$img_path"
    width="$width"
    height="$height"
/>''')
        self.SLIDEDECK_HEADER=Template('''
+++
title = "$title"
outputs = ["Reveal"]
+++''')
        self.SLIDE_DIVIDER = '''

---

        '''
        self.SINGLE_IMAGE_SLIDE = Template('''
{{< figure src="$img_path" title="$title" width="$width" height="$height" >}}
        ''')
        self.VIDEO_SLIDE = Template('''
<video data-autoplay src="$vid_path" width="$width" height="$height"></video>
        ''')

    def __str__(self):
        """
            So we can print() this class and get the full document.
        """
        return self.Deck

    def __repr__(self):
        """
            This exists so we can type() this thing. 
        """
        return "This is a SlideDeck class for building Reveal-Hugo markdowns dynamically. At location: "+hex(id(self))

    def add_single_image_slide(self, c_img_path, c_title, c_width="50%", c_height="50%"):
        self.Deck += self.SINGLE_IMAGE_SLIDE.substitute(img_path = c_img_path, title = c_title,\
                                                          width = c_width, height = c_height)
        self.Deck += self.SLIDE_DIVIDER 

    def add_video_slide(self, c_vid_path, c_width="100%", c_height="100%"):
        self.Deck += self.VIDEO_SLIDE.substitute(vid_path = c_vid_path, width = c_width, height = c_height)
        self.Deck += self.SLIDE_DIVIDER
   
    def add_slidedeck_header(self,c_title="My Presentation"):
        self.Deck += self.SLIDEDECK_HEADER.substitute(title=c_title) 

    def add_header_text(self, text="This is a Header"):
        self.Deck += "# "+text

    def add_subheader_text(self, text="This is a subheader"):
        self.Deck += "## "+text

    def add_text(self, text="This is some Text"):
        self.Deck += text

    def _add_image_to_multi_image(self, c_src, c_width="50%", c_height="%50"):
        self.multi_imgs.append({"src":c_src,"width":c_width,"height":c_height})

    def add_slide_divider(self):
        self.Deck += self.SLIDE_DIVIDER


    def _reset_multi_imgs(self):
        """
            To be used by add_multi_image_slide() to clear out
            all added images, after the slide has been created.

            otherwise these hang around and mess up any new slide being created.
        """
        self.multi_imgs = [] # will be an array of dicts with info about each image to be embedded.

    def add_multi_image_slide(self):
        """
            This one is less straight forward that others.
            To use it you have to first have use:
                ._add_image_to_multi_image() 

            This allows for having multi-image slides with N-number of images.

            once you have added all the images to the multi-image slide
            then you call this function and it will generate that slide section.
        """
        c_imgs = ""
        for multi_img in self.multi_imgs:
            c_imgs += self.IMG_SECTION.substitute(img_path = multi_img["src"], width = multi_img["width"],\
                                                    height = multi_img["height"])
        self.Deck += self.DIV_RSTACK.substitute(imgs = c_imgs)
        self.Deck += self.SLIDE_DIVIDER
        self._reset_multi_imgs()

class QuartoDeck():
    """
        This class was necessary to:
        generate (using Templates) the markdown files for a Quarto presentation
        using the contents of directories found in a threadreader_downloader directory.

        We are using Python's str.Template because it is built-in and we dont require
        the features from fancier Templating libraries.

        This class was reluctantly necessary because we have to handle cases where there
        are sections of the document that can have N-number of subsections, so we couldn't just
        a single static template. (I tried templates of templates but it was basically turning
        into a unreadable mess, so I just did the class for ease of readibility later.)

        Basic USAGE:
            deck = QuartoDeck()
            deck.add_slidedeck_header()
            deck.add_single_image_slide(".asdfasdfasdf","50%","50%","50%")
            deck.add_header_text("A SLIDE YAY")
            deck.add_slide_divider() 
            deck._add_image_to_multi_image("./asdfasdfasdf")
            deck._add_image_to_multi_image("./aasdfasdiuo8sdf", "45%")
            deck._add_image_to_multi_image("./asdfasdasdliua38asdaxczzzzzfasdf", "65%","75%")
            deck.add_multi_image_slide()
            print deck            
    """
    def __init__(self):
        self.Deck = ""  # when intialized we start with a blank document, we'll be appending to it using templates.
        self.multi_imgs = [] # will be an array of dicts with info about each image to be embedded.
        self.DIV_RSTACK=Template('''
:::: {.columns}
$imgs

::::
''')
        self.IMG_SECTION=Template('''::: {.column width="$height"}
![]($img_path)
:::
''')
        self.SLIDEDECK_HEADER=Template('''---
title: "$title"
format:
  revealjs: 
    transition: slide
    transition-speed: fast
    theme: [dark]
    menu: true
    lightbox: auto
---
''')
        self.SLIDE_DIVIDER = '''

##
        '''
        self.SINGLE_IMAGE_SLIDE = Template('''
![$title]($img_path){fig-align="center"}
        ''')
        self.VIDEO_SLIDE = Template('''
{{<video $vid_path>}}
        ''')

    def __str__(self):
        """
            So we can print() this class and get the full document.
        """
        return self.Deck

    def __repr__(self):
        """
            This exists so we can type() this thing. 
        """
        return "This is a SlideDeck class for building Reveal-Hugo markdowns dynamically. At location: "+hex(id(self))

    def add_single_image_slide(self, c_img_path, c_title, c_width="50%", c_height="50%"):
        self.Deck += self.SINGLE_IMAGE_SLIDE.substitute(img_path = c_img_path, title = c_title,\
                                                          width = c_width, height = c_height)
        self.Deck += self.SLIDE_DIVIDER 

    def add_video_slide(self, c_vid_path, c_width="100%", c_height="100%"):
        self.Deck += self.VIDEO_SLIDE.substitute(vid_path = c_vid_path, width = c_width, height = c_height)
        self.Deck += self.SLIDE_DIVIDER
   
    def add_slidedeck_header(self,c_title="My Presentation"):
        self.Deck += self.SLIDEDECK_HEADER.substitute(title=c_title) 

    def add_header_text(self, text="This is a Header"):
        self.Deck += "# "+text

    def add_subheader_text(self, text="This is a subheader"):
        self.Deck += "## "+text

    def add_text(self, text="This is some Text"):
        self.Deck += text

    def _add_image_to_multi_image(self, c_src, c_width="50%", c_height="%50"):
        self.multi_imgs.append({"src":c_src,"width":c_width,"height":c_height})

    def add_slide_divider(self):
        self.Deck += self.SLIDE_DIVIDER

    def add_slidedeck_footer(self):
        self.Deck += ('''
# End Thread

-[Restart Thread:](#)

-[Exit Thread](/threads/)''')

    def _reset_multi_imgs(self):
        """
            To be used by add_multi_image_slide() to clear out
            all added images, after the slide has been created.

            otherwise these hang around and mess up any new slide being created.
        """
        self.multi_imgs = [] # will be an array of dicts with info about each image to be embedded.

    def add_multi_image_slide(self):
        """
            This one is less straight forward that others.
            To use it you have to first have use:
                ._add_image_to_multi_image() 

            This allows for having multi-image slides with N-number of images.

            once you have added all the images to the multi-image slide
            then you call this function and it will generate that slide section.
        """
        c_imgs = ""
        for multi_img in self.multi_imgs:
            c_imgs += self.IMG_SECTION.substitute(img_path = multi_img["src"], width = multi_img["width"],\
                                                    height = multi_img["height"])
        self.Deck += self.DIV_RSTACK.substitute(imgs = c_imgs)
        self.Deck += self.SLIDE_DIVIDER
        self._reset_multi_imgs()

def quote(s):
    """
    Properly escape strings for passing to the shell.
    """
    return "'" + s.replace("'", "'\\''") + "'"

def md5(filename, mode='rb'):
    """
    return the md5sum of a file
    """
    hasher = hashlib.md5()
    with open(filename, mode) as f:
        while True:
            data=f.read()
            if not data:
                break
            hasher.update(data)
    f.close()
    return hasher.hexdigest()

def natural_sort(s):
    ''' 
        To be used in conjunction with list sorting key
        to return the "natural" sort of a list. with normal 
        "list.sort()" the value "13" would come before "2".
        e.g.
        >>> a = list(["tweet_1", "tweet_2", "tweet_20", "tweet_100", "tweet_3"])
        >>> a
        ['tweet_1', 'tweet_2', 'tweet_20', 'tweet_100', 'tweet_3']
        >>> a.sort();a
        ['tweet_1', 'tweet_100', 'tweet_2', 'tweet_20', 'tweet_3']
        >>> a.sort(key=natural_sort)
        >>> a
        ['tweet_1', 'tweet_2', 'tweet_3', 'tweet_20', 'tweet_100']
        >>> 
    '''            
    return [int(text) if text.isdigit() else text.lower() for text in re.split(re.compile('([0-9]+)'), s)]

def get_full_tweet_text(tweet_raw_f="tweet_raw.txt"):
    '''
        Since the tweet_raw.txt contains only a single DIV, we just load it up
        in the parser which returns a single object for each element. So we just
        pop() off a single object and use its text_content() method to get EVERYTHING
        including the <br> newlines. text() method stops at unicode or newlines.

        root@e57c7a2ba2a6:/dev_share/DownloadingAllMyTwitterThreads/1801956963632193980/tweet_1# python
        Python 2.7.16 (default, Oct 10 2019, 22:02:15) 
        [GCC 8.3.0] on linux2
        Type "help", "copyright", "credits" or "license" for more information.
        >>> from lxml import html          
        >>> f_h = open('tweet_raw.txt','r')
        >>> f_c = f_h.read()
        >>> tree = html.fromstring(f_c)
        >>> tree.xpath('//div').pop().text_content()
        u'\nIsn\'t it weirdly coincidental how this anonymous amorphous group of "boots-on-the ground" activists coincides with the ideology of a nameless-nationless cabal of 19th, 20th, and 21st century "BIG THINKERS"?\n\nIt\'s probably just pure coincidence. \n\n\U0001f9f5Thread of examples \U0001f447: \n\n'
        >>> 

    '''
    f_h = open(tweet_raw_f,'r')
    f_c = f_h.read()
    f_h.close()
    tree = html.fromstring(f_c)
    e = tree.xpath('//div')
    return(e.pop().text_content().encode('utf-8'))

def dir_has_images(listdir):
    """
        This will check to see if the files listed in an os.listdir() array
        contain any files that have image extensions as defined by our global
        array of image extensions (IMGEXTS).

        if it does, it returns an array of just those files so a count of
        the number of images can be with len()

        if it doesnt, it returns false.
    """        
    imgfiles = []
    for f in listdir:
        for ext in IMGEXTS:
            if ext.lower() in f.lower(): # we lowercase them both just in case
                imgfiles.append(f)
            
    if len(imgfiles)==0:
        return False
    else:
        return imgfiles

def dir_has_video(listdir):
    """
        This will check to see if the directory listing has a video (m3u8) in it.
        
        If not then return False.
        If so, then return True.
    """
    vidfiles = []
    for f in listdir:
        if 'm3u8' in f: 
            vidfiles.append(f)
            
    if len(vidfiles)==0: 
        return False
    else:
        return vidfiles
        #return True 


def get_video(tweet_raw_f="tweet_raw.txt", vid_dl_file="/tmp/"+str(time.time()).replace(".","_")):
    """
        To be used in consort with dir_has_video().
    
        If a tweet directory has a video (m3u8) then we need
        to fetch the mp4 file that ThreadReaderApp resolves 
        from the twitter m3u8 and auto-embeds in the thread page.

    """
    f_h = open(tweet_raw_f,'r')
    f_c = f_h.read()
    f_h.close()
    tree = html.fromstring(f_c)
    e = tree.xpath('//source')
    vid_url=e[len(e)-1].get('src') # the highest rez mp4 URL is the last <source> URL in tweet_raw.txt
    print "Downloading video from: ", vid_url
    download_with_progressbar(vid_url, vid_dl_file) # just use time for a temp filename

def download_with_progressbar(url, filename):
    """
        Downloads using the request library and shows little progress indicator.
    """
    with open(filename, 'wb') as f:
        response = requests.get(url, stream=True)
        total = response.headers.get('content-length')

        if total is None:
            f.write(response.content)
        else:
            downloaded = 0
            total = int(total)
            for data in response.iter_content(chunk_size=max(int(total/1000), 1024*1024)):
                downloaded += len(data)
                f.write(data)
                done = int(50*downloaded/total)
                sys.stdout.write('\r[{}{}]'.format('>' * done, '.' * (50-done)))
                sys.stdout.flush()
    sys.stdout.write('\n')

def gen_posts(threads_dir):
    """
    Search for threadreader_downloader archived threads in a directory
    and if found, create a boilerplate functional markdown for each thread located.
    """
    print("\n******\nSTARTING Search for threadreader_downloader archives here:\n'%s'\n******" % threads_dir)
    print("\t[+] Changing working directory to: %s"%threads_dir)
    os.chdir(threads_dir)

#    for root, dirs, files in os.walk(threads_dir): # since os.walk() returns a generator which contains ALL the
                                       # subdirectories and subfiles RECURSIVELY as a "flat array",  
                                       # we use .next() to only give is the top-level directory
    for candidate in os.listdir(threads_dir):
        if os.path.isdir(os.path.join(threads_dir, candidate)):
            print ("[+] Checking '%s' for thread archive" % candidate)
            if "raw_threadreaderapp_response.txt" in os.listdir(os.path.join(threads_dir,candidate)):
                print("[+] Found Thread Archive in: '%s' !!!" % candidate)
                print("\t[+] Found these tweets in '%s' " % candidate)  
                deck = QuartoDeck()
                tmpvar = os.listdir(os.path.join(threads_dir,candidate)) # we have to stash in a tmp variable, to sort.
                tmpvar.sort(key=natural_sort) # our own custom sort function cuz list.sort() 
                                              # doesnt understand alphanumerics and sorts
                                              # them with "20" coming before "3"
                if not TESTRUN:
                    new_deck_outputdir = os.path.join(OUTPUT_DIR, candidate)
                    #os.mkdir(new_deck_outputdir)
                    new_deck_outputdir_assets = os.path.join(new_deck_outputdir,"assets")
                    #os.mkdir(new_deck_outputdir_assets)
               
                deck.add_slidedeck_header() 
                for possible_tweetdir in tmpvar:
                    #import pdb;pdb.set_trace()
                    possible_tweetdir_s = os.path.join(os.path.join(threads_dir,candidate), possible_tweetdir)
                    if os.path.isdir(possible_tweetdir_s):
#                        if "tweet.txt" in os.listdir(possible_tweetdir_s): # check if this directory contains a tweet
#                            print "\t\t", possible_tweetdir
                        if "tweet_raw.txt" in os.listdir(possible_tweetdir_s): # grab the tweet contents
                            print "\t\tGrabbing tweet from: ", possible_tweetdir_s
                            #print "=== TWEET TEXT ==="
                            tweet_text = get_full_tweet_text(os.path.join(possible_tweetdir_s, "tweet_raw.txt"))
                            print "\t\t\t Got tweet text."
                            print "\t\t=================="
                        imgs_present = dir_has_images(os.listdir(possible_tweetdir_s))
                        if imgs_present:
                            print "\t\tTweet Images: ", repr(imgs_present)
                            if len(imgs_present)==1:
                                deck.add_text(tweet_text)
                                deck.add_single_image_slide("./assets/"+imgs_present[0], "","50%","50%")
                            if (len(imgs_present)>1):
                                for img_file in imgs_present:
                                    deck._add_image_to_multi_image("./assets/"+img_file,"65%","65%") 
                                deck.add_text(tweet_text)
                                deck.add_multi_image_slide()
                            #now if we arent in a testrun, copy all the files to outputdir                                
                            if not TESTRUN:
                                for img_file in imgs_present:
                                    shutil.copy2(os.path.join(possible_tweetdir_s,img_file), new_deck_outputdir_assets)
                            # add slide separator:
                            deck.add_slide_divider()
                        elif dir_has_video(os.listdir(possible_tweetdir_s)):
                            for m3u8_vid in dir_has_video(os.listdir(possible_tweetdir_s)): # theres only ever one m3u8, so this is dumb
                                mp4_vid = m3u8_vid.replace("m3u8","mp4") # we'll borrow the m3u8 filename (sans .m3u8 extension)
                                                                         # to name our downloaded video file.
                            if not TESTRUN:
                                pass
                                #get_video(os.path.join(possible_tweetdir_s, "tweet_raw.txt"), \
                                #          os.path.join(new_deck_outputdir_assets, mp4_vid))
                            else: #use default download location which is a timestamp file in /tmp
                                pass
                                #get_video(os.path.join(possible_tweetdir_s, "tweet_raw.txt"))
                            deck.add_text(tweet_text)
                            deck.add_video_slide("./assets/"+mp4_vid) # slide divider added automatically so we dont need to
                        else: # there were no images or videos in the directory, so just do a text slide
                            deck.add_text(tweet_text)
                            deck.add_slide_divider()
                deck.add_slidedeck_footer()
                print "=============================="
                print "== QUARTODECK MARKDOWN FOR: =="
                print "===  ",candidate, "  ==="
                print "==       WILL LOOK LIKE:    =="
                print "=============================="
                print deck            
                print "=============================="
                if not TESTRUN:
                    f_h = open(os.path.join(new_deck_outputdir, "_index.qmd"),'w')
                    print "[+] Writing deck ", candidate," to ", os.path.join(new_deck_outputdir, "_index.qmd")
                    f_h.write(str(deck))
                    f_h.close
            else:
                print("\t[-] Directory '%s' isn't a Thread Archive ;-(" % candidate)
            

if __name__== "__main__":
    #ocrdir()
    import time
    CONFIG = ConfigParser.ConfigParser()
    print("[+] Reading config file: '%s' " % CONFIG_FNAME)
    try:
        CONFIG.read(CONFIG_FNAME)
    except:
        print("UNABLE TO READ CONFIGURATION FILE: '%s' " % CONFIG_FNAME)
        sys.exit(1)
    TESTRUN = CONFIG.getboolean('DEBUG','testrun')
    if TESTRUN:
        print("[+] Running in TESTRUN mode, outputting only, no actions will be taken.")
    OUTPUT_DIR = CONFIG.get("MAIN","output_dir")
    if not os.path.exists(OUTPUT_DIR):
        print("\n[+] OUTPUT Directory '%s' Doesnt already Exist, need to run threadreader_to_slideshow first!"%  OUTPUT_DIR)
        sys.exit(1)
    else:
        print("[+] Output Directory '%s' exists, will use that."%  OUTPUT_DIR)
        #print("[+] Output Directory '%s' does not exist."%  OUTPUT_DIR)
        # if not TESTRUN:
        #    print("[+] Creating our output directory: '%s' ", OUTPUT_DIR)
        #    os.mkdir(OUTPUT_DIR)
    gen_posts(threads_dir=CONFIG.get("MAIN",'threads_dir'))
