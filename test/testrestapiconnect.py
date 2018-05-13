import requests
import json

# application url
URL_LOCAL = 'http://127.0.0.1:8881'
URL_ONLINE = 'https://enkiws.appspot.com'

# default values
DEFAULT_URL = URL_LOCAL
DEFAULT_DISPLAYNAME = ''    # e.g. 'Silvia#2702'
DEFAULT_APP_ID = ''         # e.g. '5141470990303232'
DEFAULT_APP_SECRET = ''     # e.g. '0ZYWOlI71zDTRG7GhuLhmh14wxxXa9uCQDSfk9Y9Xq'

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


# parameters
url = DEFAULT_URL
displayname = DEFAULT_DISPLAYNAME
app_id = DEFAULT_APP_ID
app_secret = DEFAULT_APP_SECRET

# HandlerAPIv1Connect
code = ''
code = raw_input( '> Enter code (connection token, format: 5 alphanumeric characters): ' )
payload = { 'displayname' : displayname, 'code' : code, 'app_id' : app_id, 'app_secret' : app_secret }
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
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret }
get_response( ROUTE_VALIDATE, payload )

# HandlerAPIv1OwnsProducts
products = []
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret }
s = raw_input( "\n> Enter list of products to check (format comma separated, e.g. product_a, product_b, product_c. If left blank - press Enter - all activated products are returned.): " )
if s:
	products = map( str, s.split( ', ' ))
	payload.update({ 'products' : products })
get_response( ROUTE_PRODUCTS, payload )

# HandlerAPIv1Friends
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret }
get_response( ROUTE_FRIENDS, payload )

# HandlerAPIv1DataStoreSet
data_type = 'settings'
data_id = 's01p12'
data_payload = json.loads( '{ "colour":"blue", "size":"0.7", "calc_ip_addr" : "" }' )
time_expires = 3600
read_access = 'public'
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret, 'data_type' : data_type, 'data_id' : data_id, 'data_payload' : data_payload, 'time_expires' : time_expires, 'read_access' : read_access }
get_response( ROUTE_DATASTORESET, payload )

# HandlerAPIv1DataStoreGet
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret, 'data_type' : data_type, 'data_id' : data_id }
get_response( ROUTE_DATASTOREGET, payload )

# HandlerAPIv1DataStoreGetList
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret, 'data_type' : data_type, 'read_access': read_access }
get_response( ROUTE_DATASTOREGETLIST, payload )

# HandlerAPIv1DataStoreDel
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret, 'data_type' : data_type, 'data_id' : data_id }
get_response( ROUTE_DATASTOREDEL, payload )

# HandlerAPIv1Logout
payload = { 'user_id' : user_id, 'auth_token' : auth_token, 'app_secret' : app_secret }
get_response( ROUTE_LOGOUT, payload )
