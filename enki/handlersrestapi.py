import webapp2
import json

import enki
import enki.libuser
import enki.librestapi
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modeltokenverify import EnkiModelTokenVerify


class HandlerPageRestAPI( enki.HandlerBase ):

	def post( self ):
		# generate a new token (and delete old one if they exist)
		if self.ensure_is_logged_in() and self.ensure_has_display_name( self.request.referrer ):
			self.check_CSRF()
			user_id = self.enki_user.key.id()
			token = enki.librestapi.cleanup_and_get_new_connection_token( user_id )
			self.add_infomessage( 'success', MSG.SUCCESS(), MSG.GAME_CONNECTION_TOKEN( token ))
			self.redirect_to_relevant_page()


class HandlerPageAPIv1Connect( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		user_id = ''
		auth_token = ''
		if jsonobject:
			code = jsonobject.get( 'code', '')
			user_displayname = jsonobject.get( 'user_displayname', '')
			if code and user_displayname:
				entity = enki.librestapi.get_EnkiModelRestAPIConnectToken_by_token_prefix_valid_age( token = code, prefix = user_displayname)
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
		           'user_id' : user_id,
		           'auth_token' : auth_token
		           }
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class HandlerPageAPIv1AuthValidate( webapp2.RequestHandler ):

	def post( self ):
		jsonobject = json.loads( self.request.body )
		success = False
		error = 'Invalid request'
		if jsonobject:
			user_id = jsonobject.get( 'user_id', '')
			auth_token = jsonobject.get( 'auth_token', '')
			if user_id and auth_token:
				if enki.libuser.exist_VerifyToken_by_user_id_token( user_id, auth_token ):
					success = True
					error = ''
				else:
					error = 'Unauthorised'
		answer = { 'success' : success,
		           'error' : error
		           }
		self.response.headers[ 'Content-Type' ] = 'application/json'
		self.response.write( json.dumps( answer, separators=(',',':') ))


class ExtensionPageRestAPI( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'increstapi.html' )


class ExtensionRestAPI( Extension ):

	def get_routes( self ):
		return  [ webapp2.Route( '/restapi', HandlerPageRestAPI, name = 'restapi' ),
		          webapp2.Route( '/api/v1/connect', HandlerPageAPIv1Connect, name = 'apiv1connect' ),
		          webapp2.Route( '/api/v1/authvalidate', HandlerPageAPIv1AuthValidate, name = 'apiv1authvalidate' ),
				  ]

	def get_page_extensions( self ):
		return [ ExtensionPageRestAPI()]
