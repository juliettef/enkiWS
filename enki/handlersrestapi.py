import webapp2_extras.security

from enki.extensions import Extension
from enki.extensions import ExtensionPage


def generate_connection_token():
	code = webapp2_extras.security.generate_random_string( length = 5, pool = webapp2_extras.security.UPPERCASE_ALPHANUMERIC )
	return code


class ExtensionPageRestAPI( ExtensionPage ):

	def __init__( self ):
		ExtensionPage.__init__( self, route_name = 'profile', template_include = 'increstapi.html' )

	def get_data( self, handler ):
		if handler.ensure_is_logged_in():
			data = [ generate_connection_token()]
			return data


class ExtensionRestAPI( Extension ):

	def get_page_extensions( self ):
		return [ ExtensionPageRestAPI()]
