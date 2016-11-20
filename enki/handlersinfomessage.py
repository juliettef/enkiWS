import webapp2

import enki
import enki.textmessages as MSG


# ------
# Requires enkiDL
class HandlerEnkiDLError( enki.HandlerBase ):

	def get( self ):
		self.add_infomessage( 'warning', MSG.WARNING(), 'Error retrieving download' )
		self.redirect_to_relevant_page()
# -------


routes_infomessage = [ webapp2.Route( '/enkidlerror', HandlerEnkiDLError, name = 'enkidlerror' )]
