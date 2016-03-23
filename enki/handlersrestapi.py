import datetime, time
import webapp2
import json

from google.appengine.ext import ndb

import enki
import enki.libuser
import enki.libdisplayname
import enki.libfriends
import enki.libstore
import enki.librestapi
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modelrestapitokenverify import EnkiModelRestAPITokenVerify
from enki.modelrestapidatastore import EnkiModelRestAPIDataStore


class HandlerPageRestAPI( enki.HandlerBase ):

	def post( self ):
		# generate a new token (and delete old one if they exist)
		if self.ensure_is_logged_in() and self.ensure_has_display_name( self.request.referrer ):
			self.check_CSRF()
			user_id = self.enki_user.key.id()
			token = enki.librestapi.cleanup_and_get_new_connection_token( user_id )
			self.add_infomessage( 'success', MSG.SUCCESS(), MSG.GAME_CONNECTION_TOKEN( token, enki.librestapi.MAX_AGE ))
			self.redirect_to_relevant_page()


class HandlerAPIv1Connect( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			code = jsonobject.get( 'code', '')
			displayname = jsonobject.get( 'displayname', '')
			app_id = jsonobject.get( 'app_id', '')
			if code and displayname and app_id:
				user_id = enki.libdisplayname.get_user_id_from_display_name( displayname )
				if user_id:
					entity = enki.librestapi.get_EnkiModelRestAPIConnectToken_by_token_user_id_valid_age( token = code, user_id = user_id )
					if entity:
						auth_token = enki.librestapi.generate_auth_token()
						entity.key.delete()     # single use token
						verification_token = EnkiModelRestAPITokenVerify( token = auth_token, user_id = user_id, app_id = app_id, type = 'apiconnect' )
						verification_token.put()    # persistent authentication token, a user may have several
						answer.update({ 'user_id' : str( user_id ), 'auth_token' : auth_token })
						success = True
						error = ''
					else:
						error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1Logout( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			if user_id and auth_token:
				if EnkiModelRestAPITokenVerify.delete_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1AuthValidate( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			if user_id and auth_token:
				if EnkiModelRestAPITokenVerify.exist_by_user_id_token( user_id, auth_token ):
					user_displayname = enki.libdisplayname.get_display_name( user_id )
					if user_displayname:
						answer.update({ 'user_displayname' : user_displayname })
						success = True
						error = ''
					else:
						error = 'Not found'
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1OwnsProducts( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			products = jsonobject.get( 'products', '')
			if user_id and auth_token:
				if EnkiModelRestAPITokenVerify.exist_by_user_id_token( user_id, auth_token ):
					if products:   # check which products in the list are activated by the user and return them
						list_entities = enki.libstore.fetch_EnkiProductKey_by_activator_products_list( user_id, products )
					else:    # no product specified, return all products activated by the user
						list_entities = enki.libstore.fetch_EnkiProductKey_by_activator( user_id )
					if list_entities:
						list_products = []
						for i, item in enumerate( list_entities ):
							list_products.append( item.product_name )
						answer.update({ 'products_owned' : list_products })
						success = True
						error = ''
					else:
						error = 'Not found'
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1Friends( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			if user_id and auth_token:
				if EnkiModelRestAPITokenVerify.exist_by_user_id_token( user_id, auth_token ):
					friends = enki.libfriends.get_friends_user_id_display_name( user_id )
					if friends:
						answer.update({ 'friends' : friends })
						success = True
						error = ''
					else:
						error = 'Not found'
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1DataStoreSet( webapp2.RequestHandler ):
# data identified by the combination of user_id (app_id) & data_type
	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			data_type = jsonobject.get( 'data_type', '')
			data_id = jsonobject.get( 'data_id', '')
			data_payload = jsonobject.get( 'data_payload' )
			# set the expiry time
			time_to_expiry = int(jsonobject.get( 'time_expires', enki.librestapi.DATASTORE_EXPIRY_DEFAULT ))  # default lifetime if unspecified: 24h
			if time_to_expiry == 0: # non-expiring lifetime
				time_to_expiry = enki.librestapi.DATASTORE_NON_EXPIRING   # 100 years
			time_expires = datetime.datetime.now() + datetime.timedelta( seconds = time_to_expiry )
			read_access = jsonobject.get( 'read_access', '' )
			if user_id and auth_token and data_type and data_id and data_payload and time_expires:
				token_valid = EnkiModelRestAPITokenVerify.get_by_user_id_token( user_id, auth_token )
				if token_valid:   # user is valid
					# add optional calculated properties to the data payload
					if 'calc_ip_addr' in data_payload:    # IP address of the request
						remote_address = self.request.remote_addr
						data_payload.update({ 'calc_ip_addr' : remote_address })
					data_store = enki.librestapi.get_EnkiModelRestAPIDataStore_by_user_id_app_id_data_type_data_id( user_id, token_valid.app_id, data_type, data_id )
					if data_store:  # update
						data_store.data_payload = data_payload
						data_store.time_expires = time_expires  # update the expiry time
						if read_access: # if read_access is not specified, don't update it
							data_store.read_access = read_access
					else:   # create new
						if not read_access: # if read_access is not specified, use the default value defined in the model
							data_store = EnkiModelRestAPIDataStore( user_id = user_id, app_id = token_valid.app_id, data_type = data_type, data_id = data_id, data_payload = data_payload, time_expires = time_expires )
						else:
							data_store = EnkiModelRestAPIDataStore( user_id = user_id, app_id = token_valid.app_id, data_type = data_type, data_id = data_id, data_payload = data_payload, time_expires = time_expires, read_access = read_access )
					data_store.put()
					success = True
					error = ''
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1DataStoreGet( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			data_type = jsonobject.get( 'data_type', '')
			data_id = jsonobject.get( 'data_id', '')
			if user_id and auth_token and data_type and data_id:
				token_valid = EnkiModelRestAPITokenVerify.get_by_user_id_token( user_id, auth_token )
				if token_valid:   # user is valid
					data_store_item = enki.librestapi.get_EnkiModelRestAPIDataStore_by_user_id_app_id_data_type_data_id_not_expired( user_id, token_valid.app_id, data_type, data_id )
					if data_store_item:
						answer.update({ 'data_payload' : data_store_item.data_payload, 'time_expires' : enki.librestapi.seconds_from_epoch( data_store_item.time_expires ) , 'read_access' : data_store_item.read_access, 'server_time' : int( time.time())})
						success = True
						error = ''
					else:
						error = 'Not found'
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1DataStoreGetList( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', '' ))
			auth_token = jsonobject.get( 'auth_token', '' )
			data_type = jsonobject.get( 'data_type', '' )
			read_access = jsonobject.get( 'read_access', '' )
			if user_id and auth_token and data_type and ( read_access == 'public' or read_access == 'private' or read_access == 'friends' ):
				token_valid = EnkiModelRestAPITokenVerify.get_by_user_id_token( user_id, auth_token )
				if token_valid:   # user is valid
					error = 'Not found'
					data_store_list = []
					if read_access == 'public':   # returns all data with read-access "public"
						data_store_list = enki.librestapi.fetch_EnkiModelRestAPIDataStore_by_app_id_data_type_read_access_not_expired( token_valid.app_id, data_type, read_access )
					else:
						people_list = []
						if read_access == 'private':    # returns all user's data with read-access "private"
							people_list = [ user_id ]
						elif read_access == 'friends':    # returns list of user's friends' data with friends' read_access "friends"
							people_list = enki.libfriends.get_friends_user_id( user_id )    # get the user's friends' ids
						if people_list:
							for person_id in people_list:   # get each persons' data
								data_store_list = enki.librestapi.fetch_EnkiModelRestAPIDataStore_by_user_id_app_id_data_type_read_access_not_expired( person_id, token_valid.app_id, data_type, read_access )
					if data_store_list:
						data_payloads = []
						for data_store_item in data_store_list:
							data_payloads.append({ 'user_id' : str( data_store_item.user_id ), 'data_id' : data_store_item.data_id, 'data_payload' : data_store_item.data_payload, 'time_expires' : enki.librestapi.seconds_from_epoch( data_store_item.time_expires )})
						if data_payloads:
							answer.update({ 'data_payloads' : data_payloads, 'server_time' : int( time.time())})
							success = True
							error = ''
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1DataStoreDel( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		answer = {}
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			data_type = jsonobject.get( 'data_type', '')
			data_id = jsonobject.get( 'data_id', '')
			if user_id and auth_token and data_type and data_id:
				token_valid = EnkiModelRestAPITokenVerify.get_by_user_id_token( user_id, auth_token )
				if token_valid:   # user is valid
					data_stores = enki.librestapi.fetch_EnkiModelRestAPIDataStore_by_user_id_app_id_data_type_data_id( user_id, token_valid.app_id, data_type, data_id )
					ndb.delete_multi( data_stores )
					success = True
					error = ''
				else:
					error = 'Unauthorised'
		answer.update({ 'success' : success, 'error' : error })
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class ExtensionPageRestAPI( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'increstapi.html' )


class ExtensionRestAPI( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/restapi', HandlerPageRestAPI, name = 'restapi' ),
		          webapp2.Route( '/api/v1/connect', HandlerAPIv1Connect, name = 'apiv1connect' ),
		          webapp2.Route( '/api/v1/logout', HandlerAPIv1Logout, name = 'apiv1logout' ),
		          webapp2.Route( '/api/v1/authvalidate', HandlerAPIv1AuthValidate, name = 'apiv1authvalidate' ),
		          webapp2.Route( '/api/v1/ownsproducts', HandlerAPIv1OwnsProducts, name = 'apiv1ownsproducts' ),
		          webapp2.Route( '/api/v1/friends', HandlerAPIv1Friends, name = 'apiv1friends' ),
		          webapp2.Route( '/api/v1/datastore/set', HandlerAPIv1DataStoreSet, name = 'apiv1datastoreset' ),
		          webapp2.Route( '/api/v1/datastore/get', HandlerAPIv1DataStoreGet, name = 'apiv1datastoreget' ),
		          webapp2.Route( '/api/v1/datastore/getlist', HandlerAPIv1DataStoreGetList, name = 'apiv1datastoregetlist' ),
		          webapp2.Route( '/api/v1/datastore/del', HandlerAPIv1DataStoreDel, name = 'apiv1datastoredel' ),
				  ]

	def get_page_extensions( self ):
		return [ ExtensionPageRestAPI()]
