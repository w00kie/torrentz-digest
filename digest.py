import requests
from bs4 import BeautifulSoup
import re

QUERY = 'movies added:1d'

WHITELIST = ['720p', '1080p']
BLACKLIST = ['cam', 'hdcam']

# Scene keywords to try to identify the movie title
KEYWORDS = [
	'brrip',
	'x264',
	'dvdscr',
	'dual audio',
	'hevc',
	'[0-9]{3,4}p',
	'[0-9]{3,}mb'
]

# Get the search results
payload = {'f':QUERY}
r = requests.get('http://torrentz.eu/verified', params=payload)

# Parse the html page
soup = BeautifulSoup(r.text)

# Find each result hit on the page and get the info
for hit in soup.select('.results dl'):
	name = hit.dt.a.string
	url = 'http://torrentz.eu/' + hit.dt.a.get('href')
	size = hit.find('span', class_='s').string
	seeds = hit.find('span', class_='u').string
	peers = hit.find('span', class_='d').string

	print(name, url, size, seeds, peers)
