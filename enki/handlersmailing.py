import webapp2

import enki
import enki.libutil
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modelmailing import EnkiModelMailing


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
		if data[ 0 ]:	# is_logged_in
			if submit_type == 'subscribe':
				EnkiModelMailing.add_email_mailing( self.enki_user.email, 'default' )
				self.add_infomessage(MSG.SUCCESS(), MSG.MAILING_SUBSCRIBED('default'))
				data[ 1 ] = True	# has_subscriptions
			elif submit_type == 'unsubscribe':
				EnkiModelMailing.remove_email_mailing( self.enki_user.email, 'default' )
				self.add_infomessage( MSG.SUCCESS(), MSG.MAILING_UNSUBSCRIBED( 'default' ))
				data[ 1 ] = False	# has_subscriptions - ASSUMPTION: ONLY ONE MAILING LIST AVAILABLE
		elif submit_type == 'subscribe_email':
			pass #TODO
		self.render_tmpl( 'mailing.html',
						  active_menu = 'profile',
						  data = data )

	def get_mailing_data( self ):
		is_logged_in = False
		has_subscriptions = False
		has_email = ''
		if self.is_logged_in() and self.enki_user.email:
			is_logged_in = True
			has_subscriptions = EnkiModelMailing.exist_by_email( self.enki_user.email )
			has_email = self.enki_user.email if ( self.enki_user.email != 'removed' ) else ''
		return [ is_logged_in, has_subscriptions, has_email ]


class ExtensionPageMailing( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'incmailing.html' )

	def get_data( self, handler ):
		count_subscriptions = 0
		count_subscriptions = EnkiModelMailing.count_by_email(handler.enki_user.email)
		if handler.is_logged_in() and handler.enki_user.email:
			count_subscriptions = EnkiModelMailing.count_by_email( handler.enki_user.email )
		return count_subscriptions


class ExtensionMailing( Extension ):

	def get_routes( self ):
		return [ webapp2.Route( '/mailing', HandlerMailing, name = 'mailing' )]

	def get_page_extensions( self ):
		return [ ExtensionPageMailing()]
