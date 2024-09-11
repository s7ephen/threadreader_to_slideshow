#!/usr/bin/env python2
# 
# The purpose of this tool is to take a tweet URL as a commandline argument and output the twitter embed code
#
# root@74335c43cccd:/tmp# ./fetch_twitter_embed.py https://twitter.com/s7ephen/status/1780992685891015142
#   ------------------------------
#   Fetching Embed Code from:
#   https://publish.twitter.com/oembed?url=https://twitter.com/s7ephen/status/1780992685891015142&hideConversation=on&partner=&hide_thread=true
#   ------------------------------
#   {
#       "provider_url": "https://twitter.com", 
#       "version": "1.0", 
#       "url": "https://twitter.com/s7ephen/status/1780992685891015142", 
#       "author_name": "Stephen A. Ridley", 
#       "height": null, 
#       "width": 550, 
#       "html": "<blockquote class=\"twitter-tweet\"><p lang=\"en\" dir=\"ltr\">The Swastika, the &quot;Star of David&quot;, and the Iron Cross (which is actually also emblazoned on the British Crown along with the Fleur De Lys if you look closely)......<br><br>HOW DID HE KNOW back in 1878 that these symbols would be so pivotal in the coming century? \ud83e\udd14 <a href=\"https://t.co/PFGwSconai\">https://t.co/PFGwSconai</a></p>&mdash; Stephen A. Ridley (@s7ephen) <a href=\"https://twitter.com/s7ephen/status/1780992685891015142?ref_src=twsrc%5Etfw\">April 18, 2024</a></blockquote>\n<script async src=\"https://platform.twitter.com/widgets.js\" charset=\"utf-8\"></script>\n\n", 
#       "author_url": "https://twitter.com/s7ephen", 
#       "provider_name": "Twitter", 
#       "cache_age": "3153600000", 
#       "type": "rich"
#   }
#   ------------------------------
#      The Embed code is below:   
#   ------------------------------
#   <blockquote class="twitter-tweet"><p lang="en" dir="ltr">The Swastika, the &quot;Star of David&quot;, and the Iron Cross (which is actually also emblazoned on the British Crown along with the Fleur De Lys if you look closely)......<br><br>HOW DID HE KNOW back in 1878 that these symbols would be so pivotal in the coming century? <a href="https://t.co/PFGwSconai">https://t.co/PFGwSconai</a></p>&mdash; Stephen A. Ridley (@s7ephen) <a href="https://twitter.com/s7ephen/status/1780992685891015142?ref_src=twsrc%5Etfw">April 18, 2024</a></blockquote>
#   <script async src="https://platform.twitter.com/widgets.js" charset="utf-8"></script>
#   
#   
#   root@74335c43cccd:/tmp#
#
#
#
import requests
import json
import sys

if len(sys.argv) <= 1:
    print("\nUSAGE:\n'%s' <tweet_url>\n\n\tExample:\n\t%s https://twitter.com/s7ephen/status/1780992685891015142\n" % (sys.argv[0],sys.argv[0]))
    sys.exit(1)
tweet = sys.argv[1]
url = '''https://publish.twitter.com/oembed?url=%s&hideConversation=on&partner=&hide_thread=true''' % sys.argv[1]
print "------------------------------"
print "Fetching Embed Code from:\n",url
print "------------------------------"
response  = requests.get(url)
parsed = json.loads(response.content)
print(json.dumps(parsed, indent=4))
print "------------------------------"
print "   The Embed code is below:   "
print "------------------------------"
#import pdb;pdb.set_trace()
html = parsed.get("html")
print html.encode('utf-8')
