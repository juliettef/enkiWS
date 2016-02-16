import requests

print( 'TEST - Rest API')

# set domain name url
url_default = 'http://127.0.0.1:8881'   # local
# url_default = 'https://enkisoftware-webservices.appspot.com'
url = ''
url = raw_input( 'url (domain name, press enter to use default url ' + url_default + '): ' )
if not url:
	url = url_default

# HandlerPageAPIv1Connect
print( 'STEP 1 - Connection token' )
url_connect = url + '/api/v1/connect'
prefix = ''
code = ''
prefix = raw_input( 'Enter prefix (display name without the # and suffix numbers): ' )
code = raw_input( 'Enter code (connection token, 5 alphanumeric characters): ' )
payload = { 'user_displayname' : prefix, 'code' : code }
r_connect = requests.post( url_connect, json = payload )
print( 'Response: ' )
print( r_connect.text )

# HandlerPageAPIv1AuthValidate
print( 'STEP 2 - Validate auth token' )
url_validate = url + '/api/v1/authvalidate'
r_connect = r_connect.json()
user_id = r_connect[ 'user_id' ]
auth_token = r_connect[ 'auth_token' ]
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
r_validate = requests.post( url_validate, json = payload )
print( 'Response: ')
print r_validate.text
