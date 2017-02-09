import webapp2

import enki
import enki.libutil
import enki.libstore
import enki.modelcounter
from enki.modelsummary import EnkiModelSummary


class HandlerAdmin( enki.HandlerBase ):

	def get( self ):
		self.render_tmpl( 'admin.html',
							counter_downloads_product_a = enki.modelcounter.get_count( 'downloads_product_a' ),
							counter_purchases_product_a = enki.modelcounter.get_count( 'purchases_product_a' ),
							counter_views_forum = enki.modelcounter.get_count( 'views_forum' ),
							counter_licence_keys_fastspring_purchase_not_activated = enki.libstore.count_licence_keys( 'FastSpring', 'purchase', False ),
							counter_licence_keys_fastspring_purchase_activated = enki.libstore.count_licence_keys( 'FastSpring', 'purchase', True ),
							counter_licence_keys_generator_freegift_not_activated = enki.libstore.count_licence_keys( 'Generator', 'free-gift', False ),
							counter_licence_keys_generator_freegift_activated = enki.libstore.count_licence_keys( 'Generator', 'free-gift', True ),
							counter_licence_keys_generator_freepress_not_activated = enki.libstore.count_licence_keys( 'Generator', 'free-press', False ),
							counter_licence_keys_generator_freepress_activated = enki.libstore.count_licence_keys( 'Generator', 'free-press', True ),
							counter_licence_keys_generator_freepromo_not_activated = enki.libstore.count_licence_keys( 'Generator', 'free-promo', False ),
							counter_licence_keys_generator_freepromo_activated = enki.libstore.count_licence_keys( 'Generator', 'free-promo', True ),
						)


class HandlerSummary( enki.HandlerBase ):

	def get( self ):
		test = enki.libutil.is_debug()
		if self.request.headers.get( 'X-AppEngine-Cron' ) or enki.libutil.is_debug():
			counters_from_modelcounter = [ 'downloads_product_a', 'purchases_product_a', 'views_forum' ]
			for item in counters_from_modelcounter:
				EnkiModelSummary.create( item, enki.modelcounter.get_count( item ))
			EnkiModelSummary.create( 'lic_fs_purch_not_act', enki.libstore.count_licence_keys( 'FastSpring', 'purchase', False ))
			EnkiModelSummary.create( 'lic_fs_purch_act', enki.libstore.count_licence_keys( 'FastSpring', 'purchase', True ))
			EnkiModelSummary.create( 'lic_gen_gift_not_act', enki.libstore.count_licence_keys( 'Generator', 'free-gift', False ))
			EnkiModelSummary.create( 'lic_gen_gift_act', enki.libstore.count_licence_keys( 'Generator', 'free-gift', True ))
			EnkiModelSummary.create( 'lic_gen_press_not_act', enki.libstore.count_licence_keys( 'Generator', 'free-press', False ))
			EnkiModelSummary.create( 'lic_gen_press_act', enki.libstore.count_licence_keys( 'Generator', 'free-press', True ))
			EnkiModelSummary.create( 'lic_gen_promo_not_act', enki.libstore.count_licence_keys( 'Generator', 'free-promo', False ))
			EnkiModelSummary.create( 'lic_gen_promo_act', enki.libstore.count_licence_keys( 'Generator', 'free-promo', True ))
			self.response.status = 200
		else:
			self.error( 403 )


routes_admin = [ webapp2.Route( '/admin/admin', HandlerAdmin, name = 'admin' ),
				 webapp2.Route( '/admin/summary', HandlerSummary, name = 'summary') ]
