import webapp2
import collections

import settings
import enki
import enki.libutil
import enki.libuser
import enki.libdisplayname
import enki.libforum
import enki.textmessages as MSG
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.modelrestapitokenverify import EnkiModelRestAPITokenVerify


class HandlerLogout( enki.HandlerBase ):

	def get( self ):
		self.log_out()
		self.add_infomessage( 'success', MSG.SUCCESS(), MSG.LOGGED_OUT())
		self.redirect_to_relevant_page()


class HandlerLogin( enki.HandlerBase ):

	def get( self ):
		email = self.request.get( 'email' )
		# Get referal path to return the user to the page they were on after they've logged in
		if 'sessionloginrefpath' in self.session:
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.LOGIN_NEEDED())
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
		email = self.request.get( 'email' )
		if submit_type == 'login':
			password = self.request.get( 'password' )
			if self.log_in_with_email( email, password ):
				self.add_infomessage( 'success', MSG.SUCCESS(), MSG.LOGGED_IN())
				self.redirect_to_relevant_page()
			else:
				error_message = MSG.WRONG_EMAIL_OR_PW()
				if enki.libuser.exist_EnkiUser( email ):
				# if the email exist as part of an Auth account (doesn't have a password), silently email them to set a password.
					user = enki.libuser.get_EnkiUser( email )
					if not user.password:
						self.add_debugmessage( '''Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.''' )
						link = enki.libutil.get_local_url( 'passwordrecover', { 'email': email })
						self.send_email( email, MSG.SEND_EMAIL_LOGIN_ATTEMPT_WITH_YOUR_EMAIL_NO_PW_SUBJECT( ), MSG.SEND_EMAIL_LOGIN_ATTEMPT_WITH_YOUR_EMAIL_NO_PW_BODY( link, email ))
				backoff_timer = self.get_backoff_timer( email )
				if backoff_timer != 0:
					error_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ))
				self.render_tmpl( 'login.html',
				                  active_menu = 'login',
				                  authhandlers = settings.HANDLERS,
				                  email = email,
				                  error = error_message )
		elif submit_type == 'register':
			self.redirect( enki.libutil.get_local_url( 'register', { 'email': email }))
		else:
			self.redirect( enki.libutil.get_local_url( 'passwordrecover', { 'email': email }))


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
						self.add_infomessage( 'success', MSG.SUCCESS(), MSG.REAUTHENTICATED())
						self.redirect_to_relevant_page()
					else:
						error_message = MSG.WRONG_EMAIL_OR_PW()
						backoff_timer = self.get_backoff_timer( self.enki_user.email )
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
					self.redirect( enki.libutil.get_local_url( 'passwordrecover', { 'email': self.enki_user.email }))


class HandlerConnectedAccounts( enki.HandlerBaseReauthenticate ):

	def get_reauthenticated( self ):
		data = collections.namedtuple( 'data', 'email, allow_change_pw, auth_providers, enough_accounts' )

		email = self.enki_user.email
		allow_change_pw = True
		if ( not email or email == 'removed' ) and not self.enki_user.password:
			allow_change_pw = False

		auth_providers = []
		providers_temp_list = []    # temp list of providers the user registered or blocked
		for item in self.enki_user.auth_ids_provider:   # registered, unblocked providers
			colon = item.find( ':' )
			provider_name = str( item[ :colon ])
			if provider_name not in self.enki_user.auth_ids_provider_blocked:
				auth_providers.append({ 'provider_name': provider_name, 'provider_uid': str( item[ colon+1: ]), 'status': 'registered'})
				providers_temp_list.append( provider_name )
		for item in self.enki_user.auth_ids_provider_blocked:   # blocked providers
			provider_name = str( item )
			auth_providers.append({ 'provider_name': provider_name, 'provider_uid': 'n/a', 'status': 'blocked'})
			providers_temp_list.append( provider_name )
		for item in settings.HANDLERS:   # remaning providers
			provider = item.get_provider_name()
			if provider not in providers_temp_list:
				auth_providers.append({ 'provider_name': provider, 'provider_uid': 'n/a', 'status': 'unregistered'})

		enough_accounts = self.has_enough_accounts()

		data = data( email, allow_change_pw, auth_providers, enough_accounts )
		self.render_tmpl( 'connectedaccounts.html',
		                  active_menu = 'profile',
		                  data = data )

	def post_reauthenticated( self, params ):
		block = params.get( 'block' )
		unblock = params.get( 'unblock' )
		# register = params.get( 'register' ) # TODO
		deregister = params.get( 'deregister' )
		if block and block not in self.enki_user.auth_ids_provider_blocked:
			self.enki_user.auth_ids_provider_blocked.append( block )
			self.enki_user.put()
			self.add_infomessage( 'success', MSG.SUCCESS( ), 'blocked') #MSG.AUTH_PROVIDER_BLOCKED( block )) # TODO
		if unblock and unblock in self.enki_user.auth_ids_provider_blocked:
			self.enki_user.auth_ids_provider_blocked.remove( unblock )
			self.enki_user.put()
			self.add_infomessage( 'success', MSG.SUCCESS( ), 'unblocked') #MSG.AUTH_PROVIDER_UNBLOCKED( unblock )) #TODO
		if deregister:
			self.remove_authid( deregister )
			provider_name = str( deregister[ :deregister.find( ':' )])
			self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.AUTH_METHOD_REMOVED( provider_name ))

		self.redirect( enki.libutil.get_local_url( 'connectedaccounts' ))


class HandlerProfile( enki.HandlerBaseReauthenticate ):

	def get_reauthenticated( self ):
		data = collections.namedtuple( 'data', 'current_display_name, previous_display_names, email, auth_provider, enough_accounts, allow_change_pw, sessions, sessions_app' )

		current_display_name = ''
		previous_display_names = ''
		user_display_name = enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( self.user_id )
		if user_display_name:
			current_display_name = enki.libdisplayname.get_user_id_display_name_url( user_display_name )
			previous_display_names = enki.libdisplayname.get_user_display_name_old( self.user_id )

		email = self.enki_user.email
		allow_change_pw = True
		if ( not email or email == 'removed' ) and not self.enki_user.password:
			allow_change_pw = False

		auth_provider = []
		for item in self.enki_user.auth_ids_provider:
			colon = item.find( ':' )
			auth_provider.append({ 'provider_name': str( item[ :colon ]), 'provider_uid': str( item[ colon+1: ])})
		enough_accounts = self.has_enough_accounts()

		sessions = []
		current_token = self.session.get( 'auth_token' )
		auth_tokens = enki.libuser.fetch_AuthTokens( self.user_id )
		for item in auth_tokens:
			current = False
			if current_token == item.token:
				current = True
			sessions.append({ 'tokenauth_id' : item.key.id(), 'time_created' : item.time_created, 'current' : current })

		sessions_app = []
		list = EnkiModelRestAPITokenVerify.fetch_by_user_id_type( user_id = self.user_id, type = 'apiconnect' )
		for item in list:
			sessions_app.append({ 'token_id' : item.key.id(), 'time_created' : item.time_created })

		data = data( current_display_name, previous_display_names, email, auth_provider, enough_accounts, allow_change_pw, sessions, sessions_app )
		self.render_tmpl( 'profile.html',
		                  active_menu = 'profile',
		                  data = data )

	def post( self ):
		remove_account = self.request.get( 'remove' )
		if remove_account:  # requires reauthentication:
			enki.HandlerBaseReauthenticate.post( self )
		else:
			if self.ensure_is_logged_in():
				self.check_CSRF()
				disconnect_session_token = self.request.get( 'disconnect' )
				disconnect_app_token = self.request.get( 'disconnect_app' )
				if disconnect_session_token:
					enki.libuser.delete_session_token_auth( disconnect_session_token )
					self.add_infomessage( 'success', MSG.SUCCESS(), MSG.DISCONNECTED_SESSION())
				elif disconnect_app_token:
					EnkiModelRestAPITokenVerify.delete_token_by_id( disconnect_app_token )
					self.add_infomessage( 'success', MSG.SUCCESS(), MSG.DISCONNECTED_APP())
				self.redirect( enki.libutil.get_local_url( 'profile' ))

	def post_reauthenticated( self, params ):
		remove_account = params.get( 'remove' )
		if remove_account:
			self.remove_authid( remove_account )
			provider_name = str( remove_account[ :remove_account.find( ':' )])
			self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.AUTH_METHOD_REMOVED( provider_name ))
		self.redirect( enki.libutil.get_local_url( 'profile' ))


class HandlerProfilePublic( enki.HandlerBase ):

	def get( self, useridnumber ):
		if self.ensure_is_logged_in():
			display_name_data = None
			if useridnumber.isdigit and enki.libuser.EnkiModelUser.get_by_id( int( useridnumber )):
				display_name_data = enki.libdisplayname.get_display_name_data( int( useridnumber ))
			else:
				self.add_infomessage( 'info', MSG.INFORMATION(), MSG.USER_NOT_EXIST())
			self.render_tmpl( 'profilepublic.html', False,
			                  active_menu = 'home',
			                  display_name_data = display_name_data )


class HandlerRegister( enki.HandlerBase ):

	def get( self ):
		email = self.request.get( 'email' )
		# Get referal path to return the user to the page they were on after they've logged in using auth
		self.session[ 'sessionrefpath' ] = self.request.referrer
		self.render_tmpl( 'register.html',
		                  active_menu = 'register',
		                  authhandlers = settings.HANDLERS,
		                  email = email )

	def post( self ):
		self.check_CSRF()
		submit_type = self.request.get( 'submittype' )
		email = self.request.get( 'email' )
		if submit_type == 'register':
			result = self.email_set_request( email )
			error_message = ''
			if result == enki.libutil.ENKILIB_OK or result == enki.handlerbase.ERROR_EMAIL_IN_USE:
			# if email exists, pretend there was a registration (i.e. hide the fact that the email exists) to prevent email checking
				self.add_infomessage( 'info', MSG.INFORMATION(), MSG.REGISTRATION_INFO_EMAIL_SENT( email ))
				if result == enki.handlerbase.ERROR_EMAIL_IN_USE:
					self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
					link = enki.libutil.get_local_url( 'passwordrecover', { 'email': email } )
					self.send_email( email, MSG.SEND_EMAIL_REGISTER_ATTEMPT_WITH_YOUR_EMAIL_SUBJECT(), MSG.SEND_EMAIL_REGISTER_ATTEMPT_WITH_YOUR_EMAIL_BODY( link, email ))
				self.redirect_to_relevant_page()
				return
			else:
				if result == enki.libuser.ERROR_EMAIL_FORMAT_INVALID:
					error_message = MSG.WRONG_EMAIL_FORMAT()
				elif result == enki.libuser.ERROR_EMAIL_MISSING:
					error_message = MSG.MISSING_EMAIL()
				self.render_tmpl( 'register.html',
				                  active_menu = 'register',
				                  authhandlers = settings.HANDLERS,
				                  email = email,
				                  error = error_message )
		elif submit_type == 'login':
			self.redirect( enki.libutil.get_local_url( 'login', { 'email': email } ) )
		else:
			self.redirect( enki.libutil.get_local_url( 'passwordrecover', { 'email': email } ) )


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
			result = enki.libuser.validate_password( password )
			link = enki.libutil.get_local_url( 'registerconfirm', { 'verifytoken': token } )
			if result == enki.libutil.ENKILIB_OK:
				result = self.create_user_from_email_pw( email, password )
				if result == enki.libutil.ENKILIB_OK:
					self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.ACCOUNT_CREATED())
					self.log_in_with_email( email, password )
					self.redirect_to_relevant_page()
				elif result == enki.handlerbase.ERROR_USER_NOT_CREATED:
					error_message = MSG.FAIL_REGISTRATION()
					self.render_tmpl( 'register.html',
					                  active_menu = 'register',
					                  email = email,
					                  error = error_message )
			else:
				error_message = ''
				if result == enki.libuser.ERROR_PASSWORD_BLANK:
					error_message = MSG.MISSING_PW()
				elif result == enki.libuser.ERROR_PASSWORD_TOO_SHORT :
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
# create or edit user based on auth login info
	def get( self ):
		token = self.session.get( 'tokenregisterauth' )
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'register' )
		if tokenEntity:
			colon = tokenEntity.auth_ids_provider.find( ':' )
			provider_name = str( tokenEntity.auth_ids_provider[ :colon ])
			provider_uid = str( tokenEntity.auth_ids_provider[ colon+1: ])
			self.render_tmpl( 'registeroauthconfirm.html',
			                  active_menu = 'register',
			                  token = tokenEntity,
			                  provider_name = provider_name,
			                  provider_uid = provider_uid )
		else:
			self.abort( 404 )

	def post( self ):
		choice = self.request.get( 'choice' )
		# step 1
		if choice == 'create' or choice == 'cancel':
			token = self.session.get( 'tokenregisterauth' )
			tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'register' )
			authId = tokenEntity.auth_ids_provider
			colon = authId.find( ':' )
			provider_name = str( authId[ :colon ])
			provider_uid = str( authId[ colon+1: ])
			auth_email = tokenEntity.email if tokenEntity.email else None
			if choice == 'create':
				if auth_email: # if the email is given by the provider, it is verified. Create the account.
					user = self.get_or_create_user_from_authid( authId, auth_email, allow_create = True )
					if user: # login the user through auth
						self.log_in_session_token_create( user )
						self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.LOGGED_IN())
					else: # user creation failed (timeout etc.)
						self.add_infomessage( 'warning', MSG.WARNING(), MSG.AUTH_LOGIN_FAILED( provider_name ))
					self.redirect_to_relevant_page()
					tokenEntity.key.delete()
					tokenEntity.key.delete()
					self.session.pop( 'tokenregisterauth' )
				else: # if the email isn't given by the provider, use the manually entered email.
					self.check_CSRF()
					email = self.request.get( 'email' )
					user = self.get_or_create_user_from_authid( authId, allow_create = True )
					self.log_in_session_token_create( user )
					error_message = ''
					success = False
					result = enki.libuser.validate_email( email )
					if result == enki.libutil.ENKILIB_OK:
						result = self.email_change_request( email )
						# send an email for verification. Since it's not verified at this point, create the account without the email.
						self.add_infomessage( 'info', MSG.INFORMATION(), MSG.REGISTER_AUTH_ADD_EMAIL_INFO_EMAIL_SENT( email ) )
						if result == enki.handlerbase.ERROR_EMAIL_IN_USE:
							self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
						success = True
						tokenEntity.key.delete()
						self.session.pop( 'tokenregisterauth' )
					elif result == enki.libuser.ERROR_EMAIL_FORMAT_INVALID:
							error_message = MSG.WRONG_EMAIL_FORMAT()
					elif result == enki.libuser.ERROR_EMAIL_MISSING:
							error_message = MSG.MISSING_EMAIL()
					self.render_tmpl( 'registeroauthconfirm.html',
					                  active_menu = 'register',
					                  token = tokenEntity,
					                  provider_name = provider_name,
					                  provider_uid = provider_uid,
					                  error = error_message,
					                  success = success )
			elif choice == 'cancel':
				self.add_infomessage( 'info', MSG.INFORMATION(), MSG.REGISTRATION_ABORT())
				self.redirect_to_relevant_page()
				tokenEntity.key.delete()
				self.session.pop( 'tokenregisterauth' )
		# step 2 (those choices will only be presented to the user if they successfully added an email manually).
		elif choice == 'continue':
			self.redirect_to_relevant_page()
		elif choice == 'profile':
			url = enki.libutil.get_local_url( 'profile' )
			self.session[ 'sessionrefpath' ] = url
			self.redirect( url )


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
				result = enki.libuser.set_password( self.enki_user, password_new )
				if result == enki.libutil.ENKILIB_OK:
					self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.PASSWORD_UPDATED())
					self.redirect( enki.libutil.get_local_url( 'profile' ) )
					return
				else:
					if result == enki.libuser.ERROR_PASSWORD_BLANK:
						error_passwordnew_message = MSG.MISSING_NEW_PW()
					elif result == enki.libuser.ERROR_PASSWORD_TOO_SHORT :
						length = len( password_new )
						error_passwordnew_message = " ".join( [ MSG.PW_TOO_SHORT( length ), MSG.PW_ENSURE_MIN_LENGTH(
							self.app.config.get( 'enki' ).get( 'user' ).get( 'PASSWORD_LENGTH_MIN' ) ) ] )
			else:
				error_password_message = MSG.WRONG_PW()
				backoff_timer = self.get_backoff_timer( email )
				if backoff_timer != 0:
					error_password_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ) )
			self.render_tmpl( 'passwordchange.html',
			                  active_menu = 'profile',
			                  error_password = error_password_message,
			                  error_passwordnew = error_passwordnew_message )


class HandlerPasswordRecover( enki.HandlerBase ):
# change password - user can't log in so email them

	def get( self ):
		email = self.request.get( 'email' )
		if not email and self.is_logged_in():
			email = self.enki_user.email
		self.render_tmpl( 'passwordrecover.html',
		                  email = email )

	def post( self ):
		self.check_CSRF()
		submit_type = self.request.get( 'submittype' )
		email = self.request.get( 'email' )
		if submit_type == 'recoverpass':
			result = enki.libuser.validate_email( email )
			error_message = ''
			if result == enki.libutil.ENKILIB_OK:
				result = self.password_change_request( email )
				if result == enki.libutil.ENKILIB_OK or result == enki.handlerbase.ERROR_EMAIL_NOT_EXIST:
					# The info displayed is identical whether the email corresponds to an existing account or not to prevent email checking.
					self.add_infomessage( 'info' , MSG.INFORMATION(), MSG.PASSWORD_RESET_INFO_EMAIL_SENT( email ))
					if result == enki.handlerbase.ERROR_EMAIL_NOT_EXIST:
						self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
					self.redirect_to_relevant_page()
					return
			elif result == enki.libuser.ERROR_EMAIL_FORMAT_INVALID:
				error_message = MSG.WRONG_EMAIL_FORMAT()
			elif result == enki.libuser.ERROR_EMAIL_MISSING:
				error_message = MSG.MISSING_EMAIL()
			self.render_tmpl( 'passwordrecover.html',
			                  email = email,
			                  error = error_message )
		elif submit_type == 'login':
			self.redirect( enki.libutil.get_local_url( 'login', { 'email': email } ) )
		else:
			self.redirect( enki.libutil.get_local_url( 'register', { 'email': email } ) )


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
			user = enki.libuser.get_EnkiUser( email )
			if user:
				password = self.request.get( 'password' )
				result = enki.libuser.set_password( user, password )
				if result == enki.libutil.ENKILIB_OK:
					enki.libuser.delete_verifytoken_by_email( email, 'passwordchange' )
					self.log_in_with_id( user.key.id(), password )
					self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.PASSWORD_SET())
					self.redirect( enki.libutil.get_local_url( 'profile' ) )
					return
				else:
					error_message = ''
					if result == enki.libuser.ERROR_PASSWORD_BLANK :
						error_message = MSG.MISSING_PW()
					elif result == enki.libuser.ERROR_PASSWORD_TOO_SHORT :
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

	def get_reauthenticated( self ):
		self.session[ 'sessiondisplaynamerefpath' ] = self.session.pop( 'sessiondisplaynamerefpath', self.request.referrer )
		self.session[ 'sessionreauth' ] = self.session[ 'sessiondisplaynamerefpath' ]
		auto_generated = ''
		intro_message = ''
		if not enki.libdisplayname.exist_EnkiUserDisplayName_by_user_id( self.user_id ):
			# if no displayname exists, auto-generate one
			auto_generated = enki.libdisplayname.cosmopompe()[ 0 ]
			intro_message = " ".join([ MSG.DISPLAY_NAME_INTRO(), MSG.DISPLAY_NAME_AUTO_GENERATED()])
		self.render_tmpl( 'displayname.html',
		                  active_menu = 'profile',
		                  auto_generated = auto_generated,
		                  intro = intro_message,
		                  data = enki.libdisplayname.get_display_name_data( self.user_id ),
		                  prefix_length_min = enki.libdisplayname.PREFIX_LENGTH_MIN,
		                  prefix_length_max = enki.libdisplayname.PREFIX_LENGTH_MAX )

	def post_reauthenticated( self, params ):
		prefix = params.get( 'prefix' )
		error_message = ''
		result = enki.libdisplayname.make_unique_and_set_display_name( self.user_id, prefix )
		if result == enki.libutil.ENKILIB_OK:
			self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.DISPLAYNAME_SET())
			self.session[ 'sessiondisplaynamerefpath' ] = self.session.pop( 'sessionreauth', self.request.referrer )
			self.redirect_to_relevant_page()
			return
		else:
			if result == enki.libdisplayname.ERROR_DISPLAY_NAME_LENGTH:
				length = len( prefix )
				instruction = ''
				if length < enki.libdisplayname.PREFIX_LENGTH_MIN:
					instruction = MSG.DISPLAY_NAME_TOO_SHORT_LENGTHEN( enki.libdisplayname.PREFIX_LENGTH_MIN )
				elif length > enki.libdisplayname.PREFIX_LENGTH_MAX:
					instruction = MSG.DISPLAY_NAME_TOO_LONG_SHORTEN( enki.libdisplayname.PREFIX_LENGTH_MAX )
				error_message = " ".join([ MSG.DISPLAY_NAME_WRONG_LENGTH( length ), instruction ])
			elif result == enki.libdisplayname.ERROR_DISPLAY_NAME_ALNUM:
				error_message = MSG.DISPLAY_NAME_WRONG_SYMBOLS()
			elif result == enki.libdisplayname.ERROR_DISPLAY_NAME_IN_USE:
				error_message = MSG.DISPLAY_NAME_ALREADY_USED()
			self.render_tmpl( 'displayname.html',
			                  active_menu = 'profile',
			                  prefix = prefix,
			                  data = enki.libdisplayname.get_display_name_data( self.user_id ),
			                  prefix_length_min = enki.libdisplayname.PREFIX_LENGTH_MIN,
			                  prefix_length_max = enki.libdisplayname.PREFIX_LENGTH_MAX,
			                  error = error_message )


class HandlerEmailChange( enki.HandlerBaseReauthenticate ):
# user requests an email change. Current email stored in rollback db

	def get_reauthenticated( self ):
		self.render_tmpl( 'emailchange.html',
		                  active_menu = 'profile' )

	def post_reauthenticated( self, params ):
		email = params.get( 'email' )
		old_email_existed = True if ( self.enki_user.email and self.enki_user.email != 'removed' ) else False
		result = enki.libuser.validate_email( email )
		error_message = ''
		if result == enki.libutil.ENKILIB_OK or result == enki.libuser.ERROR_EMAIL_MISSING:
			result_of_change_request = self.email_change_request( email )
			if result_of_change_request == 'same':
				error_message = MSG.CURRENT_EMAIL()
			elif result_of_change_request == 'cannot_remove':
				error_message = MSG.CANNOT_DELETE_EMAIL()
			elif result_of_change_request == 'removed':
				self.add_infomessage( 'success', MSG.SUCCESS(), MSG.EMAIL_REMOVED())
				if old_email_existed:
					self.add_infomessage( 'info', MSG.INFORMATION(), MSG.EMAIL_ROLLBACK_INFO_EMAIL_SENT())
				self.redirect( enki.libutil.get_local_url( 'profile' ))
			elif result_of_change_request == 'change' or result_of_change_request == enki.handlerbase.ERROR_EMAIL_IN_USE:
				self.add_infomessage( 'info', MSG.INFORMATION(), MSG.EMAIL_CHANGE_CONFIRM_INFO_EMAIL_SENT( email ))
				if self.enki_user.email and self.enki_user.email != 'removed':
					self.add_infomessage( 'info', MSG.INFORMATION(), MSG.EMAIL_CHANGE_UNDO_INFO_EMAIL_SENT())
				self.redirect( enki.libutil.get_local_url( 'profile' ))
				return
		elif result == enki.libuser.ERROR_EMAIL_FORMAT_INVALID:
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
			self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.EMAIL_SET())
			self.redirect( enki.libutil.get_local_url( 'profile' ) )
		else:
			self.abort( 404 )


class HandlerEmailRollback( enki.HandlerBase ):
# rollback to an older email

	def get( self, **kwargs ):
		token = kwargs[ 'rollbacktoken' ]
		tokenEntity = enki.libuser.get_RollbackToken_by_token( token )
		if tokenEntity:
			self.email_rollback( tokenEntity )
			self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.EMAIL_RESTORED())
			self.redirect( enki.libutil.get_local_url( 'profile' ) )
		else:
			self.abort( 404 )


class HandlerAccountDelete( enki.HandlerBase ):
# delete user account

	def get( self ):
		if self.ensure_is_logged_in():
			data = collections.namedtuple( 'data', 'current_display_name, previous_display_names, email, password, auth_provider, has_posts, has_messages, has_friends' )
			current_display_name = ''
			if enki.libdisplayname.exist_EnkiUserDisplayName_by_user_id( self.user_id ):
				user_display_name = enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( self.user_id )
				current_display_name = enki.libdisplayname.get_user_id_display_name_url( user_display_name )
			previous_display_names = enki.libdisplayname.get_user_display_name_old( self.user_id )
			email = self.enki_user.email
			password = True if self.enki_user.password else False
			auth_provider = []
			for item in self.enki_user.auth_ids_provider:
				colon = item.find( ':' )
				auth_provider.append({ 'provider_name': str( item[ :colon ]), 'provider_uid': str( item[ colon+1: ])})
			has_posts = True if enki.libforum.fetch_EnkiPost_by_author( self.enki_user.key.id( ) ) else False
			has_messages = 'debug c'
			has_friends = 'debug d'
			data = data( current_display_name, previous_display_names, email, password, auth_provider, has_posts, has_messages, has_friends )
			self.render_tmpl( 'accountdelete.html',
			                  active_menu = 'profile',
			                  data = data,
			                  is_active = True if enki.HandlerBase.account_is_active( self.enki_user.key.id( ) ) else False )

	def post( self ):
		if self.ensure_is_logged_in():
			self.check_CSRF()
			submit_type = self.request.get( 'submittype' )
			if submit_type == 'cancel':
				self.redirect( enki.libutil.get_local_url( 'profile' ) )
			elif submit_type == 'delete':
				delete_posts = False
				if enki.HandlerBase.account_is_active( self.enki_user.key.id( ) ):
					has_posts = True if enki.libforum.fetch_EnkiPost_by_author( self.enki_user.key.id( ) ) else False
					if has_posts and self.request.get( 'deleteposts' ) == 'on':
						delete_posts = True
				if self.enki_user.email and self.enki_user.email != 'removed':
					# if the user has an email, send a confirmation email
					self.account_deletion_request( delete_posts )
					if delete_posts:
						self.add_infomessage( 'info', MSG.INFORMATION(), MSG.ACCOUNT_AND_POSTS_DELETE_INFO_EMAIL_SENT( self.enki_user.email ))
					else:
						self.add_infomessage( 'info', MSG.INFORMATION(), MSG.ACCOUNT_DELETE_INFO_EMAIL_SENT( self.enki_user.email ))
				else:
					# otherwise just delete the account
					self.delete_account( delete_posts )
					if delete_posts:
						self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.ACCOUNT_AND_POSTS_DELETED())
					else:
						self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.ACCOUNT_DELETED())
				self.redirect( enki.libutil.get_local_url( ) )


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
				self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.ACCOUNT_AND_POSTS_DELETED())
			else:
				self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.ACCOUNT_DELETED())
			self.redirect( enki.libutil.get_local_url( ) )
		else:
			self.abort( 404 )


routes_account = [ webapp2.Route( '/login', HandlerLogin, name = 'login' ),
                   webapp2.Route( '/reauthenticate', HandlerReauthenticate, name = 'reauthenticate' ),
		           webapp2.Route( '/logout', HandlerLogout, name = 'logout' ),
		           webapp2.Route( '/connectedaccounts', HandlerConnectedAccounts, name = 'connectedaccounts' ),
				   webapp2.Route( '/profile', HandlerProfile, name = 'profile' ),
				   webapp2.Route( '/u/<useridnumber>', HandlerProfilePublic, name = 'profilepublic' ),
				   webapp2.Route( '/register', HandlerRegister, name = 'register' ),
				   webapp2.Route( '/rc/<verifytoken>', HandlerRegisterConfirm, name = 'registerconfirm' ),
				   webapp2.Route( '/registeroauthconfirm', HandlerRegisterOAuthConfirm, name = 'registeroauthconfirm' ),
				   webapp2.Route( '/passwordchange', HandlerPasswordChange, name = 'passwordchange' ),
				   webapp2.Route( '/passwordrecover', HandlerPasswordRecover, name = 'passwordrecover' ),
				   webapp2.Route( '/pc/<verifytoken>', HandlerPasswordRecoverConfirm, name = 'passwordrecoverconfirm' ),
		           webapp2.Route( '/displayname', HandlerDisplayName, name = 'displayname' ),
		           webapp2.Route( '/emailchange', HandlerEmailChange, name = 'emailchange' ),
		           webapp2.Route( '/ec/<verifytoken>', HandlerEmailChangeConfirm, name = 'emailchangeconfirm' ),
		           webapp2.Route( '/er/<rollbacktoken>', HandlerEmailRollback, name = 'emailrollback' ),
		           webapp2.Route( '/accountdelete', HandlerAccountDelete, name = 'accountdelete' ),
		           webapp2.Route( '/ad/<verifytoken>', HandlerAccountDeleteConfirm, name = 'accountdeleteconfirm' ),
				   ]
