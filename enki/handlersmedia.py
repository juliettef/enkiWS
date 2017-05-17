import webapp2

import enki


class HandlerMedia( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'media.html', False, active_menu = 'media' )


routes_media = [ webapp2.Route( '/media', HandlerMedia, name = 'media' )]
