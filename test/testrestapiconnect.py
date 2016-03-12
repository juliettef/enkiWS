import requests
import json

# application url
URL_LOCAL = 'http://127.0.0.1:8881'
URL_ONLINE = 'https://enkisoftware-webservices.appspot.com'

# default values
URL_DEFAULT = URL_LOCAL
DISPLAYNAME_DEFAULT = ''

# routes
ROUTE_CONNECT = '/api/v1/connect'
ROUTE_LOGOUT = '/api/v1/logout'
ROUTE_VALIDATE = '/api/v1/authvalidate'
ROUTE_PRODUCTS = '/api/v1/ownsproducts'
ROUTE_FRIENDS = '/api/v1/friends'
ROUTE_DATASTORESET = '/api/v1/datastore/set'
ROUTE_DATASTOREGET = '/api/v1/datastore/get'
ROUTE_DATASTOREGETLIST = '/api/v1/datastore/getlist'
ROUTE_DATASTOREDEL = '/api/v1/datastore/del'


def get_response( route, payload ):
	url_route = url + route
	response = requests.post( url_route, json = payload )
	print( '\n> ' + route )
	print( response.text + '\n' )
	return response


# set domain name url
url = ''
url = raw_input( '> Enter url (domain name, press enter to use default url ' + URL_DEFAULT + '): ' )
if not url:
	url = URL_DEFAULT

# HandlerAPIv1Connect
displayname = ''
msg_default = ''
if DISPLAYNAME_DEFAULT:
	msg_default = ", press enter to use default display name " + DISPLAYNAME_DEFAULT
displayname = raw_input( "> Enter display name (format: alphanumeric prefix + '#' + 4 digits" + msg_default + "): " )
if not displayname:
	displayname = DISPLAYNAME_DEFAULT
code = ''
code = raw_input( '> Enter code (connection token, format: 5 alphanumeric characters): ' )
payload = { 'user_displayname' : displayname, 'code' : code }
r_connect = get_response( ROUTE_CONNECT, payload )

# get user_id and auth_token from connect response
r_connect_json = r_connect.json()
if r_connect_json[ 'success' ]:
	user_id = r_connect_json[ 'user_id' ]
	auth_token = r_connect_json[ 'auth_token' ]
else:
	print( 'Abort test: missing user_id and/or auth_token' )
	exit()

# HandlerAPIv1AuthValidate
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
get_response( ROUTE_VALIDATE, payload )

# HandlerAPIv1OwnsProducts
products = []
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
s = raw_input( "\n> Enter list of products to check (format comma separated, e.g. product_a, product_b, product_c. If left blank - press Enter - all activated products are returned.): " )
if s:
	products = map( str, s.split( ', ' ))
	payload.update({ 'products' : products })
get_response( ROUTE_PRODUCTS, payload )

# HandlerAPIv1Friends
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
get_response( ROUTE_FRIENDS, payload )

# HandlerAPIv1DataStoreSet
app_id = 'product_a'
data_key = 'settings'
data_payload = json.loads( '{ "colour":"blue", "shape":"cube", "size":"0.7", "ip_addr_verified" : "" }' )
read_access = 'public'
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_id' : app_id, 'data_key' : data_key, 'data_payload' : data_payload, 'read_access' : read_access }
get_response( ROUTE_DATASTORESET, payload )

# HandlerAPIv1DataStoreGet
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_id' : app_id, 'data_key' : data_key }
get_response( ROUTE_DATASTOREGET, payload )

# HandlerAPIv1DataStoreGetList
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_id' : app_id, 'data_key' : data_key, 'read_access': read_access }
get_response( ROUTE_DATASTOREGETLIST, payload )

# HandlerAPIv1DataStoreDel
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_id' : app_id, 'data_key' : data_key }
get_response( ROUTE_DATASTOREDEL, payload )

# HandlerAPIv1Logout
payload = { 'user_id' : user_id, 'auth_token' : auth_token }
get_response( ROUTE_LOGOUT, payload )
