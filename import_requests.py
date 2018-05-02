import requests

count  = 0

while count < 1000:
	print count
	response = requests.get('http://bit.ly/mapathon2018')
	count += 1
	