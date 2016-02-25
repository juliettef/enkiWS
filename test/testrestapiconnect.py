import requests
import json

print( 'TEST Rest API')

# set domain name url
# url_default = 'http://127.0.0.1:8881'   # local
url_default = 'https://enkisoftware-webservices.appspot.com'
url = ''
url = raw_input( ' - Enter url (domain name, press enter to use default url ' + url_default + '): ' )
if not url:
	url = url_default

# HandlerAPIv1Connect
print( '* Connection token' )
url_connect = url + '/api/v1/connect'
prefix = ''
code = ''
prefix = raw_input( " - Enter display name (format: alphanumeric prefix + '#' + 4 digits): " )
code = raw_input( ' - Enter code (connection token, format: 5 alphanumeric characters): ' )
payload = { 'user_displayname' : prefix, 'code' : code }
r_connect = requests.post( url_connect, json = payload )
print( ' => Response: ' + r_connect.text )

# HandlerAPIv1AuthValidate
print( '* Validate auth token' )
url_validate = url + '/api/v1/authvalidate'
r_connect_json = r_connect.json()
user_id = r_connect_json[ 'user_id' ]
auth_token = r_connect_json[ 'auth_token' ]
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
r_validate = requests.post( url_validate, json = payload )
print( ' => Response: ' + r_validate.text )

# HandlerAPIv1OwnsProducts
print( "* Validate auth token and list user's owned (activated) products" )
url_products = url + '/api/v1/ownsproducts'
products = []
s = raw_input( " - Enter list of products to check (format comma separated, e.g. product_a, product_b, product_c. If left blank - press Enter - all activated products are returned.): " )
if s:
	products = map( str, s.split( ', ' ))
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'products' : products }
r_products = requests.post( url_products, json = payload )
print( ' => Response: ' + r_products.text )

# HandlerAPIv1Logout
print( '* Logout, delete auth token' )
url_logout = url + '/api/v1/logout'
user_id = r_connect_json[ 'user_id' ]
auth_token = r_connect_json[ 'auth_token' ]
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
r_validate = requests.post( url_logout, json = payload )
print( ' => Response: ' + r_validate.text )
