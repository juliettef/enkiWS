import webapp2
import re

import enki
import enki.textmessages as MSG


class HandlerInfoMessage( enki.HandlerBase ):

	def get( self ):
		# retrieve message code, must be 2 lower case letters
		message = self.request.get( 'm' )
		if message and re.search('[a-z]{2}', message):
			if message == 'dl':
				# enkiDL error
				self.add_infomessage( 'warning', MSG.WARNING(), 'Error retrieving download' )
		self.render_tmpl( 'infomessage.html',
						  active_menu = 'home' )

	def post( self ):
		self.redirect_to_relevant_page()

routes_infomessage = [ webapp2.Route( '/infomessage', HandlerInfoMessage, name = 'infomessage' )]
