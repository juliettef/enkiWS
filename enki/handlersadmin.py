import webapp2

import enki
import enki.textmessages as MSG
import enki.modelcounter


class HandlerAdmin( enki.HandlerBase ):

	def get( self ):
		counter_downloads_product_a = enki.modelcounter.get_count( 'downloads_product_a' )
		counter_purchases_product_a = enki.modelcounter.get_count( 'purchases_product_a' )
		counter_views_forum = enki.modelcounter.get_count( 'views_forum' )
		self.render_tmpl( 'admin.html',
						  counter_downloads_product_a = counter_downloads_product_a,
						  counter_purchases_product_a = counter_purchases_product_a,
						  counter_views_forum = counter_views_forum, )

	def post( self ):
		pass


routes_admin = [ webapp2.Route( '/admin/admin', HandlerAdmin, name = 'admin' )]
