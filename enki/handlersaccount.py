import webapp2
import collections

from webapp2_extras import security

import settings
import enki
import enki.libutil
import enki.textmessages as MSG
from enki.modelbackofftimer import EnkiModelBackoffTimer
from enki.modeltokenauth import EnkiModelTokenAuth
from enki.modeltokenemailrollback import EnkiModelTokenEmailRollback
from enki.modeluser import EnkiModelUser
from enki.modeldisplayname import EnkiModelDisplayName
from enki.modelfriends import EnkiModelFriends
from enki.modelmessage import EnkiModelMessage
from enki.modelproductkey import EnkiModelProductKey
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.modelpost import EnkiModelPost
from enki.modelrestapitokenverify import EnkiModelRestAPITokenVerify


class HandlerLogout( enki.HandlerBase ):

	def get( self ):
		self.log_out()
		self.add_infomessage( MSG.SUCCESS(), MSG.LOGGED_OUT())
		self.redirect_to_relevant_page()


class HandlerLogin( enki.HandlerBase ):

	def get( self ):
		email = self.session.pop( 'email_prefill', '' )
		# Get referal path to return the user to the page they were on after they've logged in
		if 'sessionloginrefpath' in self.session:
			self.add_infomessage( MSG.INFORMATION(), MSG.LOGIN_NEEDED())
		self.session[ 'sessionrefpath' ] = self.session.pop( 'sessionloginrefpath', self.request.referrer )
		self.render_tmpl( 'login.html',
		                  active_menu = 'login',
		                  authhandlers = settings.HANDLERS,
		                  email = email )

	def post( self ):
		self.cleanup_item()
		self.log_out()
		self.check_CSRF()
		submit_type = self.request.get( 'submittype' )
		email_unsafe = self.request.get( 'email' )
		email, result = self.validate_email( email_unsafe )
		if submit_type == 'login':
			password = self.request.get( 'password' )
			if result == enki.libutil.ENKILIB_OK and self.log_in_with_email( email, password ):
				self.add_infomessage( MSG.SUCCESS(), MSG.LOGGED_IN())
				self.redirect_to_relevant_page()
			else:
				error_message = MSG.WRONG_EMAIL_OR_PW()
				if EnkiModelUser.exist_by_email( email ):
				# if the email exist as part of an Auth account (doesn't have a password), silently email them to set a password.
					user = EnkiModelUser.get_by_email( email )
					if not user.password:
						self.add_debugmessage( '''Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.''' )
						link = enki.libutil.get_local_url( 'passwordrecover' )
						self.send_email( email, MSG.SEND_EMAIL_LOGIN_ATTEMPT_WITH_YOUR_EMAIL_NO_PW_SUBJECT( ), MSG.SEND_EMAIL_LOGIN_ATTEMPT_WITH_YOUR_EMAIL_NO_PW_BODY( link ))
				backoff_timer = EnkiModelBackoffTimer.get( email )
				if backoff_timer != 0:
					error_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ))
				self.render_tmpl( 'login.html',
				                  active_menu = 'login',
				                  authhandlers = settings.HANDLERS,
				                  email = email,
				                  error = error_message )
		else:
			self.session[ 'email_prefill' ] = email if email else ''
			if submit_type == 'register':
				self.redirect( enki.libutil.get_local_url( 'register' ))
			else:
				self.redirect( enki.libutil.get_local_url( 'passwordrecover' ))


class HandlerReauthenticate( enki.HandlerBase ):

	def get( self ):
		if self.ensure_is_logged_in():
			self.session[ 'sessionrefpath' ] = self.request.referrer
			self.render_tmpl( 'reauthenticate.html',
			                  active_menu = 'profile',
			                  authhandlers = self.get_user_auth_providers(),
			                  email = self.enki_user.email if ( self.enki_user.email and self.enki_user.password ) else None )

	def post( self ):
		if self.ensure_is_logged_in():
			self.check_CSRF()
			submit_type = self.request.get( 'submittype' )
			if self.enki_user.email:
				if self.enki_user.password and submit_type == 'reauthenticate':
					password = self.request.get( 'password' )
					if self.reauthenticate( self.enki_user.email, password ):
						self.add_infomessage( MSG.SUCCESS(), MSG.REAUTHENTICATED())
						self.redirect_to_relevant_page()
					else:
						error_message = MSG.WRONG_EMAIL_OR_PW()
						backoff_timer = EnkiModelBackoffTimer.get( self.enki_user.email )
						if backoff_timer != 0:
							error_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ))
						self.render_tmpl( 'reauthenticate.html',
						                  active_menu = 'profile',
						                  authhandlers = self.get_user_auth_providers(),
						                  email = self.enki_user.email,
						                  error = error_message )
				elif submit_type == 'cancel':
					self.redirect_to_relevant_page()
				elif submit_type == 'recoverpass':
					self.session[ 'email_prefill' ] = self.enki_user.email if self.enki_user.email else ''
					self.redirect( enki.libutil.get_local_url( 'passwordrecover' ))


class HandlerStayLoggedIn( enki.HandlerBaseReauthenticate ):

	def toggle_stay_logged_in( self ):
		token = self.session.get('auth_token')
		old_token_auth = EnkiModelTokenAuth.get_by_user_id_token( self.user_id, token )
		if old_token_auth:
			# create a new token with stay_logged_in set as async refresh of token can be overwrite old one
			self.session.modified = True  # force session to be saved
			stay_logged_in = not old_token_auth.stay_logged_in
			self.log_in_session_token_create( self.enki_user , stay_logged_in )
			old_token_auth.key.delete_async()
		self.redirect_to_relevant_page()

	def get_logged_in( self ):
		self.toggle_stay_logged_in()

	def post_reauthenticated(self, params):
		request_url = params.get( 'request_url' )
		if request_url:
			request_url_u = enki.libutil.xstr( request_url )
			self.session[ 'sessionrefpath' ] = request_url_u.encode( 'ascii'  )
		self.toggle_stay_logged_in()


class HandlerAccountConnect( enki.HandlerBaseReauthenticate ):

	def get_logged_in( self ):
		data = collections.namedtuple( 'data', 'email, allow_change_pw, auth_providers, enough_accounts' )

		email = self.enki_user.email
		allow_change_pw = True
		if ( not email or email == 'removed' ) and not self.enki_user.password:
			allow_change_pw = False

		auth_providers = []
		providers_temp_list = []    # list of providers the user is registered with
		for item in self.enki_user.auth_ids_provider:
			provider_name, provider_uid = item.partition( ':' )[ ::2 ] # save even list items starting at 0
			auth_providers.append({ 'provider_name': provider_name, 'provider_uid': str( provider_uid ), 'status': 'registered' })
			providers_temp_list.append( provider_name )
		for item in settings.HANDLERS:   # remaning providers
			provider = item.get_provider_name()
			if provider not in providers_temp_list:
				auth_providers.append({ 'provider_name': provider, 'provider_uid': 'none', 'status': 'unregistered' })
		enough_accounts = self.has_enough_accounts()

		data = data( email, allow_change_pw, auth_providers, enough_accounts )
		self.render_tmpl( 'accountconnect.html',
		                  active_menu = 'profile',
		                  authhandlers = settings.HANDLERS,
		                  data = data )

	def post_reauthenticated( self, params ):
		register = params.get( 'register' )
		deregister = params.get( 'deregister' )
		if register:  # initiate adding a new authentication method to the account
			for authhandler in settings.HANDLERS:
				if register == authhandler.get_provider_name():
					token = security.generate_random_string( entropy = 256 )
					LoginAddToken = EnkiModelTokenVerify( token = token, user_id = self.user_id, state = register, type = 'loginaddconfirm_1' )
					LoginAddToken.put()
					self.redirect( authhandler.get_button().href )
					break
		elif deregister:
			self.remove_auth_id( deregister)
			self.add_infomessage( MSG.SUCCESS(), MSG.AUTH_PROVIDER_REMOVED( deregister ))
			self.redirect( enki.libutil.get_local_url( 'accountconnect' ))


class HandlerLoginAddConfirm( enki.HandlerBaseReauthenticate ):

	def get_logged_in( self ):
		tokenEntity = EnkiModelTokenVerify.get_by_user_id_type( self.user_id, 'loginaddconfirm_2' )
		if tokenEntity:
			provider_name, provider_uid = tokenEntity.state.partition( ':' )[ ::2 ]
			tokenEntity.type = 'loginaddconfirm_3'
			tokenEntity.put()
			self.render_tmpl( 'loginaddconfirm.html',
							  active_menu = 'profile',
							  provider_name = provider_name,
							  provider_uid = provider_uid,
							  token = tokenEntity.token )
		else:
			self.redirect( enki.libutil.get_local_url( 'accountconnect' ))


	def post_reauthenticated( self, params ):
		choice = params.get( 'choice' )
		if choice != 'cancel':
			tokenEntity = EnkiModelTokenVerify.get_by_user_id_state_type( self.user_id, choice, 'loginaddconfirm_3')
			if tokenEntity:
				self.set_auth_id( tokenEntity.state, self.user_id )
				self.add_infomessage( MSG.SUCCESS(), MSG.AUTH_PROVIDER_ADDED( str( tokenEntity.state )))
			tokenEntity.key.delete()
		self.redirect( enki.libutil.get_local_url( 'accountconnect' ))


class HandlerProfile( enki.HandlerBaseReauthenticate ):

	def get( self ):
		if self.ensure_is_logged_in():
			data = collections.namedtuple( 'data', '''current_display_name, previous_display_names,
													email, has_password, has_auth_id_providers
												   friends, messages, sessions_browsers, sessions_apps''' )
			current_display_name = ''
			previous_display_names = ''
			user_display_name = EnkiModelDisplayName.get_by_user_id_current( self.user_id )
			if user_display_name:
				current_display_name = EnkiModelDisplayName.get_user_id_display_name_url( user_display_name )
				previous_display_names = EnkiModelDisplayName.get_user_display_name_old( self.user_id )

			email = self.enki_user.email
			if email == 'removed':
				email = ''
			has_password = False
			if self.enki_user.password:
				has_password = True
			has_auth_id_providers = False
			if self.enki_user.auth_ids_provider:
				has_auth_id_providers = True

			friends = EnkiModelFriends.count_by_user_id( self.user_id )
			messages = EnkiModelMessage.count_by_recipient( self.user_id )

			sessions_browsers = EnkiModelTokenAuth.count_by_user_id( self.user_id )
			sessions_apps = EnkiModelRestAPITokenVerify.count_by_user_id_type( user_id = self.user_id, type = 'apiconnect' )

			data = data( current_display_name, previous_display_names,
						 email, has_password, has_auth_id_providers,
						 friends, messages, sessions_browsers, sessions_apps )
			self.render_tmpl( 'profile.html',
			                  active_menu = 'profile',
			                  data = data )


class HandlerSessions( enki.HandlerBaseReauthenticate ):

	def get_logged_in( self ):
		self.render_tmpl( 'sessions.html',
						  active_menu = 'profile',
						  data = self.get_data())

	def post_reauthenticated( self, params ):
		token_disconnect_browser = params.get( 'disconnect_browser' )
		token_disconnect_app = params.get( 'disconnect_app' )
		if token_disconnect_browser:
			EnkiModelTokenAuth.delete( token_disconnect_browser )
			self.add_infomessage( MSG.SUCCESS(), MSG.DISCONNECTED_SESSION())
		elif token_disconnect_app:
			EnkiModelRestAPITokenVerify.delete_token_by_id( token_disconnect_app )
			self.add_infomessage( MSG.SUCCESS(), MSG.DISCONNECTED_APP())
		self.render_tmpl( 'sessions.html',
						  active_menu = 'profile',
						  data = self.get_data())

	def get_data( self ):
		data = collections.namedtuple( 'data', '''sessions_browsers, sessions_apps''' )
		sessions_browsers = []
		current_token = self.session.get( 'auth_token' )
		auth_tokens = EnkiModelTokenAuth.fetch_by_user_id( self.user_id )
		for item in auth_tokens:
			current = False
			if current_token == item.token:
				current = True
			sessions_browsers.append({ 'tokenauth_id':item.key.id(), 'time_created':item.time_created, 'current':current })
		sessions_apps = []
		list = EnkiModelRestAPITokenVerify.fetch_by_user_id_type(user_id = self.user_id, type = 'apiconnect')
		for item in list:
			sessions_apps.append({ 'token_id':item.key.id(), 'time_created':item.time_created })
		data = data( sessions_browsers, sessions_apps )
		return data


class HandlerProfilePublic( enki.HandlerBase ):

	def get( self, useridnumber ):
		if self.ensure_is_logged_in():
			display_name_data = None
			if useridnumber.isdigit and EnkiModelUser.get_by_id( int( useridnumber )):
				display_name_data = EnkiModelDisplayName.get_display_name_data( int( useridnumber ))
			else:
				self.add_infomessage( MSG.INFORMATION(), MSG.USER_NOT_EXIST())
			self.render_tmpl( 'profilepublic.html', False,
			                  active_menu = 'home',
			                  display_name_data = display_name_data )


class HandlerRegister( enki.HandlerBase ):

	def get( self ):
		email = self.session.pop( 'email_prefill', '' )
		# Get referal path to return the user to the page they were on after they've logged in using auth
		self.session[ 'sessionrefpath' ] = self.request.referrer
		self.render_tmpl( 'register.html',
		                  active_menu = 'register',
		                  authhandlers = settings.HANDLERS,
		                  email = email )

	def post( self ):
		self.check_CSRF()
		submit_type = self.request.get( 'submittype' )
		email_unsafe = self.request.get( 'email' )
		email, result = self.validate_email( email_unsafe )
		if submit_type == 'register':
			if result == enki.libutil.ENKILIB_OK:
				result = self.email_set_request( email )
			error_message = ''
			if result == enki.libutil.ENKILIB_OK or result == self.ERROR_EMAIL_IN_USE:
			# if email exists, pretend there was a registration (i.e. hide the fact that the email exists) to prevent email checking
				self.add_infomessage( MSG.INFORMATION(), MSG.REGISTRATION_INFO_EMAIL_SENT( email ))
				if result == self.ERROR_EMAIL_IN_USE:
					self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
					link = enki.libutil.get_local_url( 'passwordrecover' )
					self.send_email( email, MSG.SEND_EMAIL_REGISTER_ATTEMPT_WITH_YOUR_EMAIL_SUBJECT(), MSG.SEND_EMAIL_REGISTER_ATTEMPT_WITH_YOUR_EMAIL_BODY( link ))
				self.redirect_to_relevant_page()
				return
			else:
				if result == self.ERROR_EMAIL_FORMAT_INVALID:
					error_message = MSG.WRONG_EMAIL_FORMAT()
				elif result == self.ERROR_EMAIL_MISSING:
					error_message = MSG.MISSING_EMAIL()
				self.render_tmpl( 'register.html',
				                  active_menu = 'register',
				                  authhandlers = settings.HANDLERS,
				                  email = email,
				                  error = error_message )
		else:
			self.session[ 'email_prefill' ] = email if email else ''
			if submit_type == 'login':
				self.redirect( enki.libutil.get_local_url( 'login' ))
			else:
				self.redirect( enki.libutil.get_local_url( 'passwordrecover' ))


class HandlerRegisterConfirm( enki.HandlerBase ):

	def get( self, **kwargs ):
		token = kwargs[ 'verifytoken' ]
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'register' )
		if tokenEntity:
			email = tokenEntity.email
			link = enki.libutil.get_local_url( 'registerconfirm', { 'verifytoken': token } )
			self.render_tmpl( 'registerconfirm.html',
			                  active_menu = 'register',
			                  email = email,
			                  url = link )
		else:
			self.abort( 404 )

	def post( self, **kwargs ):
		self.check_CSRF(),
		token = kwargs[ 'verifytoken' ]
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'register' )
		if tokenEntity:
			email = tokenEntity.email
			password = self.request.get( 'password' )
			result = self.validate_password( password )
			link = enki.libutil.get_local_url( 'registerconfirm', { 'verifytoken': token } )
			if result == enki.libutil.ENKILIB_OK:
				result = self.create_user_from_email_pw( email, password )
				if result == enki.libutil.ENKILIB_OK:
					self.add_infomessage( MSG.SUCCESS(), MSG.ACCOUNT_CREATED())
					self.log_in_with_email( email, password )
					self.redirect_to_relevant_page()
				elif result == self.ERROR_USER_NOT_CREATED:
					error_message = MSG.FAIL_REGISTRATION()
					self.render_tmpl( 'register.html',
					                  active_menu = 'register',
					                  email = email,
					                  error = error_message )
			else:
				error_message = ''
				if result == self.ERROR_PASSWORD_BLANK:
					error_message = MSG.MISSING_PW()
				elif result == self.ERROR_PASSWORD_TOO_SHORT :
					length = len( password )
					error_message = " ".join( [ MSG.PW_TOO_SHORT( length ), MSG.PW_ENSURE_MIN_LENGTH( self.app.config.get( 'enki' ).get( 'user' ).get( 'PASSWORD_LENGTH_MIN' ))])
				self.render_tmpl( 'registerconfirm.html',
				                  active_menu = 'register',
				                  email = email,
				                  url = link,
				                  error = error_message )
		else:
			self.abort( 404 )


class HandlerRegisterOAuthConfirm( enki.HandlerBase ):
	# Create or edit user based on auth login info
	def get( self ):
		token = self.session.get( 'tokenregisterauth' )
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'register', retry = 3 )
		if tokenEntity:
			provider_name, provider_uid = tokenEntity.state.partition( ':' )[ ::2 ]
			self.render_tmpl( 'registeroauthconfirm.html',
			                  active_menu = 'register',
			                  token = tokenEntity,
			                  provider_name = provider_name,
			                  provider_uid = str( provider_uid ))
		else:
			self.abort( 404 )

	def post( self ):
		choice = self.request.get( 'choice' )
		# Step 1
		if choice == 'create' or choice == 'cancel':
			token = self.session.get( 'tokenregisterauth' )
			tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'register' )
			authId = tokenEntity.state
			provider_name, provider_uid = authId.partition( ':' )[ ::2 ]
			auth_email = tokenEntity.email if tokenEntity.email else None
			if choice == 'create':
				if auth_email:
					# If the email is given by the provider, it is verified. Get or ceate the account and log the user in.
					user = self.get_or_create_user_from_authid( authId, auth_email )
					if user: # login the user through auth
						self.log_in_session_token_create( user )
						self.add_infomessage( MSG.SUCCESS(), MSG.LOGGED_IN())
					else: # user creation failed (timeout etc.)
						self.add_infomessage( MSG.WARNING(), MSG.AUTH_LOGIN_FAILED( provider_name ))
					self.redirect_to_relevant_page()
					tokenEntity.key.delete()
					self.session.pop( 'tokenregisterauth' )
				else:
					# If the email isn't given by the provider, use the manually entered email.
					self.check_CSRF()
					email_unsafe = self.request.get( 'email' )
					user = self.get_or_create_user_from_authid( authId )
					self.log_in_session_token_create( user )
					error_message = ''
					success = False
					email, result = self.validate_email( email_unsafe )
					if result == enki.libutil.ENKILIB_OK:
						result = self.email_change_request( email )	# send an email for verification. Since it's not verified at this point, create the account without the email.
						self.add_infomessage( MSG.INFORMATION(), MSG.REGISTER_AUTH_ADD_EMAIL_INFO_EMAIL_SENT( email ))
						if result == self.ERROR_EMAIL_IN_USE:
							self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
						success = True
						tokenEntity.key.delete()
						self.session.pop( 'tokenregisterauth' )
					elif result == self.ERROR_EMAIL_FORMAT_INVALID:
							error_message = MSG.WRONG_EMAIL_FORMAT()
					elif result == self.ERROR_EMAIL_MISSING:
							error_message = MSG.MISSING_EMAIL()
					self.render_tmpl( 'registeroauthconfirm.html',
					                  active_menu = 'register',
					                  token = tokenEntity,
					                  provider_name = provider_name,
					                  provider_uid = str( provider_uid ),
					                  error = error_message,
					                  success = success )
			elif choice == 'cancel':
				self.add_infomessage( MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
				self.redirect_to_relevant_page()
				tokenEntity.key.delete()
				self.session.pop( 'tokenregisterauth' )
		# Step 2 (those choices will only be presented to the user if they successfully added an email manually).
		elif choice == 'continue':
			self.redirect_to_relevant_page()
		elif choice == 'profile':
			url = enki.libutil.get_local_url( 'profile' )
			self.session[ 'sessionrefpath' ] = url
			self.redirect( url )


class HandlerRegisterOAuthWithExistingEmail( enki.HandlerBase ):
	# When logging in with an auth provider that has a verified email, if the email belongs to an existing account
	# but the account doesn't include the auth provider, suggest two actions to the user:
	# - A. Log in to the existing account; or
	# - B. Create a new account using the auth provider, but with a different email.
	# - Note case A: if the provider used for login is also registered with the account (with a different user Id),
	# add a message to inform the user that they should log out of the provider's account or use a different browser.
	# - Note case C. not implemented: Add the new auth provider to the existing email account. Unnecessary as the user
	# can do it from their profile page once they've logged in.
	def get( self ):
		token = self.session.get( 'tokenregisterauth' )
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'register', retry = 3 )
		if tokenEntity:
			provider_name, provider_uid = tokenEntity.state.partition( ':' )[ ::2 ]
			provider_email = tokenEntity.email
			provider_authhandler = ''
			for handler in settings.HANDLERS:
				if handler.get_provider_name() == provider_name:
					provider_authhandler = handler
			# only display the email/pw login if the user has a password
			email_user_has_pw = EnkiModelUser.has_password_by_email( provider_email )
			# list of email user's auth providers
			authhandlers = []
			user = EnkiModelUser.get_by_email( provider_email )
			for user_provider_uid in user.auth_ids_provider:
				for handler in settings.HANDLERS:
					if ( handler.get_provider_name() in user_provider_uid ) and ( handler not in authhandlers ):
						authhandlers.append( handler )
						break
			self.render_tmpl( 'registeroauthwithexistingemail.html',
			                  active_menu = 'login',
			                  token = tokenEntity,
							  email = provider_email,
							  email_user_has_pw = email_user_has_pw,
			                  provider_name = provider_name,
			                  provider_uid = str( provider_uid ),
							  provider_authhandler = provider_authhandler,
							  authhandlers = authhandlers,
							  )
		else:
			self.abort( 404 )

	def post( self ):
		self.cleanup_item()
		self.log_out()
		self.check_CSRF()
		token = self.session.get('tokenregisterauth')
		tokenEntity = EnkiModelTokenVerify.get_by_token_type(token, 'register')
		if tokenEntity:
			submit_type = self.request.get( 'submittype' )
			# Log in with email and password
			if submit_type == 'login':
				email = tokenEntity.email
				tokenEntity.key.delete()
				password = self.request.get( 'password' )
				if self.log_in_with_email( email, password ):
					self.add_infomessage( MSG.SUCCESS(), MSG.LOGGED_IN())
					self.redirect_to_relevant_page()
				else:
					error_message = MSG.WRONG_EMAIL_OR_PW()
					backoff_timer = EnkiModelBackoffTimer.get( email )
					if backoff_timer != 0:
						error_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ))
					self.render_tmpl( 'login.html',
									  active_menu = 'login',
									  authhandlers = settings.HANDLERS,
									  email = email,
									  error = error_message )
			elif submit_type == 'recoverpass':
				email = tokenEntity.email
				tokenEntity.key.delete()
				self.session[ 'email_prefill' ] = email if email else ''
				self.redirect( enki.libutil.get_local_url( 'passwordrecover' ))
			# Create a new account using the OAuth provider but without the email
			elif submit_type == 'register':
				email = tokenEntity.email
				tokenEntity.email = ''
				tokenEntity.put()
				self.add_infomessage( MSG.INFORMATION() , MSG.REGISTRATION_INFO_EMAIL_CANNOT_USE( email ))
				self.redirect( enki.libutil.get_local_url( 'registeroauthconfirm' ))
			else:
				tokenEntity.key.delete()
				self.add_infomessage( MSG.INFORMATION(), MSG.LOGIN_FAILED())
				self.redirect( enki.libutil.get_local_url( 'home' ))
		else:
			self.abort(404)



class HandlerPasswordChange( enki.HandlerBase ):
# change password - logged in user

	def get( self ):
		if self.ensure_is_logged_in():
			if self.enki_user.email and not self.enki_user.password:
				# if the user doesn't currently have a pw (e.g. logged in through auth)
				self.redirect( enki.libutil.get_local_url( 'passwordrecover' ) )
			else:
				self.render_tmpl( 'passwordchange.html',
				                  active_menu = 'profile', )

	def post( self ):
		if self.ensure_is_logged_in():
			self.check_CSRF()
			password = self.request.get( 'password' )
			email = self.enki_user.email
			error_password_message = ''
			error_passwordnew_message = ''
			if self.log_in_with_id( self.enki_user.key.id(), password ):
				password_new = self.request.get( 'passwordnew' )
				result = self.set_password( self.enki_user, password_new )
				if result == enki.libutil.ENKILIB_OK:
					self.add_infomessage( MSG.SUCCESS( ), MSG.PASSWORD_UPDATED())
					self.redirect( enki.libutil.get_local_url( 'profile' ) )
					return
				else:
					if result == self.ERROR_PASSWORD_BLANK:
						error_passwordnew_message = MSG.MISSING_NEW_PW()
					elif result == self.ERROR_PASSWORD_TOO_SHORT :
						length = len( password_new )
						error_passwordnew_message = " ".join( [ MSG.PW_TOO_SHORT( length ), MSG.PW_ENSURE_MIN_LENGTH(
							self.app.config.get( 'enki' ).get( 'user' ).get( 'PASSWORD_LENGTH_MIN' ) ) ] )
			else:
				error_password_message = MSG.WRONG_PW()
				backoff_timer = EnkiModelBackoffTimer.get( email )
				if backoff_timer != 0:
					error_password_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ) )
			self.render_tmpl( 'passwordchange.html',
			                  active_menu = 'profile',
			                  error_password = error_password_message,
			                  error_passwordnew = error_passwordnew_message )


class HandlerPasswordRecover( enki.HandlerBase ):
# change password - user can't log in so email them

	def get( self ):
		email = self.session.pop( 'email_prefill', '' )
		if not email and self.is_logged_in():
			email = self.enki_user.email
		self.render_tmpl( 'passwordrecover.html',
		                  email = email )

	def post( self ):
		self.check_CSRF()
		submit_type = self.request.get( 'submittype' )
		email_unsafe = self.request.get( 'email' )
		email, result = self.validate_email( email_unsafe )
		if submit_type == 'recoverpass':
			error_message = ''
			if result == enki.libutil.ENKILIB_OK:
				result = self.password_change_request( email )
				if result == enki.libutil.ENKILIB_OK or result == self.ERROR_EMAIL_NOT_EXIST:
					# The info displayed is identical whether the email corresponds to an existing account or not to prevent email checking.
					self.add_infomessage( MSG.INFORMATION(), MSG.PASSWORD_RESET_INFO_EMAIL_SENT( email ))
					if result == self.ERROR_EMAIL_NOT_EXIST:
						self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
					self.redirect_to_relevant_page()
					return
			elif result == self.ERROR_EMAIL_FORMAT_INVALID:
				error_message = MSG.WRONG_EMAIL_FORMAT()
			elif result == self.ERROR_EMAIL_MISSING:
				error_message = MSG.MISSING_EMAIL()
			self.render_tmpl( 'passwordrecover.html',
			                  email = email,
			                  error = error_message )
		else:
			self.session[ 'email_prefill' ] = email if email else ''
			if submit_type == 'login':
				self.redirect( enki.libutil.get_local_url( 'login' ))
			else:
				self.redirect( enki.libutil.get_local_url( 'register' ))


class HandlerPasswordRecoverConfirm( enki.HandlerBase ):
# recover password - user got link in email

	def get( self, **kwargs):
		token = kwargs[ 'verifytoken' ]
		if EnkiModelTokenVerify.exist_by_token_type( token, 'passwordchange' ):
			link = enki.libutil.get_local_url( 'passwordrecoverconfirm', { 'verifytoken': token } )
			self.render_tmpl( 'passwordrecoverconfirm.html',
			                  active_menu = 'profile',
			                  url = link )
		else:
			self.abort( 404 )

	def post( self, **kwargs ):
		self.check_CSRF()
		token = kwargs[ 'verifytoken' ]
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'passwordchange' )
		if tokenEntity:
			email = tokenEntity.email
			user = EnkiModelUser.get_by_email( email )
			if user:
				password = self.request.get( 'password' )
				result = self.set_password( user, password )
				if result == enki.libutil.ENKILIB_OK:
					EnkiModelTokenVerify.delete_by_email_type( email, 'passwordchange' )
					EnkiModelBackoffTimer.remove( user.email )
					self.log_in_with_id( user.key.id(), password )
					self.add_infomessage( MSG.SUCCESS( ), MSG.PASSWORD_SET())
					self.redirect( enki.libutil.get_local_url( 'profile' ))
					return
				else:
					error_message = ''
					if result == self.ERROR_PASSWORD_BLANK :
						error_message = MSG.MISSING_PW()
					elif result == self.ERROR_PASSWORD_TOO_SHORT :
						length = len( password )
						error_message = " ".join( [ MSG.PW_TOO_SHORT( length ), MSG.PW_ENSURE_MIN_LENGTH( self.app.config.get( 'enki' ).get( 'user' ).get( 'PASSWORD_LENGTH_MIN' ) ) ] )
					self.render_tmpl( 'passwordrecoverconfirm.html',
					                  error = error_message )
			else:
				self.abort( 401 )
		else:
			self.abort( 404 )


class HandlerDisplayName( enki.HandlerBaseReauthenticate ):
# set/change display name

	def get_logged_in( self ):
		self.session[ 'sessiondisplaynamerefpath' ] = self.session.pop( 'sessiondisplaynamerefpath', self.request.referrer )
		self.session[ 'sessionreauth' ] = self.session[ 'sessiondisplaynamerefpath' ]
		auto_generated = ''
		intro_message = ''
		if not EnkiModelDisplayName.exist_by_user_id( self.user_id ):
			# if no displayname exists, auto-generate one
			auto_generated = EnkiModelDisplayName.cosmopompe()[ 0 ]
			intro_message = " ".join([ MSG.DISPLAY_NAME_INTRO(), MSG.DISPLAY_NAME_AUTO_GENERATED()])
		self.render_tmpl( 'displayname.html',
		                  active_menu = 'profile',
		                  auto_generated = auto_generated,
		                  intro = intro_message,
		                  data = EnkiModelDisplayName.get_display_name_data( self.user_id ),
		                  prefix_length_min = EnkiModelDisplayName.PREFIX_LENGTH_MIN,
		                  prefix_length_max = EnkiModelDisplayName.PREFIX_LENGTH_MAX )

	def post_reauthenticated( self, params ):
		prefix = params.get( 'prefix' )
		error_message = ''
		result = EnkiModelDisplayName.make_unique_and_set_display_name( self.user_id, prefix )
		if result == enki.libutil.ENKILIB_OK:
			self.add_roles( self.enki_user, [ 'RUC' ])
			self.add_infomessage( MSG.SUCCESS( ), MSG.DISPLAYNAME_SET())
			self.session[ 'sessiondisplaynamerefpath' ] = self.session.pop( 'sessionreauth', self.request.referrer )
			self.redirect_to_relevant_page()
			return
		else:
			if result == EnkiModelDisplayName.ERROR_DISPLAY_NAME_LENGTH:
				length = len( prefix )
				instruction = ''
				if length < EnkiModelDisplayName.PREFIX_LENGTH_MIN:
					instruction = MSG.DISPLAY_NAME_TOO_SHORT_LENGTHEN( EnkiModelDisplayName.PREFIX_LENGTH_MIN )
				elif length > EnkiModelDisplayName.PREFIX_LENGTH_MAX:
					instruction = MSG.DISPLAY_NAME_TOO_LONG_SHORTEN( EnkiModelDisplayName.PREFIX_LENGTH_MAX )
				error_message = " ".join([ MSG.DISPLAY_NAME_WRONG_LENGTH( length ), instruction ])
			elif result == EnkiModelDisplayName.ERROR_DISPLAY_NAME_ALNUM:
				error_message = MSG.DISPLAY_NAME_WRONG_SYMBOLS()
			elif result == EnkiModelDisplayName.ERROR_DISPLAY_NAME_IN_USE:
				error_message = MSG.DISPLAY_NAME_ALREADY_USED()
			self.render_tmpl( 'displayname.html',
			                  active_menu = 'profile',
			                  prefix = prefix,
			                  data = EnkiModelDisplayName.get_display_name_data( self.user_id ),
			                  prefix_length_min = EnkiModelDisplayName.PREFIX_LENGTH_MIN,
			                  prefix_length_max = EnkiModelDisplayName.PREFIX_LENGTH_MAX,
			                  error = error_message )


class HandlerEmailChange( enki.HandlerBaseReauthenticate ):
# user requests an email change. Current email stored in rollback db

	def get_logged_in( self ):
		self.render_tmpl( 'emailchange.html',
		                  active_menu = 'profile' )

	def post_reauthenticated( self, params ):
		email_unsafe = params.get( 'email' )
		email, result = self.validate_email( email_unsafe )
		error_message = ''
		if result == enki.libutil.ENKILIB_OK or result == self.ERROR_EMAIL_MISSING:
			result_of_change_request = self.email_change_request( email )
			if result_of_change_request == 'same':
				error_message = MSG.CURRENT_EMAIL()
			elif result_of_change_request == 'cannot_remove':
				error_message = MSG.CANNOT_DELETE_EMAIL()
			elif result_of_change_request == 'removed':
				self.add_infomessage( MSG.SUCCESS(), MSG.EMAIL_REMOVED())
				old_email_existed = True if (self.enki_user.email and self.enki_user.email != 'removed') else False
				if old_email_existed:
					self.add_infomessage( MSG.INFORMATION(), MSG.EMAIL_ROLLBACK_INFO_EMAIL_SENT())
				self.redirect( enki.libutil.get_local_url( 'profile' ))
			elif result_of_change_request == 'change' or result_of_change_request == self.ERROR_EMAIL_IN_USE:
				self.add_infomessage( MSG.INFORMATION(), MSG.EMAIL_CHANGE_CONFIRM_INFO_EMAIL_SENT( email ))
				if self.enki_user.email and self.enki_user.email != 'removed':
					self.add_infomessage( MSG.INFORMATION(), MSG.EMAIL_CHANGE_UNDO_INFO_EMAIL_SENT())
				self.redirect( enki.libutil.get_local_url( 'profile' ))
				return
		elif result == self.ERROR_EMAIL_FORMAT_INVALID:
			error_message = MSG.WRONG_EMAIL_FORMAT()
		if error_message:
			self.render_tmpl( 'emailchange.html',
			                  active_menu = 'profile',
			                  email = email,
			                  error = error_message )


class HandlerEmailChangeConfirm( enki.HandlerBase ):
# do the email change

	def get( self, **kwargs ):
		token = kwargs[ 'verifytoken' ]
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'emailchange' )
		if tokenEntity:
			self.email_change( tokenEntity )
			self.add_infomessage( MSG.SUCCESS( ), MSG.EMAIL_SET())
			self.redirect( enki.libutil.get_local_url( 'profile' ) )
		else:
			self.abort( 404 )


class HandlerEmailRollback( enki.HandlerBase ):
# rollback to an older email

	def get( self, **kwargs ):
		token = kwargs[ 'rollbacktoken' ]
		tokenEntity = EnkiModelTokenEmailRollback.get_by_token( token )
		if tokenEntity:
			self.email_rollback( tokenEntity )
			self.add_infomessage( MSG.SUCCESS( ), MSG.EMAIL_RESTORED())
			self.redirect( enki.libutil.get_local_url( 'profile' ) )
		else:
			self.abort( 404 )


class HandlerAccountDelete( enki.HandlerBaseReauthenticate ):
# delete user account

	def get_logged_in( self ):
		data = collections.namedtuple( 'data', 'current_display_name, previous_display_names, email, password, auth_provider, has_posts, has_messages, has_friends, has_product_purchased_unactivated, has_product_activated' )
		current_display_name = ''
		if EnkiModelDisplayName.exist_by_user_id( self.user_id ):
			user_display_name = EnkiModelDisplayName.get_by_user_id_current( self.user_id )
			current_display_name = EnkiModelDisplayName.get_user_id_display_name_url( user_display_name )
		previous_display_names = EnkiModelDisplayName.get_user_display_name_old( self.user_id )
		email = self.enki_user.email if ( self.enki_user.email and self.enki_user.email != 'removed' ) else ''
		password = True if self.enki_user.password else False
		auth_provider = []
		for item in self.enki_user.auth_ids_provider:
			provider_name, provider_uid = item.partition( ':' )[ ::2 ]
			auth_provider.append({ 'provider_name': provider_name, 'provider_uid': str( provider_uid )})
		has_posts = True if EnkiModelPost.fetch_by_author( self.enki_user.key.id()) else False
		has_messages = True if EnkiModelMessage.exist_sent_or_received( self.user_id ) else False
		has_friends = True if EnkiModelFriends.exist_by_user_id( self.user_id ) else False
		has_product_purchased_unactivated = True if EnkiModelProductKey.exist_by_purchaser_not_activated( self.user_id ) else False
		has_product_activated = True if EnkiModelProductKey.exist_by_activator( self.user_id ) else False
		data = data( current_display_name, previous_display_names, email, password, auth_provider, has_posts, has_messages, has_friends, has_product_purchased_unactivated, has_product_activated )
		self.render_tmpl( 'accountdelete.html',
						  active_menu = 'profile',
						  data = data,
						  is_active = True if ( self.account_is_active( self.enki_user.key.id()) or email ) else False )

	def post_reauthenticated( self, params ):
		submit_type = params.get( 'submittype' )
		if submit_type == 'cancel':
			self.redirect( enki.libutil.get_local_url( 'profile' ))
		elif submit_type == 'delete':
			delete_posts = False
			if self.account_is_active( self.enki_user.key.id()):
				has_posts = True if EnkiModelPost.fetch_by_author( self.enki_user.key.id()) else False
				if has_posts and params.get( 'deleteposts' ) == 'on':
					delete_posts = True
			if self.enki_user.email and self.enki_user.email != 'removed':
				# if the user has an email, send a confirmation email
				self.account_deletion_request( delete_posts )
				if delete_posts:
					self.add_infomessage( MSG.INFORMATION(), MSG.ACCOUNT_AND_POSTS_DELETE_INFO_EMAIL_SENT( self.enki_user.email ))
				else:
					self.add_infomessage( MSG.INFORMATION(), MSG.ACCOUNT_DELETE_INFO_EMAIL_SENT( self.enki_user.email ))
			else:
				# otherwise just delete the account
				self.delete_account( delete_posts )
				if delete_posts:
					self.add_infomessage( MSG.SUCCESS(), MSG.ACCOUNT_AND_POSTS_DELETED())
				else:
					self.add_infomessage( MSG.SUCCESS(), MSG.ACCOUNT_DELETED())
			self.redirect( enki.libutil.get_local_url())


class HandlerAccountDeleteConfirm( enki.HandlerBase ):
# do the account deletion

	def get( self, **kwargs ):
		token = kwargs[ 'verifytoken' ]
		delete_posts = False
		tokenExists = EnkiModelTokenVerify.exist_by_token_type( token, 'accountdelete' )
		if not tokenExists:
			tokenExists = EnkiModelTokenVerify.exist_by_token_type( token, 'accountandpostsdelete' )
			if tokenExists:
				delete_posts = True
		if tokenExists:
			result = self.delete_account( delete_posts, token )
			if delete_posts:
				self.add_infomessage( MSG.SUCCESS(), MSG.ACCOUNT_AND_POSTS_DELETED())
			else:
				self.add_infomessage( MSG.SUCCESS(), MSG.ACCOUNT_DELETED())
			self.redirect( enki.libutil.get_local_url())
		else:
			self.abort( 404 )


routes_account = [ webapp2.Route( '/login', HandlerLogin, name = 'login' ),
                   webapp2.Route( '/reauthenticate', HandlerReauthenticate, name = 'reauthenticate' ),
		           webapp2.Route( '/logout', HandlerLogout, name = 'logout' ),
				   webapp2.Route( '/stayloggedin', HandlerStayLoggedIn, name='stayloggedin'),
				   webapp2.Route( '/accountconnect', HandlerAccountConnect, name = 'accountconnect' ),
				   webapp2.Route( '/loginaddconfirm', HandlerLoginAddConfirm, name = 'loginaddconfirm'),
				   webapp2.Route( '/profile', HandlerProfile, name = 'profile' ),
				   webapp2.Route( '/u/<useridnumber>', HandlerProfilePublic, name = 'profilepublic' ),
				   webapp2.Route( '/register', HandlerRegister, name = 'register' ),
				   webapp2.Route( '/rc/<verifytoken>', HandlerRegisterConfirm, name = 'registerconfirm' ),
				   webapp2.Route( '/registeroauthconfirm', HandlerRegisterOAuthConfirm, name = 'registeroauthconfirm' ),
				   webapp2.Route( '/registeroauthwithexistingemail', HandlerRegisterOAuthWithExistingEmail, name = 'registeroauthwithexistingemail' ),
				   webapp2.Route( '/passwordchange', HandlerPasswordChange, name = 'passwordchange' ),
				   webapp2.Route( '/passwordrecover', HandlerPasswordRecover, name = 'passwordrecover' ),
				   webapp2.Route( '/pc/<verifytoken>', HandlerPasswordRecoverConfirm, name = 'passwordrecoverconfirm' ),
		           webapp2.Route( '/displayname', HandlerDisplayName, name = 'displayname' ),
		           webapp2.Route( '/emailchange', HandlerEmailChange, name = 'emailchange' ),
		           webapp2.Route( '/ec/<verifytoken>', HandlerEmailChangeConfirm, name = 'emailchangeconfirm' ),
		           webapp2.Route( '/er/<rollbacktoken>', HandlerEmailRollback, name = 'emailrollback' ),
		           webapp2.Route( '/accountdelete', HandlerAccountDelete, name = 'accountdelete' ),
		           webapp2.Route( '/ad/<verifytoken>', HandlerAccountDeleteConfirm, name = 'accountdeleteconfirm' ),
				   webapp2.Route( '/sessions', HandlerSessions, name = 'sessions' ),
				   ]
