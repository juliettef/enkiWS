import webapp2
import re

import enki
import enki.textmessages as MSG


class HandlerInfo( enki.HandlerBase ):

	def get( self ):
		# retrieve optional message code - must be 2 lower case letters
		message = self.request.get( 'm' )
		if message and re.search('[a-z]{2}', message):
			if message == 'dl':
				# enkiDL error
				self.add_infomessage( MSG.WARNING(), MSG.DOWNLOAD_ERROR())
		self.render_tmpl( 'info.html' )

	def post( self ):
		self.redirect_to_relevant_page()


routes_info = [ webapp2.Route( '/info', HandlerInfo, name = 'info' )]
