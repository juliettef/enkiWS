import webapp2

import enki
import enki.libutil
import enki.modelcounter
from enki.modelsummary import EnkiModelSummary


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


class HandlerSummary( enki.HandlerBase ):

	def get( self ):
		test = enki.libutil.is_debug()
		if self.request.headers.get( 'X-AppEngine-Cron' ) or enki.libutil.is_debug():
			EnkiModelSummary.create( 'downloads_product_a' )
			EnkiModelSummary.create( 'purchases_product_a' )
			EnkiModelSummary.create( 'views_forum' )
			self.response.status = 200
		else:
			self.error( 403 )


routes_admin = [ webapp2.Route( '/admin/admin', HandlerAdmin, name = 'admin' ),
				 webapp2.Route( '/admin/summary', HandlerSummary, name = 'summary') ]
