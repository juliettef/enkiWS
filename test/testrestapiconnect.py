import requests

url = ''
prefix = ''
code = ''
url = raw_input( 'url (domain name):\n' )
prefix = raw_input( 'prefix (display name without the # and suffix numbers):\n' )
code = raw_input( 'code (connection token, 5 alphanumeric characters):\n' )

if not url:
	url = 'http://127.0.0.1:8881'   # local
	# url = 'https://enkisoftware-webservices.appspot.com'
url += '/api/v1/connect'

payload = { 'user_displayname' : prefix, 'code' : code }
r = requests.post( url, json = payload )

print r.text
