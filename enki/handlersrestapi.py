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
from enki.modeltokenverify import EnkiModelTokenVerify
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
		user_id = ''
		auth_token = ''
		if jsonobject:
			code = jsonobject.get( 'code', '')
			user_displayname = jsonobject.get( 'user_displayname', '')
			user_id = enki.libdisplayname.get_user_id_from_display_name( user_displayname )
			if code and user_displayname:
				entity = enki.librestapi.get_EnkiModelRestAPIConnectToken_by_token_user_id_valid_age( token = code, user_id = user_id )
				if entity:
					success = True
					error = ''
					user_id = entity.user_id
					auth_token = enki.librestapi.generate_auth_token()
					entity.key.delete()     # single use token
					verification_token = EnkiModelTokenVerify( token = auth_token, user_id = user_id, type = 'apiconnect' )
					verification_token.put()    # persistent authentication token, a user may have several
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
		           'user_id' : str( user_id ),
		           'auth_token' : auth_token
		           }
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1Logout( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			if user_id and auth_token:
				if EnkiModelTokenVerify.delete_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
					}
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1AuthValidate( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		user_displayname = ''
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			if user_id and auth_token:
				if EnkiModelTokenVerify.exist_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
					user_displayname = enki.libdisplayname.get_display_name( user_id )
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
		           'user_displayname' : user_displayname,
					}
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1OwnsProducts( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		list_products = []
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			products = jsonobject.get( 'products', '')
			if user_id and auth_token:
				if EnkiModelTokenVerify.exist_by_user_id_token( user_id, auth_token ):
					if products:   # check which products in the list are activated by the user and return them
						list_entities = enki.libstore.fetch_EnkiProductKey_by_activator_products_list( user_id, products )
					else:    # no product specified, return all products activated by the user
						list_entities = enki.libstore.fetch_EnkiProductKey_by_activator( user_id )
					for i, item in enumerate( list_entities ):
						list_products.append( item.product_name )
					success = True
					error = ''
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
		           'products_owned' : list_products,
		           }
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1Friends( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		friends = []
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			if user_id and auth_token:
				if EnkiModelTokenVerify.exist_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
					friends = enki.libfriends.get_friends_user_id_display_name( user_id )
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
		           'friends' : friends,
		           }
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1DataStoreSet( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			app_id = jsonobject.get( 'app_id', '')
			data_key = jsonobject.get( 'data_key', '')
			data_payload = jsonobject.get( 'data_payload' )
			if user_id and auth_token and data_payload:
				if EnkiModelTokenVerify.exist_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
					data_store = enki.librestapi.get_EnkiModelRestAPIDataStore_by_user_id_app_id_data_key( user_id, app_id, data_key )
					if data_store:  # update
						data_store.data_payload = data_payload
					else:   # create new
						data_store = EnkiModelRestAPIDataStore( user_id = user_id, app_id = app_id, data_key = data_key, data_payload = data_payload )
					data_store.put()
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
		           }
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1DataStoreGet( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			app_id = jsonobject.get( 'app_id', '')
			data_key = jsonobject.get( 'data_key', '')
			if user_id and auth_token:
				if EnkiModelTokenVerify.exist_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
					data_payload = enki.librestapi.get_EnkiModelRestAPIDataStore_by_user_id_app_id_data_key( user_id, app_id, data_key ).data_payload
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
		           'data_payload' : data_payload
		           }
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerAPIv1DataStoreDel( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		if jsonobject:
			user_id = int( jsonobject.get( 'user_id', ''))
			auth_token = jsonobject.get( 'auth_token', '')
			app_id = jsonobject.get( 'app_id', '')
			data_key = jsonobject.get( 'data_key', '')
			if user_id and auth_token:
				if EnkiModelTokenVerify.exist_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
					data_stores = enki.librestapi.fetch_EnkiModelRestAPIDataStore_by_user_id_app_id_data_key( user_id, app_id, data_key )
					ndb.delete_multi( data_stores )
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error,
		           }
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
		          webapp2.Route( '/api/v1/datastore/del', HandlerAPIv1DataStoreDel, name = 'apiv1datastoredel' ),
				  ]

	def get_page_extensions( self ):
		return [ ExtensionPageRestAPI()]
