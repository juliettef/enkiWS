import webapp2

import enki
import enki.libutil
import enki.textmessages as MSG

from enki.extensions import Extension
from enki.extensions import ExtensionPage
from enki.modelmailing import EnkiModelMailing


# mailing list settings for logged in users (not necessarily with display name)
class HandlerMailing( enki.HandlerBase ):

	def get( self ):
		return 0

	def post( self ):
		return 0


class ExtensionPageMailing( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'incmailing.html' )


class ExtensionMailing( Extension ):

	def get_routes( self ):
		return [ webapp2.Route( '/mailing', HandlerMailing, name = 'mailing' )]

	def get_page_extensions( self ):
		return [ ExtensionPageMailing()]
