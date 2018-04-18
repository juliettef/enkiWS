import webapp2

from webapp2_extras import security

import enki
import enki.libutil
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modelemailsubscriptions import EnkiModelEmailSubscriptions
from enki.modelbackofftimer import EnkiModelBackoffTimer
from enki.modeltokenverify import EnkiModelTokenVerify


# subscription settings users (users may be unconfirmed, logged in or not)
# NOTE - implemented for only one 'default' newsletter
class HandlerEmailSubscriptions(enki.HandlerBase):

	def get( self ):
		self.render_tmpl( 'emailsubscriptions.html',
						  active_menu = 'profile',
						  data = self.get_email_subscriptions_data())

	def post( self ):
		self.check_CSRF()
		submit_type = self.request.get( 'submittype' )
		data = self.get_email_subscriptions_data()
		email = ''
		error_message = ''
		if data[ 0 ]:	# is_logged_in
			if submit_type == 'subscribe':
				EnkiModelEmailSubscriptions.add( self.enki_user.email, 'default' )
				self.add_infomessage(MSG.SUCCESS(), MSG.EMAIL_SUBSCRIBED('default'))
				data[ 1 ] = True	# has_email_subscriptions
			elif submit_type == 'unsubscribe':
				EnkiModelEmailSubscriptions.remove( self.enki_user.email, 'default' )
				self.add_infomessage(MSG.SUCCESS(), MSG.EMAIL_UNSUBSCRIBED('default'))
				data[ 1 ] = False	# has_email_subscriptions - ASSUMPTION: ONLY ONE NEWSLETTER AVAILABLE
		elif submit_type == 'subscribeemail':
			email_unsafe = self.request.get( 'email' )
			email, result = self.validate_email( email_unsafe )
			if result == self.ERROR_EMAIL_FORMAT_INVALID:
				error_message = MSG.WRONG_EMAIL_FORMAT()
			elif result == self.ERROR_EMAIL_MISSING:
				error_message = MSG.MISSING_EMAIL()
			elif result == enki.libutil.ENKILIB_OK:
				if EnkiModelBackoffTimer.get( 'es:' + email, True ) == 0:
					# email the address with a link to allow the user to confirm their subscription
					tokenEntity = EnkiModelTokenVerify.get_by_email_state_type( email, 'default', 'emailsubscriptionconfirm')
					if tokenEntity:
						# if a verify token for the same new email address and user already exists, use its token
						token = tokenEntity.token
					else:
						# otherwise create a new token
						token = security.generate_random_string( entropy = 256 )
						emailToken = EnkiModelTokenVerify( token = token, email = email, state = 'default', type = 'emailsubscriptionconfirm' )
						emailToken.put()
					link = enki.libutil.get_local_url( 'emailsubscriptionconfirm', { 'verifytoken':token })
					self.send_email( email, MSG.SEND_EMAIL_EMAIL_SUBSCRIBE_CONFIRM_SUBJECT(), MSG.SEND_EMAIL_EMAIL_SUBSCRIBE_CONFIRM_BODY( link, 'default' ))
					self.add_infomessage( MSG.INFORMATION(), MSG.EMAIL_SUBSCRIBE_CONFIRM_EMAIL_SENT( email, 'default' ))
					self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
					email = ''
				else:
					backoff_timer = EnkiModelBackoffTimer.get( 'es:' + email )
					if backoff_timer != 0:
						error_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ))
		self.render_tmpl( 'emailsubscriptions.html',
							  active_menu = 'profile',
							  data = data,
							  email = email,
							  error = error_message )

	def get_email_subscriptions_data( self ):
		is_logged_in = False
		has_email_subscriptions = False
		has_email = ''
		if self.is_logged_in() and self.enki_user.email:
			is_logged_in = True
			has_email_subscriptions = EnkiModelEmailSubscriptions.exist_by_email( self.enki_user.email )
			has_email = self.enki_user.email if ( self.enki_user.email != 'removed' ) else ''
		return [ is_logged_in, has_email_subscriptions, has_email ]


class HandlerEmailSubscriptionConfirm( enki.HandlerBase ):

	def get( self, **kwargs ):
		token = kwargs[ 'verifytoken' ]
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'emailsubscriptionconfirm' )
		if tokenEntity:
			EnkiModelBackoffTimer.remove( 'es:' + tokenEntity.email )
			EnkiModelEmailSubscriptions.add( tokenEntity.email, tokenEntity.state )
			self.add_infomessage(MSG.SUCCESS(), MSG.EMAIL_SUBSCRIBED(tokenEntity.state))
			self.redirect( enki.libutil.get_local_url( 'home' ))
			tokenEntity.key.delete()
		else:
			self.abort(404)


class ExtensionPageEmailSubscriptions(ExtensionPage):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'incemailsubscriptions.html' )

	def get_data( self, handler ):
		count_email_subscriptions = 0
		if handler.is_logged_in() and handler.enki_user.email:
			count_email_subscriptions = EnkiModelEmailSubscriptions.count_by_email( handler.enki_user.email )
		return count_email_subscriptions


class ExtensionEmailSubscriptions(Extension):

	def get_routes( self ):
		return [ webapp2.Route( '/emailsubscriptions', HandlerEmailSubscriptions, name = 'emailsubscriptions'),
				 webapp2.Route( '/es/<verifytoken>', HandlerEmailSubscriptionConfirm, name = 'emailsubscriptionconfirm'),]

	def get_page_extensions( self ):
		return [ ExtensionPageEmailSubscriptions() ]
