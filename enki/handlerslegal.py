import webapp2

import enki


class HandlerLegalTerms( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'terms.html', False )


class HandlerLegalPrivacy( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'privacy.html', False )


routes_legal = [ webapp2.Route( '/terms', HandlerLegalTerms, name = 'terms' ),
				 webapp2.Route( '/privacy', HandlerLegalPrivacy, name = 'privacy' ),
				 ]
