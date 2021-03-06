import argparse
import os
import socket
import re
import requests
from bs4 import BeautifulSoup, NavigableString
from jinja2 import Environment, FileSystemLoader
from premailer import transform
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

QUERY = 'movies added:1d'

WHITELIST = re.compile(r'\s(720p|1080p)\s', re.IGNORECASE)
BLACKLIST = re.compile(r'\s(cam|hdcam|hindi|punjabi|telugu)\s', re.IGNORECASE)

# Scene keywords to try to identify the movie title
KEYWORDS = [r'brrip',
	r'dvdscr',
	r'dvdrip',
	r'dvd5',
	r'cam',
	r'hdcam',
	r'web\-?dl',
	r'unrated',
	r'extended',
	r'limited',
	r'x264',
	r'xvid',
	r'aac',
	r'ac3',
	r'dual audio',
	r'tc',
	r'hc',
	r'hevc',
	r'1CD',
	r'readnfo',
	r'[0-9]{3,4}p',
	r'[0-9]{3,}mb'
]
TITLE_FILTER = re.compile(r'\s(' + '|'.join(KEYWORDS) + ')\s', re.IGNORECASE)

# Setup the command line arguments management
parser = argparse.ArgumentParser(description=
	'Send a digest of new torrents from Torrentz.eu')
# Find user and hostname to create default from address
default_from = os.environ['LOGNAME'] + '@' + socket.gethostname()
# Add arguments
parser.add_argument('--from', dest='from_', default=default_from,
	help='''E-mail address from which the email originates.
	Defaults to: %s''' % (default_from,))
parser.add_argument('--to', required=True,
	help='E-mail address to which digest is sent')
parser.add_argument('--debug', action='store_true')
# Parse the arguments
args = parser.parse_args()
FROM_ADDRESS = args.from_
TO_ADDRESS = args.to
DEBUG = args.debug

# Setup Jinja2 templates
env = Environment(loader=FileSystemLoader('templates'))
plaintext = env.get_template('plaintext-email.txt')
html = env.get_template('html-email.html')

# Get the search results - hide under a fake Chrome user-agent
payload = {'f': QUERY}
headers = {'User-agent': 'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/36.0.1985.143 Safari/537.36'}
r = requests.get('http://torrentz2.eu/verified', params=payload, headers=headers)

# Parse the html page
soup = BeautifulSoup(r.text, 'lxml')

# Helper to get a string out of a tag even if it contains another tag
def merge_contents(tag):
	if type(tag) is NavigableString:
		return tag
	else:
		return ''.join(map(merge_contents, tag.contents))

# Find each result hit on the page and get the info
highlights = []
others = []
for hit in soup.select('.results dl'):
	try:
		attributes = hit.dd.find_all('span')
		torrent = {'name': hit.dt.a.string,
			'url': hit.dt.a.get('href'),
			'size': attributes[2].string,
			'seeds': attributes[3].string,
			'peers': attributes[4].string}
	except AttributeError:
		continue

	# Clean torrent name, removing scene formatting
	torrent['name'] = re.sub(r'\.|\[|\]|\(|\)', ' ', torrent['name'])

	# Identify title and tags from torrent name
	title = TITLE_FILTER.split(torrent['name'])[0]
	tags = torrent['name'][len(title) + 1:]

	torrent['title'] = title
	torrent['tags'] = tags

	# Categorize into highlights, others and trash
	if BLACKLIST.search(torrent['name']):
		pass
	elif WHITELIST.search(torrent['name']):
		highlights.append(torrent)
	else:
		others.append(torrent)

# Render templates
plain_email = plaintext.render(highlights=highlights, others=others)
html_email = transform(html.render(highlights=highlights, others=others))

# Prepare the email message
msg = MIMEMultipart('alternative')
msg['Subject'] = 'Torrentz Digest'
msg['From'] = FROM_ADDRESS
msg['To'] = TO_ADDRESS
msg.attach(MIMEText(plain_email, 'plain', 'utf-8'))
msg.attach(MIMEText(html_email, 'html', 'utf-8'))

if not DEBUG:
	# Send the message via local SMTP server
	s = smtplib.SMTP('localhost')
	s.sendmail(FROM_ADDRESS, TO_ADDRESS, msg.as_string())
	s.quit()
else:
	print(plain_email)
