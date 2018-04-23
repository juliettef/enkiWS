import webapp2
import base64

from google.appengine.api import app_identity
from google.appengine.api import mail
from google.appengine.api import urlfetch
from webapp2_extras import security

import settings
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
				# delete eventual verification tokens for this email and newsletter
				tokenEntity = EnkiModelTokenVerify.get_by_email_state_type( self.enki_user.email, settings.email_newsletter_name[ 0 ],'emailsubscriptionconfirm' )
				if tokenEntity:
					tokenEntity.key.delete()
				EnkiModelEmailSubscriptions.add_newsletter( self.enki_user.email, settings.email_newsletter_name[ 0 ])
				self.add_infomessage( MSG.SUCCESS(), MSG.EMAIL_SUBSCRIBED( settings.email_newsletter_name[ 0 ]))
				data[ 1 ] = True	# has_email_subscriptions
			elif submit_type == 'unsubscribe':
				EnkiModelEmailSubscriptions.remove_newsletter_by_email( self.enki_user.email, settings.email_newsletter_name[ 0 ])
				self.add_infomessage( MSG.SUCCESS(), MSG.EMAIL_UNSUBSCRIBED( settings.email_newsletter_name[ 0 ]))
				data[ 1 ] = False	# has_email_subscriptions - ASSUMPTION: ONLY ONE NEWSLETTER AVAILABLE
		if submit_type == 'subscribeemail':
			email_unsafe = self.request.get( 'email' )
			email, result = self.validate_email( email_unsafe )
			if result == self.ERROR_EMAIL_FORMAT_INVALID:
				error_message = MSG.WRONG_EMAIL_FORMAT()
			elif result == self.ERROR_EMAIL_MISSING:
				error_message = MSG.MISSING_EMAIL()
			elif result == enki.libutil.ENKILIB_OK:
				if EnkiModelBackoffTimer.get( 'es:' + email, True ) == 0:
					if not EnkiModelEmailSubscriptions.exist_by_email_newsletter( email, settings.email_newsletter_name[ 0 ]):
						# if not already subscribed, create a token and send email with a link to allow the user to confirm their subscription
						if not EnkiModelTokenVerify.get_by_email_state_type( email, settings.email_newsletter_name[ 0 ], 'emailsubscriptionconfirm'):
							# if a verify token already exists, skip as an email was already sent.
							token = security.generate_random_string( entropy = 256 )
							emailToken = EnkiModelTokenVerify( token = token, email = email, state = settings.email_newsletter_name[ 0 ], type = 'emailsubscriptionconfirm' )
							emailToken.put()
							link = enki.libutil.get_local_url( 'emailsubscriptionconfirm', { 'verifytoken':token })
							self.send_email( email, MSG.SEND_EMAIL_EMAIL_SUBSCRIBE_CONFIRM_SUBJECT(), MSG.SEND_EMAIL_EMAIL_SUBSCRIBE_CONFIRM_BODY( link, settings.email_newsletter_name[ 0 ]))
					self.add_infomessage( MSG.INFORMATION(), MSG.EMAIL_SUBSCRIBE_CONFIRM_EMAIL_SENT( email, settings.email_newsletter_name[ 0 ]))
					self.add_debugmessage( 'Comment - whether the email is sent or not, the feedback through the UI is identical to prevent email checking.' )
					email = ''
				else:
					backoff_timer = EnkiModelBackoffTimer.get( 'es:' + email )
					if backoff_timer != 0:
						error_message = MSG.TIMEOUT( enki.libutil.format_timedelta( backoff_timer ))
		if data[ 0 ]:	# is_logged_in
			self.redirect(enki.libutil.get_local_url('profile'))
		else:
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
			has_email = self.enki_user.email if ( self.enki_user.email != 'removed' ) else ''
			if has_email:
				has_email_subscriptions = True if EnkiModelEmailSubscriptions.count_newsletters_by_email( self.enki_user.email ) else False
		return [ is_logged_in, has_email_subscriptions, has_email ]


class HandlerEmailSubscriptionConfirm( enki.HandlerBase ):

	def get( self, **kwargs ):
		token = kwargs[ 'verifytoken' ]
		tokenEntity = EnkiModelTokenVerify.get_by_token_type( token, 'emailsubscriptionconfirm' )
		if tokenEntity:
			EnkiModelBackoffTimer.remove( 'es:' + tokenEntity.email )
			EnkiModelEmailSubscriptions.add_newsletter( tokenEntity.email, tokenEntity.state )
			self.add_infomessage( MSG.SUCCESS(), MSG.EMAIL_SUBSCRIBED( tokenEntity.state ))
			self.redirect( enki.libutil.get_local_url( 'home' ))
			tokenEntity.key.delete()
		else:
			self.abort(404)


class HandlerEmailBatchSending( enki.HandlerBase ):

	def get( self ):
		default_newsletter = settings.email_newsletter_name[ 0 ]
		default_subject = settings.email_newsletter_name[ 0 ] + ' newsletter - <subject>'
		default_body_text = 'Hello,\n\n<your text>'
		self.render_tmpl( 'emailbatchsending.html',
						  newsletter = default_newsletter,
						  subject = default_subject,
						  body_text = default_body_text,
						  footer = self.get_email_footer_template())

	def post( self ):
		self.check_CSRF()
		newsletter = self.request.get( 'newsletter' )
		subject = self.request.get( 'subject' )
		body_text = self.request.get( 'body_text' )
		footer_template = self.get_email_footer_template()
		batches_emails, batches_emails_recipient_variables = EnkiModelEmailSubscriptions.get_mailgun_email_batches( newsletter )
		for batch_emails, batch_emails_recipient_variables in zip( batches_emails, batches_emails_recipient_variables ):
			self.send_mailgun_batch_email( batch_emails, subject, body_text, footer_template, batch_emails_recipient_variables )
		self.add_infomessage( MSG.SUCCESS(), 'Batch email sent' )
		self.render_tmpl( 'emailbatchsending.html',
						  newsletter = newsletter,
						  subject = subject,
						  body_text = body_text,
						  footer = footer_template )

	def get_email_footer_template( self, newsletter = '' ):
		return ( "{unsubscribe from newsletter}{unsubscribe from all}{contact us}" )	# TODO


	def send_mailgun_batch_email( self, email_addresses, email_subject, email_body, email_footer_template, recipient_variables ):
		if enki.libutil.is_debug():
			self.debug_output_email(( "Batch of " + str( len( email_addresses )) + " email addresses" ), email_subject, email_body + email_footer_template )
			return
		# Sends an email and displays a message in the browser. If running locally an additional message is displayed in the browser.
		if settings.SECRET_API_KEY_MAILGUN:
			# use mailgun to send, this has higher limits than Google App Engine send_mail
			headers = { 'Authorization' : 'Basic ' + base64.b64encode( 'api:' + settings.SECRET_API_KEY_MAILGUN )}
			url_mailgun = settings.secrets.URL_API_MAILGUN
			data = { 'from' : settings.secrets.NOREPLY_SEND_MAILGUN,
					 'to' : email_addresses,
					 'subject' : email_subject,
					 'text' : email_body + email_footer_template,
					 'recipient-variables' : recipient_variables }
			form_data = enki.libutil.urlencode( data )
			send_success = True
			try:
				result = urlfetch.fetch( url=url_mailgun,
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
		mail.send_mail( sender = email_sender,
						to = ( str( len( email_addresses )) + " email addresses" ),
						subject = email_subject,
						body = email_body + email_footer_template )
		return

class ExtensionPageEmailSubscriptions(ExtensionPage):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'incemailsubscriptions.html' )

	def get_data( self, handler ):
		count_email_subscriptions = 0
		if handler.is_logged_in() and handler.enki_user.email and handler.enki_user.email != 'removed':
			count_email_subscriptions = EnkiModelEmailSubscriptions.count_newsletters_by_email( handler.enki_user.email )
		return count_email_subscriptions


class ExtensionPageEmailSubscriptionsLink(ExtensionPage):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'navbar', template_include = 'incemailsubscriptionslink.html' )


class ExtensionEmailSubscriptions(Extension):

	def get_routes( self ):
		return [ webapp2.Route( '/emailsubscriptions', HandlerEmailSubscriptions, name = 'emailsubscriptions' ),
				 webapp2.Route( '/es/<verifytoken>', HandlerEmailSubscriptionConfirm, name = 'emailsubscriptionconfirm' ),
				 webapp2.Route( '/admin/emailbatchsending', HandlerEmailBatchSending, name = 'emailbatchsending' ),
				 ]

	def get_page_extensions( self ):
		return [ ExtensionPageEmailSubscriptions(), ExtensionPageEmailSubscriptionsLink() ]
