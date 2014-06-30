import re
import requests
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from premailer import transform

QUERY = 'movies added:1d'

WHITELIST = re.compile('\s(720p|1080p)\s', re.IGNORECASE)
BLACKLIST = re.compile('\s(cam|hdcam|hindi|punjabi|telugu)\s', re.IGNORECASE)

# Scene keywords to try to identify the movie title
KEYWORDS = ['brrip',
	'dvdscr',
	'dvdrip',
	'dvd5',
	'cam',
	'hdcam',
	'x264',
	'aac',
	'ac3',
	'dual audio',
	'hindi',
	'hevc',
	'1CD',
	'readnfo',
	'[0-9]{3,4}p',
	'[0-9]{3,}mb']
TITLE_FILTER = re.compile('\s(' + '|'.join(KEYWORDS) + ')\s', re.IGNORECASE)

# Setup Jinja2 templates
env = Environment(loader=FileSystemLoader('templates'))
plaintext = env.get_template('plaintext-email.txt')
html = env.get_template('html-email.html')

# Get the search results
payload = {'f': QUERY}
r = requests.get('http://torrentz.eu/verified', params=payload)

# Parse the html page
soup = BeautifulSoup(r.text)

# Find each result hit on the page and get the info
highlights = []
others = []
for hit in soup.select('.results dl'):
	torrent = {'name': hit.dt.a.string,
		'url': hit.dt.a.get('href'),
		'size': hit.find('span', class_='s').string,
		'seeds': hit.find('span', class_='u').string,
		'peers': hit.find('span', class_='d').string}

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

plain_email = plaintext.render(highlights=highlights, others=others)
html_email = transform(html.render(highlights=highlights, others=others))

print(html_email)
