# https://developers.google.com/accounts/docs/OpenIDConnect
import time
import hmac
import hashlib
import webapp2
import webapp2_extras
import webapp2_extras.security
import base64
import json
import collections
import urllib
import urlparse
from google.appengine.api import urlfetch

import settings
import enki
import enki.libutil
import enki.textmessages as MSG


button = collections.namedtuple( 'button', 'href, icon' )


class HandlerOAuthBase( enki.HandlerBase ):

	def auth_callback( self ):
		self.auth_check_CSRF()
		# set referral
		ref_d = self.session.get( 'sessionrefpath', self.request.referrer )
		ref = self.session.get( 'sessionloginrefpath', ref_d )
		if not ref:
			ref = enki.libutil.get_local_url( ) # home
		self.session[ 'sessionloginrefpath' ] = ref
		self.auth_callback_provider()

	def process_login_info( self, loginInfoSettings, result ):
		loginInfo = {}
		for key in loginInfoSettings:
			if loginInfoSettings[ key ] in result:
				loginInfo.update({ key: result[ loginInfoSettings[ key ]]})
			else:
				loginInfo.update({ key: ''})
		loginInfo.update({ 'provider_name': self.get_provider_name()})
		return loginInfo

	def auth_check_CSRF( self ):
		self.check_CSRF( 'state' )

	def process_result_as_JSON( self, result ):
		return json.loads( result.content )

	def process_result_as_query_string( self, result ):
		return dict( urlparse.parse_qsl( result.content ))

	def urlfetch_safe(self, *args, **kwargs ):
		haveError = False
		try:
			result = urlfetch.fetch( *args, **kwargs )
			if result.status_code != 200:
				haveError = True
		except:
			haveError = True

		if haveError:
			self.add_infomessage( MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
			self.redirect_to_relevant_page( True )
		return result

	@classmethod
	def get_provider_name_obfuscated( self ):
		return self.get_provider_name()[:3].lower()


class HandlerOAuthOAUTH2( HandlerOAuthBase ):

	def auth_request( self ):    # let the user authenticate themselves with the 3rd party provider
		params = { 'client_id': self.get_auth_request_client_id(),
					'response_type': 'code',
					'scope': self.get_scope(),
					'state': self.create_CSRF( 'oauth' ),
					'redirect_uri': self.domain_name[ :-1 ] + self.get_auth_callback(),
				   }
		params.update( self.get_optional_params( ) )
		urlParams = enki.libutil.urlencode( params )
		fullURL = str( self.auth_endpoint() + '?' + urlParams )  # note: casting to string so works online with permissions restricted to Admin (app.yaml) as this was generating a unicode error
		self.redirect( fullURL )

	def get_optional_params( self ): # override this to add your own parameters to auth_request, e.g. "return { 'favourite_animal': 'cat' }"
		return {}

	def auth_callback_provider( self ):
		params = { 'code': self.request.get( 'code' ),
				   'client_id': self.get_auth_request_client_id(),
				   'client_secret': self.get_client_secret(),
				   'redirect_uri': self.domain_name[ :-1 ] + self.get_auth_callback(),
				   'grant_type': 'authorization_code',
				   }
		urlParams = enki.libutil.urlencode( params )
		url = self.token_endpoint()

		result = self.urlfetch_safe( url = url,
									 payload = urlParams,
									 method = urlfetch.POST,
									 headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
									)

		self.process_token_result( result )

	def get_profile( self, token, params = {} ):
		params.update( { 'access_token': token } )
		fullUrl = self.profile_endpoint() + '?' + enki.libutil.urlencode( params )
		profile = self.urlfetch_safe( url = fullUrl )
		return profile


class HandlerOAuthOpenIDConnect( HandlerOAuthOAUTH2 ):

	@webapp2.cached_property
	def discovery_doc( self ):
		url = self.get_discovery_URL()
		result = self.urlfetch_safe( url )
		jdoc = json.loads( result.content )
		return jdoc

	def auth_endpoint( self ):
		jdoc = self.discovery_doc
		return jdoc[ 'authorization_endpoint' ]

	def token_endpoint( self ):
		jdoc = self.discovery_doc
		return jdoc[ 'token_endpoint' ]

	def get_scope( self ):   # get scope (compulsory) to add to params
		return 'openid email'


	def validate_token_doc( self, tokenDoc ):
		# validate jwt according to http://openid.net/specs/openid-connect-basic-1_0.html#IDTokenValidation
		if tokenDoc.get( 'iss') != self.discovery_doc.get( 'issuer' ):
			return False
		if tokenDoc.get( 'aud' ) != self.get_auth_request_client_id( ):
			return False
		if 'azp' in tokenDoc and tokenDoc['azp'] != self.get_auth_request_client_id():
			return False
		exp = tokenDoc.get( 'exp' )
		currtime = int( time.time() )
		# use a 120 second margin for expiry
		if not isinstance( exp, ( int, long ) ) or int( exp ) + 120 < currtime:
			return False
		# ToDo could check iat
		return True

	def process_token_result( self, result ): # select the processing function
		jdoc = self.process_result_as_JSON( result )
		if 'error' in jdoc or 'id_token' not in jdoc:  # failed
			self.add_infomessage( MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
			self.redirect_to_relevant_page()
			return
		id_token = jdoc[ 'id_token' ]
		if type( id_token ) == bytes:
			segments = id_token.split( b'.' )
		else:
			segments = id_token.split( u'.' )
		jwtencoded = segments[ 1 ]
		if isinstance( jwtencoded, unicode ):
			jwtencoded = jwtencoded.encode( 'ascii' )
		jwtencoded = jwtencoded + b'=' * ( 4 - len( jwtencoded ) % 4 )
		jwt = json.loads( base64.urlsafe_b64decode( jwtencoded ).decode( 'utf-8' ))

		if not self.validate_token_doc( jwt ):
			self.add_infomessage( MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
			self.redirect_to_relevant_page()
			return


		loginInfoSettings = {   'provider_uid': 'sub',
								'email': 'email',
								'email_verified': 'email_verified' }
		loginInfo = self.process_login_info( loginInfoSettings, jwt )
		self.provider_authenticated_callback( loginInfo )


#===== GOOGLE ==========================================================================================================

class HandlerOAuthGoogle( HandlerOAuthOpenIDConnect ):

	AUTHCALLBACK = '/googleauthcallback'
	AUTHREQUEST = '/googleauthrequest'

	@classmethod
	def get_routes( cls ):
		routes = [ webapp2.Route( cls.AUTHREQUEST, handler = 'enki.handlersoauth.HandlerOAuthGoogle:auth_request', methods = [ 'GET' ] ),
		           webapp2.Route( cls.AUTHCALLBACK, handler = 'enki.handlersoauth.HandlerOAuthGoogle:auth_callback', methods = [ 'GET' ] ), ]
		return routes

	@classmethod
	def get_button( cls ):
		href = cls.AUTHREQUEST
		icon = 'fa-google'
		return button( href, icon )

	@classmethod
	def get_provider_name( cls ):
		return 'Google'

	def get_discovery_URL( self ):
		return 'https://accounts.google.com/.well-known/openid-configuration'

	def get_auth_request_client_id( self ):
		return settings.secrets.CLIENT_ID_GOOGLE

	def get_client_secret( self ):
		return settings.secrets.CLIENT_SECRET_GOOGLE

	def get_auth_callback( self ):
		return self.AUTHCALLBACK


#===== FACEBOOK ========================================================================================================

class HandlerOAuthFacebook( HandlerOAuthOAUTH2 ):

	AUTHCALLBACK = '/facebookcallback'
	AUTHREQUEST = '/facebookauthrequest'

	@classmethod
	def get_routes( cls ):
		routes = [ webapp2.Route( cls.AUTHREQUEST, handler = 'enki.handlersoauth.HandlerOAuthFacebook:auth_request', methods = [ 'GET' ] ),
		           webapp2.Route( cls.AUTHCALLBACK, handler = 'enki.handlersoauth.HandlerOAuthFacebook:auth_callback', methods = [ 'GET' ] ), ]
		return routes

	@classmethod
	def get_button( cls ):
		href = cls.AUTHREQUEST
		icon = 'fa-facebook'
		return button( href, icon )

	@classmethod
	def get_provider_name( cls ):
		return 'Facebook'

	def get_auth_request_client_id( self ):
		return settings.secrets.CLIENT_ID_FACEBOOK

	def get_client_secret( self ):
		return settings.secrets.CLIENT_SECRET_FACEBOOK

	def get_auth_callback( self ):
		return self.AUTHCALLBACK

	def auth_endpoint( self ):
		return 'https://www.facebook.com/dialog/oauth'

	def token_endpoint( self ):
		return 'https://graph.facebook.com/oauth/access_token'

	def profile_endpoint( self ):
		return 'https://graph.facebook.com/me'

	def get_scope( self ):   # get scope (compulsory) to add to params
		return 'public_profile email' # https://developers.facebook.com/docs/facebook-login/permissions/v2.2#reference

	def process_token_result( self, result ): # select the processing function
		data = self.process_result_as_JSON( result )
		if not data: # failed
			self.add_infomessage( MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
			self.redirect_to_relevant_page()
			return
		token = data[ 'access_token' ]
		profile = self.get_profile( token, { 'fields': 'id,email'} )
		jdoc = self.process_result_as_JSON( profile )
		jdoc[ 'email_verified' ] = True # Facebook emails only given if verified.
		loginInfoSettings = {   'provider_uid': 'id',
								'email': 'email',
								'email_verified': 'email_verified' }
		loginInfo = self.process_login_info( loginInfoSettings, jdoc )
		self.provider_authenticated_callback( loginInfo )


#===== GITHUB ==========================================================================================================

class HandlerOAuthGithub( HandlerOAuthOAUTH2 ):

	AUTHCALLBACK = '/githubcallback'
	AUTHREQUEST = '/githubauthrequest'

	@classmethod
	def get_routes( cls ):
		routes = [ webapp2.Route( cls.AUTHREQUEST, handler = 'enki.handlersoauth.HandlerOAuthGithub:auth_request', methods = [ 'GET' ] ),
		           webapp2.Route( cls.AUTHCALLBACK, handler = 'enki.handlersoauth.HandlerOAuthGithub:auth_callback', methods = [ 'GET' ] ), ]
		return routes

	@classmethod
	def get_button( cls ):
		href = cls.AUTHREQUEST
		icon = 'fa-github'
		return button( href, icon )

	@classmethod
	def get_provider_name( cls ):
		return 'GitHub'

	def get_auth_request_client_id( self ):
		return settings.secrets.CLIENT_ID_GITHUB

	def get_client_secret( self ):
		return settings.secrets.CLIENT_SECRET_GITHUB

	def get_auth_callback( self ):
		return self.AUTHCALLBACK

	def auth_endpoint( self ):
		return 'https://github.com/login/oauth/authorize'

	def token_endpoint( self ):
		return 'https://github.com/login/oauth/access_token'

	def profile_endpoint( self ):
		return 'https://api.github.com/user'

	def get_scope( self ):   # get scope (compulsory) to add to params
		return 'user:email'

	def process_token_result( self, result ): # select the processing function
		data = self.process_result_as_query_string( result )
		if not data: # failed
			self.add_infomessage( MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
			self.redirect_to_relevant_page()
			return
		token = data[ 'access_token' ]
		profile = self.get_profile( token )
		jdoc = self.process_result_as_JSON( profile )

		emailUrl ='https://api.github.com/user/emails?' + enki.libutil.urlencode({ 'access_token': token })
		emailDoc = self.urlfetch_safe( url = emailUrl )
		jemails = self.process_result_as_JSON( emailDoc )
		for item in jemails:
			if item.get( 'verified', False ):
				jdoc.update(item)
				if item.get( 'primary', False ):
					break # if we have a verified primary we stop and use that
		if jemails and not jdoc.get('email', None):
			jdoc.update( jemails[0] )

		jdoc['id'] = str( jdoc['id'] ) # convert id to string

		loginInfoSettings = {   'provider_uid': 'id',
								'email': 'email',
								'email_verified': 'verified' }
		loginInfo = self.process_login_info( loginInfoSettings, jdoc )
		self.provider_authenticated_callback( loginInfo )


#===== STEAM ===========================================================================================================

class HandlerOAuthSteam( HandlerOAuthBase ):

	AUTHCALLBACK = '/steamauthcallback'
	AUTHREQUEST = '/steamauthrequest'

	@classmethod
	def get_routes( cls ):
		routes = [ webapp2.Route( cls.AUTHREQUEST, handler = 'enki.handlersoauth.HandlerOAuthSteam:auth_request', methods = [ 'GET' ] ),
		           webapp2.Route( cls.AUTHCALLBACK, handler = 'enki.handlersoauth.HandlerOAuthSteam:auth_callback', methods = [ 'GET' ] ), ]
		return routes

	@classmethod
	def get_button( cls ):
		href = cls.AUTHREQUEST
		icon = 'fa-steam'
		return button( href, icon )

	@classmethod
	def get_provider_name( cls ):
		return 'Steam'

	def get_auth_callback( self ):
		return self.AUTHCALLBACK

	def auth_request( self ):
		params = {  'openid.ns': 'http://specs.openid.net/auth/2.0',
					'openid.mode': 'checkid_setup',
					'openid.claimed_id': 'http://specs.openid.net/auth/2.0/identifier_select',
					'openid.identity': 'http://specs.openid.net/auth/2.0/identifier_select',
					'openid.return_to': self.domain_name[ :-1 ] + self.get_auth_callback( ) + '?state=' + self.create_CSRF( 'oauth' ),
					'openid.realm': self.domain_name[ :-1 ] + self.get_auth_callback( ),
					}
		urlParams = enki.libutil.urlencode( params )
		fullURL = 'https://steamcommunity.com/openid/login?' + urlParams
		self.redirect( fullURL )

	def auth_callback_provider( self ):
		params = { 'openid.ns': '',
				   'openid.op_endpoint': '',
				   'openid.claimed_id': '',
				   'openid.identity': '',
				   'openid.return_to': '',
				   'openid.response_nonce': '',
				   'openid.assoc_handle': '',
				   'openid.signed': '',
				   'openid.sig': '',
				   }
		for key in params:
			params[ key ] = self.request.get( key )
		params[ 'openid.mode' ] = 'check_authentication'

		# param {'openid.claimed_id': u'http://steamcommunity.com/openid/id/7****************'}
		claimedId = str( params[ 'openid.claimed_id' ])[ len( 'http://steamcommunity.com/openid/id/' ): ]
		loginInfo = { 'provider_name': self.get_provider_name( ),
		              'provider_uid': claimedId,
		              'email': '',
		              'email_verified': '' }

		urlParams = enki.libutil.urlencode( params )
		fullURL = 'https://steamcommunity.com/openid/login'
		result = self.urlfetch_safe( url = fullURL, payload = urlParams, method = urlfetch.POST )
		if 'ns:http://specs.openid.net/auth/2.0\nis_valid:true\n' in result.content: # only if is_valid do we trust the loginInfo
			self.provider_authenticated_callback( loginInfo )


#===== TWITTER =========================================================================================================

def percent_encode( str_to_encode ):
	encoded = urllib.quote( str_to_encode.encode( 'utf-8' ), safe = '~' )
	return encoded


class HandlerOAuthTwitter( HandlerOAuthBase ):

	AUTHCALLBACK = '/twitterauthcallback'
	AUTHREQUEST = '/twitterauthrequest'

	@classmethod
	def get_routes( cls ):
		routes = [ webapp2.Route( cls.AUTHREQUEST, handler = 'enki.handlersoauth.HandlerOAuthTwitter:auth_request', methods = [ 'GET' ] ),
		           webapp2.Route( cls.AUTHCALLBACK, handler = 'enki.handlersoauth.HandlerOAuthTwitter:auth_callback', methods = [ 'GET' ] ), ]
		return routes

	@classmethod
	def get_button( cls ):
		href = cls.AUTHREQUEST
		icon = 'fa-twitter'
		return button( href, icon )

	@classmethod
	def get_provider_name( cls ):
		return 'Twitter'

	def get_auth_request_client_id( self ):
		return settings.secrets.CLIENT_ID_TWITTER

	def get_client_secret( self ):
		return settings.secrets.CLIENT_SECRET_TWITTER

	def get_auth_callback( self ):
		return self.AUTHCALLBACK

	def auth_check_CSRF( self ):
		session_token = self.session.get( 'twitter_oauth_token' )
		request_token = self.request.get( 'oauth_token' )
		if session_token != request_token:
			self.abort( 401 )
			return
		return

	def auth_sign( self, normalised_url, ordered_params, token_secret = '', method_get = False ):
		# note: create signature see https://dev.twitter.com/oauth/overview/creating-signatures
		params_to_sign = enki.libutil.urlencode( ordered_params )
		oauth_signature_string = ''
		if method_get:
			oauth_signature_string = 'GET&' + percent_encode( normalised_url ) + '&' + percent_encode( params_to_sign )
		else:
			oauth_signature_string = 'POST&' + percent_encode( normalised_url ) + '&' + percent_encode( params_to_sign )
		key = percent_encode( settings.secrets.CLIENT_SECRET_TWITTER ) + '&' + token_secret
		hmac_hash = hmac.new( key, oauth_signature_string, hashlib.sha1 )
		oauth_signature = base64.b64encode( hmac_hash.digest())
		return oauth_signature

	def auth_request( self ):
		# STEP 1
		# note: these parameters need to be sorted alphabetically by key. They are therefore a list of tuples and not a dictionary.
		params = [( 'oauth_callback' , self.domain_name[ :-1 ] + self.get_auth_callback()),
		          ( 'oauth_consumer_key' , settings.secrets.CLIENT_ID_TWITTER ),
		          ( 'oauth_nonce' , webapp2_extras.security.generate_random_string( length = 42, pool = webapp2_extras.security.ALPHANUMERIC ).encode( 'utf-8' )),
		          ( 'oauth_signature_method' , "HMAC-SHA1" ),
		          ( 'oauth_timestamp' , str( int( time.time()))),
		          ( 'oauth_version' , "1.0" )]
		normalised_url = 'https://api.twitter.com/oauth/request_token/'
		oauth_signature = self.auth_sign( normalised_url, params )
		params.append(( 'oauth_signature', oauth_signature ))
		url_params = enki.libutil.urlencode( params )
		result = self.urlfetch_safe( url = normalised_url, payload = url_params, method = urlfetch.POST )
		response = self.process_result_as_query_string( result )
		# STEP 2
		if response.get( 'oauth_callback_confirmed' ) != 'true' :
			self.abort( 401 )
			return
		else:
			oauth_token = response.get( 'oauth_token' )
			self.session[ 'twitter_oauth_token' ] = oauth_token
			self.session[ 'twitter_oauth_token_secret' ] = response.get( 'oauth_token_secret' )
			url_redirect_params = enki.libutil.urlencode([( 'oauth_token', oauth_token )])
			url_redirect = 'https://api.twitter.com/oauth/authenticate?' + url_redirect_params
			self.redirect( url_redirect )
		return

	def auth_callback_provider( self ):
		# STEP 3
		oauth_verifier = self.request.get( 'oauth_verifier' )
		params = [( 'oauth_consumer_key' , settings.secrets.CLIENT_ID_TWITTER ),
		          ( 'oauth_nonce' , webapp2_extras.security.generate_random_string( length = 42, pool = webapp2_extras.security.ALPHANUMERIC ).encode( 'utf-8' )),
		          ( 'oauth_signature_method' , "HMAC-SHA1" ),
		          ( 'oauth_timestamp' , str( int( time.time()))),
		          ( 'oauth_token', self.session.get( 'twitter_oauth_token' )),
		          ( 'oauth_version' , "1.0" )]
		normalised_url = 'https://api.twitter.com/oauth/access_token/'
		oauth_signature = self.auth_sign( normalised_url, params, self.session.get( 'twitter_oauth_token_secret') )
		params.append(( 'oauth_signature', oauth_signature ))
		params.append(( 'oauth_verifier', oauth_verifier ))
		url_params = enki.libutil.urlencode( params )
		result = self.urlfetch_safe( url = normalised_url, payload = url_params, method = urlfetch.POST )
		response = self.process_result_as_query_string( result )
		oauth_token = response.get( 'oauth_token' )
		oauth_token_secret = response.get('oauth_token_secret')
		user_id = response.get( 'user_id')
		if user_id and oauth_token:
			#get email address if we can
			verify_params = [('include_email', 'true'),
				             ('include_entities','false'),
			                 ('oauth_consumer_key', settings.secrets.CLIENT_ID_TWITTER ),
			                 ('oauth_nonce', webapp2_extras.security.generate_random_string( length = 42, pool = webapp2_extras.security.ALPHANUMERIC ).encode( 'utf-8' )),
			                 ('oauth_signature_method', "HMAC-SHA1"),
			                 ('oauth_timestamp', str(int(time.time()))),
			                 ('oauth_token', oauth_token ),
			                 ('oauth_version', "1.0"),
							 ('skip_status', 'true')]
			verify_oauth_signature = self.auth_sign('https://api.twitter.com/1.1/account/verify_credentials.json', verify_params,oauth_token_secret, method_get=True )
			verify_params.append(('oauth_signature', verify_oauth_signature))
			verify_url_params = enki.libutil.urlencode( verify_params )
			full_url = 'https://api.twitter.com/1.1/account/verify_credentials.json?' + verify_url_params
			verify_credentials_result_json = self.urlfetch_safe( url = full_url, method = urlfetch.GET )
			verify_credentials_result = self.process_result_as_JSON(verify_credentials_result_json)
			response['email'] = verify_credentials_result['email']
			response['email_verified'] = True
			loginInfoSettings = { 'provider_uid': 'user_id',
		              			  'email': 'email',
		                          'email_verified': 'email_verified' }
			loginInfo = self.process_login_info( loginInfoSettings, response )
			self.provider_authenticated_callback( loginInfo )
		else:
			self.abort( 401 )
		return
