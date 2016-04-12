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
import enki.textmessages as MSG


button = collections.namedtuple( 'button', 'href, src, alt' )


class HandlerOAuthBase( enki.HandlerBase ):

	def auth_callback( self ):
		self.auth_check_CSRF()
		# set referral and locale
		ref_d = self.session.get( 'sessionrefpath', self.request.referrer )
		ref = self.session.get( 'sessionloginrefpath', ref_d )
		if not ref:
			ref = enki.libutil.get_local_url( ) # home
		self.session[ 'sessionloginrefpath' ] = ref
		locale = ''
		parameters = urlparse.parse_qs( urlparse.urlparse( ref ).query )
		if 'locale' in parameters:
			locale_param = parameters[ 'locale' ][ 0 ]
			if locale_param in enki.handlerbase.LOCALES:
				locale = locale_param
		webapp2_extras.i18n.get_i18n().set_locale( locale )
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


class HandlerOAuthOAUTH2( HandlerOAuthBase ):

	def auth_request( self ):    # let the user authenticate themselves with the 3rd party provider
		params = { 'client_id': self.get_auth_request_client_id(),
					'response_type': 'code',
					'scope': self.get_scope(),
					'state': self.create_CSRF( 'oauth' ),
					'redirect_uri': self.domain_name[ :-1 ] + self.get_auth_callback(),
				   }
		params.update( self.get_optional_params( ) )
		urlParams = urllib.urlencode( params )
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
		urlParams = urllib.urlencode( params )
		url = self.token_endpoint()
		result = urlfetch.fetch( url = url,
								 payload = urlParams,
								 method = urlfetch.POST,
								 headers = { 'Content-Type': 'application/x-www-form-urlencoded' }
								)
		self.process_token_result( result )

	def get_profile( self, token ):
		fullUrl = self.profile_endpoint() + '?' + urllib.urlencode({ 'access_token': token })
		return urlfetch.fetch( url = fullUrl )


class HandlerOAuthOpenIDConnect( HandlerOAuthOAUTH2 ):

	def fetch_discovery_doc( self ):
		url = self.get_discovery_URL()
		result = urlfetch.fetch( url )
		jdoc = json.loads( result.content )
		return jdoc

	def auth_endpoint( self ):
		jdoc = self.fetch_discovery_doc( )
		return jdoc[ 'authorization_endpoint' ]

	def token_endpoint( self ):
		jdoc = self.fetch_discovery_doc( )
		return jdoc[ 'token_endpoint' ]

	def get_scope( self ):   # get scope (compulsory) to add to params
		return 'openid email'

	def process_token_result( self, result ): # select the processing function
		jdoc = self.process_result_as_JSON( result )
		if 'error' in jdoc:  # failed
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
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
		src = '/images/btn_google_signin_dark_normal_web.png'
		alt = MSG.CONNECT_WITH_GOOGLE()
		return button( href, src, alt )

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
		src = '/images/button_login_facebook_46.png'
		alt = MSG.CONNECT_WITH_FACEBOOK()
		return button( href, src, alt )

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
		return 'public_profile email' # https://developers.facebook.com/docs/facebook-login/permissions/v2.2?locale=en_GB#reference

	def process_token_result( self, result ): # select the processing function
		data = self.process_result_as_query_string( result )
		if not data: # failed
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
			self.redirect_to_relevant_page()
			return
		token = data[ 'access_token' ]
		profile = self.get_profile( token )
		jdoc = self.process_result_as_JSON( profile )

		loginInfoSettings = {   'provider_uid': 'id',
								'email': 'email',
								'email_verified': 'verified' }
		loginInfo = self.process_login_info( loginInfoSettings, jdoc )
		self.provider_authenticated_callback( loginInfo )

#===== FACEBOOK ========================================================================================================

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
		src = '/images/button_login_facebook_46.png'
		alt = MSG.CONNECT_WITH_GITHUB()
		return button( href, src, alt )

	@classmethod
	def get_provider_name( cls ):
		return 'Github'

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
		return 'user:email' # https://developers.facebook.com/docs/facebook-login/permissions/v2.2?locale=en_GB#reference

	def process_token_result( self, result ): # select the processing function
		data = self.process_result_as_query_string( result )
		if not data: # failed
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
			self.redirect_to_relevant_page()
			return
		token = data[ 'access_token' ]
		profile = self.get_profile( token )
		jdoc = self.process_result_as_JSON( profile )

		emailUrl ='https://api.github.com/user/emails?' + urllib.urlencode({ 'access_token': token })
		emailDoc = urlfetch.fetch( url = emailUrl )
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
		src = '/images/button_login_steam_sits_large_noborder.png'
		alt = MSG.CONNECT_WITH_STEAM()
		return button( href, src, alt )

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
		urlParams = urllib.urlencode( params )
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

		urlParams = urllib.urlencode( params )
		fullURL = 'https://steamcommunity.com/openid/login'
		result = urlfetch.fetch( url = fullURL, payload = urlParams, method = urlfetch.POST )
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
		src = '/images/sign-in-with-twitter-link.png'
		alt = MSG.CONNECT_WITH_TWITTER()
		return button( href, src, alt )

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

	def auth_sign( self, normalised_url, ordered_params, token_secret = '' ):
		# note: create signature see https://dev.twitter.com/oauth/overview/creating-signatures
		params_to_sign = urllib.urlencode( ordered_params )
		oauth_signature_string = 'POST&' + percent_encode( normalised_url ) + '&' + percent_encode( params_to_sign )
		key = percent_encode( settings.secrets.CLIENT_SECRET_TWITTER ) + '&' + token_secret
		hmac_hash = hmac.new( key, oauth_signature_string, hashlib.sha1 )
		oauth_signature = base64.b64encode( hmac_hash.digest())
		return oauth_signature

	def auth_request( self ):
		# STEP 1
		# note: these parameters need to be sorted alphabetically by key
		params = [( 'oauth_callback' , self.domain_name[ :-1 ] + self.get_auth_callback()),
		          ( 'oauth_consumer_key' , settings.secrets.CLIENT_ID_TWITTER ),
		          ( 'oauth_nonce' , webapp2_extras.security.generate_random_string( length = 42, pool = webapp2_extras.security.ALPHANUMERIC ).encode( 'utf-8' )),
		          ( 'oauth_signature_method' , "HMAC-SHA1" ),
		          ( 'oauth_timestamp' , str( int( time.time()))),
		          ( 'oauth_version' , "1.0" )]
		normalised_url = 'https://api.twitter.com/oauth/request_token/'
		oauth_signature = self.auth_sign( normalised_url, params )
		params.append(( 'oauth_signature', oauth_signature ))
		url_params = urllib.urlencode( params )
		result = urlfetch.fetch( url = normalised_url, payload = url_params, method = urlfetch.POST )
		response = self.process_result_as_query_string( result )
		# STEP 2
		if response.get( 'oauth_callback_confirmed' ) != 'true' :
			self.abort( 401 )
			return
		else:
			oauth_token = response.get( 'oauth_token' )
			self.session[ 'twitter_oauth_token' ] = oauth_token
			self.session[ 'twitter_oauth_token_secret' ] = response.get( 'oauth_token_secret' )
			url_redirect_params = urllib.urlencode([( 'oauth_token', oauth_token )])
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
		url_params = urllib.urlencode( params )
		result = urlfetch.fetch( url = normalised_url, payload = url_params, method = urlfetch.POST )
		response = self.process_result_as_query_string( result )
		oauth_token = response.get( 'oauth_token' )
		user_id = response.get( 'user_id')
		if user_id and oauth_token:
			#TODO get email address if we can
			#url_params = urllib.urlencode([( 'oauth_token', oauth_token )])
			#full_url = 'https://api.twitter.com/1.1/account/verify_credentials.json?' + url_params
			#result_credentials = urlfetch.fetch( url = full_url, method = urlfetch.GET )
			loginInfoSettings = { 'provider_uid': 'user_id',
		              			  'email': '',
		                          'email_verified': '' }
			loginInfo = self.process_login_info( loginInfoSettings, response )
			self.provider_authenticated_callback( loginInfo )
		else:
			self.abort( 401 )
		return
