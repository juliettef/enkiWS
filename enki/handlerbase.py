import datetime
import random
import re
import urlparse
import webapp2

from google.appengine.api import app_identity
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import ndb
from jinja2.runtime import TemplateNotFound
from webapp2_extras import i18n
from webapp2_extras import jinja2
from webapp2_extras import security
from webapp2_extras import sessions
from webapp2_extras import sessions_ndb

import enki.libdisplayname
import enki.libforum
import enki.libfriends
import enki.libmessage
import enki.libuser
import enki.libutil
import enki.libdisplayname
import enki.librestapi
import enki.modeltokenverify
from enki import textmessages as MSG
from enki.modelbackofftimer import EnkiModelBackoffTimer
from enki.modeltokenauth import EnkiModelTokenAuth
from enki.modeltokenemailrollback import EnkiModelTokenEmailRollback
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.modeluser import EnkiModelUser


ERROR_EMAIL_IN_USE = -13
ERROR_EMAIL_NOT_EXIST = -14
ERROR_USER_NOT_CREATED = -31

LOCALES = [ 'en_US', 'en_EN', 'fr_FR' ]


class HandlerBase( webapp2.RequestHandler ):


	def __init__( self, request, response ):
		self.initialize( request, response )
		self.just_logged_in = False
		self.just_checked_CSRF = False


	def dispatch( self ): # https://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
		self.session_store = sessions.get_store( request = self.request )
		locale = self.request.GET.get( 'locale' )
		if locale ==  'en_US': # default locale
			locale = ''
		elif locale not in LOCALES:
			locale = self.session.get( 'locale' )
			if locale not in LOCALES:
				locale = ''
		i18n.get_i18n().set_locale( locale )
		self.session[ 'locale' ] = locale
		try:
			webapp2.RequestHandler.dispatch( self )
		finally:
			self.session_store.save_sessions( self.response )


	@webapp2.cached_property
	def session( self ): #  https://webapp-improved.appspot.com/api/webapp2_extras/sessions.html
		return self.session_store.get_session( backend = 'datastore' )


	@webapp2.cached_property
	def jinja2( self ): # Returns a Jinja2 renderer cached in the app registry
		return jinja2.get_jinja2( app = self.app )


	@webapp2.cached_property
	def domain_name( self ):
		return self.uri_for( 'home', _full = True )


	@webapp2.cached_property
	def user_id( self ): # The currently logged in user
		return self.session.get( 'user_id' )


	def create_CSRF( self, form_name ):    # protect against forging login requests http://en.wikipedia.org/wiki/Cross-site_request_forgery http://www.ethicalhack3r.co.uk/login-cross-site-request-forgery-csrf/
		# check if the CSRF token for this form already exists, if so reuse it. Otherwise create a new one and add it to the dictionary
		sessionCSRFs = self.session.get( 'CSRF' )
		if not sessionCSRFs:
			sessionCSRFs = {}
		sessionCSRF = sessionCSRFs.get( form_name )
		if sessionCSRF:
			CSRFToken = sessionCSRF
		else:
			random = security.generate_random_string( entropy=256 ).encode( 'utf-8' )
			CSRFToken = ( random )
			sessionCSRFs.update({ form_name : CSRFToken })
			self.session[ 'CSRF' ] = sessionCSRFs
		return form_name + '-' + CSRFToken


	def check_CSRF( self, query_name = 'CSRF' ):    # protect against forging login requests http://en.wikipedia.org/wiki/Cross-site_request_forgery http://www.ethicalhack3r.co.uk/login-cross-site-request-forgery-csrf/
		if self.just_checked_CSRF:
			return
		if 'CSRF' in self.session:
			request_token = self.request.get( query_name ).rsplit( '-', 1 )
			form_name = request_token[ 0 ]
			CSRFToken = request_token[ 1 ]
			sessionCSRFs = self.session.get( 'CSRF' )
			sessionCSRF = sessionCSRFs.get( form_name )
			if sessionCSRF == CSRFToken and CSRFToken:
				del self.session[ 'CSRF' ][ form_name ]
				self.just_checked_CSRF = True
				return
		self.redirect_to_relevant_page()


	def is_logged_in( self ):   # returns true if a session exists and corresponds to a logged in user (i.e. a user with a valid auth token)
		# get session info
		if self.just_logged_in:
			return True
		token = self.session.get( 'auth_token' )
		if enki.libuser.exist_AuthToken( self.user_id, token ):
			return True
		else:
			return False


	def ensure_is_logged_in( self ):       # force the user out if not logged in
		if not self.is_logged_in():
			self.session[ 'sessionloginrefpath' ] = self.request.url # get referal path to return the user to it after they've logged in
			self.redirect( enki.libutil.get_local_url( 'login' ) )
			return False
		return True


	def ensure_has_display_name( self, url = None ):    # user must set their display_name to continue
		user_display_name = enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( self.user_id )
		if not user_display_name:
			if not url:
				url = self.request.url
			self.session[ 'sessiondisplaynamerefpath' ] = url # get referal path to return the user to it after they've set their display name
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.DISPLAYNAME_NEEDED())
			self.redirect( enki.libutil.get_local_url( 'displayname' ) )
			return False
		return True


	def get_backoff_timer( self, identifier, increment = False ):
		if self.exist_backoff_timer( identifier ):
			entity = self.get_backofftimer( identifier )
			result = entity.last_failure - datetime.datetime.now() + entity.backoff_duration
			if result <= datetime.timedelta( 0 ):
				# inactive backoff timer. Increase the delay.
				if increment:
					entity.backoff_duration += entity.backoff_duration
					entity.last_failure = datetime.datetime.now()
					entity.put()
				return 0
			else:
				return result
		else:
			if increment:
				self.add_backoff_timer( identifier )
			return 0


	def add_backoff_timer( self, identifier ):
		if not self.exist_backoff_timer( identifier ):
			entity = EnkiModelBackoffTimer( identifier = identifier,
			                                last_failure = datetime.datetime.now(),
			                                backoff_duration = datetime.timedelta( milliseconds = 15 ))
			entity.put()


	def remove_backoff_timer( self, identifier ):
		entity = EnkiModelBackoffTimer.query( EnkiModelBackoffTimer.identifier == identifier ).get()
		if entity:
			entity.key.delete()


	def get_backofftimer( self, identifier ):
		entity = EnkiModelBackoffTimer.query( EnkiModelBackoffTimer.identifier == identifier ).get()
		return entity


	def exist_backoff_timer( self, identifier ):
		count = EnkiModelBackoffTimer.query( EnkiModelBackoffTimer.identifier == identifier ).count( 1 )
		return count > 0


	def fetch_old_backoff_timers( self, days_old ):
		list = EnkiModelBackoffTimer.query( EnkiModelBackoffTimer.last_failure <= (datetime.datetime.now( ) - datetime.timedelta( days = days_old )) ).fetch( keys_only = True )
		return list


	def log_in_with_id( self, userId, password ):
	# log the user in using their Id
		enkiKey = ndb.Key( EnkiModelUser, userId )
		if enkiKey:
			user = enkiKey.get()
			if self.get_backoff_timer( user.email, True ) == 0:
				validPassword = enki.authcryptcontext.pwd_context.verify( password, user.password )
				if validPassword:
					self.log_in_session_token_create( user )
					self.remove_backoff_timer( user.email )
					return True
		return False


	def log_in_with_email( self, email, password ):
	# log the user in using their email
		if self.get_backoff_timer( email, True ) == 0:
			user = enki.libuser.get_EnkiUser( email )
			if user and user.password:
				validPassword = enki.authcryptcontext.pwd_context.verify( password, user.password )
				if validPassword:
					self.log_in_session_token_create( user )
					self.remove_backoff_timer( user.email )
					return True
		return False


	def log_in_session_token_create( self, user ):
		# generate authentication token and add it to the db and the session
		token = security.generate_random_string( entropy = 128 )
		authtoken = EnkiModelTokenAuth( token = token, user_id = user.key.id() )
		authtoken.put()
		self.session[ 'auth_token' ] = token
		self.session[ 'user_id' ] = user.key.id()
		self.just_logged_in = True


	def log_out( self ):
	# log out the currently logged in user
		if self.is_logged_in():
			token = self.session.get( 'auth_token' )
			tokenEntity = enki.libuser.get_AuthToken( self.user_id, token )
			if tokenEntity:
				# delete the token from the db
				tokenEntity.key.delete()
			#delete the session
			self.session.clear()
			self.just_logged_in = False


	@webapp2.cached_property
	def enki_user( self ):
	# get the user instance
		if self.is_logged_in():
			enkiKey = ndb.Key( EnkiModelUser, self.user_id )
			return enkiKey.get()
		else:
			return None


	def render_tmpl( self, template_file, CSRFneeded = True, **kwargs ):
	# render an html template with data using jinja2
		try:
			navbar_items = enki.ExtensionLibrary.get_navbar_items()
			navbar_extensions = enki.ExtensionLibrary.get_navbar_extensions( self )
			page_extensions = enki.ExtensionLibrary.get_page_extensions( self )
			display_name = enki.libdisplayname.get_display_name( self.user_id ) if self.is_logged_in( ) else ''
			CSRFtoken = ''
			if CSRFneeded:
				CSRFtoken = self.create_CSRF( self.request.path )
			self.response.write( self.jinja2.render_template(
									template_file,
									request_url = self.request.url,
									CSRFtoken = CSRFtoken,
				                    is_logged_in = self.is_logged_in(),
									navbar_items = navbar_items,
									page_extensions = page_extensions,
									navbar_extensions = navbar_extensions,
									display_name = display_name,
									locale = i18n.get_i18n().locale,
				                    debug = self.session.pop( 'debugmessage', None ) if enki.libutil.is_debug else None,
				                    infomessage = self.session.pop( 'infomessage', None ),
									deleted_post = enki.libforum.POST_DELETED,
									deleted_post_display = MSG.POST_DELETED_DISPLAY(),
									deleted_dn = enki.libdisplayname.DELETED_PREFIX + enki.libdisplayname.DELETED_SUFFIX,
									deleted_dn_display = MSG.DISPLAY_NAME_DELETED_DISPLAY(),
				                    **kwargs ))
		except TemplateNotFound:
			self.abort( 404 )


	def add_debugmessage( self, message_body ):
		if enki.libutil.is_debug():
			self.session[ 'debugmessage' ] = self.session.pop( 'debugmessage', '' ) + message_body + '<hr>'


	def add_infomessage( self, message_type, message_header, message_body ):
	# reference: http://bootswatch.com/flatly/#indicators
	# message_type values: 'success', 'info', 'warning', 'danger'
		self.session[ 'infomessage' ] = self.session.pop( 'infomessage', [] ) + [[ message_type, message_header, message_body ]]


	def send_email( self, email_address, email_subject, email_body ):
	# Sends an email and displays a message in the browser. If running locally an additional message is displayed in the browser.
		email_sender = "Company no reply <noreply@" + app_identity.get_application_id() + ".appspotmail.com>"
		if enki.libutil.is_debug():
			# display email on page to enable debugging
			result = '<p><b>Sent email</b></p>' +\
						'<p><b>From:</b> ' + email_sender.replace ( '<', '&lt;' ).replace( '>', '&gt;' ) + '</p>' +\
						'<p><b>To:</b> ' + email_address + '</p>' +\
						'<p><b>Subject:</b> ' + email_subject + '</p>' +\
						'<p><b>Body:</b> ' + email_body + '</p>'
			# parse email body for links to list them below as hyperlinks for convenience
			hyperlinks = re.findall( r'https?://\S+', email_body )
			if hyperlinks:
				result += '<p><b>Hyperlinks:</b></p><ul>'
				for link in hyperlinks:
					hyperlink = '<li><p><a href="{!s}">{!s}</a></p></li>'.format( link, link )
					result += hyperlink
				result += '</ul>'
			self.add_debugmessage( result )
		else:
			mail.send_mail( sender = email_sender, to = email_address, subject = email_subject, body = email_body )
			result = ''
		return result


	def email_set_request( self, email ):
	# request the creation of a new account based on an email address
		result = enki.libuser.validate_email( email )
		if result == enki.libutil.ENKILIB_OK :
			if enki.libuser.exist_EnkiUser( email ):
				result = ERROR_EMAIL_IN_USE
			else:
				# create an email verify token, send it to the email address
				token = security.generate_random_string( entropy = 256 )
				emailToken = EnkiModelTokenVerify( token = token, email = email, type = 'register' )
				emailToken.put()
				link = enki.libutil.get_local_url( 'registerconfirm', { 'verifytoken': emailToken.token } )
				self.send_email( email, MSG.SEND_EMAIL_REGISTER_CONFIRM_SUBJECT(), MSG.SEND_EMAIL_REGISTER_CONFIRM_BODY( link ))
				result = enki.libutil.ENKILIB_OK
		return result


	def email_change_request( self, email ):
	# request an email address to be modified. Create a rollback option.
		result = 'cannot_remove'
		emailCurrent = self.enki_user.email
		userId = self.enki_user.key.id()
		if email != '' and enki.libuser.exist_EnkiUser( email ):
			# if the new email matches an existing verified user email, reject it
			if emailCurrent == email:
				result = 'same'
			else:
				result = ERROR_EMAIL_IN_USE # Note: send an email to emailcurrent regardless to prevent email checking (see below)
		else:
			if email == '':
				# if the user erased the email, and they can log in through auth, store "removed" in the email field, so it isn't overwritten by an auth login with a verified email
				if self.enki_user.auth_ids_provider:
					self.enki_user.email = 'removed'
					self.enki_user.put()
					result = 'removed'
				else:
					return result
			else:
				# email the new, unverified address with a link to allow the user to verify the email
				tokenEntity = EnkiModelTokenVerify.get_by_user_id_email_type( userId, email, 'emailchange' )
				if tokenEntity:
					# if a verify token for the same new email address and user already exists, use its token
					token = tokenEntity.token
				else:
					# otherwise create a new token
					token = security.generate_random_string( entropy = 256 )
					emailToken = EnkiModelTokenVerify( token = token, email = email, user_id = userId, type = 'emailchange' )
					emailToken.put()
				link = enki.libutil.get_local_url( 'emailchangeconfirm', { 'verifytoken': token } )
				self.send_email( email, MSG.SEND_EMAIL_EMAIL_CHANGE_CONFIRM_SUBJECT( ), MSG.SEND_EMAIL_EMAIL_CHANGE_CONFIRM_BODY( link, email ))
				result = 'change'
		if emailCurrent and emailCurrent != 'removed' and result != 'same':
			# email the current, verified address in case they want to undo the change (useful if account has been hacked)
			# skip this step if the current email is empty (case if user logged in with auth id without email with e.g. Steam) or "removed".
			# If the email is already in use, mask the fact to prevent email checking.
			tokenEntity = enki.libuser.get_EmailRollbackToken_by_user_id_email( userId, emailCurrent )
			if tokenEntity:
				# if the old email is already in the archive, use its token
				token = tokenEntity.token
			else:
				# otherwise create a new token
				token = security.generate_random_string( entropy = 256 )
				emailOldToken = EnkiModelTokenEmailRollback( token = token, email = emailCurrent, user_id = userId )
				emailOldToken.put()
			if result == ERROR_EMAIL_IN_USE:
				self.add_debugmessage( '''Comment - whether the email is available or not, the feedback through both the UI AND EMAIL is identical to prevent email checking.''' )
			link = enki.libutil.get_local_url( 'emailrollback', { 'rollbacktoken': token } )
			self.send_email( emailCurrent, MSG.SEND_EMAIL_EMAIL_CHANGE_UNDO_SUBJECT(), MSG.SEND_EMAIL_EMAIL_CHANGE_UNDO_BODY( link, emailCurrent ))
		return result


	def email_change( self, token ):
		email = token.email
		user_id = token.user_id
		# change the email
		user = self.set_email( email, user_id )
		if user:
			# delete all potential remaining email verify tokens for that user
			tokens = EnkiModelTokenVerify.fetch_keys_by_user_id_type( user_id, 'emailchange' )
			if tokens:
				ndb.delete_multi( tokens )
			# note: the old email remains saved in the rollback token db
		else:
			# delete the email verification token
			token.key.delete()


	def email_rollback( self, token ):
		email = token.email
		user_id = token.user_id
		# change the email
		user = self.set_email( email, user_id )
		if user:
			# retrieve all rollback tokens that are more recent, including the current one, and delete them
			tokenDateCreated = token.time_created
			youngerTokens = enki.libuser.fetch_keys_RollbackToken_by_time( user_id, tokenDateCreated )
			if youngerTokens:
				ndb.delete_multi( youngerTokens )
			# delete all potential remaining email verify tokens for that user
			userTokens = EnkiModelTokenVerify.fetch_keys_by_user_id_type( user_id, 'emailchange' )
			if userTokens:
				ndb.delete_multi( userTokens )


	def password_change_request( self, email ):
		if enki.libuser.exist_EnkiUser( email ):
		# create an email verify token, send it to the email address
			token = security.generate_random_string( entropy = 256 )
			emailToken = EnkiModelTokenVerify( token = token, email = email, type = 'passwordchange' )
			emailToken.put()
			link = enki.libutil.get_local_url( 'passwordrecoverconfirm', { 'verifytoken': emailToken.token } )
			self.send_email( email, MSG.SEND_EMAIL_PASSWORD_RESET_SUBJECT(), MSG.SEND_EMAIL_PASSWORD_RESET_BODY( link ))
			result = enki.libutil.ENKILIB_OK
		else:
			result = ERROR_EMAIL_NOT_EXIST
		return result


	def create_user_from_email_pw( self, email, password ):
		result = enki.libutil.ENKILIB_OK
		# create a user with the email provided
		user = self.set_email( email )
		if user:
			# set the user's password
			result = enki.libuser.set_password( user, password )
			if result == enki.libutil.ENKILIB_OK:
				# cleanup: delete all verify tokens created when registering the email
				enki.libuser.delete_verifytoken_by_email( email, 'register' )
		else:
			result = ERROR_USER_NOT_CREATED
		return result


	@db.transactional
	def set_email( self, email, user_id = None ):
	# set or change a user's email address
		user_key = enki.libuser.get_key_EnkiUser( email )
		if email and (not user_key or user_key.id() == user_id):
		# if the email doesn't exist in the db or already belongs to the user:
			if user_id == None:
				# create a new user
				user = EnkiModelUser( email = email )
			else:
				# update existing user
				user = ndb.Key( EnkiModelUser, user_id ).get()
				user.email = email
			user.put()
			return user
		else:
			return None


	@db.transactional
	def set_authid( self, authId, user_id ):
		# add a new auth Id to an existing account
		user = ndb.Key( EnkiModelUser, user_id ).get()
		if user:
			# add the authId to the account
			user.auth_ids_provider.append( authId )
			user.put()
			return user
		else:
			return None


	@db.transactional
	def get_or_create_user_from_authid( self, authId, email = None, allow_create = False ):
		user = None
		user_with_same_auth_id = EnkiModelUser.query( EnkiModelUser.auth_ids_provider == authId ).get()
		if user_with_same_auth_id:
			# if a user with the same auth id already exists but has a blank email: add the email to the account.
			# note: if the account has an email, we don't overwrite it.
			if email and user_with_same_auth_id.email == None:
				user = self.set_email( email, user_with_same_auth_id.key.id())
			else:
				user = user_with_same_auth_id
		elif email:
			# no user with the same auth id, but there is a user with the same email: add the auth id to the account
			user_with_same_email = EnkiModelUser.query( EnkiModelUser.email == email ).get()
			if user_with_same_email:
				colon = authId.find( ':' )
				provider_name = str( authId[ :colon ])
				provider_uid = str( authId[ colon+1: ])
				self.send_email( email, MSG.SEND_EMAIL_AUTH_NEW_SUBJECT(), MSG.SEND_EMAIL_AUTH_NEW_BODY( enki.libutil.get_local_url( 'profile' ), provider_name, provider_uid ) )
				user = self.set_authid( authId, user_with_same_email.key.id())
		if not user and allow_create:
			# create a new user
			user = EnkiModelUser( email = email, auth_ids_provider = [ authId ])
			user.put()
		return user


	@db.transactional
	def remove_authid( self, authid_to_remove ):
	# remove an auth Id from a user account
		if self.has_enough_accounts() and ( authid_to_remove in self.enki_user.auth_ids_provider ):
			index = self.enki_user.auth_ids_provider.index( authid_to_remove )
			del self.enki_user.auth_ids_provider[ index ]
			self.enki_user.put()
			return True
		else:
			return False


	def has_enough_accounts( self ):
		# note: if the user only has anemail but no password, they can do a 'forgot password'
		has_email = True if ( self.enki_user.email and self.enki_user.email <> 'removed' ) else False
		has_two_auth_id = True if len( self.enki_user.auth_ids_provider ) > 1 else False
		if has_email or has_two_auth_id:
			return True
		else:
			return False


	def provider_authenticated_callback( self, loginInfo ):
		# We expect the fields of the dictionary to be:
		# - 'provider_name' unique 'pretty' provider name (e.g. google, facebook,...)
		# - 'provider_uid' provider specific (a.k.a "locally unique") user Id, i.e unique to the provider (e.g. the google user id number)
		# - 'email'
		# - 'email_verified'
		# We IGNORE: username, gender (facebook), avatar link, etc.

		# get the verified email from the auth provider
		email = None
		if loginInfo[ 'email' ] and loginInfo[ 'email_verified' ] == True:
			email = loginInfo[ 'email' ]
		# get the authId from the auth provider
		authId = loginInfo[ 'provider_name' ] + ':' + loginInfo[ 'provider_uid' ]

		if authId:
		# modify existing or create user
			user = self.get_or_create_user_from_authid( authId, email, allow_create = False )
			if user:
				self.log_in_session_token_create( user )
				self.add_infomessage( 'success', MSG.SUCCESS( ), MSG.LOGGED_IN())
				self.redirect_to_relevant_page()
			else:
				# generate & store a verification token and the auth provider. save the token number in the session.
				register_token =  EnkiModelTokenVerify.get_by_authid_type( authId, 'register' )
				if register_token:
					# if a token already exists, get the token value and update the email
					token = register_token.token
					register_token.email = email # update in case the user changed their email or modified their email access permission
				else:
					# create a new token
					token = security.generate_random_string( entropy = 256 )
					register_token = EnkiModelTokenVerify( token = token, email = email, auth_ids_provider = authId, type = 'register' )
				register_token.put()
				self.session[ 'tokenregisterauth' ] = token
				self.redirect( enki.libutil.get_local_url( 'registeroauthconfirm' ))
		else:
			self.redirect_to_relevant_page()


	def redirect_to_relevant_page( self ):
		# Redirect user to a previous page after login (& sign up) and logout,
		# but only if they're allowed to be on the page with their new login status and the page is relevant.
		# Otherwise redirect to Home.
		home_page = enki.libutil.get_local_url( )
		redirect_path = home_page
		# retrieve the referrer that's been saved as a session parameter. Otherwise retrieve the request referrer.
		ref_d = self.session.pop( 'sessiondisplaynamerefpath', self.request.referrer ) # note: we should test if these are valid one by one (avoid overwriting a valid value with an invalid one)
		ref = self.session.pop( 'sessionrefpath', ref_d )
		if ref and ref != home_page:
			ref_path = urlparse.urlparse( ref ).path
			# Create the list of pages the user can be sent to (relevant pages)
			relevant_pages = { '/forums', '/store' }
			relevant_paths = { '/f/', '/t/', '/p/' }
			if self.is_logged_in():
				relevant_pages |= { '/profile', '/displayname', '/emailchange', '/passwordchange', '/friends', '/messages' }
				relevant_paths |= { '/u/' }
			# Choose the redirection
			if ( ref_path in relevant_pages ) or any( path in ref_path for path in relevant_paths ):
				redirect_path = ref
		self.redirect( redirect_path )


	@classmethod
	def account_is_active( cls, user_id ):
		# detect activity on a user account
		result = False
		has_friends = True if enki.libfriends.fetch_EnkiFriends_by_user( user_id ) else False
		has_messages = True if enki.libmessage.exist_sent_or_received_message( user_id ) else False
		has_forum_posts = True if enki.libforum.fetch_EnkiPost_by_author( user_id ) else False
		if has_friends or has_messages or has_forum_posts:
			result = True
		return result


	def account_deletion_request( self, delete_posts = False ):
		token_type = 'accountdelete'
		if delete_posts:
			token_type = 'accountandpostsdelete'
		# if the user has an email, create an email verify token, send it to the email address
		tokenEntity = EnkiModelTokenVerify.get_by_user_id_email_type( self.enki_user.key.id( ), self.enki_user.email, token_type )
		if tokenEntity:
			# if a verify token for the same new email address and user already exists, use its token
			token = tokenEntity.token
		else:
			# otherwise create a new token
			token = security.generate_random_string( entropy = 256 )
			delete_account_token = EnkiModelTokenVerify( token = token, user_id = self.enki_user.key.id(), email = self.enki_user.email, type = token_type )
			delete_account_token.put()
			link = enki.libutil.get_local_url( 'accountdeleteconfirm', { 'verifytoken': delete_account_token.token } )
			delete_posts_message = ''
			if delete_posts:
				self.send_email( self.enki_user.email, MSG.SEND_EMAIL_ACCOUT_POSTS_DELETE_SUBJECT(), MSG.SEND_EMAIL_ACCOUT_POSTS_DELETE_BODY( link ))
			else:
				self.send_email( self.enki_user.email, MSG.SEND_EMAIL_ACCOUT_DELETE_SUBJECT(), MSG.SEND_EMAIL_ACCOUT_DELETE_BODY( link ))


	@db.transactional
	def delete_account( self, delete_posts = False, token = '' ):
		token_to_save = 'accountdelete'
		if not token:
			# there is no token if the user has no email address: they are deleted immediately. They must be logged in.
			user = self.enki_user
		else:
			# a user has followed a accountdelete token link. The user account associated with the token will be deleted
			tokenEntity = EnkiModelTokenVerify.get_by_token( token )
			user = EnkiModelUser.get_by_id( tokenEntity.user_id )
			# delete all user related tokens except any verify token related to account deletion that's not yet been used
			if tokenEntity.type == token_to_save:
				token_to_save = 'accountandpostsdelete'
		verify_tokens_to_delete = EnkiModelTokenVerify.fetch_keys_by_user_id_except_type( user.key.id( ), token_to_save )
		if verify_tokens_to_delete:
			ndb.delete_multi( verify_tokens_to_delete )
		email_rollback_tokens_to_delete = enki.libuser.fetch_keys_RollbackToken( user.key.id())
		if email_rollback_tokens_to_delete:
			ndb.delete_multi( email_rollback_tokens_to_delete )
		# Delete the user account and log them out.
		if not HandlerBase.account_is_active( user.key.id()):
			# delete user if the account is inactive
			display_names = enki.libdisplayname.fetch_EnkiUserDisplayName_by_user_id( user.key.id())
			if display_names:
				ndb.delete_multi( display_names )
			user.key.delete()
		else:
			# anonymise the user
			if user.email:
				user.email = None
			if user.password:
				user.password = None
			if user.auth_ids_provider:
				user.auth_ids_provider = []
			user.put()
			# keep all historical display_names. Add a new current display_name '[deleted]' (unless it's already been deleted)
			display_name = enki.libdisplayname.get_EnkiUserDisplayName_by_user_id_current( user.key.id())
			if display_name:
				if display_name.prefix != enki.libdisplayname.DELETED_PREFIX or display_name.suffix != enki.libdisplayname.DELETED_SUFFIX:
					enki.libdisplayname.set_display_name( user.key.id(), enki.libdisplayname.DELETED_PREFIX, enki.libdisplayname.DELETED_SUFFIX )
		# delete user's posts if required
		if delete_posts:
			enki.libforum.delete_user_posts( user.key.id())
		# log the deleted user out
		if self.enki_user == user.key.id():
			self.log_out()
		enki.libuser.revoke_user_authentications( user.key.id())


	def cleanup_item( self ):
		likelyhood = 10 # deletion occurs with a probability of 1%
		number = random.randint( 1, 1000 )
		if number < likelyhood:
			ndb.delete_multi_async ( self.fetch_old_backoff_timers( 3 ))
			ndb.delete_multi_async ( self.fetch_old_auth_tokens( 3 ))
			ndb.delete_multi_async ( self.fetch_old_sessions( 30 ))
			ndb.delete_multi_async ( enki.librestapi.fetch_old_rest_api_connect_tokens( ) )


	def fetch_old_auth_tokens( self, days_old ):
		list = EnkiModelTokenAuth.query( EnkiModelTokenAuth.time_created <= ( datetime.datetime.now() - datetime.timedelta( days = days_old ))).fetch( keys_only = True)
		return list


	def fetch_old_sessions( self, days_old ):
		list = sessions_ndb.Session.query( sessions_ndb.Session.updated <= ( datetime.datetime.now() - datetime.timedelta( days = days_old ))).fetch( keys_only = True)
		return list
