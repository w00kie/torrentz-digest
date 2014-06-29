import requests
from bs4 import BeautifulSoup
import re

WHITELIST = ['720p', '1080p']
BLACKLIST = ['cam', 'hdcam']

payload = {'f':'movies added:1d'}
r = requests.get('http://torrentz.eu/verified', params=payload)

soup = BeautifulSoup(r.text)

for hit in soup.select('.results dl'):
	name = hit.dt.a.string
	url = 'http://torrentz.eu/' + hit.dt.a.get('href')
	size = hit.find('span', class_='s').string
	seeds = hit.find('span', class_='u').string
	peers = hit.find('span', class_='d').string

	print(name, url, size, seeds, peers)
