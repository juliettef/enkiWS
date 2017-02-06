import webapp2

import enki


class HandlerStaticTerms( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'terms.html', False )


class HandlerStaticPrivacy( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'privacy.html', False )


routes_static = [ webapp2.Route( '/terms', HandlerStaticTerms, name = 'terms' ),
				  webapp2.Route( '/privacy', HandlerStaticPrivacy, name = 'privacy' ),
				 ]
