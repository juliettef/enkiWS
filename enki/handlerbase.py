import datetime
import random
import re
import urlparse
import webapp2
import urllib
import base64

from google.appengine.api import app_identity
from google.appengine.api import mail
from google.appengine.ext import db
from google.appengine.ext import ndb
from google.appengine.api import urlfetch
from jinja2.runtime import TemplateNotFound
from webapp2_extras import i18n
from webapp2_extras import jinja2
from webapp2_extras import security
from webapp2_extras import sessions
from webapp2_extras import sessions_ndb

import settings
import enki
import enki.authcryptcontext
import enki.libutil
import enki.libuser
import enki.modeltokenverify
from enki import textmessages as MSG
from enki.modelbackofftimer import EnkiModelBackoffTimer
from enki.modeltokenauth import EnkiModelTokenAuth
from enki.modeltokenemailrollback import EnkiModelTokenEmailRollback
from enki.modeltokenverify import EnkiModelTokenVerify
from enki.modeluser import EnkiModelUser
from enki.modeldisplayname import EnkiModelDisplayName
from enki.modelfriends import EnkiModelFriends
from enki.modelmessage import EnkiModelMessage
from enki.modelproductkey import EnkiModelProductKey
from enki.modelpost import EnkiModelPost
from enki.modelrestapiconnecttoken import EnkiModelRestAPIConnectToken
from enki.modelrestapidatastore import EnkiModelRestAPIDataStore


ERROR_EMAIL_IN_USE = -13
ERROR_EMAIL_NOT_EXIST = -14
ERROR_USER_NOT_CREATED = -31


class HandlerBase( webapp2.RequestHandler ):


	def __init__( self, request, response ):
		self.initialize( request, response )
		self.just_logged_in = False
		self.just_checked_CSRF = False


	def dispatch( self ):

		if settings.CANONICAL_HOST_URL and settings.CANONICAL_HOST_URL != self.request.host_url and not self.request.headers.get('X-AppEngine-Cron'):
			domain_redirect_URL = settings.CANONICAL_HOST_URL + self.request.path + (
			('?' + self.request.query_string) if self.request.query_string else '')
			self.redirect(domain_redirect_URL, permanent=True)
			return

		self.session_store = sessions.get_store( request = self.request ) # https://webapp-improved.appspot.com/api/webapp2_extras/sessions.html

		if 'locale' in self.request.route_kwargs:
			locale = self.request.route_kwargs.pop('locale')
		else:
			locale = self.session.get('locale')
		if locale ==  'en_US': # default locale
			locale = ''
		elif locale not in settings.LOCALES:
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

	def is_logged_in( self ):
	# returns true if a session exists and corresponds to a logged in user (i.e. a user with a valid auth token)
		# get session info
		if self.just_logged_in:
			return True
		token = self.session.get( 'auth_token' )
		if enki.libuser.exist_AuthToken( self.user_id, token ):
			return True
		else:
			return False

	def ensure_is_logged_in( self ):
	# force the user out if not logged in
		if not self.is_logged_in():
			# get referal path to return the user to it after they've logged in
			self.session[ 'sessionloginrefpath' ] = self.request.url
			self.redirect( enki.libutil.get_local_url( 'login' ))
			return False
		return True

	def ensure_has_display_name( self, url = None ):
	# user must set their display_name to continue
		user_display_name = EnkiModelDisplayName.get_by_user_id_current( self.user_id )
		if not user_display_name:
			if not url:
				url = self.request.url
			# get referal path to return the user to it after they've set their display name
			self.session[ 'sessiondisplaynamerefpath' ] = url
			self.add_infomessage( 'info', MSG.INFORMATION(), MSG.DISPLAYNAME_NEEDED())
			self.redirect( enki.libutil.get_local_url( 'displayname' ))
			return False
		return True


	def get_backoff_timer( self, identifier, increment = False ):
		entity = self.get_backofftimer(identifier)
		if entity:
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

	def reauthenticate( self, email, password ):
	# reauthenticate the user
		if self.get_backoff_timer( email, True ) == 0:
			user = enki.libuser.get_EnkiUser( email )
			if user and user.password:
				validPassword = enki.authcryptcontext.pwd_context.verify( password, user.password )
				if validPassword and self.is_logged_in() and self.user_id == user.key.id():
					self.session[ 'reauth_time' ] = datetime.datetime.now()
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
			token_key = enki.libuser.fetch_keys_AuthToken_by_user_id_token(self.user_id, token)
			if token_key:
				# delete the token from the db
				ndb.delete_multi( token_key )
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
			display_name = EnkiModelDisplayName.get_display_name( self.user_id ) if self.is_logged_in() else ''
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
									deleted_post = EnkiModelPost.POST_DELETED,
									deleted_post_display = MSG.POST_DELETED_DISPLAY(),
									deleted_dn = EnkiModelDisplayName.DELETED_PREFIX + EnkiModelDisplayName.DELETED_SUFFIX,
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

	def debug_output_email( self, email_address, email_subject, email_body ):
	# display email on page to enable debugging
		result = '<p><b>Sent email</b></p>' + \
				 '<p><b>To:</b> ' + email_address + '</p>' + \
				 '<p><b>Subject:</b> ' + email_subject + '</p>' + \
				 '<p><b>Body:</b> ' + email_body + '</p>'
		# parse email body for links to list them below as hyperlinks for convenience
		hyperlinks = re.findall(r'https?://\S+', email_body)
		if hyperlinks:
			result += '<p><b>Hyperlinks:</b></p><ul>'
			for link in hyperlinks:
				hyperlink = '<li><p><a href="{!s}">{!s}</a></p></li>'.format(link, link)
				result += hyperlink
			result += '</ul>'
		self.add_debugmessage(result)

	def send_email( self, email_address, email_subject, email_body ):
		if enki.libutil.is_debug():
			self.debug_output_email( email_address, email_subject, email_body )
			return
		# Sends an email and displays a message in the browser. If running locally an additional message is displayed in the browser.
		if settings.SECRET_API_KEY_MAILGUN:
			# use mailgun to send, this has higher limits than Google App Engine send_mail
			headers = {'Authorization': 'Basic ' + base64.b64encode( 'api:' + settings.SECRET_API_KEY_MAILGUN ) }
			url_mailgun = settings.secrets.URL_API_MAILGUN
			data = { 'from': settings.secrets.NOREPLY_SEND_MAILGUN, 'to': email_address,
					 'subject': email_subject, 'text': email_body }
			form_data = urllib.urlencode( data )
			send_success = True
			try:
				result = urlfetch.fetch(
					url=url_mailgun,
					payload=form_data,
					method=urlfetch.POST,
					headers=headers)
				if result.status_code != 200:
					send_success = False
			except:
				send_success = False
			if send_success:
				return
		# we use app engine email if either we failed to send with mailgun or have no mailgun account
		email_sender = settings.COMPANY_NAME + " no reply <noreply@" + app_identity.get_application_id() + ".appspotmail.com>"
		mail.send_mail( sender = email_sender, to = email_address, subject = email_subject, body = email_body )
		return

	def send_email_admin( self, email_type, email_body ):
	# send email notification to administrators when an event type occurs
		for email_address, email_types in settings.ADMIN_EMAIL_ADDRESSES.iteritems():
			if email_type in email_types:
				self.send_email( email_address, settings.ADMIN_EMAIL_SUBJECT_PREFIX + settings.ADMIN_EMAIL_TYPES[ email_type ], email_body )
		return

	def email_set_request( self, email ):
	# request the creation of a new account based on an email address
		result = enki.libutil.ENKILIB_OK
		if enki.libuser.exist_EnkiUser( email ):
			result = ERROR_EMAIL_IN_USE
		else:
			# create an email verify token, send it to the email address
			token = security.generate_random_string( entropy = 256 )
			emailToken = EnkiModelTokenVerify( token = token, email = email, type = 'register' )
			emailToken.put()
			link = enki.libutil.get_local_url( 'registerconfirm', { 'verifytoken': emailToken.token })
			self.send_email( email, MSG.SEND_EMAIL_REGISTER_CONFIRM_SUBJECT(), MSG.SEND_EMAIL_REGISTER_CONFIRM_BODY( link ))
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
				result = ERROR_EMAIL_IN_USE
				# Note: send an email to emailcurrent regardless to prevent email checking (see below)
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
				link = enki.libutil.get_local_url( 'emailchangeconfirm', { 'verifytoken': token })
				self.send_email( email, MSG.SEND_EMAIL_EMAIL_CHANGE_CONFIRM_SUBJECT(), MSG.SEND_EMAIL_EMAIL_CHANGE_CONFIRM_BODY( link, email ))
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
	def set_auth_id( self, auth_id, user_id ):
	# add a new auth Id to an existing account
		user_has_same_auth_id = enki.libuser.exist_Auth_Id( auth_id )
		if not user_has_same_auth_id:
			user = ndb.Key( EnkiModelUser, user_id ).get()
			if user:
				# add the auth_id to the account
				user.auth_ids_provider.append( auth_id )
				user.put()
				return user
			else:
				return None
		else:
			return None

	def get_user_from_authid( self, auth_id, email = None ):
		user = self.get_or_create_user_from_authid( auth_id = auth_id, email = email, allow_create = False )
		return user

	@db.transactional
	def get_or_create_user_from_authid( self, auth_id, email = None, allow_create = True ):
		user = None
		user_with_same_auth_id = enki.libuser.get_EnkiUser_by_auth_id( auth_id )
		if user_with_same_auth_id:
			# if a user with the same auth id already exists but has a blank email: add the email to the account.
			# note: if the account has an email or they've removed their email, we don't overwrite it.
			if email and user_with_same_auth_id.email == None:
				user = self.set_email( email, user_with_same_auth_id.key.id())
			else:
				user = user_with_same_auth_id
		if not user and allow_create:
			# create a new user
			user = EnkiModelUser( email = email, auth_ids_provider = [ auth_id ])
			user.put()
		return user

	@db.transactional
	def remove_auth_id( self, auth_id_to_remove ):
	# remove an auth Id from a user account
		if self.has_enough_accounts() and ( auth_id_to_remove in self.enki_user.auth_ids_provider ):
			index = self.enki_user.auth_ids_provider.index( auth_id_to_remove )
			del self.enki_user.auth_ids_provider[ index ]
			self.enki_user.put()
			return True
		else:
			return False

	def get_user_auth_providers( self ):
	# get list of the user's OAuth handlers
		user_auth_providers = []
		for user_provider in self.enki_user.auth_ids_provider:
			for auth_provider in settings.HANDLERS:
				if ( auth_provider.get_provider_name() in user_provider ) and ( auth_provider not in user_auth_providers ):
					user_auth_providers.append( auth_provider )
					break
		return user_auth_providers

	def has_enough_accounts( self ):
		# note: if the user only has an email but no password, we don't count it as a valid acocunt (even though they could do a forget password)
		has_email = True if ( self.enki_user.email and self.enki_user.email <> 'removed' and self.enki_user.password ) else False
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
		auth_id = loginInfo[ 'provider_name' ] + ':' + loginInfo[ 'provider_uid' ]

		if auth_id:
			# Modify existing or create user
			# check if it's an add login method request
			LoginAddToken = EnkiModelTokenVerify.get_by_user_id_auth_id_type( user_id = self.user_id, auth_id = loginInfo[ 'provider_name' ], type = 'loginaddconfirm_1' )
			if LoginAddToken:
				# Add a login method
				if not enki.libuser.exist_Auth_Id( auth_id ):
					# store the new auth prov + id in the session
					LoginAddToken.auth_ids_provider = auth_id
					LoginAddToken.type = 'loginaddconfirm_2'
					LoginAddToken.put()
					self.redirect( enki.libutil.get_local_url( 'loginaddconfirm' ))
				else:
					self.add_infomessage( 'info', MSG.INFORMATION(), MSG.AUTH_PROVIDER_CANNOT_BE_ADDED( str( auth_id )))
					self.redirect( enki.libutil.get_local_url( 'accountconnect' ))
				return
			else:
				user = self.get_user_from_authid( auth_id, email )
				if user:
					# Existing authentication method / user
					if self.is_logged_in() and self.user_id == user.key.id():
						# Refresh the reauthenticated status
						self.session[ 'reauth_time' ] = datetime.datetime.now()
						self.add_infomessage( 'success', MSG.SUCCESS(), MSG.REAUTHENTICATED())
						self.redirect_to_relevant_page()
						return
					# Login
					self.log_in_session_token_create( user )
					self.add_infomessage( 'success', MSG.SUCCESS(), MSG.LOGGED_IN())
					self.redirect_to_relevant_page()
				else:
					# New authentication method
					register_token =  EnkiModelTokenVerify.get_by_auth_id_type( auth_id, 'register' )
					if register_token:
						# If a token already exists, get the token value and update the email
						token = register_token.token
						register_token.email = email # update in case the user changed their email or modified their email access permission
					else:
						# Create a new token
						token = security.generate_random_string( entropy = 256 )
						register_token = EnkiModelTokenVerify( token = token, email = email, auth_ids_provider = auth_id, type = 'register' )
					register_token.put()
					self.session[ 'tokenregisterauth' ] = token
					if enki.libuser.exist_EnkiUser( email ):
						self.redirect( enki.libutil.get_local_url( 'registeroauthwithexistingemail' ))
					else:
						self.redirect( enki.libutil.get_local_url( 'registeroauthconfirm' ))
		else:
			self.redirect_to_relevant_page()

	def redirect_to_relevant_page( self, abort = False ):
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
			ref_path = enki.libutil.strip_current_locale_from_path( ref_path )
			# Create the list of pages the user can be sent to (relevant pages)
			relevant_pages = { '/forums', '/store' }
			relevant_paths = { '/f/', '/t/', '/p/' }
			if self.is_logged_in():
				relevant_pages |= { '/profile', '/accountconnect', '/displayname', '/emailchange',
									'/passwordchange', '/friends', '/messages', '/admin/apps',
									'/appdatastores', '/loginaddconfirm', '/accountdelete', '/library',
									'/sessions' }
				# note: '/reauthenticate' not included in relevant_pages as users should only be sent there explicitely
				relevant_paths |= { '/u/' }
			# Choose the redirection
			if ( ref_path in relevant_pages ) or any( path in ref_path for path in relevant_paths ):
				redirect_path = ref
		self.redirect( redirect_path, abort = abort )

	@classmethod
	def account_is_active( cls, user_id ):
	# detect activity on a user account
		result = False
		has_friends = True if EnkiModelFriends.fetch_by_user_id( user_id ) else False
		has_messages = True if EnkiModelMessage.exist_sent_or_received( user_id ) else False
		has_forum_posts = True if EnkiModelPost.fetch_by_author( user_id ) else False
		has_product = True if EnkiModelProductKey.exist_by_purchaser_or_activator( user_id ) else False
		if has_friends or has_messages or has_forum_posts or has_product:
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
			user_to_delete = self.enki_user
		else:
			# a user has followed a accountdelete token link. The user account associated with the token will be deleted
			tokenEntity = EnkiModelTokenVerify.get_by_token( token )
			user_to_delete = EnkiModelUser.get_by_id( tokenEntity.user_id )
			# delete all user related tokens except any verify token related to account deletion that's not yet been used
			if tokenEntity.type == token_to_save:
				token_to_save = 'accountandpostsdelete'
		verify_tokens_to_delete = EnkiModelTokenVerify.fetch_keys_by_user_id_except_type( user_to_delete.key.id(), token_to_save )
		if verify_tokens_to_delete:
			ndb.delete_multi( verify_tokens_to_delete )
		email_rollback_tokens_to_delete = enki.libuser.fetch_keys_RollbackToken( user_to_delete.key.id())
		if email_rollback_tokens_to_delete:
			ndb.delete_multi( email_rollback_tokens_to_delete )
		# Delete the user account and log them out.
		if not HandlerBase.account_is_active( user_to_delete.key.id()):
			# delete user if the account is inactive
			display_names = EnkiModelDisplayName.fetch_keys_by_user_id(user_to_delete.key.id())
			if display_names:
				ndb.delete_multi( display_names )
			user_to_delete.key.delete()
		else:
			# anonymise the user
			if user_to_delete.email:
				user_to_delete.email = None
			if user_to_delete.password:
				user_to_delete.password = None
			if user_to_delete.auth_ids_provider:
				user_to_delete.auth_ids_provider = []
			user_to_delete.put()
			# keep all historical display_names. Add a new current display_name '[deleted]' (unless it's already been deleted)
			display_name = EnkiModelDisplayName.get_by_user_id_current( user_to_delete.key.id())
			if display_name:
				if display_name.prefix != EnkiModelDisplayName.DELETED_PREFIX or display_name.suffix != EnkiModelDisplayName.DELETED_SUFFIX:
					EnkiModelDisplayName.set_display_name( user_to_delete.key.id(), EnkiModelDisplayName.DELETED_PREFIX, EnkiModelDisplayName.DELETED_SUFFIX )
			# delete user's sent and received messages
			EnkiModelMessage.delete_user_messages( user_to_delete.key.id())
			# delete user's posts if required
			if delete_posts:
				EnkiModelPost.delete_user_posts( user_to_delete.key.id())
		# log the deleted user out
		if self.enki_user == user_to_delete.key.id():
			self.log_out()
		enki.libuser.revoke_user_authentications( user_to_delete.key.id())


	def cleanup_item( self ):
		likelihood = 10 # occurs with a probability of 1%
		number = random.randint( 1, 1000 )
		if number < likelihood:
			ndb.delete_multi_async( self.fetch_old_backoff_timers( 3 ))
			ndb.delete_multi_async( self.fetch_old_auth_tokens( 3 ))
			ndb.delete_multi_async( self.fetch_old_sessions( 3 ))
			ndb.delete_multi_async( EnkiModelRestAPIConnectToken.fetch_expired())
			ndb.delete_multi_async( EnkiModelRestAPIDataStore.fetch_expired())
			ndb.delete_multi_async( EnkiModelTokenVerify.fetch_old_tokens_by_types( 0.007, [ 'loginaddconfirm_1', 'loginaddconfirm_2', 'loginaddconfirm_3' ]))
			EnkiModelRestAPIDataStore.refresh_non_expiring()


	def fetch_old_auth_tokens( self, days_old ):
		list = EnkiModelTokenAuth.query( EnkiModelTokenAuth.time_created <= ( datetime.datetime.now() - datetime.timedelta( days = days_old ))).fetch( keys_only = True)
		return list


	def fetch_old_sessions( self, days_old ):
		list = sessions_ndb.Session.query( sessions_ndb.Session.updated <= ( datetime.datetime.now() - datetime.timedelta( days = days_old ))).fetch( keys_only = True)
		return list
