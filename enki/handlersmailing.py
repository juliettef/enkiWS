import webapp2

from webapp2_extras import security

import enki
import enki.libutil
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modelmailing import EnkiModelMailing
from enki.modelbackofftimer import EnkiModelBackoffTimer
from enki.modeltokenverify import EnkiModelTokenVerify


# mailing list settings for logged in users (not necessarily with display name)
# NOTE - implemented mailing.html for only one 'default' mailing list
class HandlerMailing( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'mailing.html',
						  active_menu = 'profile',
						  data = self.get_mailing_data() )

	def post( self ):
		self.check_CSRF()
		submit_type = self.request.get( 'submittype' )
		data = self.get_mailing_data()
		email = ''
		error_message = ''
		if data[ 0 ]:	# is_logged_in
			if submit_type == 'subscribe':
				EnkiModelMailing.add( self.enki_user.email, 'default' )
				self.add_infomessage( MSG.SUCCESS(), MSG.MAILING_SUBSCRIBED( 'default' ))
				data[ 1 ] = True	# has_subscriptions
			elif submit_type == 'unsubscribe':
				EnkiModelMailing.remove( self.enki_user.email, 'default' )
				self.add_infomessage( MSG.SUCCESS(), MSG.MAILING_UNSUBSCRIBED( 'default' ))
				data[ 1 ] = False	# has_subscriptions - ASSUMPTION: ONLY ONE MAILING LIST AVAILABLE
		elif submit_type == 'subscribeemail':
			email_unsafe = self.request.get( 'email' )
			email, result = self.validate_email( email_unsafe )
			if result == self.ERROR_EMAIL_FORMAT_INVALID:
				error_message = MSG.WRONG_EMAIL_FORMAT()
			elif result == self.ERROR_EMAIL_MISSING:
				error_message = MSG.MISSING_EMAIL()
			elif result == enki.libutil.ENKILIB_OK:
				# email the address with a link to allow the user to confirm their subscription
				tokenEntity = EnkiModelTokenVerify.get_by_email_state_type( email, 'default', 'subscriptionconfirm')
				if tokenEntity:
					# if a verify token for the same new email address and user already exists, use its token
					token = tokenEntity.token
				else:
					# otherwise create a new token
					token = security.generate_random_string(entropy = 256)
					emailToken = EnkiModelTokenVerify( token = token, email = email, state = 'default', type = 'subscriptionconfirm' )
					emailToken.put()
				# TODO add backoff timer
				link = enki.libutil.get_local_url( 'subscriptionconfirm', { 'verifytoken':token })
				self.send_email( email, MSG.SEND_EMAIL_SUBSCRIBE_CONFIRM_SUBJECT(), MSG.SEND_EMAIL_SUBSCRIBE_CONFIRM_BODY( link ))
				self.add_infomessage( MSG.INFORMATION(), MSG.SUBSCRIBE_CONFIRM_EMAIL_SENT( email ))
				self.add_debugmessage( 'Comment - whether the email is available or not, the feedback through the UI is identical to prevent email checking.' )
		self.render_tmpl( 'mailing.html',
						  active_menu = 'profile',
						  data = data,
						  email = email,
						  error = error_message )

	def get_mailing_data( self ):
		is_logged_in = False
		has_subscriptions = False
		has_email = ''
		if self.is_logged_in() and self.enki_user.email:
			is_logged_in = True
			has_subscriptions = EnkiModelMailing.exist_by_email( self.enki_user.email )
			has_email = self.enki_user.email if ( self.enki_user.email != 'removed' ) else ''
		return [ is_logged_in, has_subscriptions, has_email ]


class HandlerSubscriptionConfirm( enki.HandlerBase ):

	def get( self, **kwargs ):
		token = kwargs[ 'verifytoken' ]
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'subscriptionconfirm' )
		if tokenEntity:
			EnkiModelMailing.add( tokenEntity.email, tokenEntity.state )
			self.add_infomessage( MSG.SUCCESS(), MSG.MAILING_SUBSCRIBED( tokenEntity.state ))
			self.redirect(enki.libutil.get_local_url( 'home' ))
			tokenEntity.key.delete()
		else:
			self.abort(404)


class ExtensionPageMailing( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'incmailing.html' )

	def get_data( self, handler ):
		count_subscriptions = 0
		if handler.is_logged_in() and handler.enki_user.email:
			count_subscriptions = EnkiModelMailing.count_by_email( handler.enki_user.email )
		return count_subscriptions


class ExtensionMailing( Extension ):

	def get_routes( self ):
		return [ webapp2.Route( '/mailing', HandlerMailing, name = 'mailing' ),
				 webapp2.Route( '/sc/<verifytoken>', HandlerSubscriptionConfirm, name = 'subscriptionconfirm'),]

	def get_page_extensions( self ):
		return [ ExtensionPageMailing()]
