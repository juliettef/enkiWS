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
print( ' => Response:\n' + r_connect.text + '\n' )

# HandlerAPIv1AuthValidate
print( '* Validate auth token' )
url_validate = url + '/api/v1/authvalidate'
r_connect_json = r_connect.json()
user_id = r_connect_json[ 'user_id' ]
auth_token = r_connect_json[ 'auth_token' ]
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
r_validate = requests.post( url_validate, json = payload )
print( ' => Response:\n' + r_validate.text + '\n' )

# HandlerAPIv1OwnsProducts
print( "* Validate auth token and list user's owned (activated) products" )
url_products = url + '/api/v1/ownsproducts'
products = []
s = raw_input( " - Enter list of products to check (format comma separated, e.g. product_a, product_b, product_c. If left blank - press Enter - all activated products are returned.): " )
if s:
	products = map( str, s.split( ', ' ))
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'products' : products }
r_products = requests.post( url_products, json = payload )
print( ' => Response:\n' + r_products.text + '\n' )

# HandlerAPIv1Friends
print( '* Friends' )
url_friends = url + '/api/v1/friends'
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
r_friends = requests.post( url_friends, json = payload )
print( ' => Response:\n' + r_friends.text + '\n' )

# HandlerAPIv1DataStoreSet
print( '* Data Store set - add new' )
url_datastoreset = url + '/api/v1/datastore/set'
data_type = 'appearance'
data_json = json.loads( '{"colour":"blue", "shape":"cube", "size":"0.7"}' )
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'data_type' : data_type, 'data_json' : data_json }
r_datastoreset = requests.post( url_datastoreset, json = payload )
print( ' => Response:\n' + r_datastoreset.text + '\n' )

# HandlerAPIv1DataStoreGet
print( '* Data Store get' )
url_datastoreget = url + '/api/v1/datastore/get'
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'data_type' : data_type }
r_datastoreget = requests.post( url_datastoreget, json = payload )
print( ' => Response:\n' + r_datastoreget.text + '\n' )

# HandlerAPIv1DataStoreDel
print( '* Data Store delete' )
url_datastoredel = url + '/api/v1/datastore/del'
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'data_type' : data_type }
r_datastoredel = requests.post( url_datastoredel, json = payload )
print( ' => Response:\n' + r_datastoredel.text + '\n' )

# HandlerAPIv1Logout
print( '* Logout, delete auth token' )
url_logout = url + '/api/v1/logout'
user_id = r_connect_json[ 'user_id' ]
auth_token = r_connect_json[ 'auth_token' ]
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
r_validate = requests.post( url_logout, json = payload )
print( ' => Response:\n' + r_validate.text + '\n' )
